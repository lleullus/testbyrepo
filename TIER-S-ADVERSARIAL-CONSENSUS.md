# S Tier Adversarial Consensus

## Decision

S tier accepts exactly two wording-level corrections in
`verification-lead/SKILL.md`:

1. Avoid a new Coverage Challenger invocation when a rebuilt envelope has an
   unchanged `challenge_fp` and the existing effective-PASS receipt passes the
   current local `coverage_gate.py approve` path's validation.
2. Replace the two adjacent approval requests with one explicit request for the
   exact plan.

No code, API, cache, role, authority, evidence, route-index, or product-runtime
change is accepted in this tier. This document records the design decision; it
does not implement the two corrections.

## Review Frame

- Default: preserve the current design.
- Acceptance threshold: provable semantic equivalence or removal of a concrete
  repeated call with unchanged safety, authority, freshness, failure behavior,
  and independent-verification guarantees.
- Oracle role: attack the preservation default and expose hidden costs.
- Lead role: defend authority and freshness boundaries, attack Oracle proposals'
  tradeoffs, and accept only strict Pareto improvements.
- Evidence: the complete current repository was supplied as a fresh ZIP on
  every substantive Oracle turn.

## Accepted Change 1: Challenger Receipt Reuse

### Conflict

`verification-lead/SKILL.md` currently establishes all of these rules:

- every initial or replacement disclosure rebuilds the Coverage Gate Envelope;
- `challenge_fp` covers the Challenger-owned semantic input;
- readiness, readiness evidence, preparation, disposition, and partial-plan
  value are excluded from `challenge_fp`;
- a `plan_fp`-only change requires redisclosure and reapproval but not semantic
  rechallenge;
- an attestation may be reused while its exact semantic input remains current;
  and
- the operative paragraph nevertheless directs the Lead to invoke a Challenger
  after every successful `build`.

The unconditional invocation conflicts with the fingerprint and reuse rules.
For a plan-only rebuild, it repeats an isolated Challenger call without adding
new Challenger-owned input. It also creates a false failure path: the redundant
call can fail twice and stop the workflow as `COVERAGE_GATE_UNSUPPORTED` even
though the existing independent PASS receipt remains valid.

### Accepted Wording

Replace the opening of the Challenger-invocation paragraph with this contract:

> After `build` succeeds, invoke one Coverage Challenger unless the rebuilt
> envelope's `challenge_fp` is unchanged and an existing receipt with
> `effective_result: PASS` for that exact fingerprint is submitted to and passes
> the current local `coverage_gate.py approve` path's validation of current
> canonical sources and the complete receipt chain; any failure remains
> fail-closed. When invoked, instruct the Challenger to inspect every
> validator-extracted Ticket AC and Verification root against its raw text,
> preserve every materially distinct observable predicate and explicit
> trigger/result branch unless the same execution genuinely observes each
> distinction, and check Units, qualifier bindings, and Coverage Edges against
> the raw canonical slices.

The remainder of the existing paragraph stays unchanged.

### Why This Is Safe

- `coverage_gate.py::_fingerprints` includes the canonical package, Unit
  semantics, qualifier bindings, Coverage Edges, and referenced Scenario
  procedure semantics in `challenge_fp`.
- `coverage_gate.py::approve` calls `_validate_envelope` with current-source
  validation enabled.
- `_validate_receipt` checks the exact fingerprint, attestation digest, embedded
  attestation fingerprint, and complete receipt chain.
- `approve` derives a new approval ID from the rebuilt envelope's current
  `plan_fp` and the validated attestation digest.
- The omitted Challenger would receive the same semantic input already covered
  by the independent receipt.
- Receipt reuse does not promote Lead judgment, Implementation evidence, or
  Runtime Runner material into Challenger authority.

### Rejected Looser Wording

The phrase `current validated receipt` was rejected because it does not specify
the validator, current envelope, canonical-source reread, full receipt-chain
replay, or current invocation. It could allow a prior command result or prose
judgment to be treated as validation.

### Cost Removed

Each qualifying plan-only rebuild avoids one fresh isolated Coverage Challenger
invocation and its new-attestation validation call. The retry rule can otherwise
repeat the unnecessary Challenger attempt once. The repository contains no
reliable model-token, latency, or monetary telemetry, so no stronger performance
claim is made.

### Rollback Triggers

- Reuse occurs without the current local `approve` path.
- A stale or tampered receipt chain passes.
- Challenger-visible semantic input changes without changing `challenge_fp`.
- A changed `plan_fp` retains the old approval ID.
- `approve` ceases to validate current canonical sources or the complete receipt
  chain.

## Accepted Change 2: Single Approval Request

### Conflict

The current contract says both:

> Ask the user to approve that exact plan.

> Ask the user to explicitly approve the disclosed scenario plan.

The surrounding contract has one gate-derived `TOTAL` or `PARTIAL` plan, one
approval ID, one `plan_fp`, and one authority grant. There is no second approval
object or distinct authority boundary.

### Accepted Wording

Replace both commands with:

> Ask the user to explicitly approve that exact plan.

This retains explicit approval of the whole plan while removing one duplicate
imperative and nine words.

### Rejected Alternative

`Ask the user once to explicitly approve that exact disclosed scenario plan.`
was rejected for two reasons:

- `scenario plan` can narrow a `PARTIAL` plan by excluding blocked coverage,
  evidence-bound classification, bounded decision value, unavailable results,
  or preparation scope;
- `once` can be misread as forbidding a renewed request after an ambiguous
  response, replacement disclosure, changed `plan_fp`, or material revision.

### Preserved Scope

- the complete `TOTAL` or `PARTIAL` plan;
- disclosed Scenario revisions;
- blocked coverage and partial-plan value;
- preparation scope;
- the displayed approval ID and exact `plan_fp`; and
- renewed disclosure and approval after a material change.

### Rollback Triggers

- One approval ID causes two approval requests.
- Approval is narrowed to executable scenarios only.
- Preparation or partial-plan scope is omitted.
- Approval remains valid after `plan_fp` changes.

## Excluded From S

| Candidate | S disposition | Reason |
| --- | --- | --- |
| Remove the nominated implementation-route index | Deferred | It is non-authoritative, but its net discovery cost or benefit is unmeasured. |
| Reuse Implementation gross handoff-liveness as Verification readiness or direct AC evidence | Rejected | This changes evidence ownership, approval timing, and freshness. |
| Collapse producer/consumer or raw-material/authority reinspection | Rejected | The repeated inspection enforces distinct fact-adoption or attestation authority. |
| Cache canonical-source, path, or dependency validation across gates | Rejected | This changes freshness and time-of-check/time-of-use behavior. |
| Compress duplicated `to-spec` truth/authority wording | Deferred | Literal overlap exists, but model-behavior and salience equivalence are unproved. |
| Factor Acceptance Criteria and Verification list grammar | Deferred | Text similarity is shown; generated-output conformance equivalence is not. |
| Remove leaf Grill/Behavior/UI wording in favor of transitive loading | Deferred | Mandatory co-loading and direct-invocation equivalence are not demonstrated. |
| Other verbosity-only compression | Excluded | No other candidate met the S-tier proof threshold. |

These dispositions are S-tier boundaries only. They do not pre-judge A or B.

## Implementation Boundary

This review authorizes only the decision record. If the two wording corrections
are implemented later:

- no `coverage_gate.py` API or behavior change is warranted for receipt reuse;
- existing approval contract-test anchors must be updated to the single accepted
  sentence; and
- a focused existing-test change may verify unchanged `challenge_fp`, changed
  `plan_fp`, receipt reuse, current-source rejection, receipt-chain tampering,
  semantic-fingerprint invalidation, and new approval-ID derivation.

Those implementation and test changes were not performed in this tier review.

## Evidence And Sessions

- Initial adversarial review: `slots-context-iistiers-556b3a0153`
- Final S consensus capture: `slots-context-iistiers-d26c0ca720`
- ChatGPT conversation: `https://chatgpt.com/c/6a788f84-dfb4-83ee-903b-6a29798d09d4`
- Managed browser: slot 1, local CDP `127.0.0.1:19222`
- Reasoning selection: Pro, verified by the browser control
- Model selection: current selected model requested as GPT-5.6 Sol; exact active
  model label was not independently verified by Oracle metadata
- Final attachment: one generated ZIP containing 147 files and 1,106,774
  uncompressed bytes; Oracle reported ZIP SHA-256
  `659005303d07a42d0b12fc25c3054da47a645e445b188420f55e35ca3bfef1cc`

## Consensus Status

No material S-tier disagreement remains. Reopening S requires new evidence that
the `approve` validation path, `challenge_fp` boundary, or singular approval
object has changed.
