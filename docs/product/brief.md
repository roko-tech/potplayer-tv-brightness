# Product brief

- Status: Accepted (v0.1.0)
- Product owner: @rokogan
- Technical owner: @rokogan
- Last reviewed: 2026-09-26

## Problem

The LG C2 doubles as the PC monitor. For desktop use its OLED Pixel Brightness is kept low (20) to protect the panel and eyes. Movies in PotPlayer look dim at that level, so the owner raises it with the remote every time and often forgets to lower it again afterwards.

TVs do not support DDC/CI, so Windows brightness controls cannot change it.

## Users and stakeholders

| Group | Need | Current workaround | Risk if unmet |
| --- | --- | --- | --- |
| Owner watching in PotPlayer | Bright picture while watching, low brightness for desktop use | Change OLED Pixel Brightness with the remote, twice per movie | Dim movies, or a desktop left at movie brightness |
| Maintainer (same person) | Small, understandable code | None | Hard to fix after TV firmware changes |
| Someone else with PotPlayer and an LG webOS TV | Connect their own TV without reading the code | None: the app assumed the owner's TV address | Cannot get started |

## Proposed outcome

The TV switches to the chosen movie brightness shortly after PotPlayer starts playing, and returns to the previous value when playback pauses, stops, is minimized, or PotPlayer closes. No manual steps.

## Success measures

| Measure | Baseline | Target | Measurement window | Owner |
| --- | --- | --- | --- | --- |
| Manual brightness changes per movie | 2 | 0 | First two weeks of use | @rokogan |
| Time from play/pause to TV change | Manual | Under 3 s | Live check per release | @rokogan |
| Desktop left at movie brightness after a session | Happens | Never, including after a crash or with the TV off | Live and unit tests | @rokogan |

## Scope

### In scope

- Detect PotPlayer playing (not paused, stopped, minimized, hidden, or closed).
- Set and restore OLED Pixel Brightness on an LG webOS TV over the local network.
- Tray icon with status, movie brightness presets, and Quit.

### Non-goals

- Other players, other TV settings (contrast, picture mode), or other TV brands.
- Changing brightness in HDR or Dolby Vision picture modes.
- An installer or a packaged executable.
- Auto-discovery of the TV on the network.

## Constraints and assumptions

- Windows 10/11 and Python 3.12. The TV and PC are on the same trusted home network.
- "Screen brightness" means OLED Pixel Brightness (the `backlight` setting), not the black-level "Brightness" setting.
- The TV accepts `ssap://settings/setSystemSettings` for picture settings. Verified on the LG C2 with webOS 25 (firmware 33.x); a future firmware could remove it.
- PotPlayer answers its window-message API (`WM_USER` + `0x5006`) with its play state.

## Primary journey and acceptance

> Given the TV is at brightness 20 in picture mode "normal", when the owner plays a video in PotPlayer, then within 3 s the TV is at the movie brightness (80); when they pause, minimize, or close PotPlayer, then within 3 s it is back at 20.

Failure and recovery cases:

- The TV is off or unreachable: nothing crashes; the change is retried every 10 s.
- The app crashes or the PC restarts mid-movie: the original value is kept in `restore.json` and restored on the next start.
- The TV changed picture mode (e.g. an HDR switch): the original is only written back to the mode it came from, once that mode is active again.

First-time setup:

> Given an LG webOS TV that is on and on the same network, when a new user runs `tv_check --host <TV IP>` and accepts the prompt on the TV, then the command prints the TV's picture mode and brightness, and the app starts with that TV. A declined prompt, an unreachable TV, or a malformed address saves nothing and prints a clear error. Starting the app before connecting explains how to connect.

## Risks and unknowns

| Risk or unknown | Likelihood | Impact | Validation or mitigation | Owner |
| --- | --- | --- | --- | --- |
| LG firmware blocks the settings write | Low to medium | App stops working | `scripts/tv_check.py` detects it; fallback is the luna notification-alert method (see ADR-0002) | @rokogan |
| Restore lands on the wrong input | Low | Another input's brightness changes | Documented limitation; restore is limited to the original picture mode | @rokogan |
| PotPlayer changes its message API | Low | No detection | Live check each PotPlayer upgrade | @rokogan |

## Delivery slices

1. (Done) Play/pause/minimize/close drives the TV brightness, with a crash-safe restore and a tray preset menu.
2. (Done) First-time setup: connect a TV with one command and the Accept prompt; no built-in TV address.
