# PotPlayer TV Brightness

A Windows tray app for an LG webOS TV used as a PC monitor. While PotPlayer is playing, it sets the TV's **OLED Pixel Brightness** to your movie value. When you pause, minimize, or close PotPlayer, it puts the original value back.

Tested on an LG C2 (webOS 25) with PotPlayer 64-bit. Other LG webOS TVs may work but are untested.

## Requirements

- Windows 10 or 11, Python 3.12, [uv](https://docs.astral.sh/uv/), and PotPlayer.
- An LG webOS TV on the same home network as the PC.

## Install

```shell
git clone https://github.com/roko-tech/potplayer-tv-brightness.git
cd potplayer-tv-brightness
uv sync
```

## Connect your TV

Do this once, with the TV on.

1. Find the TV's IP address: on the TV, open **Settings > General > Network** and select your wired or Wi-Fi connection. Your router's device list shows it too.
2. Run this with your TV's address:

   ```shell
   uv run python -m scripts.tv_check --host 192.168.1.50
   ```

3. The TV asks to allow the connection. Select **Accept** with the remote within 60 seconds.

When it works, it prints the TV's picture mode and brightness. Tips and fixes: [Connect your TV](docs/user/README.md#connect-your-tv).

## Start

```shell
.venv\Scripts\pythonw.exe run.pyw
```

A sun icon appears in the tray. To start it with Windows, see the [user guide](docs/user/README.md#start-with-windows).

## Use

- Right-click the tray icon, then **Movie brightness** to pick the value (30 to 100).
- The icon turns amber while the movie brightness is on. Hover it to see the status.
- **Quit** restores the original brightness before exiting.

Details and troubleshooting: [user guide](docs/user/README.md).

## Development

```shell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/verify.py
uv run python -m unittest discover -s tests -v
uv run python -m scripts.tv_check        # live: read the TV's picture mode and brightness
```

## Docs

- [Product brief](docs/product/brief.md)
- [Architecture](docs/architecture/overview.md) and [decisions](docs/architecture/decisions/README.md)
- [Testing](docs/testing.md), [threat model](docs/security/threat-model.md), [runbook](docs/operations/runbook.md)
- [Documentation map](docs/README.md)

## License

None. Private personal tool; not for distribution.
