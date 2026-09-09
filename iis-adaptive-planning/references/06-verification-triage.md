# Verification Failure Triage and Planning Re-entry

## Purpose

A failed or inconclusive Ready Ticket verification is evidence, not an automatic instruction to change product code until the test passes.

Adaptive must distinguish:

1. valid contract + wrong implementation;
2. valid contract + broken/incorrect verification mechanism;
3. Ticket/Verification projection that overreaches or distorts parent authority;
4. Parent Spec/current INC that is itself the wrong planning shape for the Mandate and actual product ordering;
5. evidence that is insufficient to decide any of the above.

Do not change the verifier's exact verdict. Add a separate Adaptive root-cause classification and route. Apply the transition discipline in `08-delivery-continuation.md`: under explicit Adaptive mode, a material correction is followed by fresh execution at the affected owner by default; an explicit no-corrective-re-entry/fail-and-report instruction changes that handoff to report-and-STOP. This is distinct from success continuation into another Increment.

Classification begins only from the exact terminal `ready-ticket-verify` semantic result, the exact caller `ready_finalize` result when finalization was applicable, and current authority/evidence. Scenario reports, material observations, candidate interpretations, or partial evidence are verifier-internal/nonterminal and cannot by themselves receive `IMPLEMENTATION_DEFECT`, `VERIFICATION_MECHANISM_DEFECT`, `CONTRACT_OVERREACH`, `CURRENT_INCREMENT_MISMATCH`, or `INCONCLUSIVE` Adaptive classification.

Preparation `REVISE | EVIDENCE_NEEDED` and `PLAN_REVIEW_REQUIRED | PLAN_REVIEW_STALE | PLAN_NOT_ADMITTED` are not final product verdicts or Adaptive defect enums. Preserve their actual owner result and return to the affected Planner/reviewer/evidence owner before implementation. Internal final-discovery no-finding/no-lane is likewise not PASS.

## Required authority/evidence

Before classifying, reopen enough current authority to compare the failing claim precisely:

- current user instruction, relevant actual Source Authority anchors, Adaptive Mandate, and active Run Contract Goal/required scope/Boundary/Predicate/Readback;
- current Scope revision and exact INC;
- Parent Spec;
- adopted Behavior/UI authority relevant to the claim;
- exact Ticket and authored Verification flow(s);
- exact fresh `ready-ticket-verify` semantic result/evidence, including verification binding and immutable verdict-record identities;
- exact `ready_finalize` progression result, including the consumed verdict-record identity, when caller finalization was applicable;
- current runtime/repository evidence needed to attribute the observed behavior.

Apply `09-run-contract.md`'s actual-boundary evidence rule. Implementation reports, test names, logs, and mocks are navigation/support; a substitute cannot prove the boundary it replaces. Direct inspection may close the actual approved artifact-only result, and real authorized disposable execution may close its observed boundary, but neither a Ticket-authored fake nor limited evidence can override the user's promised runtime/external result.

## Classification order

Use this order so difficulty is not mistaken for overreach.

### 1. Projection authority check

Ask whether the failing Ticket/Verification requirement is an exact valid projection of its mapped Parent Spec outcome and applicable Behavior/UI authority.

If **no**, classify `CONTRACT_OVERREACH` (or projection distortion) even if implementation could be changed to satisfy it.

Outer Main also applies the Goal/required-item coverage invariant to the active Run Contract. A weak outer Predicate or omitted source obligation returns to Outer Main for faithful contract recovery, not to implementation as an invented defect. If the gap is in Scope/parent/Ticket projection, return to that exact existing owner. A valid current Increment covering only part of a broader Goal is not itself a defect: preserve it and the outer continuation obligation.

### 2. Current-INC appropriateness check

If projection is internally valid, ask whether the Parent Spec/current INC still represents the right current durable product state under the active Mandate and actual product ordering.

If **no**, classify `CURRENT_INCREMENT_MISMATCH`.

This includes a contract that is coherent in isolation but bundles later maturity, assumes a missing earlier product foundation, or is no longer the correct current-to-next transition.

### 3. Verification mechanism check

If the contract is valid and correctly placed, ask whether the integrated verifier bound the actual current authority/target, performed its material frontier and all authored flows, and measured the approved acceptance boundary/readback under attributable conditions.

If not, classify `VERIFICATION_MECHANISM_DEFECT` when the mechanism is wrong, or `INCONCLUSIVE` when required evidence/capability is unavailable. A discovery finding is not a product contradiction until the verifier adjudicates it against current authority.

A caller finalization failure is not automatically a verification-mechanism defect and never rewrites the semantic verdict sealed by the verifier. For example, `Verification Verdict: VERIFIED` with `Ticket Progression: FAILED` because stable target, authority, loaded bundle or boundary protocol changed is a progression/currentness failure under the changed target/authority/boundary owner. Preserve VERIFIED and its exact verdict-record provenance, resolve the owning drift or validation condition, and require fresh verification when the correction makes prior evidence stale. `ALREADY_DONE_MATCHING_BINDING` is current-state confirmation, not new completion proof.

### 4. Runtime contradiction check

If contract and verification mechanism are valid and attributable, ask whether the product observation contradicts the required observable result.

If **yes**, classify `IMPLEMENTATION_DEFECT`.

### 5. Evidence sufficiency

If the available evidence cannot establish the above without guessing, classify `INCONCLUSIVE`.

## `IMPLEMENTATION_DEFECT`

Use when:

- Parent Spec/Behavior/UI authority is current and coherent;
- Ticket/flow faithfully projects that authority;
- verification mechanism is appropriate and attributable;
- fresh current product behavior contradicts the approved result.

Route:

```text
Primary owner: separate Ready Ticket implementation lifecycle
Planning re-entry: None
Contract change: None
Fresh verification after implementation correction: Required
```

Do not shrink the contract merely because the correct implementation is difficult.

An implementation-local repair stays with the worker under current ADMIT. Important cause/owner/interface/persistence/readback changes require affected Planner → Heuristic → independent review before dependent implementation. A new product promise returns to original planning authority, not method review.

## `VERIFICATION_MECHANISM_DEFECT`

Use when the product contract is valid but the integrated verification apparatus does not measure or attribute it correctly, for example:

- verifier binds the wrong implementation target/authority;
- authorized exploratory actions interfere through shared state and corrupt attribution;
- wrong fixture or initial state;
- harness invokes a different flow than the authored trigger;
- observation uses a private/internal state instead of the authoritative readback;
- evidence attribution is stale or from a drifting target;
- a test assumes a condition the approved flow does not require;
- cleanup/setup corrupts the scenario.

Route:

```text
Primary owner: separate verification lifecycle / harness owner
Product implementation change: Do not infer
Planning re-entry: None unless the failure exposes an actual product-observability contract defect
Fresh verification: Required
```

Do not add product APIs, debug hooks, persistence, ledgers or test-only behavior merely to satisfy an invalid verifier harness. Correct the mechanism and obtain fresh verifier-owned evidence, not a separate exploration gate.

## `CONTRACT_OVERREACH`

Use when a Ticket or authored Verification flow strengthens, weakens, or borrows meaning beyond its exact parent authority.

Examples:

- Parent outcome promises authoritative completion readback in the current product lifecycle; Ticket verification additionally requires restart-persistent recovery.
- Parent outcome requires at-most-once user-visible submission; Ticket flow silently upgrades it to exactly-once external effect across process death.
- Parent outcome is operator-assisted; Ticket marks it independently verifiable by inventing a product sandbox not authorized by the Spec.
- Ticket adds ordering/persistence/retention requirements copied from another outcome.
- Parent outcome requires a real runtime/external result, but the Ticket authors only a mock/helper success readback; return that projection gap rather than letting verification repair the flow and declare PASS.

Route:

```text
Primary owner: To Tickets when parent meaning is correct
Upstream owner: Ask Matt / To Spec when parent meaning itself was mistranscribed or unresolved
Verifier action: Do not delete assertions and declare PASS
Planning action: Correct the canonical contract through the owning planning leaf
Fresh validation: Required
Fresh verification: Required
```

A hard or expensive requirement is **not** overreach if the current Parent Spec/Behavior authority genuinely requires it.

If the overreaching capability is still valuable under the Mandate but not current scope, Scope Shaper may defer it to provisional future construction. If current intent does not support it, drop it instead of preserving speculative future work.

## `CURRENT_INCREMENT_MISMATCH`

Use when the Ticket faithfully reflects its Parent Spec but the Parent Spec/current INC is the wrong current planning unit under actual evidence and the Mandate.

Examples:

- the current outcome is not independently meaningful until a missing stable identity product capability exists;
- one INC combines a first usable foundation with mature recovery/scaling/automation guarantees not needed for that first durable state;
- delivered/current product state moved, making the old current-to-next transition stale;
- verification shows the declared acceptance boundary can exist only after an earlier separately acceptable product state.

Route:

```text
Primary owner: Scope Shaper
Secondary owner: Ask Matt for product/Behavior details inside the reshaped INC
Action: split | replace | shrink | foundation insertion | defer | drop as current authority supports
History: preserve old verifier result and prior canonical lineage
Fresh planning validation: Required
Fresh verification of any new/current Ticket: Required
```

Do not call every infeasible implementation an INC mismatch. The mismatch must be about product-capability ordering or the observable construction unit, not a preferred internal mechanism.

## `INCONCLUSIVE`

Use when current evidence cannot attribute success/failure, for example:

- required operator evidence is unavailable;
- external condition is temporarily unavailable;
- target drift makes evidence stale;
- authoritative readback cannot currently be obtained for a reason that does not establish product contradiction;
- it is unclear whether a `ready` Ticket has already been implementation-consumed and that fact materially affects history.

Route according to the evidence gap. Do not manufacture PASS or FAIL.

An `INCONCLUSIVE` result may later reveal a planning problem, but absence of evidence alone is not permission to rewrite the contract.

## Test-is-too-much decision rule

Never decide that verification is "too much" because it is slow, difficult, expensive to implement, or inconvenient.

Use this exact question:

> Does the disputed requirement have current product authority at this exact planning level?

- **Yes** -> implementation must satisfy it unless the user changes product authority.
- **No, Ticket/flow added it** -> `CONTRACT_OVERREACH`.
- **Yes in Parent Spec, but it is the wrong current INC under Mandate/current state** -> `CURRENT_INCREMENT_MISMATCH`.
- **Contract is valid; harness does not measure it correctly** -> `VERIFICATION_MECHANISM_DEFECT`.
- **Cannot establish which** -> `INCONCLUSIVE`.

## No retroactive PASS

When planning changes after a verification result:

1. preserve the old exact result/verdict;
2. record Adaptive classification and planning re-entry in trace;
3. modify/create planning authority only through the owning IIS leaf;
4. validate new artifacts;
5. require a fresh separate verification cycle against the new current target.

Never rewrite the old result as if the new contract had been what was tested.

## Triage trace

Record a concise material entry:

```text
Verification source: <exact Ticket/result>
Original verifier verdict: <exact current verdict>
Adaptive classification: IMPLEMENTATION_DEFECT | VERIFICATION_MECHANISM_DEFECT | CONTRACT_OVERREACH | CURRENT_INCREMENT_MISMATCH | INCONCLUSIVE
Authority comparison: <exact parent/flow relationship>
Primary evidence: <anchors>
Disposition: <owner/leaf>
Contract changed: yes | no
Fresh verification required: yes | pending evidence
```
