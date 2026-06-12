import os
import tempfile
import unittest
from pathlib import Path


class SfxTests(unittest.TestCase):
    def test_explicit_suspense_sound_has_priority(self):
        from src.sfx import resolve_suspense_sound

        with tempfile.TemporaryDirectory() as tmp:
            explicit = Path(tmp) / "custom.wav"
            explicit.write_bytes(b"RIFF")

            self.assertEqual(
                resolve_suspense_sound("funny", str(explicit), base_dir=tmp),
                str(explicit),
            )

    def test_funny_theme_uses_local_pop_sound_when_available(self):
        from src.sfx import resolve_suspense_sound

        with tempfile.TemporaryDirectory() as tmp:
            sound = Path(tmp) / "assets" / "sfx" / "funny-pop.wav"
            sound.parent.mkdir(parents=True)
            sound.write_bytes(b"RIFF")

            self.assertEqual(
                resolve_suspense_sound("funny", None, base_dir=tmp),
                os.path.join(tmp, "assets", "sfx", "funny-pop.wav"),
            )

    def test_unknown_theme_falls_back_to_default_pop_sound(self):
        from src.sfx import resolve_suspense_sound

        with tempfile.TemporaryDirectory() as tmp:
            sound = Path(tmp) / "assets" / "sfx" / "funny-pop.wav"
            sound.parent.mkdir(parents=True)
            sound.write_bytes(b"RIFF")

            self.assertEqual(
                resolve_suspense_sound("unknown", None, base_dir=tmp),
                os.path.join(tmp, "assets", "sfx", "funny-pop.wav"),
            )


if __name__ == "__main__":
    unittest.main()
