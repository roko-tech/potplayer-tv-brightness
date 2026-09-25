# Release checklist

Use this checklist proportionally for a candidate release. The release owner records evidence and accepts any remaining risk.

## Scope and change control

- [ ] Version, commit, included changes, migrations, and target environments are identified.
- [ ] Acceptance criteria are met; known issues and unsupported surfaces are explicit.
- [ ] User-facing changes are in the changelog/release notes and user documentation.
- [ ] Required approvals and CI checks apply to the exact commit being released.

## Quality and compatibility

- [ ] Formatting, lint, typing, unit, integration, and end-to-end suites pass as applicable.
- [ ] The release artifact was built reproducibly and inspected/tested—not replaced after validation.
- [ ] Clean install/upgrade and primary user journeys pass on supported platforms.
- [ ] Schema/API/configuration compatibility and migration/rollback behavior are proven on realistic prior state.
- [ ] Performance, accessibility, localization, and resource limits were checked where relevant.

## Security, privacy, and supply chain

- [ ] Threat-model changes and high-risk findings are resolved or explicitly accepted by an owner.
- [ ] Secret, dependency, license, and artifact/provenance checks pass.
- [ ] Permissions, data collection, retention, deletion, export, logs, telemetry, and AI data use match documentation.
- [ ] No credentials, private data, debug endpoints, unsafe defaults, or development artifacts are included.

## Operations

- [ ] Deployment order, owner, monitoring window, success/stop signals, and communication are defined.
- [ ] Rollback or roll-forward steps are compatible with data changes and were rehearsed proportionally to risk.
- [ ] Dashboards, alerts, logs, traces, support routes, and runbooks match the release.
- [ ] Backup health is known and a restore has been rehearsed after material storage changes.

## Publish and verify

- [ ] Publish only from the reviewed Git commit through the documented release path.
- [ ] Verify checksums/signatures/attestations and repository/package metadata.
- [ ] Install or access the published artifact as a real user and run a smoke journey.
- [ ] Confirm version/update behavior and monitor user-facing indicators after release.
- [ ] Record evidence, residual risk, and any follow-up owner/date.
