# Contributing

## Before implementation

Start from an issue that names the problem, desired outcome, acceptance criteria, constraints, and known risk. Use the [feature lifecycle](docs/feature-lifecycle.md) to decide whether the issue is enough or an RFC/ADR is also required.

For bugs, include reproducible evidence. For user-visible features, define how a real user will prove the outcome. For data or operational changes, include migration, observability, and rollback expectations.

## Branches and commits

- Branch from an up-to-date `main` using a short-lived branch such as `feat/issue-123-export` or `fix/issue-456-timeout`.
- Keep each commit coherent and buildable when practical.
- Use a concise imperative subject and a substantive body for non-trivial commits: what changed, why, impact, and validation.
- Do not include generated co-author trailers for AI tools such as Codex or Claude.
- Never commit secrets, local `.env` files, credentials, production data, or unapproved personal data.

## Pull requests

Keep pull requests small enough to review accurately. Complete the pull request template with:

- the user/developer outcome and linked issue;
- implementation and decision summary;
- risk, security, data, migration, observability, and rollback impact;
- exact validation commands and results;
- screenshots or recordings for visual behavior;
- documentation and changelog changes;
- explicit limitations and untested surfaces.

Draft pull requests are welcome for early design feedback. A pull request is merge-ready only when acceptance criteria are satisfied, required checks pass, review conversations are resolved, and the branch is current under the repository rules.

## Local validation

The template baseline is:

```shell
python scripts/verify.py
python -m unittest discover -s tests -v
git diff --check
```

Projects created from this template must add their stack-specific commands here and in CI.
