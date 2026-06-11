import os
import hashlib
import shutil
from typing import List, Optional

from .scorer import ScoredCandidate
from .utils import logger, run_command
from .watermark_detector import WatermarkRegion

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
PARROT_HEIGHT_RATIO = 0.30
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".aac", ".m4a", ".ogg", ".flac"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def find_reaction_videos(parrot_dir: str) -> list[str]:
    candidate_dirs = [parrot_dir]
    if parrot_dir == "downloads/youtube":
        candidate_dirs.append("dowloads/youtube")

    for directory in candidate_dirs:
        if not directory or not os.path.isdir(directory):
            continue

        videos = []
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            ext = os.path.splitext(name)[1].lower()
            if os.path.isfile(path) and ext in VIDEO_EXTENSIONS:
                videos.append(path)

        if videos:
            return sorted(videos)

    return []


def has_audio_stream(video_path: str) -> bool:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        video_path,
    ]
    res = run_command(cmd, check=False)
    return res.returncode == 0 and bool(res.stdout.strip())


def is_valid_png(path: str) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) < len(PNG_SIGNATURE):
        return False
    try:
        with open(path, "rb") as f:
            return f.read(len(PNG_SIGNATURE)) == PNG_SIGNATURE
    except OSError:
        return False


def is_valid_video_output(path: str) -> bool:
    if not os.path.exists(path) or os.path.getsize(path) < 1024:
        return False

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "default=noprint_wrappers=1",
        path,
    ]
    res = run_command(cmd, check=False)
    return res.returncode == 0 and "width=" in res.stdout and "duration=" in res.stdout


def needs_ascii_alias(path: str) -> bool:
    try:
        os.fspath(path).encode("ascii")
        return False
    except UnicodeEncodeError:
        return True


def make_ffmpeg_safe_file(path: str, temp_files: list[str]) -> str:
    if not needs_ascii_alias(path):
        return path

    abs_path = os.path.abspath(path)
    ext = os.path.splitext(abs_path)[1] or ".bin"
    digest = hashlib.sha1(abs_path.encode("utf-8", errors="replace")).hexdigest()[:12]
    temp_dir = os.path.abspath(os.path.join("output", "temp_ffmpeg_paths"))
    os.makedirs(temp_dir, exist_ok=True)
    alias_path = os.path.join(temp_dir, f"input_{digest}{ext}")

    if os.path.exists(alias_path):
        temp_files.append(alias_path)
        return alias_path

    try:
        os.link(abs_path, alias_path)
    except OSError:
        shutil.copy2(abs_path, alias_path)

    temp_files.append(alias_path)
    logger.info(f"Using ASCII-safe FFmpeg alias for unicode path: {alias_path}")
    return alias_path


def cleanup_temp_files(paths: list[str]) -> None:
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def build_scene_switches(
    scene_ranges: list[tuple[float, float]],
    start_time: float,
    end_time: float,
) -> list[float]:
    switches = []
    for scene_start, _ in scene_ranges:
        if start_time + 0.35 < scene_start < end_time - 0.35:
            switches.append(round(scene_start - start_time, 3))
    return switches


def _append_watermark_filters(
    filter_parts: list[str],
    watermark_regions: Optional[List[WatermarkRegion]],
) -> str:
    current_in = "[0:v]"
    for i, reg in enumerate(watermark_regions or []):
        wm_tag = f"wm{i}"
        blur_tag = f"wm{i}b"
        out_tag = f"cln{i}"
        filter_parts.append(f"{current_in}crop={reg.width}:{reg.height}:{reg.x}:{reg.y}[{wm_tag}]")
        filter_parts.append(f"[{wm_tag}]boxblur=15:5[{blur_tag}]")
        filter_parts.append(f"{current_in}[{blur_tag}]overlay={reg.x}:{reg.y}[{out_tag}]")
        current_in = f"[{out_tag}]"
    return current_in


def _append_vertical_video_filters(
    filter_parts: list[str],
    current_in: str,
    reaction_input_index: Optional[int],
) -> str:
    if reaction_input_index is None:
        filter_parts.append(f"{current_in}split[v1][v2]")
        filter_parts.append(
            f"[v1]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},boxblur=20:20[bg]"
        )
        filter_parts.append(f"[v2]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease[fg]")
        filter_parts.append("[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2,setsar=1[main_v]")
        return "[main_v]"

    parrot_height = int(OUTPUT_HEIGHT * PARROT_HEIGHT_RATIO)
    main_height = OUTPUT_HEIGHT - parrot_height

    filter_parts.append(f"{current_in}split[bgsrc][fgsrc]")
    filter_parts.append(
        f"[bgsrc]scale={OUTPUT_WIDTH}:{main_height}:force_original_aspect_ratio=increase,"
        f"crop={OUTPUT_WIDTH}:{main_height},boxblur=20:20[topbg]"
    )
    filter_parts.append(f"[fgsrc]scale={OUTPUT_WIDTH}:{main_height}:force_original_aspect_ratio=decrease[fg]")
    filter_parts.append("[topbg][fg]overlay=x=(W-w)/2:y=(H-h)/2[topv]")
    filter_parts.append(
        f"[{reaction_input_index}:v]scale={OUTPUT_WIDTH}:{parrot_height}:force_original_aspect_ratio=increase,"
        f"crop={OUTPUT_WIDTH}:{parrot_height},setsar=1[reactv]"
    )
    filter_parts.append("[topv][reactv]vstack=inputs=2,setsar=1[main_v]")
    return "[main_v]"


def _build_audio_filter(
    duration: float,
    source_has_audio: bool,
    sfx_input_index: int,
    scene_switches: list[float],
    suspense_volume: float,
) -> str:
    filters = []

    if source_has_audio:
        filters.append(
            f"[0:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
            "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
            "volume=0.88[basea]"
        )
    else:
        filters.append(f"anullsrc=r=44100:cl=stereo:d={duration:.3f}[basea]")

    filters.append(
        f"[{sfx_input_index}:a]atrim=0:1.200,asetpts=PTS-STARTPTS,"
        "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        f"volume={suspense_volume:.3f},"
        "afade=t=in:st=0:d=0.040,afade=t=out:st=0.650:d=0.350[sfxbase]"
    )

    if len(scene_switches) == 1:
        delay_ms = max(0, int(scene_switches[0] * 1000))
        filters.append(f"[sfxbase]adelay={delay_ms}:all=1[sfxd0]")
    else:
        split_labels = "".join(f"[sfxsrc{i}]" for i in range(len(scene_switches)))
        filters.append(f"[sfxbase]asplit={len(scene_switches)}{split_labels}")
        for i, switch_time in enumerate(scene_switches):
            delay_ms = max(0, int(switch_time * 1000))
            filters.append(f"[sfxsrc{i}]adelay={delay_ms}:all=1[sfxd{i}]")

    mix_inputs = "[basea]" + "".join(f"[sfxd{i}]" for i in range(len(scene_switches)))
    filters.append(
        f"{mix_inputs}amix=inputs={len(scene_switches) + 1}:duration=first:dropout_transition=0,"
        f"atrim=0:{duration:.3f},asetpts=PTS-STARTPTS[outa]"
    )

    return ";".join(filters)


def render_short(
    video_path: str,
    cand: ScoredCandidate,
    output_path: str,
    title: str,
    part_number: int,
    add_logo: bool,
    subtitle_srt: Optional[str] = None,
    watermark_regions: Optional[List[WatermarkRegion]] = None,
    parrot_dir: str = "downloads/youtube",
    add_parrot_reaction: bool = True,
    scene_switches: Optional[list[float]] = None,
    add_suspense: bool = True,
    suspense_sound: Optional[str] = None,
    suspense_volume: float = 0.45,
) -> bool:
    start_str = str(cand.candidate.start_time)
    duration_str = str(cand.candidate.duration)
    duration = float(cand.candidate.duration)
    temp_files = []

    logger.info(f"Rendering short: {output_path} (Start: {start_str}, Duration: {duration_str})")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    ffmpeg_video_path = make_ffmpeg_safe_file(video_path, temp_files)

    logo_path = "assets/logo.png"
    has_logo = add_logo and is_valid_png(logo_path)
    if add_logo and os.path.exists(logo_path) and not has_logo:
        logger.warning(f"Logo file is invalid and will be skipped: {logo_path}")
    scene_switches = scene_switches or []

    reaction_videos = find_reaction_videos(parrot_dir) if add_parrot_reaction else []
    reaction_video = reaction_videos[(part_number - 1) % len(reaction_videos)] if reaction_videos else None
    ffmpeg_reaction_video = make_ffmpeg_safe_file(reaction_video, temp_files) if reaction_video else None
    if add_parrot_reaction and not reaction_video:
        logger.warning(f"No parrot reaction videos found in '{parrot_dir}'. Rendering without bottom reaction.")
    elif reaction_video:
        logger.info(f"Using parrot reaction video: {reaction_video}")

    valid_suspense_sound = (
        suspense_sound
        and os.path.isfile(suspense_sound)
        and os.path.splitext(suspense_sound)[1].lower() in AUDIO_EXTENSIONS
    )
    ffmpeg_suspense_sound = make_ffmpeg_safe_file(suspense_sound, temp_files) if valid_suspense_sound else None
    should_add_suspense = add_suspense and bool(scene_switches)
    if add_suspense and not scene_switches:
        logger.info("No internal scene/video switches found for this short; suspense sound skipped.")
    elif should_add_suspense:
        logger.info(f"Adding suspense sound at {len(scene_switches)} switch(es): {scene_switches}")

    cmd = [
        "ffmpeg", "-y",
        "-ss", start_str,
        "-t", duration_str,
        "-i", ffmpeg_video_path,
    ]

    reaction_input_index = None
    if ffmpeg_reaction_video:
        reaction_input_index = 1
        cmd.extend(["-stream_loop", "-1", "-i", ffmpeg_reaction_video])

    logo_input_index = None
    if has_logo:
        logo_input_index = 2 if ffmpeg_reaction_video else 1
        cmd.extend(["-i", logo_path])

    sfx_input_index = None
    if should_add_suspense:
        sfx_input_index = 1
        if ffmpeg_reaction_video:
            sfx_input_index += 1
        if has_logo:
            sfx_input_index += 1

        if ffmpeg_suspense_sound:
            cmd.extend(["-i", ffmpeg_suspense_sound])
        else:
            if suspense_sound and not valid_suspense_sound:
                logger.warning(f"Suspense sound file is invalid or missing: {suspense_sound}. Using generated tone.")
            cmd.extend([
                "-f", "lavfi",
                "-t", "1.2",
                "-i", "sine=frequency=96:sample_rate=44100:duration=1.2",
            ])

    filter_parts = []
    current_in = _append_watermark_filters(filter_parts, watermark_regions)
    map_v = _append_vertical_video_filters(filter_parts, current_in, reaction_input_index)

    if has_logo and logo_input_index is not None:
        filter_parts.append(f"[{logo_input_index}:v]scale=150:-1[logo]")
        filter_parts.append(f"{map_v}[logo]overlay=W-w-30:30[logo_v]")
        map_v = "[logo_v]"

    if subtitle_srt and os.path.exists(subtitle_srt):
        srt_escaped = subtitle_srt.replace("\\", "/").replace(":", r"\:")
        filter_parts.append(
            f"{map_v}subtitles='{srt_escaped}':"
            "force_style='FontSize=24,PrimaryColour=&H00FFFF,BorderStyle=3,Outline=2,Shadow=0'[sub_v]"
        )
        map_v = "[sub_v]"

    map_a = "0:a?"
    if should_add_suspense and sfx_input_index is not None:
        filter_parts.append(
            _build_audio_filter(
                duration=duration,
                source_has_audio=has_audio_stream(ffmpeg_video_path),
                sfx_input_index=sfx_input_index,
                scene_switches=scene_switches,
                suspense_volume=suspense_volume,
            )
        )
        map_a = "[outa]"

    filter_complex = ";".join(filter_parts)

    cmd += [
        "-filter_complex", filter_complex,
        "-map", map_v,
        "-map", map_a,
        "-t", duration_str,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        output_path,
    ]

    res = run_command(cmd, check=False)
    if res.returncode != 0:
        logger.error(f"Failed to render {output_path}")
        if res.stderr:
            logger.error(res.stderr[-2000:])
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        cleanup_temp_files(temp_files)
        return False

    if not is_valid_video_output(output_path):
        logger.error(f"Rendered file is invalid or empty: {output_path}")
        if res.stderr:
            logger.error(res.stderr[-2000:])
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        cleanup_temp_files(temp_files)
        return False

    wm_msg = f" (watermark blurred in {len(watermark_regions)} region{'s' if len(watermark_regions or []) > 1 else ''})" if watermark_regions else ""
    logger.info(f"Successfully rendered {output_path}{wm_msg}")
    cleanup_temp_files(temp_files)
    return True
