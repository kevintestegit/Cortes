import os
import tempfile
import unittest


class PackageTests(unittest.TestCase):
    def test_thumbnail_path_matches_short_name(self):
        from src.package import thumbnail_path_for

        self.assertEqual(
            thumbnail_path_for("output/shorts/short_001.mp4", "output/thumbnails"),
            os.path.join("output", "thumbnails", "short_001.jpg"),
        )

    def test_manifest_contains_package_fields(self):
        from src.package import build_manifest

        manifest = build_manifest(
            input_video="input/source.mp4",
            preset="funny",
            theme="funny",
            shorts_count=2,
            report_path="/tmp/report.html",
            shorts_dir="/tmp/shorts",
            thumbnails_dir="/tmp/thumbs",
        )

        self.assertEqual(manifest["preset"], "funny")
        self.assertEqual(manifest["theme"], "funny")
        self.assertEqual(manifest["shorts_count"], 2)
        self.assertIn("created_at", manifest)


if __name__ == "__main__":
    unittest.main()
