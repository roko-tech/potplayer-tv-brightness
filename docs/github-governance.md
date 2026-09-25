# GitHub governance

## Repository defaults

- Create new repositories private unless an explicit release decision says otherwise.
- Keep `main` releasable and use short-lived branches with pull requests.
- Prefer squash merge so the default branch receives one reviewed, descriptive commit per pull request. Delete merged branches.
- Keep Issues enabled for work and decisions; do not use chat as the only specification.
- Assign the narrowest repository, Actions, environment, and bot permissions that work.

## Issues, labels, and ownership

The repository includes forms for bugs, features, and architecture/RFC proposals. `python scripts/github_settings.py --apply` creates these labels and deletes GitHub's default labels that no issue or pull request uses:

- `type: bug`, `type: feature`, `type: architecture`;
- `status: triage`, `status: blocked`;
- `priority: p0`, `priority: p1`, `priority: p2`, `priority: p3`;
- `risk: high`.

Replace `.github/CODEOWNERS` with real accountable owners. Code ownership improves routing; it becomes an approval gate only when the branch/ruleset requires code-owner review.

## Default-branch rules

The desired baseline is encoded in `.github/rulesets/main.json`:

- block deletion and force pushes;
- require pull requests and resolved review conversations;
- require both Linux and Windows validation checks on an up-to-date branch.

Apply it after the first CI run so check names exist:

```shell
gh api --method POST repos/OWNER/REPOSITORY/rulesets --input .github/rulesets/main.json
```

Ruleset availability for private repositories depends on the GitHub organization plan. If GitHub rejects it, do not claim `main` is protected: use an available organization rule, upgrade the plan, or document the temporary manual merge control and owner.

For multi-maintainer projects, increase required approvals to at least one and require code-owner review for sensitive paths. Avoid configurations that make a solo repository impossible to maintain; use explicit admin bypass with audit when necessary.

## Continuous integration and Actions security

- Required CI must run on pull requests and `main`, with stable names and a timeout.
- Set workflow/token permissions to read-only by default and grant writes only at the job that needs them.
- Pin third-party actions to full 40-character commit SHAs and annotate the reviewed release tag.
- Use hosted/ephemeral runners for untrusted changes. Treat self-hosted runners as persistent sensitive infrastructure.
- Do not run fork-controlled code with repository secrets or a write token. Avoid `pull_request_target` for build/test workflows.
- Protect deployment environments with scoped secrets, reviewers, and branch/tag policies.
- Validate the exact artifact that is released; use provenance/attestations where supply-chain risk warrants them.

Dependabot is initially configured for GitHub Actions. Add each selected package ecosystem and review lockfile updates through normal CI.

## Security settings

Enable Dependabot alerts and security updates. Enable secret scanning and push protection when the plan supports them. Configure private vulnerability reporting before public release. Review repository access, deploy keys, webhooks, installed GitHub Apps, Actions allowlists, and stale credentials periodically.

## AI review

Optional Codex review can be enabled in Codex settings after the repository is connected. Root and nested `AGENTS.md` review rules should cover repository-specific consequential risks; deterministic checks stay in CI. Automatic AI review is not a required approval and cannot replace branch rules or human accountability.

## Configuration readback

`scripts/github_settings.py` encodes the repository, merge, label, Actions, and Dependabot baseline. It only reads by default and exits non-zero on drift; `--apply` applies the baseline and then reads every setting back. It checks visibility and topics without changing them, and preserves reviewed third-party action patterns in the Actions allowlist.

```shell
python scripts/github_settings.py            # check the current repository
python scripts/github_settings.py --apply    # apply, then read back
python scripts/github_settings.py --repo OWNER/REPOSITORY
```

Read back the remaining settings rather than trusting a successful command:

```shell
gh api repos/OWNER/REPOSITORY/rulesets
gh run list --repo OWNER/REPOSITORY --workflow ci.yml
```
