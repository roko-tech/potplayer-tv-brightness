"""Connect to the TV, then print its picture mode and OLED Pixel Brightness.

    uv run python -m scripts.tv_check --host 192.168.1.50   # connect a TV
    uv run python -m scripts.tv_check                        # read only
    uv run python -m scripts.tv_check --set 25               # set, then read back

The first connection shows a prompt on the TV: accept it with the remote.
--host is saved to settings.json once the TV answers.
"""

from __future__ import annotations

import argparse
import sys
import time

from potplayer_tv_brightness.app import KEY_FILE, load_settings, save_settings
from potplayer_tv_brightness.controller import TVError
from potplayer_tv_brightness.tv import LGTV


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--host", help="the TV's IP address")
    parser.add_argument("--set", type=int, metavar="0-100", help="value to set first")
    args = parser.parse_args(argv)
    settings = load_settings()
    host = args.host or settings.tv_host
    if not host:
        print(
            "No TV address yet. Run: "
            "uv run python -m scripts.tv_check --host <TV IP address>",
            file=sys.stderr,
        )
        return 1
    if not KEY_FILE.exists():
        print("Accept the connection prompt on the TV with the remote (60 s).")
    try:
        with LGTV(host, KEY_FILE).session() as tv:
            if args.set is not None:
                tv.set_backlight(max(0, min(100, args.set)))
                time.sleep(0.5)  # let the TV apply it before reading back
            picture = tv.read_picture()
    except TVError as error:
        print(f"TV check failed: {error}", file=sys.stderr)
        return 1
    if host != settings.tv_host:
        settings.tv_host = host
        save_settings(settings)
        print(f"Saved TV address {host} to settings.json.")
    print(f"Picture mode: {picture.mode}, OLED Pixel Brightness: {picture.backlight}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
