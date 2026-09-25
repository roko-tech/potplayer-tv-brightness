"""Tray app: poll PotPlayer, drive the controller, and show its status."""

from __future__ import annotations

import ctypes
import json
import logging
import math
import threading
import time
from dataclasses import asdict, dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from . import potplayer
from .controller import Controller, RestoreStore
from .tv import LGTV

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / "settings.json"
KEY_FILE = ROOT / "tv-client-key.txt"
RESTORE_FILE = ROOT / "restore.json"
LOG_FILE = ROOT / "potplayer-tv-brightness.log"
PRESETS = (30, 40, 50, 60, 70, 80, 90, 100)
POLL_S = 0.5
ERROR_ALREADY_EXISTS = 183

log = logging.getLogger("potplayer_tv_brightness")
_instance_mutex: Any = None  # single-instance handle, held until exit


@dataclass
class Settings:
    tv_host: str = "192.168.8.145"
    movie_brightness: int = 80


def load_settings(path: Path = SETTINGS_FILE) -> Settings:
    """Read settings.json, creating it with defaults on first run."""
    if not path.exists():
        settings = Settings()
        save_settings(settings, path)
        return settings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        brightness = max(0, min(100, int(data["movie_brightness"])))
        return Settings(str(data["tv_host"]), brightness)
    except (OSError, ValueError, KeyError, TypeError) as error:
        log.warning("%s is invalid (%s); using defaults", path.name, error)
        return Settings()


def save_settings(settings: Settings, path: Path = SETTINGS_FILE) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2) + "\n", encoding="utf-8")


def icon_image(active: bool) -> Image.Image:
    """A sun: amber while the movie brightness is applied, grey otherwise."""
    color = (255, 184, 0, 255) if active else (150, 150, 150, 255)
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((19, 19, 45, 45), fill=color)
    for step in range(8):
        dx, dy = math.cos(step * math.pi / 4), math.sin(step * math.pi / 4)
        draw.line((32 + 20 * dx, 32 + 20 * dy, 32 + 29 * dx, 32 + 29 * dy), color, 5)
    return image


def _already_running() -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    global _instance_mutex
    _instance_mutex = kernel32.CreateMutexW(
        None, False, "Local\\potplayer-tv-brightness"
    )
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def main() -> None:
    logging.basicConfig(
        handlers=[
            RotatingFileHandler(
                LOG_FILE, maxBytes=256_000, backupCount=1, encoding="utf-8"
            )
        ],
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    if _already_running():
        log.info("Already running; exiting")
        return

    import pystray  # Windows tray backend; imported here to keep tests headless

    settings = load_settings()
    controller = Controller(
        LGTV(settings.tv_host, KEY_FILE),
        RestoreStore(RESTORE_FILE),
        settings.movie_brightness,
    )
    stop = threading.Event()

    def choose(value: int) -> Any:
        def action(icon: Any, item: Any) -> None:
            controller.target = settings.movie_brightness = value
            save_settings(settings)
            log.info("Movie brightness set to %d", value)

        return action

    def quit_app(icon: Any, item: Any) -> None:
        stop.set()
        worker.join(timeout=15)  # lets the worker restore the TV first
        icon.stop()

    presets = pystray.Menu(
        *(
            pystray.MenuItem(
                str(value),
                choose(value),
                checked=lambda item, value=value: controller.target == value,
                radio=True,
            )
            for value in PRESETS
        )
    )
    icon = pystray.Icon(
        "potplayer-tv-brightness",
        icon_image(False),
        "PotPlayer TV Brightness",
        pystray.Menu(
            pystray.MenuItem("Movie brightness", presets),
            pystray.MenuItem("Quit", quit_app),
        ),
    )

    def poll() -> None:
        shown: tuple[bool, str] | None = None
        while not stop.wait(POLL_S):
            try:
                controller.tick(potplayer.is_watching(), time.monotonic())
            except Exception:
                log.exception("Unexpected error")
            view = (controller.boosted, controller.status)
            if view != shown:
                icon.icon = icon_image(controller.boosted)
                icon.title = f"PotPlayer TV Brightness: {controller.status}"[:127]
                shown = view
        controller.shutdown()

    worker = threading.Thread(target=poll, name="poll", daemon=True)

    def setup(icon: Any) -> None:
        icon.visible = True
        log.info(
            "Started (TV %s, movie brightness %d)", settings.tv_host, controller.target
        )
        worker.start()

    icon.run(setup)
