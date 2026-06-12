import unittest


class RendererHookTests(unittest.TestCase):
    def test_drawtext_escapes_ffmpeg_sensitive_characters(self):
        from src.renderer import _escape_drawtext_text

        self.assertEqual(_escape_drawtext_text("Bob's 100% wow: yes"), r"Bob\\'s 100\\% wow\\: yes")

    def test_hook_filter_is_empty_when_text_missing(self):
        from src.renderer import _hook_filter

        self.assertEqual(_hook_filter("[v]", "", "out"), "")

    def test_hook_filter_limits_text_to_intro_window(self):
        from src.renderer import _hook_filter

        item = _hook_filter("[v]", "OLHA ISSO", "out")

        self.assertIn("drawtext=", item)
        self.assertIn("enable='between(t,0,2.4)'", item)
        self.assertIn("[out]", item)
