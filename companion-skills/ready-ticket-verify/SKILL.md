---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, require a current COMPLETE Ready Ticket heuristic-probe handoff for normal ready verification, semantically check that its authored AC/Verification flow can meaningfully decide the approved product claims, adjudicate every authored Verification flow and AC from fresh verifier-owned evidence, and own the guarded terminal done transition. Execution defaults to DIRECT; SUBAGENT verification is supported only when the current user explicitly selects it for this exact stage and uses mandatory checkpoint continuation."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket directly from fresh current product/canonical evidence.

In `DIRECT`, the current Main owns the complete verifier core. In explicit `SUBAGENT`, exactly one delegated verifier owns semantic preflight, the complete authored Verification-flow denominator, scenario authorship, verifier-owned evidence, every flow/AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket verdict and guarded `ready -> done` progression. Parent Main owns only bounded checkpoint continuation and terminal fan-in; it does not repeat the verifier core or issue a second verdict.

Before work, read [references/verify.md](references/verify.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Required for normal delivery verification of `Status: ready`:

- Heuristic Probe Result / Evidence: `<current READY TICKET HEURISTIC PROBE RESULT for this exact Ticket/authority/implementation target>`
- Probe Machine Binding: `<exact session-local binding path produced by ready_probe_binding for that terminal Probe>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

## Execution topology

Execution defaults to `DIRECT`. `SUBAGENT` is allowed only when the current user explicitly selects it for this exact verification stage.

The canonical exact-assignment, single-verifier, checkpoint continuation, capability-failure, and no-fallback contract lives in [references/verify.md#1-direct-first-invocation](references/verify.md#1-direct-first-invocation). Apply that section before verifier work rather than duplicating its execution mechanics here.
`SUBAGENT CAPABILITY UNAVAILABLE` returns through the existing [admission/current-authority provenance schema](references/verify.md#2-admission-and-current-authority).

This entry contract keeps the authority boundary explicit: one verifier owns the complete Ticket verdict cycle, while Parent Main never becomes a second verifier.

## Canonical admission gate

Before any product/runtime action, resolve the currently discovered `iis-workflow` skill only as the canonical planning-authority locator, follow its current `### To Tickets` route target and require the adjacent `validate_ticket.py`. Run that validator against the exact Ticket.

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

## Required heuristic probe gate

Normal delivery verification of a `ready` Ticket requires one terminal result from `ready-ticket-heuristic-probe` and its exact `Probe Machine Binding` path. The complete handoff order and outcome mapping live in [references/verify.md#5-verification-target-stability](references/verify.md#5-verification-target-stability).

An earlier `VERIFICATION NOT STARTED` remains correct when an independently established current canonical/status/permission, semantic, authority/projection, direct terminal Probe-result, or exact-target gate blocks admission. Missing result or binding still returns `VERIFICATION NOT STARTED: REQUIRED HEURISTIC PROBE RESULT MISSING`; a directly stated `PARTIAL` or `BLOCKED` terminal Probe result returns `VERIFICATION NOT STARTED: HEURISTIC PROBE GATE INCOMPLETE`. Do not manufacture an earlier machine-handoff diagnosis from a binding excerpt, prose, or a parent claim.

For normal `ready` verification once those gates pass, pass the unmodified `probe_binding_path`, exact Ticket/Project Root and exact `target_paths` to `ready_guard begin_verify` before asserting any machine-binding syntax, closure or currentness reason. `begin_verify` owns raw JSON parsing and machine identity/target admission; use its actual rejection to report `HEURISTIC PROBE GATE INCOMPLETE` or `HEURISTIC PROBE RESULT STALE`, without guessing punctuation or treating a claim as a rebind. Continue only when it returns `purpose: verify` with a bound verification-target digest. Use `ready_argv execute` for ordinary runtime commands that are not read-only shell inspection; do not use generic `write`/`edit`, `ready_argv mutate`, or project-local verifier tests during the verdict cycle. Any `TARGET_DRIFT` prohibits `VERIFIED`; already attributable contradictions may still support `FAILED`, otherwise close `INCONCLUSIVE`.

Every caller-facing `VERIFICATION NOT STARTED` result includes the non-continuation provenance fields defined in [references/verify.md](references/verify.md). If a final `INCONCLUSIVE` specifically results from an authority, evidence-attribution, target-currentness, or progression boundary that prevents authoritative completion, append the same provenance fields. An ordinary `FAILED` verdict based on verifier-owned contradictory product evidence is a completed verification verdict and does not require this explanation block.

Probe findings are navigation/counterexample seeds, not flow or AC verdicts and not automatic implementation defects. `Material Findings: None` is not PASS evidence. Where a finding is material and current, the verifier incorporates it into its own scenario and obtains verifier-owned current evidence. A probe result never satisfies `Independent verification required: yes` by itself.

Explicit diagnostic re-verification of an already `done` Ticket does not require this normal delivery gate unless the current user explicitly asks for a fresh heuristic probe as part of that diagnostic.

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

## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries or workflow runtime merely to ease verification.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require existing exact authority.
- Do not automatically invoke implementation or IIS planning after the result.
