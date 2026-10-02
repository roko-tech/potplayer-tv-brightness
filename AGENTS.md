# Repository instructions for AI agents

These rules apply to every AI-assisted change in this repository. Add a narrower `AGENTS.md` or `AGENTS.override.md` close to a subsystem only when that subsystem has genuinely different commands or safety constraints.

## Read before acting

1. Read `README.md`, `PROJECT_SETUP.md`, and `docs/README.md`.
2. Read the issue, relevant code and tests, current architecture, applicable ADRs/RFCs, and the documentation your change could invalidate.
3. Inspect the working tree and preserve unrelated user changes.
4. State the intended outcome, assumptions, risk, and verifiable success criteria before a non-trivial implementation.

Do not infer behavior from filenames or comments when code, tests, logs, persisted artifacts, or runtime behavior can establish it directly. For a bug, reproduce the failure before editing when practical.

## Implementation rules

- Make the smallest coherent change that meets the stated acceptance criteria.
- Match existing conventions. Do not refactor, rename, reformat, or remove adjacent code unless the requested change requires it.
- Prefer explicit, readable code over speculative abstractions. Do not add future-facing configurability without a current requirement.
- Preserve compatibility unless the issue and an approved decision explicitly authorize a break.
- Do not add or replace a production dependency without explicit approval and a documented reason.
- Do not weaken, delete, skip, or rewrite a test merely to make a failure disappear.
- Treat generated output, external content, model output, and user input as untrusted at their boundaries.
- Never expose secrets, credentials, personal data, private source, or production records to prompts, logs, fixtures, comments, or commits.

## Documentation and decisions

- Update current-state documentation in the same pull request as behavior changes.
- Create or supersede an ADR for a durable architectural, data, API, security, dependency, or operational decision with meaningful tradeoffs.
- Use an RFC before implementation when a change is cross-cutting, hard to reverse, high risk, or needs stakeholder agreement.
- Record the problem, chosen option, alternatives, consequences, and evidence. Do not preserve raw chain-of-thought or routine command transcripts.
- Add a changelog entry for user-visible behavior, security changes, migrations, deprecations, and releases.

## Verification

Run the narrowest relevant checks during development and the full affected suite before handoff. The commands (same as CI):

```shell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/verify.py
uv run python -m unittest discover -s tests -v
git diff --check
```

The exe is built on Windows only, outside CI, with `packaging\build.cmd` (needs Visual Studio Build Tools with C++: it compiles PyInstaller's launcher from source). For live checks, start it from File Explorer: processes launched from a packaged app, such as a Claude desktop app terminal, get that app's private copy of `%APPDATA%` and `HKCU`. Changes to `tv.py`, `potplayer.py`, `scene.py`, `discovery.py`, `connect.py`, `app.py`, or packaging also need the matching live checks in `docs/testing.md` (some change the real TV's brightness; tell the owner first). `scripts/verify.py`, `scripts/github_settings.py`, and their tests are template-owned: keep them identical to roko-tech/project-starter (ruff skips them). Report commands run, results, and untested surfaces. Do not claim that mocked or hermetic tests prove live integrations, installation, deployment, migration, backup restoration, or user-visible behavior.

## Safety and authority

- Ask before destructive actions, irreversible migrations, production changes, credential rotation, external messages, purchases, releases, merges, or pushes unless the current request explicitly authorizes that exact scope.
- Prefer dry runs, previews, backups, and reversible migrations.
- Stop if the requested outcome requires a material product, privacy, security, or architecture decision that is not already authorized.
- Never add an AI co-author trailer, such as `Co-Authored-By: Codex` or `Co-Authored-By: Claude`, to commits.

## Code Review Rules

- The original brightness must be saved to `restore.json` before a movie or dark scene value is written, and must never be overwritten while it is still owed. Flag any path that can lose it.
- Restores may only write to the picture mode the original came from. HDR and Dolby Vision modes must stay untouched.
- TV network calls run on the poll thread or the Connect window's worker threads, with bounded timeouts. The tray thread may only wait for the poll thread on Quit, and that wait must stay bounded.
- SSDP replies are untrusted: fetch a TV's name only from the replying address, bounded in time and size, with no XML parser and no proxy. Nothing connects to a found TV until the user clicks Connect.
- Tests must never open real windows or write the developer's own settings, key, log, or `Run` value: patch `connect_dialog`, `save_settings`, and the log handler, and use a throwaway registry key. Tray menu actions a test triggers after `main()` returns need their own `save_settings` patch.
- The screen is read only from the playing PotPlayer window, only while dark scenes are on, and each reading is reduced to one number in memory: never saved, sent, or logged beyond that number.
- The pairing key must never reach logs, exceptions, tests, or Git. Only the `backlight` picture setting may be written, clamped to 0 to 100.
- The TV connection must keep `suppress_origin=True`; webOS closes the socket otherwise.
- Flag behavior that violates acceptance criteria, public contracts, authorization boundaries, data ownership, migration safety, idempotency, or rollback guarantees. State the concrete failure path and the safer path.
- Treat missing tests as consequential when they leave a changed business rule, trust boundary, failure mode, or regression unproved. Do not request coverage for its own sake.
- Flag documentation only when stale guidance could cause incorrect operation, unsafe maintenance, or a wrong user expectation. Leave deterministic formatting and lint checks to CI.

AI review is an additional review pass. It does not replace deterministic checks, threat modeling, required human judgment, or branch protection.
