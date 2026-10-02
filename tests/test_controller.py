from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from potplayer_tv_brightness.controller import (
    DARK_BELOW,
    LIGHT_ABOVE,
    Controller,
    Picture,
    RestoreStore,
    TVError,
)

STEP = 0.5  # the app polls PotPlayer every 0.5 s
# Picture levels (0-255), as scene.picture_level measures them.
DARK = DARK_BELOW / 2
NORMAL = LIGHT_ABOVE * 2
BETWEEN = (DARK_BELOW + LIGHT_ABOVE) / 2  # no change either way
BLACK = 0.0


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

    def make(self, target: int = 80, dark_target: int = 0) -> Controller:
        return Controller(
            self.tv,
            RestoreStore(self.path),
            target,
            dark_target,
            settle_s=1.0,
            retry_s=10.0,
            dark_s=2.0,
            light_s=1.0,
        )

    def observe(
        self,
        controller: Controller,
        watching: bool,
        seconds: float,
        level: float | None = None,
    ) -> None:
        for _ in range(round(seconds / STEP)):
            controller.tick(watching, self.now, level)
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

    # Dark scenes: their own brightness, then back to the movie value.
    def watch_dark_scene(self) -> Controller:
        """Movie value 40, dark scene value 70; ends 70 into a dark scene."""
        controller = self.make(target=40, dark_target=70)
        self.observe(controller, True, 2, NORMAL)
        self.observe(controller, True, 3, DARK)
        self.assertEqual(self.tv.writes, [("normal", 40), ("normal", 70)])
        return controller

    def test_dark_scene_raises_brightness_until_it_ends(self) -> None:
        controller = self.make(target=40, dark_target=70)
        self.observe(controller, True, 2, NORMAL)
        self.assertEqual(self.tv.backlight, 40)

        self.observe(controller, True, 1.5, DARK)  # not dark for 2 s yet
        self.assertEqual(self.tv.backlight, 40)
        self.observe(controller, True, 1, DARK)
        self.assertEqual(self.tv.backlight, 70)
        self.assertEqual(
            controller.status, "Watching a dark scene: brightness 70 (restores 20)"
        )

        self.observe(controller, True, 0.5, NORMAL)  # a flash, e.g. lightning
        self.assertEqual(self.tv.backlight, 70)
        self.observe(controller, True, 1.5, NORMAL)
        self.assertEqual(self.tv.backlight, 40)
        self.assertEqual(
            self.tv.writes, [("normal", 40), ("normal", 70), ("normal", 40)]
        )
        self.assertEqual(self.owed_on_disk(), {"normal": 20})

    def test_black_frames_and_unmeasured_levels_change_nothing(self) -> None:
        controller = self.watch_dark_scene()
        self.observe(controller, True, 5, BLACK)  # fade to black
        self.observe(controller, True, 5, None)  # e.g. a window covers it
        self.assertEqual(self.tv.backlight, 70)

        self.observe(controller, True, 2, NORMAL)
        self.observe(controller, True, 5, BLACK)
        self.observe(controller, True, 5, None)
        self.assertEqual(self.tv.backlight, 40)

    def test_levels_between_the_thresholds_keep_the_scene(self) -> None:
        controller = self.watch_dark_scene()
        self.observe(controller, True, 10, BETWEEN)
        self.assertEqual(self.tv.backlight, 70)
        self.observe(controller, True, 2, NORMAL)
        self.observe(controller, True, 10, BETWEEN)
        self.assertEqual(self.tv.backlight, 40)

    def test_a_short_dark_spell_is_ignored(self) -> None:
        controller = self.make(target=40, dark_target=70)
        self.observe(controller, True, 2, NORMAL)
        for _ in range(3):  # dark, then a level in between, which resets the wait
            self.observe(controller, True, 1.5, DARK)
            self.observe(controller, True, 0.5, BETWEEN)
        self.assertEqual(self.tv.writes, [("normal", 40)])

    def test_off_or_not_above_the_movie_value_does_nothing(self) -> None:
        for dark_target in (0, 30, 40):
            with self.subTest(dark_target=dark_target):
                self.tv = FakeTV()
                self.path.unlink(missing_ok=True)
                controller = self.make(target=40, dark_target=dark_target)
                self.observe(controller, True, 10, DARK)
                self.assertEqual(self.tv.writes, [("normal", 40)])
                self.assertFalse(controller.dark)

    def test_pause_in_a_dark_scene_restores_the_original(self) -> None:
        controller = self.watch_dark_scene()
        self.observe(controller, False, 2)
        self.assertEqual(self.tv.backlight, 20)
        self.assertEqual(self.owed_on_disk(), {})
        self.assertEqual(controller.status, "Idle")

        self.observe(controller, True, 2, DARK)  # the next session starts normal
        self.assertEqual(self.tv.writes[-1], ("normal", 40))
        self.observe(controller, True, 2, DARK)
        self.assertEqual(self.tv.backlight, 70)

    def test_restart_in_a_dark_scene_keeps_the_true_original(self) -> None:
        self.watch_dark_scene()  # then the app died at 70
        restarted = self.make(target=40, dark_target=70)
        self.observe(restarted, True, 2, NORMAL)  # reads 70 now, must not keep it
        self.observe(restarted, True, 3, DARK)
        self.assertEqual(self.owed_on_disk(), {"normal": 20})
        self.observe(restarted, False, 2)
        self.assertEqual(self.tv.backlight, 20)

    def test_hdr_mode_is_left_alone_in_dark_scenes(self) -> None:
        self.tv = FakeTV(mode="hdrStandard", backlight=100)
        controller = self.make(target=40, dark_target=70)
        self.observe(controller, True, 30, DARK)
        self.assertEqual(self.tv.writes, [])
        self.assertIn("HDR", controller.status)

    def test_menu_changes_apply_during_a_dark_scene(self) -> None:
        controller = self.watch_dark_scene()
        controller.dark_target = 90
        self.observe(controller, True, 0.5, DARK)
        self.assertEqual(self.tv.backlight, 90)
        controller.dark_target = 0  # Off
        self.observe(controller, True, 0.5, DARK)
        self.assertEqual(self.tv.backlight, 40)
        self.assertFalse(controller.dark)


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
