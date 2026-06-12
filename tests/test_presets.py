import unittest


class PresetTests(unittest.TestCase):
    def test_funny_preset_enables_viral_defaults(self):
        from src.presets import get_preset

        preset = get_preset("funny")

        self.assertTrue(preset.add_subtitles)
        self.assertTrue(preset.add_parrot_reaction)
        self.assertTrue(preset.add_suspense)
        self.assertTrue(preset.add_hook)
        self.assertEqual(preset.theme, "funny")
        self.assertEqual(preset.min_duration, 12)
        self.assertEqual(preset.max_duration, 28)

    def test_unknown_preset_falls_back_to_funny(self):
        from src.presets import get_preset

        self.assertEqual(get_preset("unknown").name, "funny")

    def test_hook_text_is_theme_specific(self):
        from src.presets import hook_text_for

        self.assertEqual(hook_text_for("funny", 1), "OLHA ISSO")
        self.assertEqual(hook_text_for("fails", 1), "NAO DEU CERTO")

    def test_podcast_and_curiosities_presets_exist(self):
        from src.presets import get_preset

        self.assertEqual(get_preset("podcast").theme, "podcast")
        self.assertEqual(get_preset("curiosities").theme, "curiosities")
