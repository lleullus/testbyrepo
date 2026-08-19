# Delivery Continuation Outside Adaptive Planning

## Ownership and closed Run Contract

Keep ownership separate even when the outer Adaptive execution continues:

1. **IIS Adaptive Planning ownership** ends at one approved Spec plus its validated complete Ready Ticket Set.
2. **Explicit Adaptive activation** defaults the outer caller to `Implementation: yes` and `Verification: yes`.
3. Current instructions override those fields independently: `planning only` or `stop after Ready Tickets` selects `no`/`no`; `do not verify` preserves implementation authority as `yes`/`no`; `do not implement` never invents implementation authority.
4. Before any planning or delivery mutation, the outer caller must carry one `CLOSED` Run Contract from [09-run-contract.md](09-run-contract.md). Planning ownership completion, one Ticket completion, and one Increment completion are not whole-run completion unless that contract's boundary says so.

The delivery calls are not actions performed **by** Adaptive Planning. `ready-ticket-implement` and `ready-ticket-verify` retain their own exact authority, admission, evidence, auditor, status, and terminal contracts. Adaptive activation never implies deployment, credentials, production/shared external mutation, destructive action, or another concrete authority not otherwise present.

## Run Contract handoff

Pass the following exact decision-critical Run Contract fields through the existing bounded `Additional User Instructions` input when they affect the Ticket or continuation decision:

- Goal Outcome;
- Required Named Items;
- Candidate Named Items;
- Required Item Policy;
- Implementation and Verification;
- Run Completion Boundary;
- Completion Predicate; and
- Authoritative Readback.

Do not turn the form into delivery authority. The exact Ticket remains the implementation and verification contract. Run Contract fields prevent the outer caller from dropping Required Named Items, treating Candidate Named Items as obligations, running a disabled delivery stage, or terminating at the wrong phase; they do not authorize a delivery owner to expand one Ticket.

A reshaped current Increment may create a new canonical Ready Ticket denominator. Re-read the current validated Set after planning correction rather than retaining a stale denominator.

## Delivery skill discovery and audit defaults

Before each enabled delivery phase, discover and use the current installed skill contract.

- `ready-ticket-implement` owns one exact Ready Ticket implementation and implementer self-check.
- `ready-ticket-verify` owns one exact Ready Ticket fresh verification, final verdict, and guarded `ready -> done` progression.
- Do not infer Ticket-set parallelism, worker scheduling, or a persistent queue from the existence of a Ready Ticket Set. Select only a currently admissible Ticket using canonical blockers, product dependencies, shared-workspace safety, and current repository evidence.

When no audit was requested and no count was supplied, let each current delivery skill apply its own normal default; under the current contracts this is `Auditor Count: 0` for implementation and `AC Runtime Auditor Count: 0` for verification. Preserve any exact user-supplied audit configuration.

Do not invoke a disabled stage merely to obtain stronger evidence. In particular, `Verification: no` means no `ready-ticket-verify` call and no `done` claim.

## Invocation-local evidence economy

Pass this bounded instruction through each enabled delivery skill's existing `Additional User Instructions` input:

> Subject to the exact Ticket contract, the closed Run Contract, and current explicit user instructions, collect only evidence that can change admission, an authored flow result, target attribution/freshness, required cleanup/terminal closure, or the next authority route. Once those obligations are decidable, stop confidence-only duplicate evidence collection and emit the owning terminal result.

This does **not** weaken authored Verification flows, independent-verification requirements, counterexamples, ordering/interruption/persistence/UI/external boundaries, cleanup, Required Named Items, or the active Run Completion Predicate. It only prevents repeating the same claim across source/tests/browser or other modalities when the approved acceptance boundary/readback has already made the owning decision possible. Do not create evidence budgets, counters, modality quotas, extra report fields, or persistent evidence state.

## Implementation handoff

Invoke implementation only when `Implementation: yes`.

Continue from implementation to verification only when all of the following hold:

- `Verification: yes`;
- the current implementation report for the exact Ticket contains `Completion: COMPLETE`; and
- the canonical Ticket remains exact `Status: ready` for the verifier.

Preserve the exact implementation target/checkpoint and self-check evidence as navigation for verification; they do not become verification verdicts.

`Completion: BLOCKED | PARTIAL` or any unavailable/non-complete implementation result is not silently converted into verification. Correct only the condition owned by implementation/current authority, and repeat the implementation lifecycle only after a material candidate delta, changed canonical authority, or genuinely new evidence makes the new pass different.

When `Verification: no`, retain the exact implementation result and canonical Ticket status. After every current canonical Ticket has one exact `Completion: COMPLETE` result, apply the active boundary:

```text
CURRENT_INCREMENT_IMPLEMENTED
  -> confirm the complete current Ticket denominator
  -> confirm every exact implementation result is COMPLETE
  -> confirm no verifier progression was claimed
  -> emit IIS ADAPTIVE RUN COMPLETE

any delivered/outcome boundary not already satisfied
  -> Run Contract inconsistency or user-authority gap
  -> do not run verification
  -> return the smallest boundary/verification decision
```

One complete implementation report is not the current-Increment implementation denominator.

## Verification terminal routing

Invoke verification only when `Verification: yes`. Route from the verifier's exact result fields, not from an inferred summary:

```text
Verification Verdict: VERIFIED
Ticket Progression: COMPLETED
Ticket status after verification: done
  -> Ticket terminal delivery complete

Verification Verdict: VERIFIED
Ticket Progression: FAILED
  -> do not claim done
  -> resolve the guarded progression/currentness failure under its owning authority

Verification Verdict: FAILED | INCONCLUSIVE
  -> classify with 06-verification-triage.md

No final Verification Verdict
  -> preserve the verifier's exact admission/capability/currentness result
  -> correct only its owning condition when current authority permits
  -> never invent an implementation/planning defect classification
```

Never reduce terminal completion to `VERIFIED -> done`; the canonical Ticket must actually be `done` after `Ticket Progression: COMPLETED`.

After one Ticket reaches `done`, re-read the complete current canonical Ticket denominator. Do not emit `CURRENT_INCREMENT_DELIVERED` until every current canonical Ticket in the validated complete Ready Ticket Set is exact `done`.

## Corrective routing is the Adaptive default

Unless the current user explicitly requested `no re-entry`, `fail and report`, or equivalent, apply authority-based correction and re-enter the affected enabled owner after a material correction/new evidence:

```text
IMPLEMENTATION_DEFECT
  -> if Implementation is yes: ready-ticket-implement on the still-ready exact Ticket
  -> if Verification is yes: fresh ready-ticket-verify
  -> if a required stage is disabled: return the exact authority gap

VERIFICATION_MECHANISM_DEFECT
  -> if Verification is yes: correct only the verification-owned setup/mechanism
  -> fresh ready-ticket-verify
  -> if Verification is no: do not invoke the verifier

CONTRACT_OVERREACH
  -> re-enter IIS Adaptive Planning at the owning planning leaf
  -> To Tickets when only Ticket projection is wrong
  -> To Spec / Ask Matt when parent product meaning is wrong or incomplete
  -> fresh validated Ready Ticket(s)
  -> repeat only the enabled delivery stages

CURRENT_INCREMENT_MISMATCH
  -> re-enter Scope Shaper against fresh actual product state
  -> current canonical planning route
  -> fresh Ready Ticket Set
  -> repeat only the enabled delivery stages

INCONCLUSIVE
  -> obtain only the missing evidence, operator condition, or attributable target owned by the current contract
  -> continue only when that new evidence makes a valid next route available
```

Do not retroactively turn an earlier verifier failure into PASS after planning changes. New planning authority requires fresh applicable delivery/verification evidence.

## Progress guard without retry machinery

Before repeating a planning or delivery owner, identify at least one material change:

- corrected planning/implementation candidate;
- changed canonical authority;
- newly attributable verification target/mechanism; or
- genuinely new evidence/external condition.

If the same artifact/target, same evidence, same finding, and same route would repeat without such a change, stop at the owning boundary and report the unresolved condition as whole-run incomplete. Do not add a numeric retry policy, persistent attempt ledger, or workflow state.

An explicit no-corrective-re-entry override stops cross-owner continuation after the current owner reports its terminal result/classification. It does not suppress normal local self-correction inside that owner before the terminal result, and it does not convert an unsatisfied Run Contract into success.

## Success continuation by Run Completion Boundary

Corrective re-entry above does not itself authorize another Increment. A current Increment is fully delivered only after every current canonical Ticket in its approved Ready Ticket Set has reached exact `done` through the owning verification lifecycle.

Apply the active Run Completion Boundary and current Mandate ceiling:

```text
READY_TICKET_SET
  -> should already have terminated at the planning ownership boundary
  -> Implementation and Verification must both be no

CURRENT_INCREMENT_IMPLEMENTED
  -> requires Implementation yes and Verification no
  -> after the complete implementation denominator is COMPLETE, Run Contract satisfied
  -> Tickets remain under verifier-owned status; do not claim done
  -> no success re-entry into another Increment

CURRENT_INCREMENT_DELIVERED
  -> requires Verification yes
  -> after the complete done denominator closes, Run Contract satisfied
  -> emit IIS ADAPTIVE RUN COMPLETE

NAMED_REQUIRED_ITEMS_DELIVERED
  -> requires non-empty Required Named Items and Verification yes
  -> inspect every Required Named Item
  -> confirm each applicable observable result and authoritative readback
  -> Candidate Named Items do not block completion
  -> if all are satisfied: Run Contract satisfied
  -> otherwise: inspect fresh actual product state and return to Scope Shaper for one new current Increment when the Mandate ceiling permits

BOUNDED_OUTCOME_SATISFIED
  -> inspect the exact bounded Completion Predicate in fresh actual product state
  -> MANDATE_SATISFIED | NEXT_INCREMENT_REQUIRED | USER_DECISION_REQUIRED

MANDATE_OUTCOME_SATISFIED
  -> inspect the Mandate Desired Product Outcome and authoritative readback in fresh actual product state
  -> MANDATE_SATISFIED | NEXT_INCREMENT_REQUIRED | USER_DECISION_REQUIRED
```

The Mandate's Continuation Authority is the ceiling for success continuation; the Run Completion Boundary is the actual terminal of this invocation. If the boundary would exceed the ceiling and the current instruction does not explicitly revise that authority, the Run Contract should never have closed. Return the exact authority gap rather than silently stopping early or expanding authority.

A broader continuation never consumes a pre-authored Work Package/Increment list as a queue. `NEXT_INCREMENT_REQUIRED` returns to Scope Shaper against fresh actual state. Scope Shaper may preserve, split, merge, reorder, replace, or discard the provisional horizon under its current rules.

For `NAMED_REQUIRED_ITEMS_DELIVERED`, an item is not complete merely because a Ticket title resembles it. Trace the item to delivered canonical authority and confirm its applicable product result. Required Named Items remain obligations across multiple Increments until satisfied or explicitly revised by the user. Candidate Named Items may be dropped without blocking completion when current authority supports that choice.

An implementation-only run cannot use verified success re-entry to span several Increments. If Required Named Items need another Increment while `Verification: no`, return the smallest verification/boundary decision rather than silently omitting an item or claiming delivery.

## Hard boundaries

- Adaptive Planning never becomes implementation or verification authority.
- Delivery skills never rewrite Scope, Spec, Ticket meaning to make verification pass.
- The outer caller never invents deployment, credential, production/shared external mutation, destructive-action, or other missing authority.
- A material user-owned product trade-off outside current authority returns to the user.
- `done` belongs only to the verifier's guarded terminal progression.
- `Verification: no` is never treated as permission to infer a verifier verdict.
- Candidate Named Items are not completion obligations; Required Named Items are not disposable.
- No phase, Ticket, or Increment may claim whole-run success before the active Completion Predicate is satisfied.
- This route is a thin handoff discipline, not a controller, scheduler, workflow database, approval engine, or generic Graph runtime.
