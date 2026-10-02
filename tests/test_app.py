from __future__ import annotations

import contextlib
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
        self.assertEqual(
            saved, {"tv_host": "", "movie_brightness": 80, "dark_scene_brightness": 0}
        )

    def test_brightness_is_clamped(self) -> None:
        self.path.write_text(
            '{"tv_host": "tv", "movie_brightness": 150, "dark_scene_brightness": -5}',
            "utf-8",
        )
        settings = self.app.load_settings(self.path)
        self.assertEqual(settings.movie_brightness, 100)
        self.assertEqual(settings.dark_scene_brightness, 0)

    def test_settings_from_before_dark_scenes_keep_the_tv(self) -> None:
        self.path.write_text('{"tv_host": "tv", "movie_brightness": 40}', "utf-8")
        self.assertEqual(
            self.app.load_settings(self.path), self.app.Settings("tv", 40, 0)
        )

    def test_invalid_settings_fall_back_without_overwriting(self) -> None:
        self.path.write_text('{"tv_host": "tv"', encoding="utf-8")
        with self.assertLogs("potplayer_tv_brightness", "WARNING"):
            self.assertEqual(self.app.load_settings(self.path), self.app.Settings())
        self.assertEqual(self.path.read_text(encoding="utf-8"), '{"tv_host": "tv"')

    def start(self, dialog_result: str | None) -> tuple[mock.MagicMock, ...]:
        """Run main() as a first run; the connect window returns dialog_result.

        Every window and real file is patched out: this must never show UI or
        touch the developer's own settings.
        """
        with (
            mock.patch.object(self.app.logging, "basicConfig"),
            mock.patch.object(self.app, "RotatingFileHandler"),
            mock.patch.object(self.app, "_already_running", return_value=False),
            mock.patch.object(
                self.app, "load_settings", return_value=self.app.Settings()
            ),
            mock.patch.object(self.app, "save_settings") as save,
            mock.patch.object(self.app, "RESTORE_FILE", self.path.parent / "r.json"),
            mock.patch.object(
                self.app.connect, "connect_dialog", return_value=dialog_result
            ) as dialog,
            mock.patch("pystray.Icon") as tray,
        ):
            self.app.main()
        return dialog, save, tray

    def test_first_run_shows_the_connect_window_then_the_tray(self) -> None:
        dialog, save, tray = self.start("192.168.1.50")
        dialog.assert_called_once()
        self.assertEqual(save.call_args.args[0].tv_host, "192.168.1.50")
        tray.assert_called_once()

    def test_dark_scene_menu_offers_values_above_the_movie_value(self) -> None:
        _, _, tray = self.start("192.168.1.50")
        menu = {item.text: item for item in tray.call_args.args[3]}
        dark = {item.text: item for item in menu["Dark scene brightness"].submenu}
        movie = {item.text: item for item in menu["Movie brightness"].submenu}
        self.assertEqual(list(dark), ["Off", *map(str, self.app.PRESETS)])
        self.assertTrue(dark["Off"].checked)
        enabled = [text for text, item in dark.items() if item.enabled]
        self.assertEqual(enabled, ["Off", "90", "100"])  # movie value: 80

        # Menu actions save the settings: patch that here too, since start()'s
        # patches have ended by now.
        with mock.patch.object(self.app, "save_settings") as save:
            dark["90"](tray.return_value)
            self.assertEqual([t for t, item in dark.items() if item.checked], ["90"])
            self.assertEqual(save.call_args.args[0].dark_scene_brightness, 90)

            movie["50"](tray.return_value)
            enabled = [text for text, item in dark.items() if item.enabled]
            self.assertEqual(enabled, ["Off", "60", "70", "80", "90", "100"])

    def test_closing_the_connect_window_exits_quietly(self) -> None:
        _, save, tray = self.start(None)
        save.assert_not_called()
        tray.assert_not_called()

    def test_start_with_windows_toggles_the_run_entry(self) -> None:
        import winreg

        parent = r"Software\potplayer-tv-brightness-tests"
        test_key = parent + r"\Run"

        def remove_test_keys() -> None:
            for key in (test_key, parent):
                with contextlib.suppress(FileNotFoundError):
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)

        self.addCleanup(remove_test_keys)
        with mock.patch.object(self.app, "RUN_KEY", test_key):
            self.assertFalse(self.app.autostart_enabled())
            self.app.set_autostart(True)
            self.assertTrue(self.app.autostart_enabled())
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key) as key:
                command = winreg.QueryValueEx(key, self.app.APP_NAME)[0]
            self.assertTrue(command.endswith('run.pyw"'), command)  # from source
            self.app.set_autostart(False)
            self.assertFalse(self.app.autostart_enabled())
            self.app.set_autostart(False)  # already off: no error

    def test_the_exe_keeps_its_files_in_appdata(self) -> None:
        appdata = r"C:\Users\u\AppData\Roaming"
        with (
            mock.patch.object(sys, "frozen", True, create=True),
            mock.patch.object(sys, "executable", r"C:\Apps\PotPlayer TV.exe"),
            mock.patch.dict("os.environ", {"APPDATA": appdata}),
        ):
            folder = self.app.data_dir()
            command = self.app.launch_command()
        self.assertEqual(folder, Path(appdata) / "PotPlayer TV Brightness")
        self.assertEqual(command, r'"C:\Apps\PotPlayer TV.exe"')

    def test_tray_icon_image(self) -> None:
        for active in (True, False):
            image = self.app.icon_image(active)
            self.assertEqual((image.size, image.mode), ((64, 64), "RGBA"))

    def test_potplayer_probe_answers_without_error(self) -> None:
        from potplayer_tv_brightness import potplayer

        self.assertIsInstance(potplayer.watching_window(), int | None)


if __name__ == "__main__":
    unittest.main()
