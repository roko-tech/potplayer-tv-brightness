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
| `tests/test_controller.py` | Boost/restore rules: primary journey, 1 s settle, HDR skip, per-mode originals, TV unreachable, crash and restart, Quit | Both |
| `tests/test_tv.py` | SSAP protocol: saved key, first-use pairing, request/response matching, errors and timeouts, malformed address, `Origin` suppressed | Both |
| `tests/test_app.py` | Settings defaults (no TV address), clamping, invalid file; first run opens the Connect window, then the tray, or exits when it is closed; Start with Windows against a throwaway registry key; the exe's `%APPDATA%` folder and launch command; tray icon image; PotPlayer probe runs | Windows |
| `tests/test_discovery.py` | TV search against a fake TV on localhost (real UDP and HTTP): name read once despite duplicate replies, never fetched from another host, non-LG devices ignored | Both |
| `tests/test_connect.py` | The Connect window, hidden, with the search and TV faked: found TV preselected and returned, nothing found, a declined prompt and retry, a typed address kept, each error explained | Windows |
| `tests/test_tv_check.py` | Connect command: saves `--host` only after the TV answers, explains a missing address, clamps `--set` | Windows |
| `tests/test_verify.py`, `tests/test_github_settings.py` | Template tooling | Both |

The fakes model the TV and PotPlayer; they do not prove the real ones behave the same. That is what the live checks are for.

## Expectations

- **Test data:** synthetic only. Fakes stand in for the TV and websocket; live runs use a generated test-pattern clip (`ffmpeg -f lavfi -i testsrc2`), never personal media.
- **Coverage:** every rule in `controller.py` and every protocol branch in `tv.py` has a test. There is no percentage target.
- **Unacceptable regressions:** losing or overwriting a saved original; writing to a different picture mode, to an HDR mode, or any setting other than `backlight`; TV calls or other waits on the tray thread (except Quit's bounded join); tests that open real windows or write the developer's own files; the pairing key appearing in logs or Git.

## Live checks

Run these after changing `tv.py` or `potplayer.py`, after a TV firmware update, and before a release. They change the TV's brightness.

1. Connect from a copy of the repository without `settings.json` and `tv-client-key.txt`: `uv run python -m scripts.tv_check --host <TV IP>`. Declining the prompt must save nothing; accepting must save the address and key and print the picture mode.
2. `uv run python -m scripts.tv_check` prints the picture mode and brightness. `--set N` writes and reads back.
3. Start the app and play a video in PotPlayer. Then pause, resume, minimize, and close it, checking the TV brightness after each step with `tv_check`.
4. Kill the app while a video plays: `restore.json` must keep the original. Restart it, then close PotPlayer: the original must come back.
5. The exe as a new user: build it, make sure `%APPDATA%\PotPlayer TV Brightness` does not exist, and start `PotPlayer-TV-Brightness.exe` from File Explorer. The Connect window must list the TV, with Connect greyed out until it does; after Connect and Accept, the tray and a notification appear and the files land in `%APPDATA%`. Then pick a preset, play and pause a video, turn on Start with Windows, use Connect TV…, and Quit. Check for a Windows Firewall prompt, and scan the exe with Windows Defender. Repeat the first run in Windows Sandbox, a clean Windows without Python, with the exe marked as downloaded.

Start the exe from File Explorer, not from a terminal inside another app. Programs started from a packaged app (such as the Claude desktop app) inherit its file and registry redirection: their `%APPDATA%` and `HKCU` writes land in that app's private copy, not the real ones.

Last run of steps 2 to 4: 2026-09-25, LG C2 webOS 25 (firmware 33.x), PotPlayer 64-bit, silent test-pattern clip in a separate PotPlayer instance. Brightness 20 → 80 on play, 20 on pause, 80 on resume, 20 on minimize, 80 kept through a crash and restart with `{"normal": 20}` on disk, 20 on close. A second, paused and minimized PotPlayer window never triggered a change.

Last run of step 1: 2026-09-26, same TV, from a scratch copy so the real key and settings stayed untouched. No address: the command explained `--host`. An address with a port (`<TV IP>:3001`): a clear "Cannot connect" error. Decline: `Pairing refused: 403 Error: User rejected pairing`, nothing saved. Accept: address and key saved, `normal` at 20 printed; a second run reused both without a prompt; `--set 20` read back 20. The tray app started without an address showed the "No TV address" dialog, logged a warning, and exited.

Last run of step 5 on the owner's PC: 2026-09-27, same TV, 18.8 MB exe built with PyInstaller 6.22.3, started from File Explorer. Defender: no threats; no firewall prompt. The first attempt did nothing visible and the owner closed the window (`No TV connected` in the log); the Connect button was clickable during the search, which is now fixed and tested. The second start connected after Accept; the files were in the real `%APPDATA%`; preset 40, then play gave `Watching: brightness 40 (restores 20)` and pause `Restored brightness 20 (normal)`; Start with Windows wrote the exe's path to the real `Run` key. An earlier run launched from inside the Claude desktop app wrote to its redirected copy instead, which is how the redirection above was found.

Last run of step 5 in Windows Sandbox: 2026-09-27, Windows 10 without Python, the release exe marked as downloaded from GitHub. SmartScreen showed "Windows protected your PC" with "Unknown publisher"; More info, then Run anyway. The search found nothing, as expected behind the sandbox's NAT, and Connect stayed greyed out until the address was typed. After Accept on the TV the log read `Connecting`, `Paired`, `Started`; the icon sat under the tray's **^** arrow with status Idle; the menu showed all four items; Start with Windows wrote the `Run` value and showed its check mark; Quit exited. No firewall rule was needed or created. VirusTotal: 4 of 71 engines flagged the exe built with PyInstaller's stock launcher, 2 of 71 (Bkav Pro, SecureAge) the one with a locally compiled launcher; Windows Defender found nothing in either.

Not live-tested yet: HDR mode switching and a switched-off TV, which are covered by unit tests only; the TV search from a second PC on the same network (the sandbox is behind NAT, so only the typed-address path ran there); and a TV without Developer Mode (the test TV has it on for other apps, and turning it off would uninstall them).

## Evidence in pull requests

Record the exact command, environment, result, and relevant artifact or screenshot. Say what was not run and why. A green hermetic suite must not be described as proof of installation, live integrations, backup restoration, media/player behavior, production scale, or another surface it did not exercise.

Flaky tests are defects: quarantine only with an owner, tracking issue, reason, and expiry. Never silently retry until red becomes green.
