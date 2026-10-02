from __future__ import annotations

import sys
import unittest


@unittest.skipUnless(sys.platform == "win32", "screen capture uses Win32 GDI")
class SceneTest(unittest.TestCase):
    def setUp(self) -> None:
        from potplayer_tv_brightness import scene

        self.scene = scene

    def pixels(self, *bgrx: tuple[int, int, int, int]) -> bytes:
        """A SAMPLE-sized image filled with the given pixels, repeated."""
        width, height = self.scene.SAMPLE
        return b"".join(bytes(p) for p in bgrx) * (width * height // len(bgrx))

    def test_level_is_the_average_luma(self) -> None:
        level = self.scene.level
        self.assertEqual(level(self.pixels((0, 0, 0, 0))), 0)
        self.assertEqual(level(self.pixels((255, 255, 255, 0))), 255)
        self.assertEqual(level(self.pixels((0, 0, 0, 0), (255, 255, 255, 0))), 127.5)
        # GDI stores blue first: pure blue is dark (29), pure red brighter (76).
        self.assertEqual(level(self.pixels((255, 0, 0, 0))), 29)
        self.assertEqual(level(self.pixels((0, 0, 255, 0))), 76)

    def test_middle_leaves_out_bars_subtitles_and_controls(self) -> None:
        middle = self.scene.middle
        # A 4K window: 4:3 pillarbox bars end at x=480, 2.39:1 letterbox bars
        # at y=277, and subtitles usually start below y=1800.
        self.assertEqual(middle((0, 0, 3840, 2160)), (480, 360, 3360, 1800))
        # A window on a monitor left of the main one has negative coordinates.
        self.assertEqual(middle((-1920, 0, 0, 1080)), (-1680, 180, -240, 900))

    def test_grab_reads_the_screen(self) -> None:
        width, height = self.scene.SAMPLE
        pixels = self.scene.grab((0, 0, width * 2, height * 2))
        assert pixels is not None
        self.assertEqual(len(pixels), width * height * 4)

    def test_no_level_for_a_missing_or_covered_window(self) -> None:
        import ctypes

        self.assertIsNone(self.scene.picture_level(0))
        # The desktop window is under every other window, so its middle is
        # covered (or not a top-level window at all): nothing to measure.
        desktop = ctypes.windll.user32.GetDesktopWindow()
        self.assertIsNone(self.scene.picture_level(desktop))


if __name__ == "__main__":
    unittest.main()
