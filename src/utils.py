import subprocess
import logging
import sys
import os
import hashlib
import shutil

def _configure_stdout_encoding() -> None:
    """Keep Windows console/GUI pipes from crashing on emoji filenames."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

def setup_logger(name: str = "shorts_cutter") -> logging.Logger:
    _configure_stdout_encoding()
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_logger()

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Error output: {e.stderr}")
        if check:
            raise
        return e

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

def format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{msecs:03d}"
