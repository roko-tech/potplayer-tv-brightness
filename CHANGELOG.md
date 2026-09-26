# Changelog

All notable changes to this project are documented here. Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and use semantic versioning when the project exposes a versioned public contract.

## [Unreleased]

### Added

- Tray app that sets the LG TV's OLED Pixel Brightness to a chosen value while PotPlayer plays, and restores the original on pause, stop, minimize, close, or Quit.
- Original brightness saved per picture mode in `restore.json`, so crashes, reboots, a switched-off TV, and HDR switches still end at the original value. HDR and Dolby Vision modes are left unchanged.
- Tray presets from 30 to 100, a status tooltip, and `scripts/tv_check.py` for live TV checks.
- Project documentation, CI (ruff, mypy, unit tests on Ubuntu and Windows), and Dependabot for uv, based on roko-tech/project-starter.
- A connection step: `uv run python -m scripts.tv_check --host <TV IP>` pairs with the TV (Accept prompt) and saves the address once the TV answers. The README and user guide explain how to find the TV's address and fix connection problems.

- MIT license. The README credits lgtv2 for the TV pairing manifest.

### Changed

- No built-in TV address. Starting the app before connecting a TV shows how to connect and exits.
- Security reports go through GitHub private vulnerability reporting.

### Fixed

- A malformed TV address (for example one with a port) now gives a clear "Cannot connect" error, retried like an unreachable TV, instead of an unexpected-error traceback.
- `tv_check --set` clamps the value to 0 to 100, like every other brightness write.
