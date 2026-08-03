---
name: verification-lead
description: Use when the user separately starts Verification Lead or 검증 리드 for one exact implementation-handoff-v1 and a finite runtime budget; coordinates fresh read-only Assessors, sealed product-flow execution, immutable verification-result-v1 publication, and separately admitted remediation without combining implementation and certification authority.
---

# Verification Lead

## Purpose

Independently verify one current `ImplementationHandoff` at its exact planning and physical source
identity. Seal every exact Acceptance Criterion to concrete source-review and/or product-flow
obligations before execution, let the owner-controlled runner execute only those requests, preserve a
complete append-only ledger, and publish one immutable `VerificationResult`.

Verification Lead is an outer Coordinator. It does not implement product changes and does not decide
criterion semantics. It allocates finite budget, fresh actor capabilities, and exclusive transition
claims. A fresh read-only Assessor owns plan semantics and criterion verdicts. A separate fresh
Remediation Lead may admit source mutation only after an immutable failed result; a selected Worker
performs that mutation through Implementation Lead's ownership transaction.

## Public and internal contracts

Public contracts:

```text
implementation-handoff-v1
verification-result-v1
```

Owner-only internal artifacts:

```text
VerificationRun
implementation transaction
actor/capability records
finite budget reservation
exclusive transition claim
immutable continuation edge
```

`implementation-result-v3` is retired and cannot seed or replace either current public contract.

## Required input

Require:

1. one exact current `ImplementationHandoff` ref;
2. access to its canonical Ticket, approved Spec, project root, and repository authority;
3. one mandatory finite outer-invocation elapsed-time and resource budget;
4. current runtime capability to issue isolated Coordinator, Assessor, Remediator, and Worker roles as
   needed;
5. explicit invocation-local authorization refs for any high-risk external effect.

Do not inherit an Assessor, Remediator, Worker, conversational conclusion, proposed fix, mapping,
rationale, or evidence selection from an ancestor run.

## Callable tool

Use `tools/verification-run/verification_run.py` as the owner-controlled command surface. Run
`python3 tools/verification-run/verification_run.py --help` for the exact arguments. Its commands are:

```text
start-invocation
issue-authorization
open-verification
seal-run
execute-step
declare-contradiction
publish-result
read-run
read-artifact
preview-process-step
replay-authorization-scope
open-remediation
```

Drafts, budget vectors, criterion refs, and assessments are read from bounded JSON files. The execute
command accepts only run/flow/step IDs; it has no request or outcome argument. `read-run` returns a
redacted plan and complete attempt ledger. Raw bounded process output is available only through
`read-artifact` with the owning Assessor capability.
"Owning" means the exact Assessor actor bound to that VerificationRun, not another Assessor from the
same outer invocation. Ancestor raw artifacts remain unavailable to a fresh Assessor; the redacted
ledger is the audit/diagnosis surface.

## Role capabilities

| Role | May | Must not |
| --- | --- | --- |
| Coordinator | allocate invocation, actors, budget, claims; route lifecycle | mutate product; assess AC; publish semantic verdict |
| Assessor | read authority/source; seal plan; execute sealed steps; assess criteria; publish result | mutate source; call Worker; publish handoff |
| Remediation Lead | independently admit an authority delta; own remediation claim/transaction | seal verification plan; assess criteria; publish result |
| Worker | mutate only one frozen envelope | acquire claims; assess criteria; publish public artifacts |

Capability tokens are opaque, runtime-issued, invocation-local, role-specific, and stored only by
digest. Each Assessor and Remediator context is bound to at most one claim. A Worker actor cannot be
reused by another remediation transaction.

## Owner-store workflow

The immutable linear graph is:

```text
ImplementationHandoff
  -> VerificationResult at the same planning/source identity

INCOMPLETE | BLOCKED
  -> fresh VerificationResult for the same handoff/source

VERIFICATION_FAILED
  -> remediation-produced ImplementationHandoff at a new source

VERIFIED
  -> terminal
```

Before a run is sealed or a Worker is dispatched, the Coordinator reserves closure capacity and
atomically acquires the current tip's exclusive `VERIFY` or `REMEDIATE` claim. A current root or tip has
at most one active claim. The successor node, continuation edge, claim consumption, budget closure, and
run/transaction closure publish under one owner-store lock.

Public current state is derived by following unique immutable edges from the root; never infer it from
timestamps or a mutable `current` field.

## Finite budget

Every outer invocation has a positive elapsed-time deadline and finite counts for:

```text
workerCalls
remediationTransactions
effectfulActions
toolCostUnits
closureOperations
```

Reserve spend plus required readback, cleanup, reconciliation, and publication closure before a unit
starts. Exhaustion blocks a new unit but never abandons containment or closure already reserved. It
does not change the current public result, invent a fifth status, or authorize replanning.

## Opening a verification

The Coordinator:

1. resolves the unique current tip and its underlying handoff;
2. requires a handoff tip or an `INCOMPLETE`/`BLOCKED` result for that same handoff/source;
3. issues a fresh Assessor actor;
4. reserves explicit `VERIFY` spend and closure budget;
5. allocates a fresh `verification:run:v1:*` ref;
6. acquires an exclusive claim binding tip, planning identity, source identity, Assessor, run, and
   reservation.

Claim failure means no product action. A malformed draft may release the claim only before a
VerificationRun or any observation/attempt fact exists. Once preflight starts or the plan seals, the
claim closes only through an immutable VerificationResult.

## Preflight

Before the first product action, the Assessor and tool establish:

- current project identity equals the handoff final source;
- canonical Ticket, Spec, blockers, planning digest, exact AC bytes, and basis anchors are current;
- executable, cwd, source binding, and target are concrete and available;
- invocation-local authorization refs exist and match their exact scope digests;
- production, tenant, money/message, credential, user-data, irreversibility, cleanup, retention, and
  evidence-privacy risks are within authority;
- ambiguous effectful attempts in all same-handoff ancestor runs are not replayed without mechanically
  authorized safety.

Start identity mismatch publishes `INCOMPLETE` with
`CANDIDATE_IDENTITY_UNAVAILABLE_AT_START`, zero product attempts, and `sealedPlanDigest = null`.
Planning or authorization prohibition publishes `BLOCKED` with a non-empty reason code and no sealed
plan. Do not auto-adopt another source or modify the draft after observing a preflight result.

## Sealed verification draft

The Assessor supplies exactly:

```text
authorizationRefs[]
criteria[]
  criterionIndex
  criterionRawSha256
  sourceReviewIds[]
  flowIds[]
sourceReviews[]
  sourceReviewId
  criterionRefs[]
  basisAnchors[]
flows[]
  flowId
  criterionRefs[]
  claim
  expectedTerminalObservation
  basisAnchors[]
  productTargetRequirement = RETAIN | DISPOSABLE | NOT_APPLICABLE
  steps[]
  optionalCorrelationBindings[]
```

Each exact AC has at least one obligation. Criterion-to-review/flow mappings are exact and
bidirectional. Every review and flow references at least one exact AC. Mapping, component composition,
request, target, order, and cleanup policy are immutable after seal. After source mutation, a fresh
Assessor must rebuild every mapping; copying or delta-editing an ancestor plan is not authority.

## Basis anchors

Local authority uses exact anchors:

```text
canonicalPath
rawSha256
startLine
endLine
selectedTextSha256
```

The tool validates canonical path, whole raw file bytes, exact line range bytes, and both digests at
preflight and publication. An invocation authorization is never disguised as a file anchor.

## PROCESS MVP

The initial callable executor set is closed to `PROCESS`. A sealed step contains:

```text
stepId
role = ACTION | READBACK | CLEANUP
executorKind = PROCESS
executorVersion = process-v2
environmentPolicy = SEALED_EMPTY_BASE_V1
executable
argv[]
cwd
environmentDelta
inputRefs = []
sourceBinding
pollPolicy
canonicalRequestDigest
```

`sourceBinding.mode` is `CURRENT_PROJECT_ROOT` in the MVP. It binds the canonical project root and exact
handoff source identity. The runner resolves the executable/cwd before seal and later executes directly
from stored bytes with no shell. `execute_step(runRef, flowId, stepId)` accepts no replacement request.

`process-v2` creates the child environment from an empty map plus the exact sealed `environmentDelta`.
It never inherits the runner's ambient `PATH`, `HOME`, proxy, tenant, credential, feature-flag, or other
process values. Required values must be explicit sealed entries. Both executor version and environment
policy are part of the canonical request digest. An older ambient-overlay plan cannot execute under v2;
close it without a verified verdict and open a fresh sealed run.

The user-visible plan exposes each argv position only as its byte count and SHA-256 while the owner-only
sealed plan retains the exact non-sensitive execution bytes. Credential, user-data, payment/message
content, and other secrets must not be supplied in PROCESS argv. The PROCESS MVP has no secret resolver;
a secret-bearing operation is unsupported until a fixed core executor with opaque secret refs exists.

HTTP, BROWSER, and MCP are future fixed core executors. Adding one requires core canonicalization,
redaction, and a conformance pilot; runtime plugins, repository discovery, provider schemas, and a
generic workflow DSL are prohibited.

## Cardinality and polling

Each sealed ACTION and CLEANUP logical step can start at most once. A durable start record is written and
budget consumed before the external process. A crash after start is recorded as an incomplete attempt
and can never be retried in the same run.

READBACK has one logical execution with `1..10` identical-request polls and a bounded interval. Every
miss, error, output digest, and terminal poll remains in the ledger. No backoff, fallback, branch,
alternate target, or changed request is allowed. Tool error or identity drift stops polling.

Steps within a flow execute in sealed order. Separate flows cannot be post-hoc combined. A nonzero exit,
timeout, empty output, or tool error is a tool fact, not an automatic semantic verdict.

Logical step `COMPLETED` means that its bounded runner operation ended; it does not make a timeout or tool
error conclusive evidence. A required READBACK is usable only when at least one identical poll produced
an exact-source `EXITED` artifact; an earlier timeout may therefore be resolved by a later successful
poll. CLEANUP timeout/tool error remains `INCOMPLETE` in the MVP. ACTION timeout/tool error is resolved
only by a later exact-source READBACK in the same sealed flow, with every declared correlation binding
`MATCH`; without that readback the aggregate is `INCOMPLETE`.

## Correlation and causal continuity

An optional binding names one sealed ACTION and READBACK. The tool generates a unique correlation token,
substitutes only the literal predeclared placeholder in both requests, and records its digest. When
declared, exact byte presence must be `MATCH`; missing evidence is `UNAVAILABLE` and cannot be hidden by
rationale. No regex, JSONPath, DOM extraction, or field-mapping DSL is introduced.

Without a mechanical token, the Assessor may still conclude causality only from one presealed flow at
one source identity with complete runner-owned action/readback artifacts and explicit rationale. Any
concurrent-state ambiguity yields `INCOMPLETE`.

## Identity drift

Before and after every attempt, recapture the project identity. Drift records
`IDENTITY_DRIFT`, stops new product ACTIONs, and prevents `VERIFIED`. Remaining steps are closed as
`NOT_RUN`. Restoration of the old bytes does not resume the run; open a fresh claim and run.

A durable contradiction established before later drift may still produce `VERIFICATION_FAILED` when
its mapped evidence was complete at the exact identity. Otherwise drift yields `INCOMPLETE`.

## Contradiction stop

After one presealed exact-identity obligation is complete, the Assessor may durably declare its exact
criterion contradicted. The runner then refuses every later ACTION with
`ACTION_STOPPED_AFTER_CONTRADICTION` while allowing already-sealed READBACK and CLEANUP. Publication
records remaining actions as `NOT_RUN_PRIOR_CONTRADICTION`; the declaration must remain
`CONTRADICTED` in the immutable result.

## Product target disposition

`RETAIN` means the product target must remain usable after verification. A RETAIN flow can be verified
only when its final sealed step is an actually executed READBACK after every CLEANUP and that logical
READBACK contains at least one exact-source `EXITED` artifact. `DISPOSABLE`
allows planned removal. `NOT_APPLICABLE` is for a direct-result flow without a persistent target.

Runner-owned request files, traces, and materializations are not product resources. Product records,
queues, deployments, containers, messages, and accounts require explicit concrete CLEANUP when cleanup
is authorized and necessary.

## Criterion assessments and result publication

After execution, the Assessor submits exactly one ordered assessment for every sealed AC:

```text
criterionIndex
criterionRawSha256
verdict = SATISFIED | CONTRADICTED | INCONCLUSIVE | BLOCKED
semanticRationale
```

The caller cannot submit receipts, selected attempts, effects, readbacks, cleanup facts, source
observations, stdout summaries, aggregate status, or a source identity. The publisher reads the entire
run, validates every request/binding/currentness fact, fills every unstarted step with a tool-owned
`NOT_RUN` reason, and derives aggregate precedence:

```text
valid exact contradiction -> VERIFICATION_FAILED
else authority/safety prohibition -> BLOCKED
else evidence/capability/identity/sequence incompleteness -> INCOMPLETE
else every exact AC satisfied -> VERIFIED
```

A conclusive `SATISFIED` claim without all presealed obligations is rejected as a forged outcome. A
contradiction needs complete exact evidence or a prior durable contradiction declaration.

The public result is exactly:

```text
protocolVersion = verification-result-v1
verificationResultRef
verificationStatus
implementationHandoffRef
planningSealDigest
finalSourceIdentity
verificationRunRef
sealedPlanDigest
criterionResults[]
reasonCodes[]
completedAt
```

Preflight terminal results have `sealedPlanDigest = null`, empty criterion results, and non-empty reason
codes. Sealed-run results include every exact criterion once. Public results never inline ledger or
artifact content.

## Cross-run effect replay

An `INCOMPLETE`/`BLOCKED` result does not erase ambiguous ACTION/CLEANUP attempts in earlier same-handoff
runs. Before any new effectful step, inspect all such ancestor ledgers. Replay requires one of:

- authoritative readback that mechanically establishes prior effect state;
- runtime-issued exact-idempotency scope for the new request and stable target;
- runtime-issued unique-correlation scope plus a newly generated correlation binding.

Missing safety authority publishes `BLOCKED`; unavailable evidence/capability publishes `INCOMPLETE`.
Per-run cardinality alone is never replay authority.

## Verification-triggered remediation

Remediation can open only from the exact current immutable `VERIFICATION_FAILED` ref. The Coordinator
issues fresh Remediator and Worker actors, reserves finite `REMEDIATE` spend and closure, and acquires
the exclusive claim. It does not decide admission.

The fresh Remediation Lead independently reads Ticket, Spec, current source, applicable product/UI/
repository authority, and tool-owned failed facts. It records `ADMITTED` only when behavior, AC meaning,
Scope, Non-Goals, public/persisted semantics, material UI choices, migration policy, target, tenant,
effect class, safety, and ownership authority are already settled.

Then use Implementation Lead's `VERIFICATION_REMEDIATION` transaction:

```text
failed source baseline Capsule
fresh selected Worker
frozen mutation envelope
ownership before/after and reconciliation
mandatory implementation checks
non-empty authorized retained delta
new non-ancestor source identity
atomically linked successor ImplementationHandoff
```

No source-changing step belongs in VerificationRun. After the handoff, issue a fresh Assessor and
reseal every exact AC. Old attempts, mappings, rationale, and provisional smoke remain audit context
only.

## Remediation progress and stop

There is no protocol cycle cap. Continue only while authority, currentness, safety, ownership, claims,
capabilities, finite budget, and progress remain valid.

When a stable structured fact exists, compare:

```text
criterionRawSha256
sealed obligation/request projection
stable target binding
structured terminal fact or correlation result
```

Only `MATCH` stops another automatic mutation. `NO_MATCH` may continue. `UNAVAILABLE` creates no generic
semantic classifier.

A no-delta or fully restored remediation may release without a handoff only after immutable ownership,
identity-restoration, preservation, and external-effect-clear closure. Any retained or ambiguous state
keeps the claim active.

## Terminal return

Return the immutable VerificationResult and current workflow tip. For a remediation cycle, also report
the successor handoff and fresh result refs, never ancestor evidence as current certification.

Do not claim success from Worker prose, a helper test, a provisional smoke, selected favorable attempts,
or a result that was not atomically published from the complete run.
