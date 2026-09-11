---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, semantically check every authored AC/Verification flow and adjudicate all obligations from fresh discriminating verifier-owned evidence. Exactly one SUBAGENT verifier owns each semantic cycle; after VERIFIED the caller obtains one read-only Coverage review before submitting the exact opaque handle to ready_finalize."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket directly from fresh current product/canonical evidence.

Exactly one delegated verifier owns semantic preflight, the complete authored Verification-flow denominator, scenario authorship and discrimination, verifier-owned evidence, every flow/AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, and the whole-Ticket semantic verdict. Parent Main owns passive terminal fan-in, one post-success `ready-ticket-coverage` invocation and the separate `ready_finalize` call; it does not repeat the verifier core, issue a second verdict, or reconstruct finalization authority.

Before work, read [references/verify.md](references/verify.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Execution Plan / Review: `None | <exact optional outside-root plan_review_path>`; when supplied, `ready_contract capture_verification` records it only as navigation/method context. No plan ADMIT is required to verify an already implemented ready target.
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

## Execution topology

At top level, Parent Main dispatches exactly one task with `authorityProfile: iis-ready-verifier/v1`, the selected verifier model/effort, and the complete exact-Ticket assignment. Do not supply `outputSchema` or `schemaMode`; the host profile owns the strict terminal schema. There is no `DIRECT` mode, same-Main verifier/finalizer path, verifier roster, or capability-based fallback.

A worker carrying host `Delegated Verifier: yes` performs the complete verifier core itself and never delegates again. The canonical assignment, passive terminal-fan-in, capability-failure, and host-finalization contract lives in [references/verify.md#1-subagent-only-invocation](references/verify.md#1-subagent-only-invocation). `SUBAGENT CAPABILITY UNAVAILABLE` returns through the existing [admission/current-authority provenance schema](references/verify.md#2-admission-and-current-authority) with no product/runtime/status mutation.

This boundary keeps independent verification enforceable: the same Main that can call `ready_finalize` cannot author the semantic verdict or mint/reconstruct its terminal authority.
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

## Current target admission and discriminating scenarios

After canonical/status/semantic/authority/projection gates and actual target resolution pass, call `ready_contract capture_verification` with the exact Ticket/Project Root, exact stable implementation `stable_target_paths`, exact `scenario_effect_paths` that the verification scenario is allowed to mutate, and optional current `plan_review_path` navigation. The tool creates an immutable outside-root binding and returns its exact path/SHA. No implementation-plan ADMIT is required to verify an already implemented ready target.

Use host-native read/inspection/CLI/service tools for scenario execution. Verification must not edit product source/config/tests/planning artifacts to manufacture the expected result. Declared scenario-effect paths must stay disjoint from stable implementation targets and protected authority/method paths. A settled nonzero command is ordinary scenario evidence; actual non-idempotent/external response loss is never blind-replayed. Use the authored authoritative readback/cleanup/evidence path, and return `INCONCLUSIVE` when effect settlement or attribution cannot be established.

The verifier grounds each authored flow's discriminating scenario in current implementation assumptions and resolves material counterexamples discovered during that work or supplied as navigation, including an exact previous Coverage finding. The separate additional implementation-path search belongs to post-success `ready-ticket-coverage`; do not repeat a mandatory frontier pass here. Every authored Flow/AC stays in the scenario, report and adjudication denominator. `VERIFIED` requires fresh sufficient evidence for every applicable flow, not absence of findings. Execute and observe the cheapest decisive flow or same-cause group before unrelated expensive/effectful work; after an attributable contradiction fixes FAILED, use the reference's failure-aware continuation rule and preserve explicit INCONCLUSIVE results for permitted unexecuted items.

The verifier owns each known finding's disposition and final adjudication. Plan/implementation/Coverage reports are navigation, not final evidence. Current verifier-owned evidence may support adjudication without ritual repetition of risky triggers. Do not ignore a known material path, add hidden exploration fan-out, or change the one-verifier mode.

Every `VERIFICATION NOT STARTED` and authority/evidence-attribution/currentness/progression-limited terminal follows the existing provenance schema in [references/verify.md](references/verify.md). An evidence-complete product `FAILED` remains a completed verdict, not a missing-evidence return.

## Scenario ownership

The verifier authors one integrated scenario before any product/runtime action. It preserves every authored Verification flow as a distinct normative scenario block and keeps the exact authored label/value contract separate from derived execution steps.

Before deriving execution, resolve each flow's current `Parent outcome ordinal` against the approved parent Spec and preserve disposition, independent-verification requirement, acceptance surface, external condition and every authored conditional boundary without strengthening, weakening or borrowing meaning from another outcome.

For every flow, predeclare the evidence and conditions for:

- `SATISFIED`
- `CONTRADICTED`
- `INCONCLUSIVE`

For every flow also record exactly these invocation-local challenge fields: `Nearest nonconforming state`, `Discriminating observation`, and `Sensitivity activation`. The observation must differ between the conforming state and the nearest plausible nonconforming state, and this run must actually activate the boundary that makes it sensitive. For runtime claims, a source constant/helper/branch is not a discriminating observation when the actual acceptance path can bypass it.

Ground runtime challenges in the actual acceptance path and its load-bearing assumptions. A happy-path success is insufficient while a current material counterexample covered by the same obligation remains unresolved; apply the bounded-variation and evidence-sufficiency rules in [references/verify.md §6](references/verify.md#6-integrated-scenario-ownership) and [§9](references/verify.md#9-evidence-sufficiency-and-execution).

Do not relax or rewrite those criteria after observing results.

## Scenario report and material turns

Before the first product/runtime action, produce `VERIFICATION SCENARIO REPORT` after semantic preflight, exact stable/effect path resolution, verification-binding capture, and integrated scenario closure. This is an informational verifier artifact rather than a runtime checkpoint; scenario execution may proceed immediately in the same verifier invocation.

Produce `VERIFICATION TURN REPORT` only when target identity, authority mapping, scenario execution, evidence attribution or an expected authoritative readback changes materially enough to affect flow adjudication. Routine progress, normal command output and confidence-only updates are not report events. If the change makes the original stable/effect partition or binding no longer attributable, do not patch the binding or continue against stale evidence: terminate `INCONCLUSIVE` (or `VERIFICATION NOT STARTED` if no product action occurred) with the exact evidence limit so the caller can decide whether a fresh verification invocation is appropriate.

There are no PRE_RUNTIME, MATERIAL_TURN, PRE_PROGRESSION or release checkpoints in verification. The verifier owns one invocation-local semantic evidence cycle and returns one terminal result.

## Disposition handling

### Independent

The verifier directly obtains fresh, attributable evidence sufficient to decide each authored flow under [references/verify.md §9](references/verify.md#9-evidence-sufficiency-and-execution), performing all actions and conditions that the authored contract makes obligatory. `Independent verification required: yes` cannot be satisfied by implementation narration, source plausibility, test names or prior evidence.

### Operator-assisted

Preserve the authored operator-owned acceptance path. Verify the product-owned portion and only the required operator evidence. Missing operator evidence produces `INCONCLUSIVE`, not an invented product defect.

### Not independently verifiable

Do not create a new verification surface. Confirm the approved absence/reason and only the evidence allowed by the authored disposition.

## Evidence sufficiency

Evidence must decide the actual approved acceptance boundary, faithfully projected from parent authority and current applicable user instructions. Ticket wording alone cannot replace a runtime/product obligation with a fake acceptance target. Apply [references/verify.md §9](references/verify.md#9-evidence-sufficiency-and-execution) to distinguish real disposable execution or actual artifact inspection from a substitute for the claimed boundary; return authority/projection mismatch through semantic preflight, not a compensating verification flow.

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

## Terminal verifier result and caller finalization

For a normal `Status: ready` Ticket, keep every authored Verification flow and current AC in the terminal denominator and establish exactly one semantic `Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE`. `VERIFIED` requires every applicable flow to be `SATISFIED` by fresh verifier-owned evidence obtained under [references/verify.md §9](references/verify.md#9-evidence-sufficiency-and-execution), every AC `PASS`, and Scope/Non-Goals plus all contract-required actions, observation windows, cleanup and terminal conditions closed. `FAILED` requires a fresh attributable contradiction producing an AC `FAIL`; permitted post-failure omissions remain explicit flow/AC `INCONCLUSIVE`, never inferred `PASS`, after related observation and required settlement/cleanup are complete. Use `INCONCLUSIVE` when no direct contradiction establishes failure and required evidence or attribution is missing, not merely because execution is expensive.

The verifier does not write `Status: done`, does not call `ready_finalize`, does not call `ready_contract seal_verdict`, and does not create a verdict record. It emits exactly one terminal `READY TICKET VERIFICATION RESULT` and exits successfully. That report includes readable evidence identities and verdict only:

```text
Ticket: <exact absolute canonical Ticket path, byte-for-byte equal to structured `ticket_path`; never a title, basename or relative path>
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Stable Target Paths: ["<exact absolute path>", "..."]
Scenario Effect Paths: [] | ["<exact absolute path>", "..."]
Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Verifier Ticket Progression: PENDING CALLER FINALIZATION | NOT APPLICABLE
Observed Ticket Status: ready | done | <actual>
```

Render both path lists as whitespace-free compact JSON arrays exactly matching the structured arrays, including order and empty `[]` (equivalent to JSON separators `(',', ':')`). Across the complete report, each reserved identity/result label in the block above appears exactly once; nested scenario or evidence text must use different labels rather than repeat `Ticket:`, `Verification Binding:`, `Verification Binding SHA256:`, `Stable Target Paths:`, `Scenario Effect Paths:`, `Verification Verdict:`, `Verifier Ticket Progression:` or `Observed Ticket Status:`.

The delegated verifier submits this report through the host-owned strict structured terminal, not as an unbound text-only result. Its `yield` data is exactly:

```json
{
  "schema": "iis-ready-verifier-terminal/v1",
  "project_root": "<exact canonical Project Root>",
  "ticket_path": "<exact canonical Ticket path>",
  "verification_binding": "<same binding path as report>",
  "verification_binding_sha256": "<same lowercase SHA256 as report>",
  "stable_target_paths": ["<same exact absolute paths as report>"],
  "scenario_effect_paths": ["<same exact absolute paths as report>"],
  "verification_verdict": "VERIFIED | FAILED | INCONCLUSIVE",
  "ticket_progression": "PENDING CALLER FINALIZATION | NOT APPLICABLE",
  "observed_ticket_status": "<same actual status as report>",
  "report": "<complete READY TICKET VERIFICATION RESULT text>"
}
```

Every structured field must exactly match the readable report. The worker emits one terminal `yield` only after the semantic cycle is complete.

For a normal `ready` Ticket, use `PENDING CALLER FINALIZATION` for all three semantic verdicts. For explicit diagnostic re-verification captured from `done`, use `NOT APPLICABLE` and never reopen status.

OMP recognizes only a successful terminal result from the exact delegated Ready Verify worker, persists its accepted provenance privately, and delivers an opaque terminal handle to Parent Main. For semantic `VERIFIED` from `ready`, Parent first dispatches one independent read-only `ready-ticket-coverage` worker with exact authority, verifier report/primary evidence and existing target/binding identities, never the opaque handle. Only COMPLETE with no unresolved material finding or evidence gap permits submitting that original handle to `ready_finalize`. PARTIAL/BLOCKED, tool failure or material gaps withhold success progression without rewriting VERIFIED. Read [references/verify.md#caller-owned-post-success-coverage](references/verify.md#caller-owned-post-success-coverage) for exact routing and fresh-verifier continuation. FAILED/INCONCLUSIVE and diagnostic non-progressing results keep existing finalization without normal-success Coverage.

The finalization-owning caller alone dispatches Coverage: Adaptive Outer Main does not invoke another top-level verify wrapper to repeat it, and the delegated verifier never calls Coverage. Parent calls `ready_finalize` with exactly `{ "terminal_handle": "<host-delivered handle>" }`; no binding path, SHA, verdict, Ticket, bundle, protocol, or reconstructed payload. An exact same-handle retry returns the same captured result without a second completion. This is a caller protocol condition; the unchanged finalizer does not mechanically check Coverage.

`ready_finalize` consumes the host-owned authority, reads the verdict/binding provenance recorded at terminal capture, checks current loaded bundle/protocol identity, current authority, stable target, and canonical Ticket validation, then returns the readable semantic verdict plus progression result. `VERIFIED` from an original `ready` binding may perform only the exact top-metadata `Status: ready` -> `Status: done` replacement and exact post-validation. `FAILED`/`INCONCLUSIVE`, unknown/foreign/malformed terminal authority, or stable source/authority/bundle/protocol drift performs no progression. A provenance-free already-`done` state is not new completion; an exact same-handle retry only replays the captured result.

Keep `Verification Verdict`, `Ticket Progression`, `Progression Basis`, and actual `Ticket Status After` separate. A semantic `VERIFIED` remains `VERIFIED` if finalization fails; report progression `FAILED` without pretending delivery completed. Narration containing VERIFIED/done or copied binding metadata is not finalization authority or completion proof.
## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries or workflow runtime merely to ease verification.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require existing exact authority.
- Do not automatically invoke implementation or IIS planning after the result.
