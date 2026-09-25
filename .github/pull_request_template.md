## Outcome

Describe the user/developer outcome and link the issue (`Closes #...`).

## What changed and why

Explain the smallest coherent implementation, important tradeoffs, and any ADR/RFC. Do not paste a file list that the diff already shows.

## Acceptance evidence

| Acceptance criterion | Evidence |
| --- | --- |
| Define | Test, screenshot, artifact, or observed result |

## Risk and operations

- [ ] No public API/compatibility impact, or it is described below.
- [ ] No schema/data migration impact, or migration and rollback/roll-forward are described below.
- [ ] No authentication, authorization, privacy, security, or abuse impact, or the threat model/tests are updated below.
- [ ] No deployment, configuration, observability, SLO, backup, or support impact, or the runbook is updated below.
- [ ] External side effects are idempotent/recoverable where required.

Risk, rollout, and rollback details:

## Validation

List exact commands, environments, and results. Include real user/platform/artifact evidence where relevant.

```text
command -> result
```

Not run or not proven:

## Documentation

- [ ] Current architecture/user/operations/testing/security docs are updated, or none became inaccurate.
- [ ] An ADR/RFC is added or superseded when a durable decision changed.
- [ ] `CHANGELOG.md` is updated for externally relevant behavior.
- [ ] Visual changes include safe current screenshots/recordings where useful.

## Final checklist

- [ ] The change is scoped to the issue and preserves unrelated work.
- [ ] New dependencies are necessary, reviewed, pinned, and approved.
- [ ] Tests prove changed behavior and important failure paths without being weakened.
- [ ] No secrets, credentials, private data, unsafe logs, or development artifacts are included.
- [ ] Limitations and untested surfaces are stated without overstating confidence.
