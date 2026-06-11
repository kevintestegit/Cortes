import json
from dataclasses import dataclass
from scenedetect import detect, ContentDetector
import cv2
from .utils import run_command, logger

@dataclass
class VideoInfo:
    duration: float
    width: int
    height: int
    fps: float

@dataclass
class SceneCandidate:
    start_time: float
    end_time: float
    duration: float
    scenes_included: int

def get_video_info(video_path: str) -> VideoInfo:
    logger.info(f"Extracting video info from {video_path}...")
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-of", "json", video_path
    ]
    result = run_command(cmd)
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    
    # Calculate FPS from fraction
    fps_str = stream.get("r_frame_rate", "30/1")
    num, den = map(int, fps_str.split('/'))
    fps = num / den if den > 0 else 30.0
    
    # Fallback duration if missing
    duration = float(stream.get("duration", 0))
    if duration == 0:
        cmd_format = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", video_path
        ]
        res2 = run_command(cmd_format)
        d2 = json.loads(res2.stdout)
        duration = float(d2["format"].get("duration", 0))
        
    return VideoInfo(
        duration=duration,
        width=int(stream.get("width", 1920)),
        height=int(stream.get("height", 1080)),
        fps=fps
    )

def detect_scenes(video_path: str) -> list[tuple[float, float]]:
    """Detect scenes in the video using PySceneDetect. Returns list of (start_time, end_time) in seconds."""
    logger.info("Detecting scenes...")
    scene_list = detect(video_path, ContentDetector(threshold=27.0))
    scenes = []
    for scene in scene_list:
        scenes.append((scene[0].get_seconds(), scene[1].get_seconds()))
    logger.info(f"Detected {len(scenes)} scenes.")
    return scenes

def generate_candidates(scenes: list[tuple[float, float]], min_dur: int, max_dur: int) -> list[SceneCandidate]:
    """Group consecutive scenes to form candidates within the duration bounds."""
    logger.info("Generating candidates from scenes...")
    candidates = []
    
    for i in range(len(scenes)):
        current_start = scenes[i][0]
        current_end = scenes[i][1]
        
        # Single scene candidate?
        if min_dur <= (current_end - current_start) <= max_dur:
            candidates.append(SceneCandidate(current_start, current_end, current_end - current_start, 1))
            
        # Group with next scenes
        for j in range(i + 1, len(scenes)):
            current_end = scenes[j][1]
            duration = current_end - current_start
            
            if duration > max_dur:
                break # Too long
                
            if duration >= min_dur:
                candidates.append(SceneCandidate(current_start, current_end, duration, j - i + 1))
                
    logger.info(f"Generated {len(candidates)} valid candidates.")
    return candidates
