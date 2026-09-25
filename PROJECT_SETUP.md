# Project setup checklist

Complete this checklist in the first pull request created from the template. Keep the file afterward as the auditable receipt of setup decisions; `scripts/verify.py` requires it.

## 1. Define the product

- [ ] Replace the template description in `README.md` with the project name, purpose, users, and quick start.
- [ ] Complete [docs/product/brief.md](docs/product/brief.md), including measurable outcomes and explicit non-goals.
- [ ] Name a product owner and technical owner.

## 2. Choose only the necessary technology

- [ ] Record runtime, framework, database, deployment target, and important constraints.
- [ ] Capture consequential choices as ADRs; do not create ADRs for reversible local preferences.
- [ ] Add the minimum application skeleton needed for the first vertical slice.
- [ ] Update `.gitignore`, `.editorconfig`, and `.env.example` for the selected stack.
- [ ] Choose and add an appropriate license before external distribution.

## 3. Make commands truthful

- [ ] Add reproducible setup, run, test, lint, type-check, build, and package commands.
- [ ] Replace or extend the commands in `AGENTS.md`, `CONTRIBUTING.md`, and CI.
- [ ] Pin direct dependencies and commit the ecosystem lockfile.
- [ ] Configure Dependabot for each package ecosystem actually used.

## 4. Design the system

- [ ] Replace the generic context and container diagrams in [docs/architecture/overview.md](docs/architecture/overview.md).
- [ ] Define module boundaries, dependency direction, data ownership, and external integrations.
- [ ] Identify trust boundaries and complete [docs/security/threat-model.md](docs/security/threat-model.md).
- [ ] Decide how configuration, secrets, logs, metrics, and errors are handled.

## 5. Establish quality evidence

- [ ] Add one end-to-end vertical-slice acceptance test for the primary user outcome.
- [ ] Add fast unit/component tests around business rules and integration tests at real boundaries.
- [ ] Add platform-specific or live-system checks where hermetic tests cannot prove behavior.
- [ ] Define test data, coverage expectations, and unacceptable regressions in [docs/testing.md](docs/testing.md).

## 6. Prepare operations

- [ ] Define environments, deployment owner, release process, and rollback procedure.
- [ ] Define service-level indicators/objectives and alert ownership.
- [ ] Configure backups where state exists and perform a measured restore rehearsal.
- [ ] Remove example operational language that does not match the real system.

## 7. Configure GitHub

- [ ] Replace or confirm `.github/CODEOWNERS` ownership.
- [ ] Run `python scripts/github_settings.py --apply` to apply the label, merge, Actions, and Dependabot baseline, then set project-specific topics.
- [ ] Enable branch rules from `.github/rulesets/main.json` or equivalent organization rules.
- [ ] Require the real CI checks and conversation resolution before merge.
- [ ] Enable Dependabot alerts/updates and secret scanning or push protection when the plan supports them.
- [ ] Restrict Actions permissions and environments to least privilege.
- [ ] Connect optional AI review only after `AGENTS.md` contains project-specific review rules.

## 8. Protect users and data

- [ ] Define the private security-reporting contact in `SECURITY.md`.
- [ ] Classify collected data, retention, deletion, export, and audit requirements.
- [ ] Add authentication/authorization tests if identities or permissions exist.
- [ ] Confirm that logs, telemetry, prompts, fixtures, and AI tools receive no unapproved sensitive data.

## 9. Prove readiness

- [ ] Run every documented local command from a clean checkout.
- [ ] Verify CI on the supported operating systems.
- [ ] Exercise the primary workflow like a real user in the intended runtime.
- [ ] Record known limitations and untested surfaces honestly.
- [ ] Review [docs/release-checklist.md](docs/release-checklist.md) before the first release.
