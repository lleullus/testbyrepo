# Delivery Continuation Outside Adaptive Planning

## Ownership and default current-Increment route

Keep ownership separate even when the outer Adaptive execution continues:

1. **IIS Adaptive Planning ownership** ends at one approved Spec plus its validated complete Ready Ticket Set.
2. **Explicit Adaptive activation** authorizes the outer caller to continue that current Increment through the separate Ready Ticket implementation and verification skills by default.
3. A current instruction such as `planning only`, `stop after Ready Tickets`, `do not implement`, or `do not verify` overrides that default continuation.

The delivery calls are not actions performed **by** Adaptive Planning. `ready-ticket-implement` and `ready-ticket-verify` retain their own exact authority, admission, evidence, auditor, status, and terminal contracts. Adaptive activation never implies deployment, credentials, production/shared external mutation, destructive action, or another concrete authority not otherwise present.

## Delivery skill discovery and audit defaults

Before each delivery phase, discover and use the current installed skill contract.

- `ready-ticket-implement` owns one exact Ready Ticket implementation and implementer self-check.
- `ready-ticket-verify` owns one exact Ready Ticket fresh verification, final verdict, and guarded `ready -> done` progression.
- Do not infer Ticket-set parallelism, worker scheduling, or a persistent queue from the existence of a Ready Ticket Set. Select only a currently admissible Ticket using canonical blockers, product dependencies, shared-workspace safety, and current repository evidence.

Do not invent auditors merely because the outer route is autonomous. When the user supplied no audit request/count, let each current delivery skill apply its own normal default; under the current contracts this is `Auditor Count: 0` for implementation and `AC Runtime Auditor Count: 0` for verification. Preserve any exact user-supplied audit configuration.

## Invocation-local evidence economy

Pass this bounded instruction through each delivery skill's existing `Additional User Instructions` input:

> Subject to the exact Ticket contract and current explicit user instructions, collect only evidence that can change admission, an authored flow result, target attribution/freshness, required cleanup/terminal closure, or the next authority route. Once those obligations are decidable, stop confidence-only duplicate evidence collection and emit the owning terminal result.

This does **not** weaken authored Verification flows, independent-verification requirements, counterexamples, ordering/interruption/persistence/UI/external boundaries, or cleanup. It only prevents repeating the same claim across source/tests/browser or other modalities when the approved acceptance boundary/readback has already made the owning decision possible. Do not create evidence budgets, counters, modality quotas, extra report fields, or persistent evidence state.

## Implementation handoff

Continue from implementation to verification only when the current implementation report for the exact Ticket contains `Completion: COMPLETE` and the canonical Ticket remains exact `Status: ready` for the verifier. Preserve the exact implementation target/checkpoint and self-check evidence as navigation for verification; they do not become verification verdicts.

`Completion: BLOCKED | PARTIAL` or any unavailable/non-complete implementation result is not silently converted into verification. Correct only the condition owned by implementation/current authority, and repeat the implementation lifecycle only after a material candidate delta, changed canonical authority, or genuinely new evidence makes the new pass different.

## Verification terminal routing

Route from the verifier's exact result fields, not from an inferred summary:

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

## Corrective routing is the Adaptive default

Unless the current user explicitly requested `no re-entry`, `fail and report`, or equivalent, apply authority-based correction and re-enter the affected owner after a material correction/new evidence:

```text
IMPLEMENTATION_DEFECT
  -> ready-ticket-implement on the still-ready exact Ticket
  -> fresh ready-ticket-verify

VERIFICATION_MECHANISM_DEFECT
  -> correct only the verification-owned setup/mechanism
  -> fresh ready-ticket-verify

CONTRACT_OVERREACH
  -> re-enter IIS Adaptive Planning at the owning planning leaf
  -> To Tickets when only Ticket projection is wrong
  -> To Spec / Ask Matt when parent product meaning is wrong or incomplete
  -> fresh validated Ready Ticket(s)
  -> separate implementation/verification again

CURRENT_INCREMENT_MISMATCH
  -> re-enter Scope Shaper against fresh actual product state
  -> current canonical planning route
  -> fresh Ready Ticket Set
  -> separate implementation/verification again

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

If the same artifact/target, same evidence, same finding, and same route would repeat without such a change, stop at the owning boundary and report the unresolved condition. Do not add a numeric retry policy, persistent attempt ledger, or workflow state.

An explicit no-corrective-re-entry override stops cross-owner continuation after the current owner reports its terminal result/classification. It does not suppress normal local self-correction inside that owner before the terminal result.

## Success continuation is separate

Corrective re-entry above does not authorize another Increment. A current Increment is fully delivered only after every current canonical Ticket in its approved Ready Ticket Set has reached exact `done` through the owning verification lifecycle.

Then apply the active Mandate's Continuation Authority:

```text
CURRENT_INCREMENT
  -> stop success continuation

BOUNDED_OUTCOME | MANDATE_OUTCOME
  -> inspect fresh actual product state and authoritative readback
  -> MANDATE_SATISFIED | NEXT_INCREMENT_REQUIRED | USER_DECISION_REQUIRED
```

`CURRENT_INCREMENT` remains the default unless the user explicitly authorized a broader success boundary. A broader continuation never consumes a pre-authored Work Package/Increment list as a queue; `NEXT_INCREMENT_REQUIRED` returns to Scope Shaper against fresh actual state. Continuation Authority is planning-continuation authority and does not by itself expand concrete deployment/external-effect authority.

## Hard boundaries

- Adaptive Planning never becomes implementation or verification authority.
- Delivery skills never rewrite Scope, Spec, Ticket meaning to make verification pass.
- The outer caller never invents deployment, credential, production/shared external mutation, destructive-action, or other missing authority.
- A material user-owned product trade-off outside current authority returns to the user.
- `done` belongs only to the verifier's guarded terminal progression.
- This route is a thin handoff discipline, not a controller, scheduler, workflow database, approval engine, or generic Graph runtime.
