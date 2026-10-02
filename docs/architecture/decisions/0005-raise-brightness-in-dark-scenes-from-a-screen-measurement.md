# ADR-0005: Raise brightness in dark scenes from a screen measurement

- Date: 2026-10-02
- Status: Accepted
- Owners: @rokogan
- Related: [ADR-0002](0002-control-tv-brightness-over-webos-ssap.md), [ADR-0003](0003-restore-per-picture-mode-with-a-persisted-debt.md)

## Context

At the movie brightness, dark scenes are hard to see, while a higher value makes normal scenes too bright. The owner asked for a second, higher value during dark scenes, with the movie value back for normal scenes.

To do this, the app has to know how dark the picture is. PotPlayer's window-message API reports play state and position, not picture content. Measurements on the owner's PC (LG C2 as a 4K monitor, PotPlayer maximized):

- A GDI copy of the screen area under PotPlayer's window shows the real video, not a black frame. PotPlayer's renderer is composed by the desktop window manager.
- Copying the whole 4K screen into 64x36 pixels with `StretchBlt` and computing the level takes about 33 ms, of which about 9 ms is CPU time. Pillow's `ImageGrab` copies the whole desktop at full size and took about 72 ms.
- One TV session (connect, register, read) takes about 0.1 s. The TV is not what makes a switch late.
- In the synthetic test clip, encoded grays of 20, 25, and 47 read 12, 18, and 43 on screen: the owner's playback chain makes dark grays darker. Fades to black read exactly 0.
- The first version averaged the middle of the window. In the owner's first session with it (movie 40, dark 80), it switched 9 times in about 2 minutes. Several switches into "dark" came at levels of 35 and 38, just under its cut-off of 40. It also boosted bright scenes in which a dark character filled the middle of the picture.

## Decision drivers

- Never put the original brightness at risk: the restore rules of ADR-0003 stay as they are.
- A scene counts as dark only if it looks dark. A dark subject in front of a bright background is not a dark scene.
- No flicker: fades, cuts to black, and brief flashes must not switch the brightness.
- No new dependency and little CPU, since it runs during every movie.
- Privacy in a public app: picture content must not be kept or sent anywhere.
- Off by default, so other users see no change.

## Considered options

### How to read the picture

- **GDI `StretchBlt` of PotPlayer's window (chosen):** about 30 lines of `ctypes`, and it works with any renderer the desktop window manager composes. It sees whatever is on screen, so another window over the picture would be measured, and exclusive fullscreen or protected video reads black.
- **Pillow `ImageGrab`:** one line, but it copies the whole desktop at full size before cropping, about twice the time.
- **DXGI Desktop Duplication or Windows.Graphics.Capture:** faster for continuous capture, but they need new dependencies (Direct3D or WinRT bindings) and far more code. Two measurements a second don't need them.
- **The TV's own dynamic picture settings:** the C2's Auto Dynamic Contrast works inside the TV, without this app's delay. But it adjusts contrast rather than OLED brightness, and it is the owner's TV setting, not this app's. It stays an alternative the owner can try.

### What number decides

- **Average of the middle (first version):** this left out the edges, where bars, subtitles, and controls usually sit. But a dark character or object in the middle of a bright scene pulled the average under the cut-off, and the scene was boosted.
- **Average of the whole window:** a large dark subject still drags the average down. Letterbox bars do too.
- **The brighter part of the whole window (chosen):** the luma that 90% of the picture stays at or below. Any bright area larger than a tenth of the picture, such as a lit background behind a dark character, makes the scene bright. Small lights, subtitles, and black bars cover less than that, so they don't stop a dark scene from counting as dark.

The offline replay used two full episodes of the show the owner was watching (51 minutes, sampled twice a second like the app), with the first version's 40/55 cut-offs against the chosen ones:

| Measure | Average of the middle, 40/55 | Brighter part, 70/100 |
| --- | --- | --- |
| Switches per minute | 1.75 | 1.52 |
| Seconds boosted while the brightest tenth was above 100 | 86 | 66 |
| Seconds not boosted while the brightest tenth was below 60 | 100 | 78 |

Most of the remaining 66 s comes from the deliberate 1 s wait after a cut from dark to bright. Halving that wait to 0.5 s cut it to 37 s, but brought switching back to 1.79 per minute, so the wait stays at 1 s for now.

## Decision

- **Measure:** while PotPlayer plays and the dark scene value is above the movie value, the poll thread reads PotPlayer's whole window every 0.5 s into 64x36 pixels. The level is the luma (0 to 255) that 90% of them stay at or below. If another window covers the center of PotPlayer, or the screen cannot be read, there is no measurement.
- **Decide:** a scene is dark once levels stay below 70 for 2 s. It is normal again once they stay above 100 for 1 s. Three things change nothing and call off a pending switch: levels in between, black frames (below 2), and missing measurements. So a fade through black between two bright scenes can't add up to a switch. Every play starts at the movie value.
- **Apply:** the controller's target becomes the dark scene value during dark scenes. Writing it goes through the same `_boost` path as the movie value, so the original is still saved before the first write and never overwritten while owed. HDR and Dolby Vision modes are still left alone.
- **Keep nothing:** the copy is reduced to one number in memory. The log records only the level at each switch.
- **Control:** a **Dark scene brightness** tray submenu with Off and the movie presets. Values at or below the movie value are greyed out. The value is saved as `dark_scene_brightness` (0 is Off), and settings files without it load as Off.

## Consequences

### Positive

- Dark scenes get brighter, normal scenes keep the movie value, and a dark subject in front of a bright background is not mistaken for a dark scene.
- The restore guarantees are unchanged and covered by the same tests.
- When off, nothing is measured.

### Negative and tradeoffs

- Switches lag the picture: about 2 to 2.5 s into a dark scene and 1 to 1.5 s out of one. The TV changes in one step, not a fade.
- The cut-offs are fixed, and what looks dark depends on the content and the playback chain. They were tuned on one dark animated show.
- A dark scene with a bright area larger than a tenth of the picture, such as a big fire or a moon, is not boosted.
- A measurement costs about 33 ms, 9 ms of it CPU, twice a second during playback: under 2% of one CPU core.
- Exclusive fullscreen or protected video measures black and is ignored, so dark scenes are not detected there.

### Follow-up

- Tune the cut-offs and hold times if viewing other content shows switches that are too frequent or too rare. The log lines `Picture level N: dark` and `Picture level N: not dark` show where switches happen. A 0.5 s exit wait is the measured option if bright shots after dark scenes stay too bright for too long.
- Watch for playback stutter. None was measured, because there is no API for dropped frames.

## Validation

- `tests/test_controller.py` covers:
  - entering and leaving dark scenes;
  - brief flashes and short dark spells;
  - black frames and a fade through black;
  - levels in between;
  - Off;
  - pause and restart in a dark scene;
  - HDR;
  - menu changes during a dark scene.
- `tests/test_scene.py` covers:
  - the level in GDI's pixel order;
  - a dark subject on a bright background, which is not dark;
  - a dark scene with a small lamp, which is dark;
  - a real screen copy;
  - missing or covered windows.
- `tests/test_app.py` covers the tray submenu and old settings files.

Live runs on 2026-10-02 used the LG C2 (webOS 25), PotPlayer 64-bit maximized, and synthetic clips:

- **First version:** it reproduced the owner's report, boosting a dark subject on a bright background and a short dark slice after a fade through black.
- **Chosen version:** the TV went to the dark value 2.3 s into a dark scene with a lamp and back about 1 s after it. It left both of those cases, a flash, black, and an in-between level unchanged. Pause, minimize, and close restored the original. See [testing](../../testing.md).
