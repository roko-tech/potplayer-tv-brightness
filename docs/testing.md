# Testing strategy

Tests are evidence about risk, not a score to maximize. Map each acceptance criterion and important failure mode to the cheapest reliable test, then add real-boundary or live evidence where isolation hides material behavior.

## Quality layers

| Layer | Proves | Typical use | Does not prove alone |
| --- | --- | --- | --- |
| Static checks | Syntax, style, types, known patterns | Every change | Runtime behavior |
| Unit/component | Business rules and local states | Dense edge-case coverage | Real adapters or deployment |
| Integration/contract | Boundaries, schemas, protocols, persistence | Database/provider/module seams | Complete user journey |
| End-to-end | Primary journey across real components | Critical outcomes and regressions | Every edge case or production scale |
| Platform/package | Built/installed artifact on supported targets | Installers, permissions, codecs, OS behavior | Production data/integration health |
| Live smoke/recovery | Actual environment, credentials, dependencies, rollback/restore | Release and operational confidence | Broad deterministic regression coverage |

## Required practices

- Derive tests from acceptance criteria, invariants, past defects, threat scenarios, and operating risks.
- For a bug, add a reproduction that fails before the fix when practical.
- Test observable behavior rather than private implementation details.
- Keep deterministic tests isolated and fast, but do not let mocks define an external contract. Add contract or integration tests against a realistic boundary.
- Test failure, timeout, retry, duplicate, cancellation, partial-write, and recovery paths where they matter.
- Keep test data minimal, synthetic, non-sensitive, deterministic, and versioned.
- Do not lower assertions, skip tests, or regenerate expected output without reviewing the semantic change.
- Treat coverage as a gap-finding signal. A percentage is not evidence that important behavior is correct.

## Change-risk matrix

| Change | Expected evidence |
| --- | --- |
| Pure domain rule | Unit tests for examples, boundaries, invalid states, and invariants |
| Database/schema | Migration test on realistic prior state, compatibility, rollback/roll-forward, backup impact |
| External API | Contract fixtures plus sandbox/live smoke where allowed; timeout/rate-limit/error behavior |
| UI/workflow | Component tests plus browser/user journey, accessibility, loading/empty/error states, screenshots when visual |
| Authentication/authorization | Positive and negative tests for every role/tenant/resource boundary |
| Concurrency/job processing | Idempotency, duplicate delivery, race, crash/restart, ordering, and retry exhaustion |
| Packaging/platform | Clean install/build and primary workflow on each supported target |
| AI behavior | Versioned eval set, adversarial cases, structured-output validation, abstention/fallback, cost/latency bounds |

## Commands

CI runs the same commands on Ubuntu and Windows:

```shell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/verify.py
uv run python -m unittest discover -s tests -v
git diff --check
```

Build the exe on Windows (not part of CI; needs Visual Studio Build Tools with C++, since PyInstaller's launcher is compiled from source):

```shell
packaging\build.cmd
```

## What each suite proves

| Suite | Proves | Runs on |
| --- | --- | --- |
| `tests/test_controller.py` | Boost/restore rules: primary journey, 1 s settle, HDR skip, per-mode originals, TV unreachable, crash and restart, Quit. Dark scenes: 2 s in and 1 s out, flashes and short dark spells, black frames, a fade through black, levels between the cut-offs, Off, pause and restart in a dark scene, HDR, menu changes | Both |
| `tests/test_scene.py` | Picture level: the luma 90% of the picture stays under, in GDI's pixel order; a dark subject on a bright background is not dark, a dark scene with a small lamp is; a real screen copy; no level for a missing or covered window | Windows |
| `tests/test_tv.py` | SSAP protocol: saved key, first-use pairing, request/response matching, errors and timeouts, malformed address, `Origin` suppressed | Both |
| `tests/test_app.py` | Settings defaults (no TV address), clamping, invalid file, files from 0.1.0 without the dark scene value; first run opens the Connect window, then the tray, or exits when it is closed; the Dark scene brightness submenu (values above the movie value only, saving); Start with Windows against a throwaway registry key; the exe's `%APPDATA%` folder and launch command; tray icon image; PotPlayer probe runs | Windows |
| `tests/test_discovery.py` | TV search against a fake TV on localhost (real UDP and HTTP): name read once despite duplicate replies, never fetched from another host, non-LG devices ignored | Both |
| `tests/test_connect.py` | The Connect window, hidden, with the search and TV faked: found TV preselected and returned, nothing found, a declined prompt and retry, a typed address kept, each error explained | Windows |
| `tests/test_tv_check.py` | Connect command: saves `--host` only after the TV answers, explains a missing address, clamps `--set` | Windows |
| `tests/test_verify.py`, `tests/test_github_settings.py` | Template tooling | Both |

The fakes model the TV and PotPlayer; they do not prove the real ones behave the same. That is what the live checks are for.

## Expectations

- **Test data:** synthetic only. Fakes stand in for the TV and websocket; live runs use generated clips (`ffmpeg -f lavfi -i testsrc2`, and the dark scene clip in step 6), never personal media.
- **Coverage:** every rule in `controller.py` and every protocol branch in `tv.py` has a test. There is no percentage target.
- **Unacceptable regressions:** losing or overwriting a saved original; writing to a different picture mode, to an HDR mode, or any setting other than `backlight`; TV calls or other waits on the tray thread (except Quit's bounded join); tests that open real windows or write the developer's own files (menu actions a test triggers after `start()` returns need their own `save_settings` patch); the pairing key appearing in logs or Git; screen content saved, logged, or sent, or measured while dark scenes are off or PotPlayer is not playing.

## Live checks

Run these after changing `tv.py`, `potplayer.py`, or `scene.py`, after a TV firmware update, and before a release. They change the TV's brightness.

1. Connect from a copy of the repository without `settings.json` and `tv-client-key.txt`: `uv run python -m scripts.tv_check --host <TV IP>`. Declining the prompt must save nothing; accepting must save the address and key and print the picture mode.
2. `uv run python -m scripts.tv_check` prints the picture mode and brightness. `--set N` writes and reads back.
3. Start the app and play a video in PotPlayer. Then pause, resume, minimize, and close it, checking the TV brightness after each step with `tv_check`.
4. Kill the app while a video plays: `restore.json` must keep the original. Restart it, then close PotPlayer: the original must come back.
5. The exe as a new user: build it, make sure `%APPDATA%\PotPlayer TV Brightness` does not exist, and start `PotPlayer-TV-Brightness.exe` from File Explorer. The Connect window must list the TV, with Connect greyed out until it does; after Connect and Accept, the tray and a notification appear and the files land in `%APPDATA%`. Then pick a preset, play and pause a video, turn on Start with Windows, use Connect TV…, and Quit. Check for a Windows Firewall prompt, and scan the exe with Windows Defender. Repeat the first run in Windows Sandbox, a clean Windows without Python, with the exe marked as downloaded.

6. Dark scenes: generate the clip below. Set **Dark scene brightness** above the movie brightness, then play the clip in PotPlayer, maximized or fullscreen, with nothing over its center. The clip runs:
   - from 0 s, gray (level about 120);
   - from 10 s, dark (20) with a small lamp, and a 0.4 s flash at 17 s;
   - from 22 s, 3 s black, then dark (25) from 25 s;
   - from 32 s, gray (110);
   - from 42 s, a dark subject (15) filling most of a bright background (140);
   - from 54 s, gray, with a fade through black between 57 and 60.7 s (0.6 s dark, 2.5 s black, 0.6 s dark);
   - from 66 s, an in-between level (85), then 4 s black from 74 s, then 60 s gray. The padding keeps a run well under the "watched" thresholds of players and scrobblers.

   Expected:
   - the movie value first;
   - the dark scene value about 2 s after 10 s;
   - no change at the flash, the black, or the dark part from 25 s;
   - the movie value about 1 s after 32 s;
   - no change after that: not for the dark subject, the fade through black, the in-between level, or the black.

   Pause, minimize, and close must still restore the original. The log shows one `Picture level N: dark` and one `Picture level N: not dark` line. With Off, nothing changes during the dark parts and the log has no `Picture level` lines.

   ```shell
   ffmpeg -f lavfi -i color=c=0x787878:s=1920x1080:r=30:d=10 -f lavfi -i color=c=0x141414:s=1920x1080:r=30:d=7,drawbox=x=1500:y=150:w=300:h=200:color=0xDCDCDC:t=fill -f lavfi -i color=c=0xC8C8C8:s=1920x1080:r=30:d=0.4 -f lavfi -i color=c=0x141414:s=1920x1080:r=30:d=4.6,drawbox=x=1500:y=150:w=300:h=200:color=0xDCDCDC:t=fill -f lavfi -i color=c=0x000000:s=1920x1080:r=30:d=3 -f lavfi -i color=c=0x191919:s=1920x1080:r=30:d=7 -f lavfi -i color=c=0x6E6E6E:s=1920x1080:r=30:d=10 -f lavfi -i color=c=0x8C8C8C:s=1920x1080:r=30:d=12,drawbox=x=300:y=200:w=1320:h=680:color=0x0F0F0F:t=fill -f lavfi -i color=c=0x787878:s=1920x1080:r=30:d=3 -f lavfi -i color=c=0x141414:s=1920x1080:r=30:d=0.6 -f lavfi -i color=c=0x000000:s=1920x1080:r=30:d=2.5 -f lavfi -i color=c=0x141414:s=1920x1080:r=30:d=0.6 -f lavfi -i color=c=0x787878:s=1920x1080:r=30:d=5.3 -f lavfi -i color=c=0x555555:s=1920x1080:r=30:d=8 -f lavfi -i color=c=0x000000:s=1920x1080:r=30:d=4 -f lavfi -i color=c=0x787878:s=1920x1080:r=30:d=60 -filter_complex "concat=n=16:v=1:a=0,format=yuv420p" -c:v libx264 -crf 18 dark-scene-test.mp4
   ```

Start the exe from File Explorer, not from a terminal inside another app. Programs started from a packaged app (such as the Claude desktop app) inherit its file redirection: their `%APPDATA%` writes land in that app's private copy, not the real one. The Claude desktop app does not redirect their registry writes: those reach the real `HKCU` (checked 2026-10-03 with version 2.19675.0.0).

Last run of steps 2 to 4: 2026-09-25, LG C2 webOS 25 (firmware 33.x), PotPlayer 64-bit, silent test-pattern clip in a separate PotPlayer instance. Brightness 20 → 80 on play, 20 on pause, 80 on resume, 20 on minimize, 80 kept through a crash and restart with `{"normal": 20}` on disk, 20 on close. A second, paused and minimized PotPlayer window never triggered a change.

Last run of step 1: 2026-09-26, same TV, from a scratch copy so the real key and settings stayed untouched. No address: the command explained `--host`. An address with a port (`<TV IP>:3001`): a clear "Cannot connect" error. Decline: `Pairing refused: 403 Error: User rejected pairing`, nothing saved. Accept: address and key saved, `normal` at 20 printed; a second run reused both without a prompt; `--set 20` read back 20. The tray app started without an address showed the "No TV address" dialog, logged a warning, and exited.

Last run of step 5 on the owner's PC: 2026-09-27, same TV, 18.8 MB exe built with PyInstaller 6.22.3, started from File Explorer. Defender: no threats; no firewall prompt. The first attempt did nothing visible and the owner closed the window (`No TV connected` in the log); the Connect button was clickable during the search, which is now fixed and tested. The second start connected after Accept; the files were in the real `%APPDATA%`; preset 40, then play gave `Watching: brightness 40 (restores 20)` and pause `Restored brightness 20 (normal)`; Start with Windows wrote the exe's path to the real `Run` key. An earlier run launched from inside the Claude desktop app kept its files in the redirected `%APPDATA%` copy instead, which is how the redirection above was found.

Last run of step 5 in Windows Sandbox: 2026-09-27, Windows 10 without Python, the release exe marked as downloaded from GitHub. SmartScreen showed "Windows protected your PC" with "Unknown publisher"; More info, then Run anyway. The search found nothing, as expected behind the sandbox's NAT, and Connect stayed greyed out until the address was typed. After Accept on the TV the log read `Connecting`, `Paired`, `Started`; the icon sat under the tray's **^** arrow with status Idle; the menu showed all four items; Start with Windows wrote the `Run` value and showed its check mark; Quit exited. No firewall rule was needed or created. VirusTotal: 4 of 71 engines flagged the exe built with PyInstaller's stock launcher, 2 of 71 (Bkav Pro, SecureAge) the one with a locally compiled launcher; Windows Defender found nothing in either.

Last runs of step 6, 2026-10-02, same TV, from source on the branch, with PotPlayer 64-bit maximized in a separate instance. The owner's playback chain makes dark grays darker on screen: the clip's 20, 25, and 47 read 12, 18, and 43, while 110 and 120 read as encoded.
- First version, average of the middle, with the earlier clip and the value at 70:
  - An old settings file started with `dark scene brightness Off`, and dark picture changed nothing.
  - With the value at 70, the TV went to 70 2.3 s into the dark part and back to 40 about 1 s after it.
  - The flash, the fade to black, and the in-between part changed nothing.
  - Pause, resume, minimize, and close while playing gave 20, 40, 20, and 20, each within about 1.8 s.
- The owner's own viewing then showed bright scenes boosted when a dark character filled the middle of the picture. The same code, with the current clip at movie 40 and dark 80, reproduced it: 80 for the dark subject on the bright background (level 26), and 80 after the fade through black.
- Current version, the brighter part of the whole window, same clip and values:
  - 80 came 2.3 s into the dark part with the lamp (level 12), and 40 came back 1 s after the gray.
  - The dark subject read 141, and neither it nor the fade through black, the in-between level (84), or the black changed anything.
  - Close restored 20.
- The tray submenu itself was not clicked by the test; the owner used it on their PC, and `test_app.py` drives its items.

Not live-tested yet:
- dark scenes in exclusive fullscreen, with PotPlayer partly covered, on monitors with different scaling, and on real films, where the cut-offs may need tuning;
- whether measuring twice a second causes playback stutter (there is no dropped-frame API to check);
- HDR mode switching and a switched-off TV, which are covered by unit tests only;
- the TV search from a second PC on the same network (the sandbox is behind NAT, so only the typed-address path ran there);
- a TV without Developer Mode (the test TV has it on for other apps, and turning it off would uninstall them).

## Evidence in pull requests

Record the exact command, environment, result, and relevant artifact or screenshot. Say what was not run and why. A green hermetic suite must not be described as proof of installation, live integrations, backup restoration, media/player behavior, production scale, or another surface it did not exercise.

Flaky tests are defects: quarantine only with an owner, tracking issue, reason, and expiry. Never silently retry until red becomes green.
