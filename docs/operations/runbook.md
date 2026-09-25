# Operations runbook

- Status: Template; replace every instruction with tested project commands.
- Service owner: Define
- Escalation contact: Define
- Last rehearsed: Never

Do not present placeholders as executable instructions in a live service. Each production procedure needs an owner, prerequisites, safe command or UI path, expected output, failure branch, rollback, and last rehearsal date.

## Service summary

- User journey served:
- Environments and URLs:
- Deployment unit/artifact:
- Data stores and external dependencies:
- Dashboards, logs, traces, and alert routes:
- Current release/version lookup:

## Health assessment

1. Confirm scope: one user, one tenant, one region, or global.
2. Check user-journey indicators and recent deployments/configuration changes.
3. Check dependency health, saturation, queue/backlog, and error classes.
4. Correlate logs/traces using safe identifiers; do not copy sensitive payloads.
5. Record timestamps, evidence, and uncertainty in the incident channel/ticket.

## Deploy

Define exact preflight checks, immutable artifact identification, migration order, deployment command, smoke test, monitoring window, and completion criteria. Prefer promotion of the artifact already validated by CI.

## Roll back or roll forward

Define when rollback is safe, especially after schema or externally visible writes. Name the previous artifact, command, data compatibility requirement, verification, and escalation point. For irreversible data changes, provide a rehearsed roll-forward or restore procedure.

## Common failure playbooks

For each alert or common symptom, add:

- user impact and urgency;
- likely and dangerous causes;
- read-only diagnostic steps first;
- bounded mitigation;
- validation and rollback;
- evidence to preserve;
- owner and follow-up issue.

## Shutdown and restart

Check active requests, jobs, migrations, and external side effects before shutdown. Drain or checkpoint work, preserve idempotency state, restart with known configuration, and verify the primary user journey—not only process health.

## Incident closure

Confirm recovery against service indicators and user behavior, communicate remaining risk, preserve a timeline, and create a postmortem for significant impact using [postmortem-template.md](postmortem-template.md).
