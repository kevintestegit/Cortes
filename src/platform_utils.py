import os
import sys
import webbrowser
from pathlib import Path


def find_project_python(
    base_dir: str,
    current_python: str | None = None,
    os_name: str | None = None,
) -> str:
    current_python = current_python or sys.executable
    os_name = os_name or os.name

    candidates = []
    if os_name == "nt":
        candidates.extend([
            os.path.join(base_dir, ".venv", "Scripts", "python.exe"),
            os.path.join(base_dir, ".venv", "bin", "python"),
        ])
    else:
        candidates.extend([
            os.path.join(base_dir, ".venv", "bin", "python"),
            os.path.join(base_dir, ".venv", "Scripts", "python.exe"),
        ])

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return current_python


def default_parrot_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "downloads", "youtube", "papagaio")


def open_path(path: str, os_name: str | None = None) -> bool:
    os_name = os_name or os.name
    if not path:
        return False

    if os_name == "nt":
        try:
            os.startfile(path)  # type: ignore[attr-defined]
            return True
        except OSError:
            return False

    return webbrowser.open(Path(path).resolve().as_uri())
