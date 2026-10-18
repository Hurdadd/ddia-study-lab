# Recovery objectives and drill protocol

Author: hurdad ashouri. Status: proposed pilot design; no platform drill has run.
The source of target values and budgets is [recovery.json](../final-project/recovery.json),
with the decision in [ADR-015](../final-project/adrs/ADR-015.md).

| Failure | RPO | RTO | Assumptions |
| --- | --- | --- | --- |
| Worker process | 0 acknowledged state | 120 s | Database/disk survive; committed checkpoints; fenced owners |
| Database/disk | 300 s | 1,800 s | Synthetic data ≤10GB; independent base backup and continuous WAL |
| Region | 900 s | 14,400 s | Cold cross-region recovery; independent backups, keys and infrastructure |
| Derived index | 0 authoritative data | 14,400 s | Source survives; one million docs; fixed arrival/service assumptions |

## Why these numbers

Worker: detection 15s + lease expiry 30s + claim 15s + replay 30s + validation 30s = 120s.
This bounds a short synthetic run disruption without paying for a hot redundant worker fleet.
Database: detection 3m + isolate/provision 5m + download 6m + replay 6m + validate 5m + reopen 5m = 30m.
A 10GB decimal transfer at 50MB/s takes about 200s; the download budget provides overhead.
A five-minute recovery gap is a conscious pilot loss budget, enforced by measuring contiguous
recoverability, not merely an archive timer. Failed archiving can violate it.
Region: 30m detect/declare + 60m provision + 60m restore + 60m validate + 30m reopen = 4h.
A 15-minute cross-region recovery gap trades pilot loss tolerance against warm-standby cost.
Real customer data or contractual requirements require revisiting both targets.
Index: 1,000,000/100 docs/s = 2.778h; catch-up with 5 changes/s arrivals and 30 changes/s
replay service takes 0.556h; validation adds 0.5h, totaling 3.834h. The four-hour budget has
about ten minutes of margin. Different throughput, arrivals or dataset size invalidates it.
These capacities are assumptions, not benchmark results.

## Planned experiment

1. Record numbered canaries, commit timestamps, tenant, policy version, checkpoint and
   expected artifact hashes in an independent journal. Never use production secrets.
2. Note failure onset; inject the scoped failure in an isolated synthetic environment.
3. Fence the old writer, restore the last contiguous recoverable point, verify artifact
   manifests, deletions and current IAM, then resume/rebuild as applicable.
4. End the clock only after an authorized end-to-end canary succeeds. A booted DB is insufficient.
5. Compute observed recovery gap and outage duration, count missing acknowledged records,
   and record stale-owner, duplicate-effect and cross-tenant checks.
6. Publish observed values, pass/fail against each target, logs and corrective actions.
   Repeat after changes; never replace a miss with a planned value.

If current IAM, deletion guards or fencing cannot be established, fail closed and record
an RTO miss. Archive timeout alone and an untested replica do not prove recovery.

## Current website

The recoverable source is the last verified pushed Git commit; unpushed work is outside
that boundary. Source RPO = 0 relative to that commit. Manual redeploy target = 30m,
not drilled, and not a hosting SLA. Clone the repository, run the checks and
static export, verify all-deployment authentication in the intended Vercel project,
then deploy and test authenticated content and anonymous denial.

References: [AWS DR terminology](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/introduction.html),
[PostgreSQL continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html).
