from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from collections.abc import Generator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from functools import partial
from pathlib import Path
from unittest import mock

from potplayer_tv_brightness.controller import Picture, TVError


class FakeTV:
    """Stands in for a TV session: one picture mode, brightness 20."""

    def __init__(self) -> None:
        self.online = True
        self.backlight = 20
        self.writes: list[int] = []

    @contextmanager
    def session(self) -> Generator[FakeTV, None, None]:
        if not self.online:
            raise TVError("Cannot connect to wss://192.168.1.50:3001: timed out")
        yield self

    def read_picture(self) -> Picture:
        return Picture("normal", self.backlight)

    def set_backlight(self, value: int) -> None:
        self.writes.append(value)
        self.backlight = value


@unittest.skipUnless(sys.platform == "win32", "the app uses Win32 APIs")
class TVCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        from potplayer_tv_brightness import app
        from scripts import tv_check

        self.tv_check = tv_check
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.settings_file = Path(folder.name) / "settings.json"
        self.tv = FakeTV()
        self.hosts: list[str] = []
        patcher = mock.patch.multiple(
            tv_check,
            KEY_FILE=Path(folder.name) / "tv-client-key.txt",
            LGTV=self.connect,
            load_settings=partial(app.load_settings, self.settings_file),
            save_settings=partial(app.save_settings, path=self.settings_file),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def connect(self, host: str, key_file: Path) -> FakeTV:
        self.hosts.append(host)
        return self.tv

    def check(self, *argv: str) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            code = self.tv_check.main(list(argv))
        return code, output.getvalue()

    def saved_host(self) -> str:
        return str(json.loads(self.settings_file.read_text("utf-8"))["tv_host"])

    def test_host_is_saved_once_the_tv_answers(self) -> None:
        code, output = self.check("--host", "192.168.1.50")
        self.assertEqual(code, 0)
        self.assertEqual(self.saved_host(), "192.168.1.50")
        self.assertIn("Accept the connection prompt on the TV", output)
        self.assertIn("Picture mode: normal, OLED Pixel Brightness: 20", output)

        code, _ = self.check()  # later runs use the saved address
        self.assertEqual((code, self.hosts), (0, ["192.168.1.50", "192.168.1.50"]))

    def test_unreachable_host_is_not_saved(self) -> None:
        self.tv.online = False
        code, output = self.check("--host", "192.168.1.50")
        self.assertEqual(code, 1)
        self.assertIn("TV check failed: Cannot connect", output)
        self.assertEqual(self.saved_host(), "")

    def test_without_an_address_it_says_how_to_connect(self) -> None:
        code, output = self.check()
        self.assertEqual(code, 1)
        self.assertIn("--host <TV IP address>", output)
        self.assertEqual(self.hosts, [])

    def test_set_is_clamped_to_0_to_100(self) -> None:
        with mock.patch("time.sleep"):
            self.check("--host", "192.168.1.50", "--set", "150")
            self.check("--set", "-5")
        self.assertEqual(self.tv.writes, [100, 0])


if __name__ == "__main__":
    unittest.main()
