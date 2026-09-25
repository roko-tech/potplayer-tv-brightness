# ADR-0001: Default to a modular monolith

- Date: 2026-08-20
- Status: Accepted
- Owners: Project maintainers
- Related: Initial project-starter architecture

## Context

New projects rarely have measured scaling, isolation, or organizational requirements that justify multiple deployable services. Starting distributed adds network failure modes, consistency decisions, deployment coordination, observability, local-development, and testing costs before product risk is reduced.

At the same time, an unstructured monolith can entangle business capabilities and make later change unsafe.

## Decision drivers

- Fast delivery of the first end-to-end user outcome.
- Low operational and cognitive overhead.
- Explicit ownership and dependency direction.
- A credible path to extract a capability if evidence later requires it.

## Considered options

### Modular monolith

One deployable unit with explicit capability modules and controlled dependencies. It keeps calls and transactions local while allowing boundaries to be tested.

### Microservices from the start

Independent deployables can isolate scale and ownership, but those benefits are hypothetical at project inception while distributed costs are immediate.

### Unstructured single application

It is initially simple but lacks enforceable ownership and creates accidental coupling as the codebase grows.

## Decision

Begin as a modular monolith. Modules own business invariants and data access, expose narrow contracts, and avoid depending on another module's internals. External providers sit behind adapters where testability or failure isolation justifies the seam.

Split a module into an independent service only after measured independent scaling, fault/security isolation, data sovereignty, deployment cadence, or ownership requirements justify the added operational cost.

## Consequences

### Positive

- The project can ship and test vertical slices with a small operational footprint.
- Most consistency and failure handling remains in-process.
- Explicit module contracts keep extraction possible without prematurely paying for distribution.

### Negative and tradeoffs

- Teams must actively enforce module boundaries inside one repository/process.
- A single deployment can couple release cadence and broad failure impact.
- Extraction later still requires migration work; boundaries reduce but do not remove it.

### Follow-up

Replace the generic module map in the architecture overview. Reconsider this ADR when operating evidence shows a persistent boundary need, and record any extraction in a superseding ADR.

## Validation

Architecture tests or dependency checks should prevent forbidden module access once a stack is chosen. Operational measures should be used to justify any proposed service split.
