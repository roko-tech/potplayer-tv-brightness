# Design documents and RFCs

Use an RFC before implementing a change that is cross-cutting, hard to reverse, high risk, externally coordinated, or likely to create a durable contract. Small local changes should remain in the issue and pull request.

Copy [rfc-template.md](rfc-template.md) to `YYYY-MM-DD-short-title.md`. Mark it `Proposed`, request review from affected owners, and record the final state as `Accepted`, `Rejected`, or `Withdrawn`. If acceptance creates a durable architectural choice, add an ADR that links back to the RFC.

RFCs explain the proposed future. The [architecture overview](../architecture/overview.md) must be updated after implementation to describe current reality.
