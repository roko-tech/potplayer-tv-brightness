# Feature lifecycle

## Classify before designing

- **Small:** local, reversible, no public contract or trust-boundary change. A well-formed issue is enough.
- **Medium:** spans modules or changes user behavior, data, an API, or operations. Add a design section to the issue or a short RFC.
- **Large/high risk:** cross-cutting, security/privacy-sensitive, difficult to reverse, costly, or externally coordinated. Use an RFC and capture accepted durable decisions in ADRs.

When uncertain, write the smallest design that exposes the uncertainty; do not expand implementation to compensate for an unclear goal.

## 1. Frame the issue

Record the problem, user outcome, non-goals, acceptance criteria, constraints, evidence, and risk. For a defect, include reproduction steps and expected versus actual behavior.

## 2. Read the system

Inspect relevant code, tests, architecture, ADRs, runbooks, logs, data shape, and real runtime behavior. Check the working tree before editing. Name assumptions that still need proof.

## 3. Design the change

Choose the smallest coherent approach. Identify affected contracts, data, trust boundaries, dependencies, observability, deployment, rollback, and documentation. Compare alternatives only where the tradeoff matters.

## 4. Define proof first

Translate acceptance criteria into tests and verification steps. A bug fix should have a failing reproduction when practical. Decide what requires unit, integration, end-to-end, platform, migration, load, security, accessibility, or live-system evidence.

## 5. Implement surgically

Keep the change focused. Avoid unrelated cleanup. Add no speculative layers or dependencies. Make invalid states explicit at boundaries and preserve user data on failure.

## 6. Validate in layers

Run fast focused checks while iterating, then the full affected suite. Inspect the actual built/installed/deployed artifact where packaging or environment differences matter. State what mocks and test doubles do not prove.

## 7. Review and merge

The pull request should make the outcome, design, risk, evidence, docs, and limitations understandable without reconstructing chat history. Resolve consequential review findings and keep `main` releasable.

## 8. Release and observe

Use a reversible release strategy proportional to risk. Confirm telemetry and user-visible behavior, then update the changelog and current documentation. If results contradict the decision, supersede it explicitly.
