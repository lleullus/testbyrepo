# ImplementationHandoff v1

This is the only active public completion contract emitted by Implementation Lead.

## Boundary

`ImplementationHandoff` proves that one durable implementation transaction closed its source,
ownership, checks, and integration responsibilities at one exact physical source identity. It does not
assert a final Acceptance-Criterion verdict and does not contain caller-authored runtime observations.

The public status is fixed:

```text
IMPLEMENTATION_HANDOFF_COMPLETE
```

Independent verification remains pending until a `verification-result-v1` node is atomically linked by
the workflow owner store.

## Exact payload

```text
protocolVersion = implementation-handoff-v1
implementationHandoffRef
implementationStatus = IMPLEMENTATION_HANDOFF_COMPLETE
projectRoot
planningSeal
planningSealDigest
baselineCapsuleRef
baselineSourceIdentity
finalSourceIdentity
implementationDeltaRef
criterionAccounting[]
  criterionIndex
  criterionRawSha256
  taskIds[]
unresolvedImplementationItems = []
completedAt
```

The publisher rejects extra caller status fields, unresolved implementation items, stale planning
bytes, stale AC identity, task linkage that differs from frozen transaction envelopes, Capsule/project
mismatch, source drift, and caller-shaped delta or identity facts.

## Initial implementation

The publisher reads one `INITIAL_IMPLEMENTATION` transaction in `READY_FOR_HANDOFF`. A zero-mutation
delta is legal when the candidate was already implementation-complete. Node insertion and transaction
closure are one owner-store transaction.

## Verification remediation

The publisher requires the active claim-owning `REMEDIATOR` capability and the exact
`VERIFICATION_REMEDIATION` transaction bound to that claim. The baseline must equal the failed result
source. Publication requires a non-empty retained Worker-attributable delta, a new final source
identity, and no ancestor source identity reuse. Preserved external/concurrent paths are retained in
the physical source and recorded in a separate delta partition, but cannot satisfy remediation
progress.

The successor handoff node, failed-result continuation edge, claim consumption, budget-reservation
closure, transaction closure, and publication event are atomic.

## Public lineage

Predecessor refs are not added to the v1 payload. The owner-only immutable edge store supplies lineage
and a unique current tip. If a deployment cannot preserve atomic unique edges, it must not expose this
protocol as callable.

## Prohibited fields and claims

Do not include:

- `verificationStatus`;
- `criterionResults` or semantic verdicts;
- runtime receipts, selected attempts, stdout summaries, or caller-authored observations;
- predecessor or trigger refs duplicated from the owner-store edge;
- an `implementation-result-v3` compatibility envelope.

Historical v3 artifacts remain byte-preserving read-only records and are never converted to a handoff.
