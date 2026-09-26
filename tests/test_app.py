from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        self.assertEqual(saved, {"tv_host": "", "movie_brightness": 80})

    def test_brightness_is_clamped(self) -> None:
        self.path.write_text('{"tv_host": "tv", "movie_brightness": 150}', "utf-8")
        self.assertEqual(self.app.load_settings(self.path).movie_brightness, 100)

    def test_invalid_settings_fall_back_without_overwriting(self) -> None:
        self.path.write_text('{"tv_host": "tv"', encoding="utf-8")
        with self.assertLogs("potplayer_tv_brightness", "WARNING"):
            self.assertEqual(self.app.load_settings(self.path), self.app.Settings())
        self.assertEqual(self.path.read_text(encoding="utf-8"), '{"tv_host": "tv"')

    def test_without_a_tv_address_it_explains_and_exits(self) -> None:
        with (
            mock.patch.object(self.app.logging, "basicConfig"),
            mock.patch.object(self.app, "_already_running", return_value=False),
            mock.patch.object(
                self.app, "load_settings", return_value=self.app.Settings()
            ),
            mock.patch("ctypes.windll.user32.MessageBoxW") as message_box,
            mock.patch("pystray.Icon") as tray,
            self.assertLogs("potplayer_tv_brightness", "WARNING"),
        ):
            self.app.main()
        self.assertIn("tv_check --host", message_box.call_args.args[1])
        tray.assert_not_called()

    def test_tray_icon_image(self) -> None:
        for active in (True, False):
            image = self.app.icon_image(active)
            self.assertEqual((image.size, image.mode), ((64, 64), "RGBA"))

    def test_potplayer_probe_answers_without_error(self) -> None:
        from potplayer_tv_brightness import potplayer

        self.assertIsInstance(potplayer.is_watching(), bool)


if __name__ == "__main__":
    unittest.main()
