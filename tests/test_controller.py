from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from potplayer_tv_brightness.controller import (
    Controller,
    Picture,
    RestoreStore,
    TVError,
)

STEP = 0.5  # the app polls PotPlayer every 0.5 s


class FakeTV:
    """Stands in for the LG TV: one picture mode active, brightness per mode."""

    def __init__(self, mode: str = "normal", backlight: int = 20) -> None:
        self.mode = mode
        self.levels = {mode: backlight}
        self.online = True
        self.writes: list[tuple[str, int]] = []

    @property
    def backlight(self) -> int:
        return self.levels[self.mode]

    def switch_mode(self, mode: str, backlight: int) -> None:
        self.mode = mode
        self.levels.setdefault(mode, backlight)

    @contextmanager
    def session(self) -> Generator[FakeTV, None, None]:
        if not self.online:
            raise TVError("TV is off")
        yield self

    def read_picture(self) -> Picture:
        return Picture(self.mode, self.backlight)

    def set_backlight(self, value: int) -> None:
        self.writes.append((self.mode, value))
        self.levels[self.mode] = value


class ControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "restore.json"
        self.tv = FakeTV()
        self.now = 0.0

    def make(self, target: int = 80) -> Controller:
        return Controller(
            self.tv, RestoreStore(self.path), target, settle_s=1.0, retry_s=10.0
        )

    def observe(self, controller: Controller, watching: bool, seconds: float) -> None:
        for _ in range(round(seconds / STEP)):
            controller.tick(watching, self.now)
            self.now += STEP

    def owed_on_disk(self) -> dict[str, int]:
        if not self.path.exists():
            return {}
        data: dict[str, int] = json.loads(self.path.read_text(encoding="utf-8"))
        return data

    # Primary journey: play -> movie brightness, pause/stop -> original.
    def test_play_boosts_and_pause_restores(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        self.assertEqual(self.tv.backlight, 80)
        self.assertEqual(self.owed_on_disk(), {"normal": 20})
        self.assertTrue(controller.boosted)

        self.observe(controller, False, 2)
        self.assertEqual(self.tv.backlight, 20)
        self.assertEqual(self.tv.writes, [("normal", 80), ("normal", 20)])
        self.assertEqual(self.owed_on_disk(), {})
        self.assertFalse(controller.boosted)
        self.assertEqual(controller.status, "Idle")

    def test_state_must_hold_before_acting(self) -> None:
        controller = self.make()
        self.observe(controller, False, 2)
        self.observe(controller, True, 0.5)  # a blip, e.g. between playlist items
        self.observe(controller, False, 2)
        self.assertEqual(self.tv.writes, [])

        self.observe(controller, True, 2)
        self.observe(controller, False, 0.5)
        self.observe(controller, True, 2)
        self.assertEqual(self.tv.writes, [("normal", 80)])

    def test_nothing_happens_before_the_first_settled_state(self) -> None:
        self.path.write_text('{"normal": 20}', encoding="utf-8")
        self.tv.levels["normal"] = 80  # left boosted by a previous run
        controller = self.make()
        self.observe(controller, True, 0.5)  # a movie was already playing
        self.assertEqual(self.tv.writes, [])

    def test_hdr_mode_is_left_alone(self) -> None:
        self.tv = FakeTV(mode="hdrStandard", backlight=100)
        controller = self.make()
        self.observe(controller, True, 30)
        self.assertEqual(self.tv.writes, [])
        self.assertIn("HDR", controller.status)
        self.assertEqual(self.owed_on_disk(), {})

    def test_restore_waits_for_the_original_picture_mode(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        self.tv.switch_mode("hdrStandard", 100)  # e.g. Windows switched to HDR
        self.observe(controller, False, 2)
        self.assertEqual(self.tv.writes, [("normal", 80)])
        self.assertEqual(self.owed_on_disk(), {"normal": 20})
        self.assertIn("waiting", controller.status)

        self.tv.switch_mode("normal", 80)
        self.observe(controller, False, 12)  # next retry
        self.assertEqual(self.tv.levels, {"normal": 20, "hdrStandard": 100})
        self.assertEqual(self.owed_on_disk(), {})

    def test_each_picture_mode_gets_its_own_original_back(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        self.tv.switch_mode("cinema", 30)  # user changed mode mid-movie
        self.observe(controller, False, 2)  # cinema was never boosted
        self.observe(controller, True, 2)  # new session boosts cinema too
        self.assertEqual(self.tv.levels, {"normal": 80, "cinema": 80})

        self.observe(controller, False, 2)
        self.assertEqual(self.tv.levels["cinema"], 30)
        self.assertEqual(self.owed_on_disk(), {"normal": 20})
        self.tv.switch_mode("normal", 80)
        self.observe(controller, False, 12)
        self.assertEqual(self.tv.levels, {"normal": 20, "cinema": 30})

    def test_unreachable_tv_is_retried(self) -> None:
        self.tv.online = False
        controller = self.make()
        self.observe(controller, True, 2)
        self.assertEqual(controller.status, "TV unreachable, retrying")

        self.tv.online = True
        self.observe(controller, True, 5)
        self.assertEqual(self.tv.writes, [])  # waits for the retry interval
        self.observe(controller, True, 6)
        self.assertEqual(self.tv.writes, [("normal", 80)])

    def test_restore_owed_before_a_restart_is_completed(self) -> None:
        self.observe(self.make(), True, 2)  # boosted, then the app died
        restarted = self.make()
        self.observe(restarted, False, 2)
        self.assertEqual(self.tv.backlight, 20)
        self.assertEqual(self.owed_on_disk(), {})

    def test_restart_mid_movie_keeps_the_true_original(self) -> None:
        self.observe(self.make(), True, 2)
        restarted = self.make()
        self.observe(restarted, True, 2)  # reads 80 now, must not keep it
        self.observe(restarted, False, 2)
        self.assertEqual(self.tv.backlight, 20)

    def test_new_target_applies_while_watching(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        controller.target = 90
        self.observe(controller, True, 1)
        self.assertEqual(self.tv.backlight, 90)
        self.observe(controller, False, 2)
        self.assertEqual(self.tv.backlight, 20)

    def test_manual_change_between_sessions_becomes_the_original(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        self.observe(controller, False, 2)
        self.tv.levels["normal"] = 35  # user adjusted it with the remote
        self.observe(controller, True, 2)
        self.observe(controller, False, 2)
        self.assertEqual(self.tv.backlight, 35)

    def test_shutdown_restores(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        controller.shutdown()
        self.assertEqual(self.tv.backlight, 20)
        self.assertEqual(self.owed_on_disk(), {})

    def test_shutdown_with_tv_off_keeps_the_debt_on_disk(self) -> None:
        controller = self.make()
        self.observe(controller, True, 2)
        self.tv.online = False
        controller.shutdown()
        self.assertEqual(self.owed_on_disk(), {"normal": 20})


class RestoreStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "restore.json"

    def test_round_trip_and_clear(self) -> None:
        store = RestoreStore(self.path)
        store.save({"normal": 20})
        self.assertEqual(RestoreStore(self.path).load(), {"normal": 20})
        store.save({})
        self.assertFalse(self.path.exists())

    def test_unreadable_file_is_ignored(self) -> None:
        for content in ("not json", "[1, 2]", '{"normal": "bright"}'):
            self.path.write_text(content, encoding="utf-8")
            with self.assertLogs("potplayer_tv_brightness.controller", "WARNING"):
                self.assertEqual(RestoreStore(self.path).load(), {})


if __name__ == "__main__":
    unittest.main()
