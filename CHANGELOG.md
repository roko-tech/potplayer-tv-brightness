# Changelog

All notable changes to this project are documented here. Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and use semantic versioning when the project exposes a versioned public contract.

## [Unreleased]

### Added

- **Dark scene brightness** in the tray menu (Off by default). While PotPlayer plays, the app measures how bright the middle of the picture is twice a second. After 2 s of dark picture it sets the TV to the dark scene value, and after 1 s of bright picture it returns to the movie value. Fades to black, short flashes, and in-between scenes change nothing. The measurement is reduced to one number in memory and never saved or sent. Settings files from 0.1.0 load with it Off.

## [0.1.0] - 2026-09-27

### Added

- Tray app that sets the LG TV's OLED Pixel Brightness to a chosen value while PotPlayer plays, and restores the original on pause, stop, minimize, close, or Quit.
- Original brightness saved per picture mode in `restore.json`, so crashes, reboots, a switched-off TV, and HDR switches still end at the original value. HDR and Dolby Vision modes are left unchanged.
- Tray presets from 30 to 100, a status tooltip, and `scripts/tv_check.py` for live TV checks.
- Project documentation, CI (ruff, mypy, unit tests on Ubuntu and Windows), and Dependabot for uv, based on roko-tech/project-starter.
- A connection step: `uv run python -m scripts.tv_check --host <TV IP>` pairs with the TV (Accept prompt) and saves the address once the TV answers. The README and user guide explain how to find the TV's address and fix connection problems.
- A single-file Windows exe, `PotPlayer-TV-Brightness.exe`, built with PyInstaller: no Python needed. Releases include `THIRD-PARTY-NOTICES.txt` and `SHA256SUMS.txt`, and are immutable.
- A Connect window on first start that finds LG TVs on the network and pairs with one click; typing the IP address still works.
- Tray menu items **Connect TV…** and **Start with Windows**.
- MIT license. The README credits lgtv2 for the TV pairing manifest.

### Changed

- No built-in TV address. Starting the app without one opens the Connect window.
- The exe keeps its files in `%APPDATA%\PotPlayer TV Brightness`; running from source keeps them in the repository folder.
- Security reports go through GitHub private vulnerability reporting.

### Fixed

- A malformed TV address (for example one with a port) now gives a clear "Cannot connect" error, retried like an unreachable TV, instead of an unexpected-error traceback.
- `tv_check --set` clamps the value to 0 to 100, like every other brightness write.

[Unreleased]: https://github.com/roko-tech/potplayer-tv-brightness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/roko-tech/potplayer-tv-brightness/releases/tag/v0.1.0
