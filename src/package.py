import json
import os
from datetime import datetime
from pathlib import Path

from .utils import logger, run_command


def thumbnail_path_for(short_path: str, thumbnails_dir: str) -> str:
    stem = Path(short_path).stem
    return os.path.join(thumbnails_dir, f"{stem}.jpg")


def generate_thumbnail(short_path: str, thumbnails_dir: str, seek_seconds: float = 1.0) -> str | None:
    if not os.path.exists(short_path):
        return None
    os.makedirs(thumbnails_dir, exist_ok=True)
    output_path = thumbnail_path_for(short_path, thumbnails_dir)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{seek_seconds:.2f}",
        "-i",
        short_path,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        output_path,
    ]
    res = run_command(cmd, check=False)
    if res.returncode != 0 or not os.path.exists(output_path):
        logger.warning(f"Could not generate thumbnail for {short_path}")
        return None
    return output_path


def build_manifest(
    input_video: str,
    preset: str,
    theme: str,
    shorts_count: int,
    report_path: str,
    shorts_dir: str,
    thumbnails_dir: str,
) -> dict:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_video": os.path.abspath(input_video),
        "preset": preset,
        "theme": theme,
        "shorts_count": shorts_count,
        "report_path": os.path.abspath(report_path),
        "shorts_dir": os.path.abspath(shorts_dir),
        "thumbnails_dir": os.path.abspath(thumbnails_dir),
    }


def write_manifest(manifest: dict, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
