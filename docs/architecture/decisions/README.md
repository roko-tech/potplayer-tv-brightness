# Architecture decision records

ADRs preserve why a consequential, durable choice was made. Use one for architecture boundaries, public contracts, data ownership, security posture, major dependencies, deployment topology, or another decision that future maintainers may otherwise undo without understanding the tradeoff.

Do not create ADRs for routine implementation details or easily reversible preferences.

## Workflow

1. Copy [0000-template.md](0000-template.md) to the next four-digit number and a short lowercase slug.
2. Set status to `Proposed` while discussion is active.
3. Record the decision only after it is accepted; link the issue/RFC and evidence.
4. If the choice changes, add a new ADR and mark the old one `Superseded by ADR-NNNN`.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-default-to-a-modular-monolith.md) | Accepted | Default to a modular monolith |
