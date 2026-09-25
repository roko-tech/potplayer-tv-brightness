# Project setup checklist

Completed in the initial commits (2026-09-25). Kept as the receipt of setup decisions; `scripts/verify.py` requires it.

## 1. Define the product

- [x] `README.md` names the project, purpose, user, and quick start.
- [x] [docs/product/brief.md](docs/product/brief.md) has measurable outcomes and non-goals.
- [x] Product and technical owner: @rokogan.

## 2. Choose only the necessary technology

- [x] Runtime: Python 3.12 on Windows; `pystray`, `Pillow`, `websocket-client`. No database, no deployment target: it runs from source on the owner's PC.
- [x] Consequential choices: [ADR-0002](docs/architecture/decisions/0002-control-tv-brightness-over-webos-ssap.md) (TV control and stack), [ADR-0003](docs/architecture/decisions/0003-restore-per-picture-mode-with-a-persisted-debt.md) (restore rules).
- [x] Application code for the first vertical slice.
- [x] `.gitignore` ignores the key, settings, and restore files. `.editorconfig` already fits Python. `.env.example` states that no environment variables are used.
- [x] License: none on purpose. Private personal tool with no external distribution.

## 3. Make commands truthful

- [x] Setup, run, format, lint, type, and test commands are in `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, and [docs/testing.md](docs/testing.md). No build or package step: runs from source.
- [x] CI runs the same commands on Ubuntu and Windows.
- [x] Exact pins in `pyproject.toml` with `uv.lock` committed.
- [x] Dependabot for `uv` and `github-actions`.

## 4. Design the system

- [x] Real context, runtime, and module map in [docs/architecture/overview.md](docs/architecture/overview.md).
- [x] Module boundaries, dependency direction, data ownership, and the TV integration are documented there.
- [x] [docs/security/threat-model.md](docs/security/threat-model.md) covers the pairing key and the unverified TLS to the TV.
- [x] Configuration: `settings.json`. Secret: `tv-client-key.txt`. Logs: rotating local file. Errors: tray tooltip and log. Metrics: none (personal tool).

## 5. Establish quality evidence

- [x] Vertical-slice acceptance test: `test_play_boosts_and_pause_restores` in `tests/test_controller.py`, plus the live run in [docs/testing.md](docs/testing.md).
- [x] Unit tests for the rules and protocol tests for the TV adapter.
- [x] Live checks: `scripts/tv_check.py` and the live procedure in [docs/testing.md](docs/testing.md).
- [x] Test data, coverage expectations, and unacceptable regressions are in [docs/testing.md](docs/testing.md).

## 6. Prepare operations

- [x] One environment (the owner's PC). Update and rollback with Git: [runbook](docs/operations/runbook.md).
- [x] SLOs and alerting: not applicable, see [slo.md](docs/operations/slo.md).
- [x] Backups: not applicable, nothing worth backing up; see [backup-restore.md](docs/operations/backup-restore.md).
- [x] Template operational language replaced.

## 7. Configure GitHub

- [x] `.github/CODEOWNERS`: @rokogan.
- [x] `python scripts/github_settings.py --apply` applied and read back with no drift; topics set.
- [ ] Branch rules from `.github/rulesets/main.json`: **not imported.** The workspace rule is to import after the first successful CI run, and no CI job has been able to start (see section 9). Requiring checks that cannot run would also block every merge. Import it with the command in [docs/github-governance.md](docs/github-governance.md) once CI runs; GitHub Free may still reject rulesets on private repositories. Until then `main` is not protected.
- [ ] Required CI checks and conversation resolution: blocked with the ruleset.
- [x] Dependabot alerts and security updates enabled. Secret scanning and push protection: GitHub refused on 2026-09-25 with HTTP 422 "Secret scanning is not available for this repository." (GitHub Free, private repository). Kept private; not upgraded.
- [x] Actions: GitHub-owned only, full-SHA pinning required, read-only workflow token.
- [x] AI review: not connected (optional). Project review rules are in `AGENTS.md`.

## 8. Protect users and data

- [x] `SECURITY.md` names the owner as the private contact.
- [x] Data classes and retention: [architecture overview](docs/architecture/overview.md#data) and the threat model. No personal data is collected.
- [x] Authentication/authorization tests: not applicable (no user identities). TV pairing is covered by `tests/test_tv.py`.
- [x] Logs, fixtures, and prompts contain no pairing key.

## 9. Prove readiness

- [x] Every documented command run from a clean clone on Windows (2026-09-25): all pass.
- [ ] CI green on Ubuntu and Windows: **blocked by GitHub billing.** Every job for every roko-tech repository fails before its first step with: "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings" (organization plan: free; seen 2026-09-25). The same commands pass locally on Windows. Ubuntu is unverified; the tests that run there are pure Python.
- [x] Primary workflow exercised on the real LG C2 and PotPlayer (see [docs/testing.md](docs/testing.md)).
- [x] Known limitations and untested surfaces recorded in the [user guide](docs/user/README.md) and [testing](docs/testing.md).
- [x] Release checklist: not applicable for now; no release or distribution is planned.
