import unittest


class RendererSfxTests(unittest.TestCase):
    def test_suspense_markers_keep_scene_switches_when_present(self):
        from src.renderer import _suspense_markers

        self.assertEqual(_suspense_markers([1.2, 4.5], duration=10.0, enabled=True), [1.2, 4.5])

    def test_suspense_markers_add_midpoint_when_no_switches(self):
        from src.renderer import _suspense_markers

        self.assertEqual(_suspense_markers([], duration=10.0, enabled=True), [5.0])

    def test_suspense_markers_stay_empty_when_disabled(self):
        from src.renderer import _suspense_markers

        self.assertEqual(_suspense_markers([], duration=10.0, enabled=False), [])


if __name__ == "__main__":
    unittest.main()
