# Documentation policy

## What to preserve

Preserve information future contributors need to use, change, operate, audit, or reverse the system:

- product intent, scope, users, constraints, and measurable outcomes;
- current architecture, interfaces, data ownership, trust boundaries, and operations;
- consequential decisions, alternatives, tradeoffs, and consequences;
- user-facing behavior and support guidance;
- validation evidence, migration/rollback instructions, incidents, and known limitations.

Do not archive every prompt, command, exploratory branch, or intermediate thought. Git history and pull requests provide change evidence; current documents must remain readable without that archaeology. Never store private chain-of-thought.

## Choose the right artifact

| Artifact | Purpose | Editing rule |
| --- | --- | --- |
| README/current docs | Explain what is true now | Update in the same change as behavior |
| Issue | Define a problem and acceptance | Refine until implementation is actionable |
| RFC/design document | Compare a proposed material change | Mark proposed, accepted, rejected, or withdrawn |
| ADR | Preserve an accepted durable decision | Supersede; do not rewrite historical rationale |
| Pull request | Explain one implementation and its proof | Preserve exact validation and limitations |
| Changelog/release notes | Explain externally relevant change | Write for affected users/operators |
| Runbook | Execute an operational response | Test steps and identify owner/last rehearsal |
| Postmortem | Learn from an incident | Separate evidence, inference, impact, and actions |

## Quality standard

Every durable document should answer:

1. Who is it for and who owns it?
2. What is fact, decision, assumption, or proposal?
3. What evidence supports it?
4. When must it be updated or reviewed?
5. What remains unknown or intentionally out of scope?

Use links instead of duplicating facts. Prefer diagrams only when relationships are clearer visually. Date time-sensitive reviews. Delete misleading boilerplate.

## Documentation in definition of done

Review changed behavior against `README.md`, architecture, ADRs, API/user docs, threat model, testing guide, runbooks, and changelog. If no documentation changed, the pull request should say why none became inaccurate.
