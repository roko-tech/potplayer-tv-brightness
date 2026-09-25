# Backup and restore plan

- Status: Not configured
- Owner: Define
- Last successful restore rehearsal: Never

A backup is not proven until a restore succeeds and the recovered system passes integrity and user-journey checks.

## Recovery objectives

| Data/system | RPO | RTO | Backup method | Retention | Encryption/access | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| Define | Define | Define | Define | Define | Define | Define |

RPO is the maximum acceptable data loss window. RTO is the maximum acceptable time to restore service.

## Backup design

Document included/excluded data, schedule, consistency mechanism, encryption, key ownership, geographic/account isolation, retention, deletion/legal requirements, monitoring, and failure alerting. Include configuration and object storage, not only the primary database, when required to reconstruct the service.

## Restore procedure

1. Declare the target point/time and isolated restore environment.
2. Verify authorization, capacity, keys, backup identity, checksum, and chain completeness.
3. Restore using the exact tested command or managed-service procedure.
4. Run schema and referential integrity checks.
5. Run critical user journeys and compare expected counts/invariants.
6. Reconcile writes that occurred after the restore point and prevent duplicate side effects.
7. Record elapsed time, achieved RPO/RTO, gaps, and evidence.
8. Destroy temporary sensitive copies according to policy.

## Rehearsal

Schedule restore drills proportional to data criticality and after material storage/migration changes. A drill that restores bytes but does not validate application semantics is incomplete.
