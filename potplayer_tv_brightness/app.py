"""Tray app: poll PotPlayer, drive the controller, and show its status."""

from __future__ import annotations

import contextlib
import ctypes
import json
import logging
import math
import os
import sys
import threading
import time
import winreg
from dataclasses import asdict, dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from . import connect, potplayer, scene
from .controller import Controller, RestoreStore
from .tv import LGTV

APP_NAME = "PotPlayer TV Brightness"


def data_dir() -> Path:
    """The exe keeps its files per user; from source they stay in the repo."""
    if getattr(sys, "frozen", False):
        return Path(os.environ["APPDATA"]) / APP_NAME
    return Path(__file__).resolve().parent.parent


DATA_DIR = data_dir()
SETTINGS_FILE = DATA_DIR / "settings.json"
KEY_FILE = DATA_DIR / "tv-client-key.txt"
RESTORE_FILE = DATA_DIR / "restore.json"
LOG_FILE = DATA_DIR / "potplayer-tv-brightness.log"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
PRESETS = (30, 40, 50, 60, 70, 80, 90, 100)
POLL_S = 0.5
ERROR_ALREADY_EXISTS = 183

log = logging.getLogger("potplayer_tv_brightness")
_instance_mutex: Any = None  # single-instance handle, held until exit


@dataclass
class Settings:
    tv_host: str = ""  # set by the connect window or scripts.tv_check --host
    movie_brightness: int = 80
    dark_scene_brightness: int = 0  # 0: off; only applies above movie_brightness


def load_settings(path: Path = SETTINGS_FILE) -> Settings:
    """Read settings.json, creating it with defaults on first run."""
    if not path.exists():
        settings = Settings()
        save_settings(settings, path)
        return settings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        brightness = max(0, min(100, int(data["movie_brightness"])))
        dark = max(0, min(100, int(data.get("dark_scene_brightness", 0))))
        return Settings(str(data["tv_host"]), brightness, dark)
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


def launch_command() -> str:
    """How Windows starts this app at sign-in."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pythonw}" "{DATA_DIR / "run.pyw"}"'


def autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            command = winreg.QueryValueEx(key, APP_NAME)[0]
    except OSError:
        return False
    return bool(command == launch_command())


def set_autostart(enabled: bool) -> None:
    """Add or remove this app from the user's Run key (no admin rights needed)."""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            with contextlib.suppress(FileNotFoundError):
                winreg.DeleteValue(key, APP_NAME)


def _already_running() -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    global _instance_mutex
    _instance_mutex = kernel32.CreateMutexW(
        None, False, "Local\\potplayer-tv-brightness"
    )
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def main() -> None:
    with contextlib.suppress(AttributeError, OSError):  # crisp windows on HiDPI
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
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
    settings = load_settings()
    first_run = not settings.tv_host
    if first_run:
        host = connect.connect_dialog("", KEY_FILE, icon_image(True))
        if not host:
            log.info("No TV connected; exiting")
            return
        settings.tv_host = host
        save_settings(settings)

    import pystray  # Windows tray backend; imported here to keep tests headless

    controller = Controller(
        LGTV(settings.tv_host, KEY_FILE),
        RestoreStore(RESTORE_FILE),
        settings.movie_brightness,
        settings.dark_scene_brightness,
    )
    stop = threading.Event()
    connecting = threading.Lock()  # one connect window at a time

    def choose(value: int) -> Any:
        def action(icon: Any, item: Any) -> None:
            controller.target = settings.movie_brightness = value
            save_settings(settings)
            log.info("Movie brightness set to %d", value)

        return action

    def choose_dark(value: int) -> Any:
        def action(icon: Any, item: Any) -> None:
            controller.dark_target = settings.dark_scene_brightness = value
            save_settings(settings)
            log.info("Dark scene brightness set to %s", value or "Off")

        return action

    def connect_tv(icon: Any, item: Any) -> None:
        def run() -> None:  # off the tray thread, so the menu keeps working
            try:
                host = connect.connect_dialog(
                    settings.tv_host, KEY_FILE, icon_image(True)
                )
                if host:
                    settings.tv_host = host
                    save_settings(settings)
                    controller.tv = LGTV(host, KEY_FILE)
                    log.info("Connected to the TV at %s", host)
            finally:
                connecting.release()

        if connecting.acquire(blocking=False):
            threading.Thread(target=run, name="connect", daemon=True).start()

    def toggle_autostart(icon: Any, item: Any) -> None:
        try:
            set_autostart(not autostart_enabled())
        except OSError:
            log.exception("Could not change Start with Windows")

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
    dark_presets = pystray.Menu(
        pystray.MenuItem(
            "Off",
            choose_dark(0),
            checked=lambda item: controller.dark_target == 0,
            radio=True,
        ),
        *(
            pystray.MenuItem(
                str(value),
                choose_dark(value),
                checked=lambda item, value=value: controller.dark_target == value,
                radio=True,
                enabled=lambda item, value=value: value > controller.target,
            )
            for value in PRESETS
        ),
    )
    icon = pystray.Icon(
        "potplayer-tv-brightness",
        icon_image(False),
        APP_NAME,
        pystray.Menu(
            pystray.MenuItem("Movie brightness", presets),
            pystray.MenuItem("Dark scene brightness", dark_presets),
            pystray.MenuItem("Connect TV…", connect_tv),
            pystray.MenuItem(
                "Start with Windows",
                toggle_autostart,
                checked=lambda item: autostart_enabled(),
            ),
            pystray.MenuItem("Quit", quit_app),
        ),
    )

    def poll() -> None:
        shown: tuple[bool, str] | None = None
        while not stop.wait(POLL_S):
            try:
                window = potplayer.watching_window()
                level = None
                if window is not None and controller.dark_on:
                    level = scene.picture_level(window)
                controller.tick(window is not None, time.monotonic(), level)
            except Exception:
                log.exception("Unexpected error")
            view = (controller.boosted, controller.status)
            if view != shown:
                icon.icon = icon_image(controller.boosted)
                icon.title = f"{APP_NAME}: {controller.status}"[:127]
                shown = view
        controller.shutdown()

    worker = threading.Thread(target=poll, name="poll", daemon=True)

    def setup(icon: Any) -> None:
        icon.visible = True
        log.info(
            "Started (TV %s, movie brightness %d, dark scene brightness %s)",
            settings.tv_host,
            controller.target,
            controller.dark_target or "Off",
        )
        worker.start()
        if first_run:
            icon.notify("Right-click the sun icon for options.", f"{APP_NAME} is on")

    icon.run(setup)
