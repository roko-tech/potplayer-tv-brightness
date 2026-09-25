# Project lifecycle

Use lightweight gates to prevent expensive ambiguity. The required evidence grows with consequence; a one-person utility and a regulated multi-user service should not carry identical process.

## 1. Discover

Define the user problem, evidence, constraints, non-goals, and measurable outcome in the [product brief](product/brief.md). Identify the smallest vertical slice and the assumptions most likely to make the project unnecessary or unsafe.

Exit when the team can state who benefits, what changes for them, and how success or failure will be measured.

## 2. Design

Map the system context, trust boundaries, data ownership, external integrations, failure modes, and operational shape. Default to the simplest deployable architecture that preserves clear module boundaries.

Use an RFC when the proposal is cross-cutting, high risk, expensive to reverse, or needs agreement. Record an ADR after the significant choice is accepted.

Exit when the first slice has testable acceptance criteria and the major risks have owners or experiments.

## 3. Establish the delivery path

Before feature volume grows, make one thin path work from local setup through CI, packaging/deployment, observability, and rollback. Pin dependencies, keep secrets outside source control, and make commands reproducible from a clean checkout.

Exit when a new contributor can build and validate the same artifact CI validates.

## 4. Build in vertical slices

Implement one user-observable outcome at a time. Keep branches and pull requests short-lived. Add behavior tests with the code, update current documentation, and record only decisions that need durable context.

Exit each slice when its acceptance criteria and definition of done are met.

## 5. Review and release

Use deterministic checks, focused human review, and optional AI review. Assess security, privacy, data migration, compatibility, observability, support, and rollback. Build once where practical and promote the same immutable artifact through environments.

Exit when the release checklist is complete and the release owner accepts the documented residual risk.

## 6. Operate and learn

Measure user outcomes and service indicators. Rehearse recovery, investigate incidents without hiding uncertainty, and turn validated lessons into tests, runbooks, current architecture, or superseding decisions.

Retire unused features and stale documentation. Complexity has an operating cost even when the code still passes.

## Proportional evidence

| Change | Minimum durable evidence |
| --- | --- |
| Small, local, reversible | Issue, acceptance criteria, tests, pull request |
| User-visible feature | Above plus user docs/changelog and end-to-end evidence |
| Cross-module/API/data change | RFC or design section, integration/compatibility tests, migration/rollback plan |
| Durable architectural choice | Accepted ADR and updated architecture |
| Security/privacy boundary | Threat-model update, abuse cases, security tests, explicit reviewer |
| Operational/release change | Runbook, observability, rollback, and live or platform-specific receipt |
