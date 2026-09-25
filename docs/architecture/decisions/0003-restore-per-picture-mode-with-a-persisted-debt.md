# ADR-0003: Restore per picture mode, with the original saved on disk

- Date: 2026-09-25
- Status: Accepted
- Owners: @rokogan
- Related: [ADR-0002](0002-control-tv-brightness-over-webos-ssap.md)

## Context

The TV stores OLED Pixel Brightness per picture mode, and the write applies to whatever mode is active. The active mode can change during a movie (Windows or PotPlayer switching to HDR, or the owner picking another mode). The app can also die mid-movie, and the TV can be off when a restore is due. A naive "remember in memory, write back on pause" design can write the desktop value into an HDR mode, or leave the desktop at movie brightness after a crash.

## Considered options

1. Remember one value in memory and write it back to whatever mode is active. Simple, but wrong after mode changes, and lost on a crash.
2. Remember one value and its mode on disk. Correct, but a pending restore for one mode would block boosting in another.
3. **Remember the original per mode on disk (chosen).**

## Decision

- When playback starts, read the active mode and brightness. If this mode has no saved original yet, save it to `restore.json` **before** writing the movie value.
- On pause, minimize, or close, write each saved original back only while its own mode is active. Anything not yet restored stays on disk and is retried every 10 s. This also covers a TV that is off.
- HDR and Dolby Vision modes (names containing `hdr` or `dolby`) are never changed.
- A saved original is never overwritten while it is owed. This is what makes a restart mid-movie safe, since the TV then reads the movie value.
- A PotPlayer state must hold for 1 s before acting.

## Consequences

- The desktop always ends up at its original value in its own mode, even after crashes, reboots, or HDR switches.
- A restore can stay pending until the owner returns to the original mode. The tray tooltip shows this.
- Mode names are the key, so a different input or app using the same mode name is not told apart (documented limitation).

## Validation

Unit tests in `tests/test_controller.py` cover each rule, including restart mid-movie, HDR switches, per-mode originals, and an unreachable TV. A live crash-and-restart run on the C2 kept `{"normal": 20}` and restored it.
