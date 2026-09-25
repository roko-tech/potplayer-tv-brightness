# PotPlayer TV Brightness

A Windows tray app for an LG webOS TV (built for the LG C2). While PotPlayer is playing, it sets the TV's **OLED Pixel Brightness** to your movie value. When you pause, minimize, or close PotPlayer, it puts the original value back.

## Quick start

Needs Windows, Python 3.12, [uv](https://docs.astral.sh/uv/), and the TV on the same network.

```shell
uv sync
.venv\Scripts\pythonw.exe run.pyw
```

A sun icon appears in the tray. On first use the TV shows an Accept prompt; accept it once. The TV address is in `settings.json`, created on first run.

## Use

- Right-click the tray icon, then **Movie brightness** to pick the value (30 to 100).
- The icon turns amber while the movie brightness is on. Hover it to see the status.
- **Quit** restores the original brightness before exiting.

Details, auto-start, and troubleshooting: [user guide](docs/user/README.md).

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
