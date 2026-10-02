# ADR-0005: Raise brightness in dark scenes from a screen measurement

- Date: 2026-10-02
- Status: Accepted
- Owners: @rokogan
- Related: [ADR-0002](0002-control-tv-brightness-over-webos-ssap.md), [ADR-0003](0003-restore-per-picture-mode-with-a-persisted-debt.md)

## Context

At the movie brightness, dark scenes are hard to see, while a higher value makes normal scenes too bright. The owner asked for a second, higher value during dark scenes, with the movie value back for normal scenes.

To do this, the app has to know how dark the picture is. PotPlayer's window-message API reports play state and position, not picture content. Measurements on the owner's PC (LG C2 as a 4K monitor, PotPlayer maximized):

- A GDI copy of the screen area under PotPlayer's window shows the real video, not a black frame. PotPlayer's renderer is composed by the desktop window manager.
- One copy of the middle of the 4K screen, scaled into 64x36 pixels with `StretchBlt`, takes about 20 ms, but only about 5 ms of it is CPU time. Pillow's `ImageGrab` copies the whole desktop first and took about 72 ms.
- One TV session (connect, register, read) takes about 0.1 s. The TV is not what makes a switch late.
- Real content on the owner's setup: a dark animated show averaged 27 to 39 (0 to 255) for long stretches, fades to black read exactly 0, and a bright shot read 58. In the synthetic test clip, encoded grays of 20, 25, and 47 read 12, 18, and 43 on screen: the owner's playback chain makes dark grays darker.

## Decision drivers

- Never put the original brightness at risk: the restore rules of ADR-0003 stay as they are.
- No flicker: fades, cuts to black, and brief flashes must not switch the brightness.
- No new dependency and little CPU, since it runs during every movie.
- Privacy in a public app: picture content must not be kept or sent anywhere.
- Off by default, so other users see no change.

## Considered options

### GDI `StretchBlt` of the middle of PotPlayer's window (chosen)

Copies the middle of the window from the screen into a 64x36 bitmap and averages it with Pillow, which the app already ships. About 30 lines of `ctypes`, and it works with any renderer the desktop window manager composes. It sees whatever is on screen, so another window over the picture would be measured. Exclusive fullscreen or protected video would read black.

### Pillow `ImageGrab`

One line, but it copies the whole desktop before cropping: about 3.5 times the cost of the chosen method.

### DXGI Desktop Duplication or Windows.Graphics.Capture

Faster for continuous capture, but needs new dependencies (Direct3D or WinRT bindings) and far more code. A measurement twice a second does not need it.

### The TV's own dynamic picture settings

The C2's Auto Dynamic Contrast works inside the TV, without this app's delay, but it adjusts contrast rather than OLED brightness, and it is the owner's TV setting rather than this app's. It stays an alternative the owner can try; the app does not touch it.

## Decision

- **Measure:** while PotPlayer plays and the dark scene value is above the movie value, the poll thread measures the picture every 0.5 s. That is the average luma (0 to 255) of the middle of the window. 1/8 of the width is left out on each side, which removes 4:3 pillarbox bars. 1/6 of the height is left out at the top and bottom, which removes 2.39:1 letterbox bars, most subtitles, and the player's controls. If the middle of the window shows another window, or the screen cannot be read, there is no measurement.
- **Decide:** a scene is dark once levels stay below 40 for 2 s. It is normal again once they stay above 55 for 1 s. Levels in between change nothing and cancel a pending switch. Black frames (below 2) and missing measurements are ignored, so a fade to black never switches. Every play starts at the movie value. Leaving dark scenes is faster than entering them, so a bright shot after a dark scene is too bright for as short a time as possible.
- **Apply:** the controller's target becomes the dark scene value during dark scenes. Writing it goes through the same `_boost` path as the movie value, so the original is still saved before the first write and never overwritten while owed. HDR and Dolby Vision modes are still left alone.
- **Keep nothing:** the copy is reduced to one number in memory. The log records only the level at each switch.
- **Control:** a **Dark scene brightness** tray submenu with Off and the movie presets. Values at or below the movie value are greyed out. The value is saved as `dark_scene_brightness` (0 is Off), and settings files without it load as Off.

## Consequences

### Positive

- Dark scenes get brighter and normal scenes keep the movie value, with no extra dependency.
- The restore guarantees are unchanged and covered by the same tests.
- When off, nothing is measured.

### Negative and tradeoffs

- Switches lag the picture: about 2 to 2.5 s into a dark scene and 1 to 1.5 s out of one. The TV changes in one step, not a fade.
- The cut-offs are fixed, and what looks dark depends on the content and the playback chain. They were chosen from the measurements above and may need tuning after real viewing.
- A measurement costs about 20 ms, 5 ms of it CPU, twice a second during playback.
- Exclusive fullscreen or protected video measures black and is ignored, so dark scenes are not detected there.

### Follow-up

- Tune the cut-offs and hold times if real viewing shows switches that are too frequent or too rare. The log lines `Picture level N: dark` and `Picture level N: not dark` show where switches happen.
- Watch for playback stutter. None was measured, because there is no API for dropped frames.

## Validation

Unit tests in `tests/test_controller.py` cover entering and leaving dark scenes, brief flashes and short dark spells, black frames, levels in between, Off, pause and restart in a dark scene, HDR, and menu changes during a dark scene. `tests/test_scene.py` covers the averaging, the middle area, a real screen copy, and missing or covered windows. `tests/test_app.py` covers the tray submenu and old settings files.

A live run on 2026-10-02 used the LG C2 (webOS 25), PotPlayer 64-bit maximized, and a synthetic clip: TV at 70 about 2.3 s after a dark segment began, back at 40 about 1 s after it ended. A flash, a fade to black, and an in-between level changed nothing, and pause, minimize, and close restored 20. See [testing](../../testing.md).
