from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "win32", "the app uses Win32 APIs")
class AppTest(unittest.TestCase):
    def setUp(self) -> None:
        from potplayer_tv_brightness import app

        self.app = app
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "settings.json"

    def test_first_run_creates_default_settings(self) -> None:
        settings = self.app.load_settings(self.path)
        self.assertEqual(settings, self.app.Settings())
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved, {"tv_host": "192.168.8.145", "movie_brightness": 80})

    def test_brightness_is_clamped(self) -> None:
        self.path.write_text('{"tv_host": "tv", "movie_brightness": 150}', "utf-8")
        self.assertEqual(self.app.load_settings(self.path).movie_brightness, 100)

    def test_invalid_settings_fall_back_without_overwriting(self) -> None:
        self.path.write_text('{"tv_host": "tv"', encoding="utf-8")
        with self.assertLogs("potplayer_tv_brightness", "WARNING"):
            self.assertEqual(self.app.load_settings(self.path), self.app.Settings())
        self.assertEqual(self.path.read_text(encoding="utf-8"), '{"tv_host": "tv"')

    def test_tray_icon_image(self) -> None:
        for active in (True, False):
            image = self.app.icon_image(active)
            self.assertEqual((image.size, image.mode), ((64, 64), "RGBA"))

    def test_potplayer_probe_answers_without_error(self) -> None:
        from potplayer_tv_brightness import potplayer

        self.assertIsInstance(potplayer.is_watching(), bool)


if __name__ == "__main__":
    unittest.main()
