import os
import tempfile
import unittest


class SourceChecklistTests(unittest.TestCase):
    def test_source_checklist_mentions_rights_and_watermark_count(self):
        from src.source_checklist import build_source_checklist, write_source_checklist

        content = build_source_checklist("input/video.mp4", watermark_count=2)

        self.assertIn("Direitos de uso", content)
        self.assertIn("input/video.mp4", content)
        self.assertIn("2", content)

        with tempfile.TemporaryDirectory() as tmp:
            path = write_source_checklist(content, tmp)
            self.assertEqual(path, os.path.join(tmp, "source_checklist.md"))
            self.assertTrue(os.path.exists(path))
