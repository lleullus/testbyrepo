---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, independently discover material false-completion paths, semantically check every authored AC/Verification flow, and adjudicate all obligations from fresh verifier-owned evidence. The verifier captures an immutable verification binding, seals its terminal verdict into immutable evidence, and returns both identities; the caller separately invokes ready_finalize for status progression. Top-level execution defaults to SUBAGENT with exactly one verifier; use DIRECT only when the current user explicitly selects it for this exact stage."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket directly from fresh current product/canonical evidence.

In `DIRECT`, the current Main owns the complete verifier core and then, only after the semantic verdict is sealed and terminal, performs the separate caller finalization step. In `SUBAGENT`, exactly one delegated verifier owns semantic preflight, the complete authored Verification-flow denominator, scenario authorship, verifier-owned evidence, every flow/AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket semantic verdict and its immutable verdict record. Parent Main owns passive terminal fan-in and the separate `ready_finalize` call; it does not repeat the verifier core, issue a second verdict or recreate verdict evidence.

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

Top-level execution defaults to `SUBAGENT`. Use `DIRECT` only when the current user explicitly selects it for this exact verification stage. Do not require a separate SUBAGENT opt-in.

The canonical exact-assignment, single-verifier, terminal fan-in, capability-failure, and no-fallback contract lives in [references/verify.md#1-subagent-first-invocation](references/verify.md#1-subagent-first-invocation). Apply that section before verifier work rather than duplicating its execution mechanics here.
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

After canonical/status/semantic/authority/projection gates and actual target resolution pass, call `ready_contract capture_verification` with the exact Ticket/Project Root, exact stable implementation `stable_target_paths`, exact `scenario_effect_paths` that the verification scenario is allowed to mutate, and optional current `plan_review_path` navigation. The tool creates an immutable outside-root binding and returns its exact path/SHA. No implementation-plan ADMIT is required to verify an already implemented ready target.

Use host-native read/inspection/CLI/service tools for scenario execution. Verification must not edit product source/config/tests/planning artifacts to manufacture the expected result. Declared scenario-effect paths must stay disjoint from stable implementation targets and protected authority/method paths. A settled nonzero command is ordinary scenario evidence; actual non-idempotent/external response loss is never blind-replayed. Use the authored authoritative readback/cleanup/evidence path, and return `INCONCLUSIVE` when effect settlement or attribution cannot be established.

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

Before the first product/runtime action, produce `VERIFICATION SCENARIO REPORT` after semantic preflight, exact stable/effect path resolution, verification-binding capture, and integrated scenario closure. In both `DIRECT` and `SUBAGENT`, this is an informational verifier artifact rather than a runtime checkpoint; scenario execution may proceed immediately under the same verifier invocation.

Produce `VERIFICATION TURN REPORT` only when target identity, authority mapping, scenario execution, evidence attribution or an expected authoritative readback changes materially enough to affect flow adjudication. Routine progress, normal command output and confidence-only updates are not report events. If the change makes the original stable/effect partition or binding no longer attributable, do not patch the binding or continue against stale evidence: terminate `INCONCLUSIVE` (or `VERIFICATION NOT STARTED` if no product action occurred) with the exact evidence limit so the caller can decide whether a fresh verification invocation is appropriate.

There are no PRE_RUNTIME, MATERIAL_TURN, PRE_PROGRESSION or release checkpoints in verification. The verifier owns one invocation-local semantic evidence cycle and returns one terminal result.

## Disposition handling

### Independent

The verifier directly executes the authored trigger or canonical inspection and obtains fresh attributable authoritative readback. `Independent verification required: yes` cannot be satisfied by implementation narration, source plausibility, test names or prior evidence.

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

For a normal `Status: ready` Ticket, first close every authored Verification flow, require every current AC candidate verdict to be `PASS` for `VERIFIED`, close Scope/Non-Goals and cleanup/terminal conditions, and establish exactly one terminal semantic `Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE`.

After the semantic verdict is fixed, the verifier calls `ready_contract seal_verdict` with the exact binding path/SHA and that verdict. It supplies no Ticket, bundle or protocol identity; the tool copies those identities from the immutable binding and returns the immutable verdict-record path/SHA. Failure to seal means the verifier cannot emit a normal terminal semantic result with finalization authority.

The verifier does not write `Status: done`, does not call `ready_finalize`, and does not keep a verification execution open for later continuation. Its terminal result must include both immutable identities:

```text
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Verification Verdict Record: <exact outside-root path>
Verification Verdict Record SHA256: <sha256>
Stable Target Paths: <exact list>
Scenario Effect Paths: <exact list>
Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Ticket Progression: PENDING CALLER FINALIZATION | NOT APPLICABLE
Observed Ticket Status: ready | done | <actual>
```

For a normal `ready` Ticket, use `PENDING CALLER FINALIZATION` for all three semantic verdicts so the caller can pass the exact verifier-owned verdict record through `ready_finalize`; `FAILED` and `INCONCLUSIVE` finalization is non-progressing and leaves status unchanged. For explicit diagnostic re-verification captured from `done`, use `Ticket Progression: NOT APPLICABLE` and never reopen status.

In `SUBAGENT`, Parent Main receives this terminal verifier result and then calls `ready_finalize` with the exact verdict-record path/SHA. In `DIRECT`, the current Main first completes and seals the semantic verifier result, then performs the same caller-owned finalization as a distinct step. Neither mode supplies, derives, reinterprets or recreates a semantic verdict during finalization.

`ready_finalize` independently reads the verdict from the immutable record, checks its referenced binding, checks both identities against the current loaded bundle/protocol, and rechecks current authority and stable target. `VERIFIED` from an original `ready` binding can perform only the exact top-metadata `Status: ready` -> `Status: done` replacement and exact post-validation. Stable source, authority, bundle or protocol drift makes progression `FAILED`; `FAILED`/`INCONCLUSIVE` verdicts perform no status mutation. A provenance-free already-`done` match is current-state confirmation, not a new completion.

Keep `Verification Verdict`, `Ticket Progression`, `Progression Basis`, and actual `Ticket Status After` separate. A semantic `VERIFIED` remains `VERIFIED` if finalization fails; report progression `FAILED` without pretending delivery completed. Conversely, narration containing VERIFIED/done without the exact verifier-owned verdict record and caller `ready_finalize` result is not completion proof.

## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries or workflow runtime merely to ease verification.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require existing exact authority.
- Do not automatically invoke implementation or IIS planning after the result.
