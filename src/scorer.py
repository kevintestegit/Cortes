import cv2
import numpy as np
from dataclasses import dataclass
from typing import List
from .scene_detector import SceneCandidate, VideoInfo
from .utils import cleanup_temp_files, make_ffmpeg_safe_file, run_command, logger
import re

@dataclass
class ScoredCandidate:
    candidate: SceneCandidate
    score: float
    reason: str
    motion_score: float
    audio_score: float
    brightness: float

def analyze_segment(video_path: str, start: float, end: float, video_info: VideoInfo) -> dict:
    """Analyze a specific segment of the video for motion, brightness, and audio."""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    
    frames_to_read = int((end - start) * 2) # Read at 2 fps
    skip_frames = int(video_info.fps / 2) if video_info.fps > 0 else 15
    
    prev_gray = None
    motion_scores = []
    brightness_scores = []
    
    for _ in range(frames_to_read):
        ret, frame = cap.read()
        if not ret:
            break
            
        # Resize for faster processing
        small = cv2.resize(frame, (320, 180))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Brightness
        brightness = np.mean(gray)
        brightness_scores.append(brightness)
        
        # Motion
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            motion = np.mean(diff)
            motion_scores.append(motion)
            
        prev_gray = gray
        
        # Skip frames
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + skip_frames - 1)
        
    cap.release()
    
    avg_motion = float(np.mean(motion_scores)) if motion_scores else 0.0
    avg_brightness = float(np.mean(brightness_scores)) if brightness_scores else 0.0
    
    # Audio volume check using ffmpeg
    temp_files = []
    ffmpeg_video_path = make_ffmpeg_safe_file(video_path, temp_files)
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", str(end - start),
        "-i", ffmpeg_video_path, "-af", "volumedetect", "-vn", "-sn", "-f", "null", "-"
    ]
    # ffmpeg outputs volumedetect to stderr
    res = run_command(cmd, check=False)
    cleanup_temp_files(temp_files)
    
    # Extract max_volume from stderr: e.g. "max_volume: -2.3 dB"
    max_vol = -50.0
    match = re.search(r"max_volume:\s+([-\d\.]+)\s+dB", res.stderr)
    if match:
        max_vol = float(match.group(1))
        
    return {
        "motion": avg_motion,
        "brightness": avg_brightness,
        "audio_max_db": max_vol
    }

def score_candidates(video_path: str, candidates: List[SceneCandidate], video_info: VideoInfo) -> List[ScoredCandidate]:
    logger.info(f"Scoring {len(candidates)} candidates. This may take a while...")
    
    scored = []
    # To save time, we might only evaluate a subset if there are hundreds, but let's evaluate all for MVP
    # or just sort them by some heuristic if there are too many. Let's limit to 50 random or evenly spaced candidates if > 50
    
    if len(candidates) > 50:
        logger.info("Too many candidates, selecting a representative sample of 50 to score...")
        step = len(candidates) / 50
        candidates = [candidates[int(i * step)] for i in range(50)]
        
    for i, cand in enumerate(candidates):
        stats = analyze_segment(video_path, cand.start_time, cand.end_time, video_info)
        
        score = 0.0
        reasons = []
        
        # 1. Motion
        motion = stats["motion"]
        if motion > 15:
            score += 3
            reasons.append("high motion")
        elif motion > 5:
            score += 1
            reasons.append("moderate motion")
        else:
            score -= 2 # Penalize static
            
        # 2. Audio
        audio_db = stats["audio_max_db"]
        if audio_db > -3:
            score += 3
            reasons.append("audio peak")
        elif audio_db > -10:
            score += 1
            reasons.append("good audio")
        elif audio_db < -30:
            score -= 3 # Too quiet
            reasons.append("too quiet")
            
        # 3. Brightness (avoid black screens)
        brightness = stats["brightness"]
        if brightness < 15:
            score -= 5 # Almost black
            reasons.append("dark/black screen")
            
        # 4. Intro/Outro penalty
        if cand.start_time < video_info.duration * 0.05:
            score -= 2
            reasons.append("intro")
        elif cand.end_time > video_info.duration * 0.95:
            score -= 2
            reasons.append("outro")
            
        # 5. Duration preference (prefer around 25-35 seconds)
        if 25 <= cand.duration <= 35:
            score += 1
            reasons.append("ideal duration")
            
        # Normalize score a bit (0 to 10 scale approx)
        final_score = max(0.0, min(10.0, 5 + score))
        
        reason_str = " + ".join(reasons) if reasons else "average"
        
        scored.append(ScoredCandidate(
            candidate=cand,
            score=final_score,
            reason=reason_str,
            motion_score=motion,
            audio_score=audio_db,
            brightness=brightness
        ))
        
        if (i + 1) % 10 == 0:
            logger.info(f"Scored {i + 1}/{len(candidates)}")
            
    # Sort by score descending
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored

def filter_overlapping(scored_candidates: List[ScoredCandidate], max_shorts: int) -> List[ScoredCandidate]:
    """Remove candidates that overlap significantly with higher-scored ones."""
    selected = []
    for cand in scored_candidates:
        if len(selected) >= max_shorts:
            break
            
        overlap = False
        for sel in selected:
            # Check overlap
            start1, end1 = cand.candidate.start_time, cand.candidate.end_time
            start2, end2 = sel.candidate.start_time, sel.candidate.end_time
            
            # If intersection > 30% of candidate's duration, consider it overlapping
            latest_start = max(start1, start2)
            earliest_end = min(end1, end2)
            intersection = max(0, earliest_end - latest_start)
            
            if intersection > (end1 - start1) * 0.3:
                overlap = True
                break
                
        if not overlap:
            selected.append(cand)
            
    return selected
