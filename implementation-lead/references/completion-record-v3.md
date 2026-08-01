# Completion Record v3

## Purpose

This reference owns the durable evidence input for new ImplementationResult
publication. It adds no RunState, TaskState, product requirement, runtime
adapter, or independent certification. The publisher checks structural
completeness and current identity bindings; Implementation Lead owns the
semantic judgment that an entry point, effect, and readback satisfy the Ticket.

## Request

The exact request fields are:

```text
protocolVersion = implementation-result-v3
projectRoot
planningSeal
capsuleRef
finalSourceIdentity
completionRecord
```

`implementationStatus` is not caller input. Successful publication writes
`IMPLEMENTATION_COMPLETE` and a new `implementation:v3:<32-lowercase-hex>` ref.
Existing v2 artifacts are immutable history; there is no v2 publish fallback.

## Exact Shape

All property names are case-sensitive and unknown properties are rejected.

```text
completionRecord
  acceptanceCriteriaDigest
  supplementalLocalAuthorityBindings[]
    authorityBindingId
    role
    canonicalPath
    rawSha256
  coverage[]
    criterionIndex
    criterionRawSha256
    state = ESTABLISHED
    evidenceRequirements[]
      requirementId
      kind = SOURCE | RUNTIME
      state = ESTABLISHED
      evidenceRefs[]
  sourceEvidence[]
    evidenceId
    coveredRequirementIds[]
    authorityLocators[]
    authorityBindingRefs[]
    sourceIdentity
    reviewSummary
  runtimeObservations[]
    observationId
    coveredRequirementIds[]
    entryPointAuthority
      authorityLocators[]
      authorityBindingRefs[]
    executionTargetBinding
      mode = CURRENT_PROJECT_ROOT | SOURCE_BOUND_MATERIALIZATION | REVISION_BOUND_TARGET
      authorityLocators[]
      finalSourceIdentity
      targetIdentityOrRevision
      bindingSummaryOrDigest
    redactedInvocationSummary
    expectedEffectSummary
    observedEffectSummary
    observationMode = DIRECT_RESULT | INDEPENDENT_READBACK
    readbackSummaryOrDigest
    planningSealDigest
    sourceIdentityBefore
    sourceIdentityAfter
    projectDeltaBinding
      ownershipSnapshotIdentityBefore
      ownershipSnapshotIdentityAfter
      changedPathCount = 0
      deltaSummaryOrDigest
      disposition = CLEAR
    cleanupDisposition
      required
      state = NOT_REQUIRED | COMPLETE
      authorityOrRationale
      readbackSummaryOrDigest
    observedAt
  unresolvedItems[] = []
```

## Invariants

- Coverage order, count, `criterionIndex`, `criterionRawSha256`, and
  `acceptanceCriteriaDigest` exactly match the current Ticket parser contract.
- Every Criterion has at least one Evidence Requirement and every requirement
  has one or more bidirectionally consistent evidence references of the same
  kind. Duplicate IDs, duplicate locators, unreferenced evidence, and
  unreferenced supplemental authority are invalid.
- Source evidence identity equals requested `finalSourceIdentity`.
- Runtime observations are created by Implementation Lead at final review, not
  promoted from Worker feedback. Their before/after source identities and
  execution-target final identity equal the requested final identity.
- Current-root and source-materialization target identity equals the final
  source identity. Revision-bound targets also require repository/deployment
  authority locators, an exact revision, and a bounded binding summary.
- `planningSealDigest` equals the publisher's digest of the already validated
  canonical PlanningInputSeal.
- Ownership snapshot identities before and after are equal, changed path count
  is zero, and disposition is `CLEAR`.
- Required cleanup has `COMPLETE` plus cleanup readback. Cleanup not required
  has `NOT_REQUIRED` plus a bounded authority or rationale.
- Supplemental local authority paths are canonical regular files whose current
  raw-byte SHA-256 equals `rawSha256` immediately before publication.
- `unresolvedItems` is empty. The caller cannot use a complete state string to
  override any missing evidence or binding.

## Stable Publication

The pre-publication Lead gate is necessary but not the publisher's final
currentness boundary. The publisher keeps the Capsule read lease through the
entire publication and uses this protocol:

1. Validate and normalize the canonical PlanningInputSeal, current Ticket
   criteria, Completion Record, supplemental local authorities, Capsule/project
   binding, and final source identity.
2. Serialize one pending result outside the public `*.json` result namespace and
   read back the exact bytes.
3. Revalidate Ticket, Spec, blocker, supplemental-authority, Acceptance Criteria,
   and final source identities after the pending write and immediately before
   the atomic exclusive publication.
4. Atomically link the pending bytes to the new immutable v3 result path, remove
   the pending name, and fsync the result directory.
5. Revalidate all identities once more and read back the published bytes before
   returning success.

Any mutation detected at a gate rejects publication with its currentness or
identity error. A failure after the atomic link removes that newly linked result;
failed publication leaves neither a public success artifact nor a pending file.
Mutation after the final successful revalidation belongs to later historical
freshness, not to the completed publication interval.

## Bounds And Privacy

The whole compact JSON request is at most 262144 bytes. It contains at most 128
criteria, 512 requirements, 512 source evidence records, 512 runtime
observations, 128 supplemental authorities, and 128 references per record.
Identifiers are at most 128 ASCII identifier characters, summaries are at most
4096 UTF-8 bytes, and locators are at most 2048 UTF-8 bytes.

Store only redacted summaries, match outcomes, locators, and digests. Raw
stdout, response bodies, screenshots, credentials, user data, payment/message
content, and generic raw-payload fields are not part of this schema.
