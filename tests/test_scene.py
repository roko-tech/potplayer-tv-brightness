from __future__ import annotations

import sys
import unittest

from potplayer_tv_brightness.controller import DARK_BELOW, LIGHT_ABOVE

BLACK, WHITE = (0, 0, 0, 0), (255, 255, 255, 0)  # BGRX, as GDI stores pixels
SUBJECT, BACKGROUND = (15, 15, 15, 0), (140, 140, 140, 0)
NIGHT, LAMP = (20, 20, 20, 0), (220, 220, 220, 0)


@unittest.skipUnless(sys.platform == "win32", "screen capture uses Win32 GDI")
class SceneTest(unittest.TestCase):
    def setUp(self) -> None:
        from potplayer_tv_brightness import scene

        self.scene = scene

    def pixels(self, *bgrx: tuple[int, int, int, int]) -> bytes:
        """A SAMPLE-sized image filled with the given pixels, repeated."""
        width, height = self.scene.SAMPLE
        return b"".join(bytes(p) for p in bgrx) * (width * height // len(bgrx))

    def test_level_is_the_luma_of_the_brighter_part(self) -> None:
        level = self.scene.level
        self.assertEqual(level(self.pixels(BLACK)), 0)
        self.assertEqual(level(self.pixels(WHITE)), 255)
        self.assertEqual(level(self.pixels(BLACK, WHITE)), 255)
        # GDI stores blue first: pure blue is dark (29), pure red brighter (76).
        self.assertEqual(level(self.pixels((255, 0, 0, 0))), 29)
        self.assertEqual(level(self.pixels((0, 0, 255, 0))), 76)

    def test_a_dark_subject_on_a_bright_background_is_not_dark(self) -> None:
        # A dark character filling most of the picture; a sixth is bright.
        picture = self.pixels(*[SUBJECT] * 10, *[BACKGROUND] * 2)
        self.assertGreater(self.scene.level(picture), LIGHT_ABOVE)

    def test_a_dark_scene_with_a_small_lamp_is_dark(self) -> None:
        picture = self.pixels(*[NIGHT] * 23, LAMP)  # the lamp: 4% of the picture
        self.assertLess(self.scene.level(picture), DARK_BELOW)

    def test_grab_reads_the_screen(self) -> None:
        width, height = self.scene.SAMPLE
        pixels = self.scene.grab((0, 0, width * 2, height * 2))
        assert pixels is not None
        self.assertEqual(len(pixels), width * height * 4)

    def test_no_level_for_a_missing_or_covered_window(self) -> None:
        import ctypes

        self.assertIsNone(self.scene.picture_level(0))
        # The desktop window is under every other window, so its center is
        # covered (or not a top-level window at all): nothing to measure.
        desktop = ctypes.windll.user32.GetDesktopWindow()
        self.assertIsNone(self.scene.picture_level(desktop))


if __name__ == "__main__":
    unittest.main()
