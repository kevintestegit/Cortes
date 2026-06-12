import unittest


class MetadataPtBrTests(unittest.TestCase):
    def test_funny_title_is_portuguese(self):
        from src.metadata import generate_title

        title = generate_title("funny", 1)

        self.assertIn("#shorts", title)
        self.assertNotIn("Try Not To Laugh", title)

    def test_football_description_uses_ptbr_hashtag(self):
        from src.metadata import generate_description, generate_hashtags

        self.assertIn("lance", generate_description("football").lower())
        self.assertIn("#futebol", generate_hashtags("football"))

    def test_unknown_theme_uses_generic_ptbr_metadata(self):
        from src.metadata import generate_description, generate_hashtags

        self.assertIn("corte", generate_description("unknown").lower())
        self.assertIn("#cortes", generate_hashtags("unknown"))
