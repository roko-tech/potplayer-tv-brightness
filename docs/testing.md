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

There is no build or package step; the app runs from source.

## What each suite proves

| Suite | Proves | Runs on |
| --- | --- | --- |
| `tests/test_controller.py` | Boost/restore rules: primary journey, 1 s settle, HDR skip, per-mode originals, TV unreachable, crash and restart, Quit | Both |
| `tests/test_tv.py` | SSAP protocol: saved key, first-use pairing, request/response matching, errors and timeouts, `Origin` suppressed | Both |
| `tests/test_app.py` | Settings defaults, clamping, invalid file; tray icon image; PotPlayer probe runs | Windows |
| `tests/test_verify.py`, `tests/test_github_settings.py` | Template tooling | Both |

The fakes model the TV and PotPlayer; they do not prove the real ones behave the same. That is what the live checks are for.

## Expectations

- **Test data:** synthetic only. Fakes stand in for the TV and websocket; live runs use a generated test-pattern clip (`ffmpeg -f lavfi -i testsrc2`), never personal media.
- **Coverage:** every rule in `controller.py` and every protocol branch in `tv.py` has a test. There is no percentage target.
- **Unacceptable regressions:** losing or overwriting a saved original; writing to a different picture mode, to an HDR mode, or any setting other than `backlight`; TV calls on the tray thread; the pairing key appearing in logs or Git.

## Live checks

Run these after changing `tv.py` or `potplayer.py`, after a TV firmware update, and before a release. They change the TV's brightness.

1. `uv run python -m scripts.tv_check` prints the picture mode and brightness. `--set N` writes and reads back.
2. Start the app and play a video in PotPlayer. Then pause, resume, minimize, and close it, checking the TV brightness after each step with `tv_check`.
3. Kill the app while a video plays: `restore.json` must keep the original. Restart it, then close PotPlayer: the original must come back.

Last run: 2026-09-25, LG C2 webOS 25 (firmware 33.x), PotPlayer 64-bit, silent test-pattern clip in a separate PotPlayer instance. Brightness 20 → 80 on play, 20 on pause, 80 on resume, 20 on minimize, 80 kept through a crash and restart with `{"normal": 20}` on disk, 20 on close. A second, paused and minimized PotPlayer window never triggered a change.

Not live-tested yet: tray menu clicks (presets, Quit), HDR mode switching, a switched-off TV, and pairing from scratch. These are covered by unit tests only.

## Evidence in pull requests

Record the exact command, environment, result, and relevant artifact or screenshot. Say what was not run and why. A green hermetic suite must not be described as proof of installation, live integrations, backup restoration, media/player behavior, production scale, or another surface it did not exercise.

Flaky tests are defects: quarantine only with an owner, tracking issue, reason, and expiry. Never silently retry until red becomes green.
