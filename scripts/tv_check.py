"""Live TV check: print the picture mode and OLED Pixel Brightness.

    uv run python -m scripts.tv_check            # read only
    uv run python -m scripts.tv_check --set 25   # set, then read back

Uses the app's settings.json and paired client key. The first run against an
unpaired TV shows an Accept prompt on the TV.
"""

from __future__ import annotations

import argparse
import sys
import time

from potplayer_tv_brightness.app import KEY_FILE, load_settings
from potplayer_tv_brightness.controller import TVError
from potplayer_tv_brightness.tv import LGTV


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--set", type=int, metavar="0-100", help="value to set first")
    args = parser.parse_args(argv)
    try:
        with LGTV(load_settings().tv_host, KEY_FILE).session() as tv:
            if args.set is not None:
                tv.set_backlight(args.set)
                time.sleep(0.5)  # let the TV apply it before reading back
            picture = tv.read_picture()
    except TVError as error:
        print(f"TV check failed: {error}", file=sys.stderr)
        return 1
    print(f"Picture mode: {picture.mode}, OLED Pixel Brightness: {picture.backlight}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
