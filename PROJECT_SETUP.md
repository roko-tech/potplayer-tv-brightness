# Project setup checklist

Completed in the initial commits (2026-09-25) and updated for public release (2026-09-26). Kept as the receipt of setup decisions; `scripts/verify.py` requires it.

## 1. Define the product

- [x] `README.md` names the project, purpose, user, and quick start.
- [x] [docs/product/brief.md](docs/product/brief.md) has measurable outcomes and non-goals.
- [x] Product and technical owner: @rokogan.

## 2. Choose only the necessary technology

- [x] Runtime: Python 3.12 on Windows; `pystray`, `Pillow`, `websocket-client`, and Tk from the standard library. No database or server: it runs on each user's PC, as a single-file exe built with PyInstaller (`build` dependency group) or from source.
- [x] Consequential choices: [ADR-0002](docs/architecture/decisions/0002-control-tv-brightness-over-webos-ssap.md) (TV control and stack), [ADR-0003](docs/architecture/decisions/0003-restore-per-picture-mode-with-a-persisted-debt.md) (restore rules), [ADR-0004](docs/architecture/decisions/0004-ship-a-single-file-exe-with-a-connect-window.md) (exe and Connect window).
- [x] Application code for the first vertical slice.
- [x] `.gitignore` ignores the key, settings, and restore files. `.editorconfig` already fits Python. `.env.example` states that no environment variables are used.
- [x] License: MIT, chosen by the owner on 2026-09-26 for public release. `pairing.json` comes from lgtv2 (MIT) and is credited in the README.

## 3. Make commands truthful

- [x] Setup, run, format, lint, type, and test commands are in `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, and [docs/testing.md](docs/testing.md). The exe build command is in `README.md`, `AGENTS.md`, and [docs/testing.md](docs/testing.md); it runs on Windows, outside CI.
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
- [x] Live checks: `scripts/tv_check.py` and the live procedure in [docs/testing.md](docs/testing.md), including the exe's first run.
- [x] Test data, coverage expectations, and unacceptable regressions are in [docs/testing.md](docs/testing.md).

## 6. Prepare operations

- [x] One environment: each user's own PC. Update and rollback with Git: [runbook](docs/operations/runbook.md).
- [x] SLOs and alerting: not applicable, see [slo.md](docs/operations/slo.md).
- [x] Backups: not applicable, nothing worth backing up; see [backup-restore.md](docs/operations/backup-restore.md).
- [x] Template operational language replaced.

## 7. Configure GitHub

- [x] `.github/CODEOWNERS`: @rokogan.
- [x] `python scripts/github_settings.py --apply` applied and read back with no drift; topics set.
- [ ] Branch rules from `.github/rulesets/main.json`: **not imported.** The workspace rule is to import after the first successful CI run, and no CI job has been able to start (see section 9). Requiring checks that cannot run would also block every merge. Import it with the command in [docs/github-governance.md](docs/github-governance.md) once CI runs; GitHub Free may still reject rulesets on private repositories. Until then `main` is not protected.
- [ ] Required CI checks and conversation resolution: blocked with the ruleset.
- [x] Dependabot alerts and security updates enabled. Secret scanning and push protection: GitHub refused on 2026-09-25 with HTTP 422 "Secret scanning is not available for this repository." (GitHub Free, private repository). Not upgraded; both are free once the repository is public (see below).
- [x] Actions: GitHub-owned only, full-SHA pinning required, read-only workflow token.
- [x] Immutable releases enabled (2026-09-27): published tags and files cannot change, and each release gets a GitHub-signed attestation.
- [x] Repository recreated on 2026-09-27, so its history and activity log hold no trace of the commits made before the identity rewrite. The previous repository was renamed and kept private for the owner to delete.
- [x] AI review: not connected (optional). Project review rules are in `AGENTS.md`.

### When the repository goes public

The repository is ready for public release but stays private until the owner switches it. Then:

1. `gh repo edit roko-tech/potplayer-tv-brightness --visibility public --accept-visibility-change-consequences`
2. Secret scanning and push protection: `gh api --method PATCH repos/roko-tech/potplayer-tv-brightness -f "security_and_analysis[secret_scanning][status]=enabled" -f "security_and_analysis[secret_scanning_push_protection][status]=enabled"`
3. Private vulnerability reporting, which `SECURITY.md` relies on: `gh api --method PUT repos/roko-tech/potplayer-tv-brightness/private-vulnerability-reporting`
4. Re-run CI on `main`: find the latest run ID with `gh run list --repo roko-tech/potplayer-tv-brightness --workflow ci.yml --limit 1`, then `gh run rerun <run ID> --repo roko-tech/potplayer-tv-brightness`. Hosted runners are free for public repositories, so the billing block may no longer apply.
5. After a green run, import the ruleset with the command in [docs/github-governance.md](docs/github-governance.md).
6. `python scripts/github_settings.py` then reports `private` as drift. That is expected: the template-owned script assumes private repositories.
7. Once CI runs: build releases in CI with artifact attestations, and apply to SignPath Foundation for free code signing (both need a public repository; see [references](docs/references.md#releasing-a-windows-exe)).

Releases follow "Release the exe" in the [runbook](docs/operations/runbook.md#release-the-exe). A release published while the repository is private is visible only to its collaborators until it goes public.

## 8. Protect users and data

- [x] `SECURITY.md` routes reports to GitHub private vulnerability reporting (enabled when the repository goes public).
- [x] Data classes and retention: [architecture overview](docs/architecture/overview.md#data) and the threat model. No personal data is collected.
- [x] Authentication/authorization tests: not applicable (no user identities). TV pairing is covered by `tests/test_tv.py`.
- [x] Logs, fixtures, and prompts contain no pairing key. Tracked files contain no TV address or local paths, and commits use the GitHub noreply identity.

## 9. Prove readiness

- [x] Every documented command run from a clean clone on Windows (2026-09-26): all pass.
- [ ] CI green on Ubuntu and Windows: **blocked by GitHub billing.** Every job for every roko-tech repository fails before its first step with: "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings" (organization plan: free; seen 2026-09-25). The same commands pass locally on Windows. Ubuntu is unverified; the tests that run there are pure Python.
- [x] Primary workflow exercised on the real LG C2 and PotPlayer (see [docs/testing.md](docs/testing.md)), from source and as the exe (2026-09-27).
- [x] Known limitations and untested surfaces recorded in the [user guide](docs/user/README.md) and [testing](docs/testing.md).
- [x] Distribution: the exe as an immutable GitHub release with `THIRD-PARTY-NOTICES.txt` and `SHA256SUMS.txt`, built and published with the runbook's release steps; source through this repository.
