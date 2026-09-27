from __future__ import annotations

import sys
import tempfile
import time
import unittest
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

from PIL import Image

from potplayer_tv_brightness.controller import Picture, TVError
from potplayer_tv_brightness.discovery import FoundTV

ICON = Image.new("RGBA", (16, 16))


class FakeTV:
    def __init__(self, refusal: TVError | None) -> None:
        self.refusal = refusal

    @contextmanager
    def session(self) -> Generator[FakeTV, None, None]:
        if self.refusal:
            raise self.refusal
        yield self

    def read_picture(self) -> Picture:
        return Picture("normal", 20)


@unittest.skipUnless(sys.platform == "win32", "the app is Windows-only")
class ConnectWindowTest(unittest.TestCase):
    def setUp(self) -> None:
        from potplayer_tv_brightness import connect

        self.connect = connect
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.key_file = Path(folder.name) / "tv-client-key.txt"
        self.hosts: list[str] = []
        self.refusal: TVError | None = None

    def lgtv(self, host: str, key_file: Path) -> FakeTV:
        self.hosts.append(host)
        return FakeTV(self.refusal)

    def open(self, tvs: list[FoundTV], host: str = "") -> Any:
        """A hidden window whose search finds tvs; the TV itself is faked."""
        patcher = mock.patch.multiple(
            self.connect, find_tvs=lambda: tvs, LGTV=self.lgtv
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        window = self.connect.ConnectWindow(host, self.key_file, ICON)
        window.root.withdraw()
        self.addCleanup(window.close)
        return window

    def pump(self, window: Any, done: Callable[[], bool]) -> None:
        """Run the window's event loop until done() or 5 s have passed."""
        deadline = time.monotonic() + 5
        while not done():
            self.assertLess(time.monotonic(), deadline, window.status.get())
            window.root.update()
            time.sleep(0.01)

    def test_found_tv_is_selected_and_connect_returns_it(self) -> None:
        window = self.open([FoundTV("192.168.1.50", "[LG] webOS TV OLED48C2")])
        self.pump(window, lambda: window.status.get().startswith("Select your TV"))
        self.assertEqual(
            window.tv_list.get(0), "[LG] webOS TV OLED48C2    192.168.1.50"
        )
        self.assertEqual(window.address.get(), "192.168.1.50")

        window.connect_button.invoke()
        self.pump(window, lambda: window.connected is not None)
        self.assertEqual(window.connected, "192.168.1.50")
        self.assertEqual(self.hosts, ["192.168.1.50"])

    def test_no_tv_found_says_how_to_type_its_address(self) -> None:
        window = self.open([])
        self.pump(window, lambda: window.status.get().startswith("No TV found"))
        self.assertIn("type its IP address", window.status.get())

    def test_connect_waits_for_an_address(self) -> None:
        # A first click during the search used to do nothing visible.
        window = self.open([])
        self.assertTrue(window.connect_button.instate(["disabled"]))  # searching
        self.pump(window, lambda: window.status.get().startswith("No TV found"))
        self.assertTrue(window.connect_button.instate(["disabled"]))
        window.address.set("192.168.1.50")  # typed by the user
        self.assertTrue(window.connect_button.instate(["!disabled"]))

    def test_a_declined_prompt_explains_logs_and_allows_a_retry(self) -> None:
        self.refusal = TVError("Pairing refused: 403 Error: User rejected pairing")
        window = self.open([], host="192.168.1.50")
        self.pump(window, lambda: window.status.get().startswith("No TV found"))
        with self.assertLogs("potplayer_tv_brightness.connect", "WARNING") as logs:
            window.connect_button.invoke()
            self.pump(window, lambda: "declined" in window.status.get())
        self.assertIn("Connecting to 192.168.1.50 failed", logs.output[0])
        self.assertIsNone(window.connected)
        self.assertTrue(window.connect_button.instate(["!disabled"]))

    def test_a_typed_address_is_kept_when_tvs_are_found(self) -> None:
        window = self.open([FoundTV("192.168.1.50", "LG TV")], host="10.0.0.9")
        self.pump(window, lambda: window.status.get().startswith("Select your TV"))
        self.assertEqual(window.address.get(), "10.0.0.9")

    def test_errors_become_next_steps(self) -> None:
        cases = {
            "Pairing refused: 403 Pairing rejected: blacklisted certificate "
            "detected": "firmware blocks",
            "ssap://settings/getSystemSettings failed: 401 insufficient "
            "permissions": "firmware blocks",
            "Pairing refused: 403 Error: User rejected pairing": "declined",
            "TV connection failed: The read operation timed out": "60 seconds",
            "Cannot connect to wss://192.168.1.50:3001: [WinError 10061] "
            "refused": "Can't reach a TV at 192.168.1.50",
        }
        for error, expected in cases.items():
            with self.subTest(error=error):
                message = self.connect.explain(TVError(error), "192.168.1.50")
                self.assertIn(expected, message)


if __name__ == "__main__":
    unittest.main()
