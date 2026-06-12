import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class PlatformUtilsTests(unittest.TestCase):
    def test_find_project_python_prefers_posix_venv_on_linux(self):
        from src.platform_utils import find_project_python

        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            posix_python = base_dir / ".venv" / "bin" / "python"
            windows_python = base_dir / ".venv" / "Scripts" / "python.exe"
            posix_python.parent.mkdir(parents=True)
            windows_python.parent.mkdir(parents=True)
            posix_python.write_text("", encoding="utf-8")
            windows_python.write_text("", encoding="utf-8")

            self.assertEqual(
                find_project_python(str(base_dir), current_python="system-python", os_name="posix"),
                str(posix_python),
            )

    def test_find_project_python_prefers_windows_venv_on_windows(self):
        from src.platform_utils import find_project_python

        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            posix_python = base_dir / ".venv" / "bin" / "python"
            windows_python = base_dir / ".venv" / "Scripts" / "python.exe"
            posix_python.parent.mkdir(parents=True)
            windows_python.parent.mkdir(parents=True)
            posix_python.write_text("", encoding="utf-8")
            windows_python.write_text("", encoding="utf-8")

            self.assertEqual(
                find_project_python(str(base_dir), current_python="system-python", os_name="nt"),
                str(windows_python),
            )

    def test_default_parrot_dir_points_to_reaction_subfolder(self):
        from src.platform_utils import default_parrot_dir

        self.assertEqual(
            default_parrot_dir("/repo"),
            os.path.join("/repo", "downloads", "youtube", "papagaio"),
        )

    def test_open_path_uses_webbrowser_off_windows(self):
        from src.platform_utils import open_path

        with mock.patch("webbrowser.open") as web_open:
            self.assertTrue(open_path("/tmp/report.html", os_name="posix"))
            web_open.assert_called_once()
            self.assertTrue(web_open.call_args.args[0].startswith("file://"))

    def test_app_import_does_not_require_tkinter(self):
        import importlib
        import sys

        with mock.patch.dict(sys.modules, {"tkinter": None}):
            sys.modules.pop("app", None)
            module = importlib.import_module("app")

        self.assertFalse(module.TKINTER_AVAILABLE)


if __name__ == "__main__":
    unittest.main()
