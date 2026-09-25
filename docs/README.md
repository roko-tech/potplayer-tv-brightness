# Documentation map

Documentation is part of the product. Keep each fact in one authoritative place and link to it elsewhere.

| Question | Source of truth | Update trigger |
| --- | --- | --- |
| Why does the product exist and how is success measured? | [Product brief](product/brief.md) | Outcome, user, scope, or constraint changes |
| How do projects move from idea to operation? | [Project lifecycle](project-lifecycle.md) | Delivery governance changes |
| How does a feature move from issue to release? | [Feature lifecycle](feature-lifecycle.md) | Contribution or quality gates change |
| What does the system look like now? | [Architecture overview](architecture/overview.md) | Boundaries, integrations, data, or deployment changes |
| Why was a consequential choice made? | [ADRs](architecture/decisions/README.md) | A durable decision is accepted or superseded |
| What larger change is being proposed? | [Design documents](design/README.md) | Before cross-cutting or hard-to-reverse implementation |
| How is behavior proved? | [Testing guide](testing.md) | Test strategy, commands, environments, or risk changes |
| What can go wrong and how is it controlled? | [Threat model](security/threat-model.md) | Assets, actors, trust boundaries, or controls change |
| How should code and dependencies be secured? | [Secure development](security/secure-development.md) | Security policy or implementation changes |
| How is the system operated and recovered? | [Runbook](operations/runbook.md) | Deployment, dependencies, alerts, or recovery changes |
| What reliability is promised? | [SLOs](operations/slo.md) | User journey or reliability target changes |
| Can state be restored? | [Backup and restore](operations/backup-restore.md) | Storage, retention, or recovery process changes |
| How do users accomplish their goals? | [User documentation](user/README.md) | User-visible behavior changes |
| How may AI assist safely? | [AI development](ai-development.md) and [AGENTS.md](../AGENTS.md) | AI workflow, model, data, or authority changes |
| How is GitHub governed? | [GitHub governance](github-governance.md) | Repository rules, CI, ownership, or automation changes |
| What must happen before release? | [Release checklist](release-checklist.md) | Release or distribution model changes |
| What evidence informed these defaults? | [References](references.md) | Guidance is reviewed or replaced |

## Documentation rules

- Current-state documents describe what is true now; update them with the code.
- ADRs explain accepted durable decisions; supersede them rather than rewriting history.
- RFCs describe proposals and alternatives before expensive implementation.
- Pull requests and commits provide change evidence; they are not substitutes for current documentation.
- Runbooks contain executable operational steps and owners, not architecture aspirations.
- Delete boilerplate that no longer matches reality. A shorter truthful document is safer than a complete-looking fiction.

The detailed policy is in [documentation-policy.md](documentation-policy.md).
