# Delivery Continuation After the IIS Planning Ownership Boundary

## Ownership and closed Run Contract

Keep ownership separate while the current explicit Adaptive invocation continues:

1. **IIS Planning ownership** ends at one approved Spec plus its validated complete Ready Ticket Set.
2. **Explicit Adaptive activation** defaults Outer Main to `Implementation: yes` and `Verification: yes`.
3. When current authority supplies no narrower stop override and no broader named-item or outcome terminal, the default current-Increment terminal is `CURRENT_INCREMENT_DELIVERED`, subject to the Run Contract Required-item coverage invariant and Mandate ceiling.
4. Current instructions override those fields independently: `planning only` or `stop after Ready Tickets` selects `no`/`no`; `do not verify` preserves implementation authority as `yes`/`no`; `do not implement` never invents implementation authority.
5. Before any planning or delivery mutation, Outer Main must carry one `CLOSED` Run Contract from [09-run-contract.md](09-run-contract.md). Planning ownership completion, one Ticket completion, and one Increment completion are not whole-run completion unless that contract's boundary says so.

Outer Main is the thin invocation-local handoff owner defined by the top-level skill. It carries the Run Contract, invokes each exact owner only when enabled, receives exact terminal results, and performs fresh completion assessment; it does not become a second planning, implementation, or verification authority.

The delivery calls are not actions performed **by** IIS Planning. `ready-ticket-implement` and `ready-ticket-verify` retain their own exact authority, admission, evidence, execution topology, status, and terminal contracts. Adaptive activation never implies deployment, credentials, production/shared external mutation, destructive action, or another concrete authority not otherwise present.

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

Do not turn the form into delivery authority. The exact Ticket remains the implementation and verification contract. Run Contract fields prevent Outer Main from dropping Required Named Items, treating Candidate Named Items as obligations, running a disabled delivery stage, or terminating at the wrong phase; they do not authorize a delivery owner to expand one Ticket.

A reshaped current Increment may create a new canonical Ready Ticket denominator. Re-read the current validated Set after planning correction rather than retaining a stale denominator.

## Delivery skill discovery and execution defaults

Before each enabled delivery phase, discover and use the current installed skill contract.

- `ready-ticket-implement` owns one exact Ready Ticket implementation and implementer self-check.
- `ready-ticket-heuristic-probe` owns one exact Ready Ticket's bounded heuristic exploration, Ticket-derived probe frontier, material findings/minimal triggers, target attribution and cleanup; it never owns verifier verdicts or `done`.
- `ready-ticket-verify` owns one exact Ready Ticket fresh verification, final verdict, and guarded `ready -> done` progression.
- Invoke each exact delivery skill once per current owner pass and follow its current execution-mode contract. Delivery defaults to `DIRECT`; Adaptive never chooses another topology from model capability, task difficulty, cost or worker availability and never falls back between topologies after a capability failure.
- `ready-ticket-implement` uses `SUBAGENT` only when the current user explicitly selects SUBAGENT for that implementation stage; otherwise current Main performs the implementation role directly. Explicit implementation SUBAGENT follows its mandatory PRE_ACTION/material-turn checkpoint contract.
- `ready-ticket-heuristic-probe` uses `SUBAGENT` only when the current user explicitly selects SUBAGENT for that probe stage; otherwise current Main performs the Heuristic Probe Lead/executor role directly. Any internal parallel lanes belong to that skill's own SUBAGENT contract.
- `ready-ticket-verify` defaults to `DIRECT`. It uses `SUBAGENT` only when the current user explicitly selects SUBAGENT for that exact verification stage; exactly one delegated verifier owns the whole verifier core and its mandatory scenario/material-turn/pre-progression checkpoint contract. Outer Main does not issue a second verifier verdict.
- Do not pass `Delegated Worker: yes`, `Delegated Probe Worker: yes`, or `Delegated Verifier: yes` from Adaptive. Those markers belong only to each delivery skill's own internal child assignment.
- Do not infer Ticket-set parallelism, worker scheduling, or a persistent queue from the existence of a Ready Ticket Set. Select only a currently admissible Ticket using canonical blockers, product dependencies, shared-workspace safety, and current repository evidence.

Do not invoke a disabled stage merely to obtain stronger evidence. `Verification: yes` includes the required current heuristic-probe gate followed by final verification; `Verification: no` means no `ready-ticket-heuristic-probe` call, no `ready-ticket-verify` call, and no `done` claim.

## Invocation-local delivery checkpoint continuation

A checkpoint from explicit implementation/verification `SUBAGENT` execution is a nonterminal invocation-local delivery message. Outer Main may release the protected next phase only after checking:

- exact Ticket, stage and target identity;
- the closed Run Contract and current user instructions;
- checkpoint denominator completeness;
- obvious authority/Scope contradiction;
- that the protected phase has not already been crossed; and
- continuation capability plus currentness.

Outer Main returns exactly:

```text
PARENT CONTINUATION DECISION

Ticket:
Stage: IMPLEMENTATION | VERIFICATION
Checkpoint: PRE_ACTION | PRE_RUNTIME | MATERIAL_TURN | PRE_PROGRESSION
Decision: CONTINUE | STEER | STOP
Authority / evidence anchor:
Bounded steering: None | <exact correction>
Reason:
```

`STEER` must identify the problematic checkpoint field, current authority/evidence anchor, why the protected phase cannot safely proceed unchanged, and the bounded correction. Vague preference-based steering is not sufficient.

Checkpoint review must not redesign the implementation diff from scratch, rerun all verifier flows, issue a Parent AC/whole-Ticket verdict, or convert a checkpoint into Adaptive defect classification. Do not forward a checkpoint as a user approval prompt. Do not create a checkpoint ledger or persistent state. A checkpoint is internal phase release under already established user authority, not the `/승인게이트` Run Contract release or any new Mandate/Scope/Spec/Ticket approval gate.

Adaptive delivery routing and verification triage wait for the exact terminal owner result. A checkpoint, candidate verdict, Parent steering decision, or partial observation is not a terminal implementation/verifier result.

## Invocation-local evidence economy

Pass this bounded instruction through each enabled delivery skill's existing `Additional User Instructions` input:

> Subject to the exact Ticket contract, the closed Run Contract, and current explicit user instructions, collect only evidence that can change admission, an authored flow result, target attribution/freshness, required cleanup/terminal closure, or the next authority route. Once those obligations are decidable, stop confidence-only duplicate evidence collection and emit the owning terminal result.

This does **not** weaken authored Verification flows, independent-verification requirements, counterexamples, ordering/interruption/persistence/UI/external boundaries, cleanup, Required Named Items, or the active Run Completion Predicate. It only prevents repeating the same claim across source/tests/browser or other modalities when the approved acceptance boundary/readback has already made the owning decision possible. Do not create evidence budgets, counters, modality quotas, extra report fields, or persistent evidence state.

## Implementation handoff

Invoke implementation only when `Implementation: yes`.

Continue from implementation to the heuristic-probe gate only when all of the following hold:

- `Verification: yes`;
- the current implementation report for the exact Ticket contains `Completion: COMPLETE`; and
- the canonical Ticket remains exact `Status: ready` for the next delivery owners.

Preserve the exact implementation target/checkpoint and self-check evidence as navigation for heuristic probing and verification; they do not become heuristic findings or verification verdicts.

`Completion: BLOCKED | PARTIAL` or any unavailable/non-complete implementation result is not silently converted into heuristic probing or verification. Correct only the condition owned by implementation/current authority, and repeat the implementation lifecycle only after a material candidate delta, changed canonical authority, or genuinely new evidence makes the new pass different.

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

## Heuristic probe gate handoff

When `Verification: yes`, every normal `Status: ready` Ticket must pass `ready-ticket-heuristic-probe` before `ready-ticket-verify`, whether the current invocation just implemented the Ticket or is verifying an already implemented current target.

Invoke the probe only after current canonical Ticket/authority and one stable attributable implementation target are established. When `Implementation: yes`, use the exact COMPLETE implementation target/checkpoint as navigation. When `Implementation: no`, bind the already implemented current target directly; do not infer that implementation history merely from a `ready` status.

Continue from heuristic probing to verification only when all of the following hold:

- the exact probe result is `READY TICKET HEURISTIC PROBE RESULT` for the same Ticket;
- `Probe Completion: COMPLETE`;
- the probe `Authority Snapshot` still matches current Ticket/Parent Spec/applicable Behavior/UI authority;
- the probe target is the same current target the verifier will bind;
- cleanup/terminal state is closed; and
- the canonical Ticket remains exact `Status: ready`.

A `COMPLETE` result with `Material Findings: None` is valid gate completion but is not PASS evidence. A `COMPLETE` result with material findings also proceeds to the verifier; Adaptive does not classify a finding as `IMPLEMENTATION_DEFECT`, planning defect, or Ticket failure before verifier adjudication. Preserve findings/minimal triggers as navigation/counterexample seeds for `ready-ticket-verify`.

`Probe Completion: PARTIAL | BLOCKED`, `HEURISTIC PROBE NOT STARTED`, unavailable SUBAGENT capability after an explicit SUBAGENT request, stale target/authority, or incomplete cleanup does not enter verification. Correct only the exact probe-owned capability/mechanism/evidence/currentness condition when current authority permits; do not silently run another topology or skip the gate.

Any material implementation or planning-authority change makes the prior probe result non-current for supportive delivery evidence and requires a fresh probe before fresh verification. A verifier-only mechanism correction may reuse the existing probe only after the verifier re-establishes that Ticket authority, probe target, cleanup and implementation target are still current.

## Verification terminal routing

Invoke verification only when `Verification: yes` and the current heuristic-probe gate above is `COMPLETE` for the same Ticket/authority/implementation target. Pass the exact current Probe Result as the verifier's required handoff. Route from the verifier's exact result fields, not from an inferred summary:

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
  -> any implementation correction changes the target -> if Verification is yes: fresh ready-ticket-heuristic-probe -> fresh ready-ticket-verify
  -> if a required stage is disabled: return the exact authority gap

VERIFICATION_MECHANISM_DEFECT
  -> identify whether the defect is in the heuristic-probe mechanism/currentness boundary or only in the final verifier mechanism
  -> probe mechanism/currentness defect: correct only that mechanism -> fresh ready-ticket-heuristic-probe -> fresh ready-ticket-verify
  -> verifier-only mechanism defect with unchanged Ticket/authority/implementation target and still-current COMPLETE probe: fresh ready-ticket-verify may reuse that current probe handoff
  -> if probe currentness cannot be established: fresh ready-ticket-heuristic-probe before fresh verification
  -> if Verification is no: do not invoke the probe or verifier

CONTRACT_OVERREACH
  -> re-enter IIS Adaptive Planning at the owning planning leaf
  -> To Tickets when only Ticket projection is wrong
  -> To Spec / Ask Matt when parent product meaning is wrong or incomplete
  -> fresh validated Ready Ticket(s)
  -> repeat only the enabled delivery stages; when Verification is yes, fresh probe precedes fresh verification

CURRENT_INCREMENT_MISMATCH
  -> re-enter Scope Shaper against fresh actual product state
  -> current canonical planning route
  -> fresh Ready Ticket Set
  -> repeat only the enabled delivery stages; when Verification is yes, fresh probe precedes fresh verification

INCONCLUSIVE
  -> obtain only the missing evidence, operator condition, attributable target, or probe/verifier mechanism state owned by the current contract
  -> if the gap invalidated or prevented the probe gate: fresh ready-ticket-heuristic-probe before verification
  -> continue only when that new evidence makes a valid next route available
```

Do not retroactively turn an earlier verifier failure into PASS after planning changes. New planning authority requires fresh applicable delivery evidence; when Verification is enabled, that includes a fresh current heuristic-probe gate before fresh verification.

## Progress guard without retry machinery

Before repeating a planning or delivery owner, identify at least one material change:

- corrected planning/implementation candidate;
- changed canonical authority;
- newly attributable heuristic-probe/verification target or mechanism; or
- genuinely new evidence/external condition.

If the same artifact/target, same evidence, same finding, and same route would repeat without such a change, stop at the owning boundary and report the unresolved condition as whole-run incomplete. Do not add a numeric retry policy, persistent attempt ledger, or workflow state.

An explicit no-corrective-re-entry override stops cross-owner continuation after the current owner reports its terminal result/classification. It does not suppress normal local self-correction inside that owner before the terminal result, and it does not convert an unsatisfied Run Contract into success.

## Completion assessment and success continuation by Run Completion Boundary

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
BOUNDED_OUTCOME_SATISFIED
MANDATE_OUTCOME_SATISFIED
  -> require fresh actual product state and attributable authoritative readback
  -> perform the completion assessment below
```

For any broader boundary, Outer Main chooses exactly one disposition from fresh actual product state:

- `RUN_CONTRACT_SATISFIED` — the active Required Named Items, bounded outcome, or Mandate outcome predicate is satisfied; emit `IIS ADAPTIVE RUN COMPLETE`.
- `NEXT_INCREMENT_REQUIRED` — the predicate is unsatisfied, current authority establishes that more product construction is required, and the Mandate ceiling permits it; return to Scope Shaper for exactly one new current Increment.
- `USER_DECISION_REQUIRED` — the predicate is unsatisfied but a material user-owned product choice remains after applying the Mandate and current authority; return only that decision.
- `EVIDENCE_REQUIRED` — current attributable evidence cannot determine satisfaction or the need for more construction; obtain only the missing authoritative readback or operator/external evidence and do not infer completion, product defect, or Scope Shaper re-entry.

The Mandate's Continuation Authority is the ceiling for success continuation; the Run Completion Boundary is the actual terminal of this invocation. If the boundary would exceed the ceiling and the current instruction does not explicitly revise that authority, the Run Contract should never have closed. Return the exact authority gap rather than silently stopping early or expanding authority.

A broader continuation never consumes a pre-authored Work Package/Increment list as a queue. `NEXT_INCREMENT_REQUIRED` returns to Scope Shaper against fresh actual state. Scope Shaper may preserve, split, merge, reorder, replace, or discard the provisional horizon under its current rules.

For `NAMED_REQUIRED_ITEMS_DELIVERED`, an item is not complete merely because a Ticket title resembles it. Trace the item to delivered canonical authority and confirm its applicable product result. Required Named Items remain obligations across multiple Increments until satisfied or explicitly revised by the user. Candidate Named Items may be dropped without blocking completion when current authority supports that choice.

An implementation-only run cannot use verified success re-entry to span several Increments. If Required Named Items need another Increment while `Verification: no`, return the smallest verification/boundary decision rather than silently omitting an item or claiming delivery.

## Hard boundaries

- Adaptive Planning never becomes implementation, heuristic-exploration, or verification authority.
- Delivery skills never rewrite Scope, Spec, Ticket meaning to make probing or verification pass.
- A heuristic finding alone is never an Adaptive implementation/planning defect classification or verifier verdict.
- Outer Main never invents deployment, credential, production/shared external mutation, destructive-action, or other missing authority.
- A material user-owned product trade-off outside current authority returns to the user.
- `done` belongs only to the verifier's guarded terminal progression.
- `Verification: no` is never treated as permission to run heuristic probing, infer a verifier verdict, or claim `done`.
- Candidate Named Items are not completion obligations; Required Named Items are not disposable.
- No phase, Ticket, or Increment may claim whole-run success before the active Completion Predicate is satisfied.
- This route is a thin handoff discipline, not a controller, scheduler, workflow database, approval engine, or generic Graph runtime.
