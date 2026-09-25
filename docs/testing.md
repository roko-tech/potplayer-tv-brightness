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

The template currently validates its own repository contract:

```shell
python scripts/verify.py
python -m unittest discover -s tests -v
git diff --check
```

During setup, add exact commands for formatting, linting, typing, unit, integration, end-to-end, build/package, dependency/security, migration, platform, and live smoke checks. CI and local documentation must invoke the same underlying commands.

## Evidence in pull requests

Record the exact command, environment, result, and relevant artifact or screenshot. Say what was not run and why. A green hermetic suite must not be described as proof of installation, live integrations, backup restoration, media/player behavior, production scale, or another surface it did not exercise.

Flaky tests are defects: quarantine only with an owner, tracking issue, reason, and expiry. Never silently retry until red becomes green.
