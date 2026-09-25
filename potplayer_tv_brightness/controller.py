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
    """

    def __init__(
        self,
        tv: TV,
        store: RestoreStore,
        target: int,
        *,
        settle_s: float = 1.0,
        retry_s: float = 10.0,
    ) -> None:
        self.tv = tv
        self.store = store
        self.target = target
        self.settle_s = settle_s
        self.retry_s = retry_s
        self.owed = store.load()  # picture mode -> original brightness
        self.boosted_to: int | None = None
        self.watching: bool | None = None  # None until the first settled state
        self.status = "Starting"
        self._seen: bool | None = None
        self._seen_since = 0.0
        self._retry_at = 0.0

    @property
    def boosted(self) -> bool:
        return self.boosted_to is not None

    def tick(self, watching: bool, now: float) -> None:
        """Feed one PotPlayer observation; act once it has held for settle_s."""
        if watching != self._seen:
            self._seen, self._seen_since = watching, now
        if self._seen != self.watching and now - self._seen_since >= self.settle_s:
            self.watching = self._seen
            self._retry_at = 0.0  # a new state deserves an immediate attempt
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

    def _boost(self) -> bool:
        target = self.target
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
        self._set_status(f"Watching: brightness {target} (restores {original})")
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
