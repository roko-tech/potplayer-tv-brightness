"""Decide when to raise the TV's OLED brightness and when to restore it.

Pure logic: no Win32 and no network. The TV adapter is injected, so every rule
here is covered by unit tests.
"""

from __future__ import annotations

import json
import logging
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

log = logging.getLogger(__name__)

# Picture levels are average brightness on a 0-255 scale (see scene.py).
DARK_BELOW = 40.0  # a scene darker than this counts as dark...
LIGHT_ABOVE = 55.0  # ...until it gets brighter than this; in between, no change
BLACK_BELOW = 2.0  # black frames (fades, cuts) say nothing about the scene


class TVError(Exception):
    """The TV is unreachable, not paired, or rejected a request."""


@dataclass(frozen=True)
class Picture:
    """The TV's current picture mode and its OLED Pixel Brightness (0-100)."""

    mode: str  # e.g. "normal" (Standard) or "hdrStandard"
    backlight: int


class TVSession(Protocol):
    def read_picture(self) -> Picture: ...

    def set_backlight(self, value: int) -> None: ...


class TV(Protocol):
    def session(self) -> AbstractContextManager[TVSession]: ...


class RestoreStore:
    """Original brightness per picture mode, kept on disk while it is owed.

    A crash, reboot, or switched-off TV mid-movie therefore still ends with the
    original value once the app runs and the TV is reachable again.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, int]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {str(mode): int(value) for mode, value in data.items()}
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, AttributeError, TypeError):
            log.warning("Ignoring unreadable %s", self.path.name)
            return {}

    def save(self, owed: dict[str, int]) -> None:
        if owed:
            self.path.write_text(json.dumps(owed), encoding="utf-8")
        else:
            self.path.unlink(missing_ok=True)


def is_hdr(mode: str) -> bool:
    """HDR and Dolby Vision picture modes are named hdr* or dolby*."""
    mode = mode.lower()
    return "hdr" in mode or "dolby" in mode


class Controller:
    """Hold the target brightness while watching; restore it otherwise.

    Picture settings are stored per picture mode, so the original value is
    remembered per mode and only written back to that same mode. A restore
    that cannot happen yet (TV off, or in another mode after an HDR switch) is
    retried every ``retry_s`` seconds.

    During a dark scene the target is ``dark_target`` instead, if that is
    higher. A scene counts as dark after ``dark_s`` seconds of dark picture
    levels, and no longer after ``light_s`` seconds of bright ones.
    """

    def __init__(
        self,
        tv: TV,
        store: RestoreStore,
        target: int,
        dark_target: int = 0,
        *,
        settle_s: float = 1.0,
        retry_s: float = 10.0,
        dark_s: float = 2.0,
        light_s: float = 1.0,
    ) -> None:
        self.tv = tv
        self.store = store
        self.target = target
        self.dark_target = dark_target  # 0, or anything not above target: off
        self.settle_s = settle_s
        self.retry_s = retry_s
        self.dark_s = dark_s
        self.light_s = light_s
        self.owed = store.load()  # picture mode -> original brightness
        self.boosted_to: int | None = None
        self.watching: bool | None = None  # None until the first settled state
        self.dark = False  # a dark scene is on screen (settled)
        self.status = "Starting"
        self._seen: bool | None = None
        self._seen_since = 0.0
        self._scene: bool | None = None  # what the latest picture level says
        self._scene_since = 0.0
        self._retry_at = 0.0

    @property
    def boosted(self) -> bool:
        return self.boosted_to is not None

    @property
    def dark_on(self) -> bool:
        """Whether dark scenes get their own brightness."""
        return self.dark_target > self.target

    def tick(self, watching: bool, now: float, level: float | None = None) -> None:
        """Feed one PotPlayer observation; act once it has held for settle_s.

        ``level`` is the picture's average brightness (0-255), if measured.
        """
        if watching != self._seen:
            self._seen, self._seen_since = watching, now
        if self._seen != self.watching and now - self._seen_since >= self.settle_s:
            self.watching = self._seen
            self._retry_at = 0.0  # a new state deserves an immediate attempt
        self._follow_scene(level, now)
        if self.watching is None or now < self._retry_at:
            return
        try:
            done = self._boost() if self.watching else self._restore()
        except TVError as error:
            self._set_status("TV unreachable, retrying", str(error))
            done = False
        if not done:
            self._retry_at = now + self.retry_s

    def shutdown(self) -> None:
        """Best-effort restore on exit; anything still owed stays on disk."""
        try:
            self._restore()
        except TVError as error:
            log.warning("Restore on exit failed: %s", error)

    def _follow_scene(self, level: float | None, now: float) -> None:
        if not self.watching or not self.dark_on:
            self.dark, self._scene = False, None  # every session starts normal
            return
        if level is None or level < BLACK_BELOW:
            return
        if level < DARK_BELOW:
            dark = True
        elif level > LIGHT_ABOVE:
            dark = False
        else:
            dark = self.dark
        if dark != self._scene:
            self._scene, self._scene_since = dark, now
        hold = self.dark_s if dark else self.light_s
        if dark != self.dark and now - self._scene_since >= hold:
            self.dark = dark
            log.info("Picture level %.0f: %s", level, "dark" if dark else "not dark")

    def _boost(self) -> bool:
        target = self.dark_target if self.dark else self.target
        if self.boosted_to == target:
            return True
        with self.tv.session() as tv:
            picture = tv.read_picture()
            if is_hdr(picture.mode):
                self._set_status(f"HDR mode ({picture.mode}), brightness left alone")
                return False  # re-check later: the TV may return to SDR
            if picture.mode not in self.owed:
                self.owed[picture.mode] = picture.backlight
                self.store.save(self.owed)
            tv.set_backlight(target)
        self.boosted_to = target
        original = self.owed[picture.mode]
        scene = "Watching a dark scene" if self.dark else "Watching"
        self._set_status(f"{scene}: brightness {target} (restores {original})")
        return True

    def _restore(self) -> bool:
        self.boosted_to = None  # the next watching session boosts afresh
        if not self.owed:
            self._set_status("Idle")
            return True
        with self.tv.session() as tv:
            picture = tv.read_picture()
            original = self.owed.get(picture.mode)
            if original is not None:
                tv.set_backlight(original)
                del self.owed[picture.mode]
                self.store.save(self.owed)
                log.info("Restored brightness %d (%s)", original, picture.mode)
        if self.owed:
            modes = ", ".join(sorted(self.owed))
            self._set_status(f"Restore waiting for picture mode: {modes}")
            return False
        self._set_status("Idle")
        return True

    def _set_status(self, status: str, detail: str = "") -> None:
        if status != self.status:
            log.info("%s%s", status, f" ({detail})" if detail else "")
            self.status = status
