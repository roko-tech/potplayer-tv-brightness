# Changelog

All notable changes to this project are documented here. Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and use semantic versioning when the project exposes a versioned public contract.

## [Unreleased]

### Added

- Tray app that sets the LG TV's OLED Pixel Brightness to a chosen value while PotPlayer plays, and restores the original on pause, stop, minimize, close, or Quit.
- Original brightness saved per picture mode in `restore.json`, so crashes, reboots, a switched-off TV, and HDR switches still end at the original value. HDR and Dolby Vision modes are left unchanged.
- Tray presets from 30 to 100, a status tooltip, and `scripts/tv_check.py` for live TV checks.
- Project documentation, CI (ruff, mypy, unit tests on Ubuntu and Windows), and Dependabot for uv, based on roko-tech/project-starter.
