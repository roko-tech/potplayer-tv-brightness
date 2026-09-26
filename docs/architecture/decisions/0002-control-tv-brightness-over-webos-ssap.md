# ADR-0002: Control TV brightness over webOS SSAP from a Python tray app

- Date: 2026-09-25
- Status: Accepted
- Owners: @rokogan
- Related: [Product brief](../../product/brief.md)

## Context

The LG C2 is the PC's display. TVs do not implement DDC/CI, so Windows monitor brightness APIs cannot change it. The app must also know when PotPlayer is playing, paused, minimized, or closed.

## Decision drivers

- Change the real OLED Pixel Brightness, not a software dimming layer.
- No visible popups on the TV and no rooting or developer-mode apps (the dev shell cannot run `luna-send` on this firmware).
- Small codebase in the owner's usual stack (Python tray apps).

## Considered options

### SSAP `ssap://settings/setSystemSettings` (chosen)

The TV's second-screen API over a TLS WebSocket on port 3001. With the standard signed LG manifest (which includes `WRITE_SETTINGS`) the TV accepts `{"category": "picture", "settings": {"backlight": N}}`. Verified live on webOS 25: 20 → 30 → 20, read back each time, no popup.

### luna call through a notification alert (bscpylgtv method)

Creates and closes an alert whose `onclose` runs `luna://com.webos.settingsservice/setSystemSettings`. It works on many firmwares but flashes an alert on screen, and LG has restricted it before. Kept as the fallback if LG removes the direct write.

### LG IP Control (port 9761)

Needs a hidden-menu setup and a keycode, and has no documented brightness command.

### Windows gamma or HDR "SDR content brightness"

Software dimming of the signal. It does not change the panel's light output and costs tonal precision.

## Decision

- **TV:** a minimal SSAP client (`tv.py`) on `websocket-client`. It reuses the widely published signed manifest (copied from the lgtv2 package as `pairing.json`), opens one short connection per operation, and suppresses the `Origin` header, which webOS rejects with "invalid origin".
- **PotPlayer:** its window-message API. `WM_USER` with `0x5006` returns -1 idle, 1 paused, 2 playing, as validated against stock PotPlayerMini64. Minimized or hidden windows count as not watching. Chosen over window titles (no state) and Windows media controls (PotPlayer does not report reliably).
- **App:** Python 3.12 with `pystray` and `Pillow` for the tray icon, managed by uv with exact pins and `uv.lock`.

## Consequences

### Positive

- Real brightness changes with no on-screen artifacts, in about a second.
- Three small runtime dependencies; the rules are pure Python and unit-tested.

### Negative and tradeoffs

- Depends on an unofficial LG API that firmware updates may change.
- The TV's self-signed certificate cannot be verified (see the threat model).
- Windows only.

### Follow-up

If a firmware update rejects the write, `uv run python -m scripts.tv_check --set N` shows it; then implement the alert fallback.

## Validation

Live runs on the LG C2 (webOS 25) with PotPlayer 64-bit: play, pause, resume, minimize, crash, restart, and close all read back the expected brightness. See [testing](../../testing.md).
