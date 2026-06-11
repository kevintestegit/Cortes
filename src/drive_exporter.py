import json
import os
import shutil
import string
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .utils import logger


MEDIA_EXTENSIONS = {".mp4", ".srt", ".ass"}
REPORT_EXTENSIONS = {".html", ".json", ".csv"}


def _slugify(value: str, fallback: str = "video") -> str:
    allowed = f"{string.ascii_letters}{string.digits}-_ "
    cleaned = "".join(ch if ch in allowed else " " for ch in value)
    cleaned = "-".join(cleaned.split())
    return cleaned[:60] or fallback


def _existing_dirs(paths: Iterable[str]) -> list[str]:
    return [path for path in paths if path and os.path.isdir(path)]


def find_google_drive_root(preferred_path: str | None = None) -> str | None:
    """Find a Google Drive Desktop mount or synced folder on Windows."""
    if preferred_path and os.path.isdir(preferred_path):
        return preferred_path

    env_path = os.getenv("GOOGLE_DRIVE_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    user_profile = os.path.expanduser("~")
    common_paths = [
        os.path.join(user_profile, "Google Drive"),
        os.path.join(user_profile, "My Drive"),
        os.path.join(user_profile, "Meu Drive"),
    ]
    existing = _existing_dirs(common_paths)
    if existing:
        return existing[0]

    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if not os.path.isdir(root):
            continue
        for child in ("Meu Drive", "My Drive"):
            candidate = os.path.join(root, child)
            if os.path.isdir(candidate):
                return candidate

    return None


def create_drive_run_dir(
    input_video: str,
    drive_root: str | None = None,
    preferred_path: str | None = None,
) -> str | None:
    root = drive_root or find_google_drive_root(preferred_path)
    if not root:
        return None

    source_slug = _slugify(Path(input_video).stem)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(root, "Shorts Auto Cutter", f"{timestamp}_{source_slug}")
    os.makedirs(os.path.join(run_dir, "shorts"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "reports"), exist_ok=True)
    return run_dir


def _copy_validated(src: str, dst: str) -> dict:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    src_size = os.path.getsize(src)
    dst_size = os.path.getsize(dst)
    if src_size <= 0 or dst_size != src_size:
        raise OSError(f"Copy validation failed for {src} -> {dst}")
    return {
        "source": os.path.abspath(src),
        "destination": os.path.abspath(dst),
        "bytes": dst_size,
    }


def export_run_to_google_drive(
    input_video: str,
    shorts_dir: str,
    reports_dir: str,
    preferred_path: str | None = None,
    delete_local_media: bool = False,
) -> dict:
    run_dir = create_drive_run_dir(input_video, preferred_path=preferred_path)
    if not run_dir:
        logger.warning("Google Drive folder was not found. Keeping files only in local output.")
        return {
            "enabled": False,
            "reason": "google_drive_not_found",
            "report_path": os.path.abspath(os.path.join(reports_dir, "index.html")),
        }

    logger.info(f"Copying generated shorts to Google Drive: {run_dir}")
    copied = []
    deleted = []

    for name in sorted(os.listdir(shorts_dir)):
        src = os.path.join(shorts_dir, name)
        if (
            not os.path.isfile(src)
            or not name.startswith("short_")
            or Path(name).suffix.lower() not in MEDIA_EXTENSIONS
        ):
            continue
        dst = os.path.join(run_dir, "shorts", name)
        copied.append(_copy_validated(src, dst))

    for name in sorted(os.listdir(reports_dir)):
        src = os.path.join(reports_dir, name)
        if not os.path.isfile(src) or Path(name).suffix.lower() not in REPORT_EXTENSIONS:
            continue
        dst = os.path.join(run_dir, "reports", name)
        copied.append(_copy_validated(src, dst))

    manifest_path = os.path.join(run_dir, "drive_manifest.json")
    manifest = {
        "input_video": os.path.abspath(input_video),
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "run_dir": os.path.abspath(run_dir),
        "copied": copied,
        "delete_local_media": delete_local_media,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    if delete_local_media:
        for item in copied:
            source = item["source"]
            if Path(source).suffix.lower() not in MEDIA_EXTENSIONS:
                continue
            try:
                os.remove(source)
                deleted.append(source)
            except OSError as exc:
                logger.warning(f"Could not delete local file after Drive copy: {source} ({exc})")

    report_path = os.path.join(run_dir, "reports", "index.html")
    logger.info(f"Google Drive export completed: {run_dir}")
    if deleted:
        logger.info(f"Deleted {len(deleted)} local media file(s) after Drive copy.")

    return {
        "enabled": True,
        "run_dir": os.path.abspath(run_dir),
        "report_path": os.path.abspath(report_path),
        "manifest_path": os.path.abspath(manifest_path),
        "copied": copied,
        "deleted": deleted,
    }
