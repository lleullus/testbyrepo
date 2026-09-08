---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, independently discover material false-completion paths, semantically check every authored AC/Verification flow, adjudicate all obligations from fresh verifier-owned evidence, and own guarded terminal done progression. Top-level execution defaults to SUBAGENT with exactly one checkpointed verifier; use DIRECT only when the current user explicitly selects it for this exact stage."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket directly from fresh current product/canonical evidence.

In `DIRECT`, the current Main owns the complete verifier core. In `SUBAGENT`, exactly one delegated verifier owns semantic preflight, the complete authored Verification-flow denominator, scenario authorship, verifier-owned evidence, every flow/AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket verdict and guarded `ready -> done` progression. Parent Main owns only bounded checkpoint continuation and terminal fan-in; it does not repeat the verifier core or issue a second verdict.

Before work, read [references/verify.md](references/verify.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Execution Plan / Review: `None | <exact optional outside-root plan_review_path>`; runtime derives checked method-context plans from this single input. No plan ADMIT is required to verify an already implemented ready target.
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

## Execution topology

Top-level execution defaults to `SUBAGENT`. Use `DIRECT` only when the current user explicitly selects it for this exact verification stage. Do not require a separate SUBAGENT opt-in.

The canonical exact-assignment, single-verifier, checkpoint continuation, capability-failure, and no-fallback contract lives in [references/verify.md#1-subagent-first-invocation](references/verify.md#1-subagent-first-invocation). Apply that section before verifier work rather than duplicating its execution mechanics here.
`SUBAGENT CAPABILITY UNAVAILABLE` returns through the existing [admission/current-authority provenance schema](references/verify.md#2-admission-and-current-authority).

This entry contract keeps the authority boundary explicit: one verifier owns the complete Ticket verdict cycle, while Parent Main never becomes a second verifier.

## Canonical admission gate

Before any product/runtime action, resolve the current canonical `validate_ticket.py` adjacent to To Tickets in the same pinned IIS bundle used by the runtime, and validate the exact Ticket. The discovered `iis-workflow` routes are planning navigation, not permission to mix validators from another release or a historical source path.

- Unavailable route/validator: `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`.
- Validator result other than exact `VALID`: `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`.
- Structural `VALID` admits schema only; the verifier must still perform semantic, authority, projection and current-target checks in `references/verify.md`.

Before deriving runtime execution, semantically compare every AC and mapped Verification flow against the approved parent/Behavior/UI meaning. Confirm that the authored observation/readback actually decides the material AC obligation rather than only a weaker proxy, and challenge concrete plausible false-positive or false-negative paths when they could change the verdict. If the authored verification contract has a material semantic gap, stop before runtime action and report the exact planning-contract defect without issuing AC verdicts. Do not repair, strengthen or normalize planning meaning inside verification.

## Ticket status gate

- Normal delivery verification input is exact `Status: ready`.
- `draft` or `blocked` does not enter verification and receives no AC verdicts.
- `done` permits only explicit diagnostic re-verification. Diagnostic re-verification never reopens or rewrites status.
- `FAILED` or `INCONCLUSIVE` leaves a normal `ready` Ticket at `ready`.
- A normal `ready` Ticket changes to `done` only after final `VERIFIED` on a stable target and the guarded progression succeeds.

## Current target admission and integrated discovery

After canonical/status/semantic/authority/projection gates and actual target resolution pass, call `ready_guard begin_verify` with exact Ticket/Project Root and `target_paths`. This directly binds current product authority and the actual target; no prior exploration result/binding or implementation-plan ADMIT is required. Preserve the actual admission outcome, not a guessed diagnosis. Continue only with `purpose: verify` and a bound target digest.

Use supported guarded inspection and structured `ready_argv execute` for runtime commands. Generic product source/config/test/planning mutation and `ready_argv mutate` are forbidden. Any declared output must stay outside Project Root and cannot cover protected authority/target/method files. Runtime drift and unknown effects are not resolved by a prose claim.

The final verifier derives a bounded frontier from original purpose, every authored flow/conditional boundary and current implementation, in addition to the mandatory scenario. Admit extra discovery only with a current contract anchor, reachable plausible false-completion/attribution path, material impact and decisive observable readback. Safely minimize triggers and preserve fresh attributable evidence. No distinct lane/no finding is not PASS; all authored Flow/AC and cleanup obligations still close independently. This method is self-contained and has no external Skill dependency.

The verifier owns each finding's disposition and final adjudication. Existing plan/implementation reports or permitted exploration assistance are navigation, not final evidence. Current Main in explicit DIRECT may verify, but cannot elevate its prior implementation self-check into final PASS. Same-cycle verifier-owned discovery evidence may serve adjudication without ritual repetition of risky triggers. Do not add hidden exploration fan-out or change the selected verification mode.

Every `VERIFICATION NOT STARTED` and authority/evidence-attribution/currentness/progression-limited terminal follows the existing provenance schema in [references/verify.md](references/verify.md). An evidence-complete product `FAILED` remains a completed verdict, not a missing-evidence return.

## Scenario ownership

The verifier authors one integrated scenario before any product/runtime action. It preserves every authored Verification flow as a distinct normative scenario block and keeps the exact authored label/value contract separate from derived execution steps.

Before deriving execution, resolve each flow's current `Parent outcome ordinal` against the approved parent Spec and preserve disposition, independent-verification requirement, acceptance surface, external condition and every authored conditional boundary without strengthening, weakening or borrowing meaning from another outcome.

For every flow, predeclare the evidence and conditions for:

- `SATISFIED`
- `CONTRADICTED`
- `INCONCLUSIVE`

For every flow also record exactly these invocation-local challenge fields: `Nearest nonconforming state`, `Discriminating observation`, and `Sensitivity activation`. The observation must differ between the conforming state and the nearest plausible nonconforming state, and this run must actually activate the boundary that makes it sensitive. For runtime claims, a source constant/helper/branch is not a discriminating observation when the actual acceptance path can bypass it.

Do not relax or rewrite those criteria after observing results.

## Scenario report and material turns

Before the first product/runtime action, produce `VERIFICATION SCENARIO REPORT` after semantic preflight and integrated scenario closure.

- `DIRECT`: the report remains informational with `Checkpoint: NOT_APPLICABLE`; continue under the existing direct verifier authority.
- `SUBAGENT`: return the report as `Checkpoint: PRE_RUNTIME`, `Protected next phase: FIRST_PRODUCT_OR_RUNTIME_ACTION`, `Checkpoint state: PARENT_CONTINUATION_REQUIRED`. Do not perform the protected product/runtime action before Parent `CONTINUE`.
- Public guard calls use `checkpoint` with `kind: PRE_RUNTIME | MATERIAL_TURN | PRE_PROGRESSION`, then exact owner/Parent `release_checkpoint`. Source mutation while PAUSED remains forbidden; parent continuation does not bypass currentness or effect uncertainty.

Produce `VERIFICATION TURN REPORT` only when target identity, authority mapping, scenario execution, evidence attribution or an expected authoritative readback changes materially enough to affect flow adjudication or safe terminal progression. Routine progress, normal command output and confidence-only updates are not report events. In `SUBAGENT`, a material turn is a `MATERIAL_TURN` checkpoint and work depending on the changed direction does not continue before Parent continuation.

Checkpoint continuation is a logical phase boundary, not a required live-wait primitive, direct-user approval gate or durable workflow state. Parent returns exactly one of `CONTINUE | STEER | STOP`. If bounded continuation cannot resolve required caller/operator/external authority, return the correct `VERIFICATION NOT STARTED`, `INCONCLUSIVE` or terminal progression result with exact evidence limits.

## Disposition handling

### Independent

The verifier directly executes the authored trigger or canonical inspection and obtains fresh attributable authoritative readback. `Independent verification required: yes` cannot be satisfied by implementation narration, source plausibility, test names or prior evidence.

### Operator-assisted

Preserve the authored operator-owned acceptance path. Verify the product-owned portion and only the required operator evidence. Missing operator evidence produces `INCONCLUSIVE`, not an invented product defect.

### Not independently verifiable

Do not create a new verification surface. Confirm the approved absence/reason and only the evidence allowed by the authored disposition.

## Evidence sufficiency

Runtime/acceptance-surface observation and authoritative readback are load-bearing when the Ticket defines them. Implementation reports, source shape, mocks, logs, tests or prior verification are navigation/support only unless the Ticket explicitly makes that exact target the acceptance boundary.

Match evidence to the actual claim:

- **Existence/state:** directly read the exact canonical or product target that decides the claim.
- **Absence/retirement:** define the bounded active-surface universe authorized by the contract and inspect the relevant entrypoints/config/package/runtime/storage surfaces; do not turn a narrow search into an unbounded repository-wide absence claim.
- **Preservation:** establish the current authoritative identity/readback and, when the verification trigger itself could mutate the deciding state, obtain the applicable pre/post evidence rather than inferring preservation from narration.
- **Semantic/qualitative result:** directly compare the source authority and produced result for the required meaning, grounding, causal connection, uncertainty or other authored quality boundary; keywords, test names and plausible source shape do not substitute.
- **Process/history claim:** require process/history evidence only when the approved acceptance contract makes it load-bearing; do not invent a ledger or retained evidence surface to make verification easier.

The source/config/build target must remain stable throughout the authoritative cycle. Unrelated target drift makes affected PASS evidence stale or unattributable and requires fresh applicable observation.

Exact declared method-context plan/review navigation changes only stale that navigation; they do not automatically invalidate product PASS. Actual product source/config/authority or runtime/readback drift still affects attribution. Undeclared new files remain conservatively product-target candidates, and a file required as a product deliverable stays product authority even if called a plan.

The verifier assigns exactly one result to every authored flow and one verdict to every current top-level AC in authored order.

```text
Flow result: SATISFIED | CONTRADICTED | INCONCLUSIVE
AC verdict: PASS | FAIL | INCONCLUSIVE
Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE
```

- Every AC `PASS` -> `VERIFIED`
- Any AC `FAIL` -> `FAILED`
- Otherwise -> `INCONCLUSIVE`

## Terminal `done` transition

For a normal `Status: ready` Ticket, first close every authored Verification flow, require every current AC candidate verdict to be `PASS`, close Scope/Non-Goals and cleanup/terminal conditions, and establish candidate `Whole Ticket: VERIFIED`.

In `SUBAGENT`, before final `VERIFIED` emission or any `ready -> done` mutation, the delegated verifier must return `VERIFICATION PRE-PROGRESSION CHECKPOINT` with `Checkpoint: PRE_PROGRESSION`, `Protected next phase: FINAL_VERIFIED_AND_GUARDED_READY_TO_DONE`, and `Checkpoint state: PARENT_CONTINUATION_REQUIRED`. Parent reviews only denominator/closure completeness, obvious contradiction, target/status drift and evidence-limit consistency; it does not rerun runtime flows or issue a second verdict. `FAILED` or `INCONCLUSIVE` candidates do not use this checkpoint.

After `CONTINUE` (`DIRECT` reaches this point without Parent checkpoint), the verifier may attempt `Status: done` only after:

1. every authored Verification flow has an attributable final result;
2. every current AC is `PASS`;
3. no unresolved material semantic-contract defect, evidence conflict, authority gate, target drift or cleanup/terminal-condition gap remains;
4. the verification target remains current and attributable;
5. the exact Ticket passes the same current canonical validator again as exact `VALID`;
6. current parent Spec / Behavior / UI authority and Ticket-to-parent projection checks still hold; and
7. the exact Ticket is still the same canonical `Status: ready` contract immediately before the write.

Do not perform that write through generic file tools. Call Ready runtime `ready_guard finalize_verification` with the exact execution and final verifier verdict. For `VERIFIED` on a normal `ready` Ticket, the runtime alone performs the single guarded top-metadata `Status: ready` -> `Status: done` replacement and immediate exact `VALID` post-write validation; for `FAILED`, `INCONCLUSIVE`, or diagnostic `done` re-verification it performs no status progression.

If Parent returns `STEER`, the delegated verifier reopens only the bounded flow/evidence/closure identified by the steering and resubmits `PRE_PROGRESSION` if the candidate remains `VERIFIED`. Parent may return `STOP` at `PRE_PROGRESSION` only when current authority, target currentness, current user instruction, evidence closure, or progression authority means candidate `VERIFIED` can no longer be finalized. In that case the delegated verifier, not Parent Main, emits the existing terminal `Verification Verdict: INCONCLUSIVE`, reports `Ticket Progression: NOT APPLICABLE`, leaves the Ticket at `Status: ready`, and performs no `done` mutation.

Keep `Verification Verdict` separate from `Ticket Progression`. A `VERIFIED` verdict remains the evidence verdict if the guarded write or post-write validation fails; report `Ticket Progression: FAILED` without pretending delivery progression completed.

Report actual status even if it is `done` while progression is FAILED. The finalizer conditionally restores only its exact status-only candidate under unchanged ownership/authority; external changes and unresolved intent/effects must not be overwritten or silently declared complete.

## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries or workflow runtime merely to ease verification.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require existing exact authority.
- Do not automatically invoke implementation or IIS planning after the result.
