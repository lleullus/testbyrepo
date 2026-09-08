# Delivery Continuation After the IIS Planning Ownership Boundary

## Ownership and closed Run Contract

Keep ownership separate while the current explicit Adaptive invocation continues:

1. **IIS Planning ownership** ends at one approved Spec plus its validated complete Ready Ticket Set.
2. **Explicit Adaptive activation** defaults Outer Main to `Implementation: yes` and `Verification: yes`.
3. When current authority supplies no narrower stop override and no broader named-item or outcome terminal, the default current-Increment terminal is `CURRENT_INCREMENT_DELIVERED`, subject to the Run Contract Required-item coverage invariant and Mandate ceiling.
4. Current instructions override those fields independently: `planning only` or `stop after Ready Tickets` selects `no`/`no`; `do not verify` preserves implementation authority as `yes`/`no`; `do not implement` never invents implementation authority.
   Execution-preparation-only selects READY_EXECUTION_PLANS, both switches no and exact required Tickets; this is distinct from product-planning-only READY_TICKET_SET.
5. Before any planning or delivery mutation, Outer Main must carry one `CLOSED` Run Contract from [09-run-contract.md](09-run-contract.md). Planning ownership completion, one Ticket completion, and one Increment completion are not whole-run completion unless that contract's boundary says so.

Outer Main is the thin invocation-local handoff owner defined by the top-level skill. It carries the Run Contract, invokes each exact owner only when enabled, receives exact terminal results, and performs fresh completion assessment by comparing the active boundary's applicable parent obligations, their existing acceptance owners, and current attributable readback. It does not become a second planning, implementation, or verification authority and does not issue or revise an AC/whole-Ticket verdict.

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

Skill-contract discovery during planning, routing, or documentation review is read-only: canonical `skill://` and filesystem Skill reads do not start delivery admission. Follow the selected owner's explicit begin/assignment path only after the actual current `ready` Ticket and enabled delivery phase are established. If an explicit unbound admission must be cancelled, use the owning runtime's `cancel_admission` contract; do not cancel admission merely because a Skill was read. Bound executions, assignments and workers remain with their existing owner's completion, block or recovery path.

- `ready-ticket-implement` owns one exact Ready Ticket implementation and implementer self-check.
- `ready-ticket-plan` owns method preparation, pre-implementation Heuristic and independent current per-Ticket start review.
- `ready-ticket-verify` owns integrated discovery, fresh exact-Ticket verification, final verdict and guarded ready→done progression.
- Invoke each owner once per current pass and follow its current mode contract. Implementation/verification default SUBAGENT without opt-in and use DIRECT only when explicitly selected for that stage. Preparation follows its own current-selection/independent-invocation rules. No model capability, difficulty, cost or worker availability authorizes topology substitution or fallback.
- Execution mode does not select a model. Apply the closed Run Contract's [Delivery Model Selection](09-run-contract.md#delivery-model-selection): carry that stage's exact user-selected model/effort and selection basis through the current owner's existing assignment path. An unresolved recommendation or host default cannot stand in for a selected configuration. Do not ask again per Ticket, automatically escalate effort, or substitute another model when a selected configuration is unavailable.
- Implementation uses one worker by default. Current ADMIT replaces normal first-source-change PRE_ACTION review; material changes still use affected method review and the material-turn boundary. Explicit implementation DIRECT uses current Main.
- Preparation uses only actual delegated Planner/Heuristic/Plan Review invocations under current selected modes/models. The writer cannot approve itself in the same invocation; no fixed three-model roster or hidden fallback creates independence.
- `ready-ticket-verify` defaults to `SUBAGENT`: exactly one delegated verifier owns the whole verifier core and its mandatory scenario/material-turn/pre-progression checkpoint contract. Under an explicit verification `DIRECT` override, current Main owns that core directly. Outer Main does not issue a second verifier verdict.
- Do not pass `Delegated Worker: yes` or `Delegated Verifier: yes` from Adaptive; the owning Skill alone sets its child marker.
- Treat each currently discovered delivery skill's required input/handoff fields as the canonical owner interface. Adaptive owns routing, not a remembered copy of that interface: before invoking a downstream owner, forward every current required handoff field from the exact upstream owner result/context unchanged, and never synthesize a missing binding, verdict, target identity, or evidence field. If a required field is absent, stale, or malformed, preserve the downstream owner's exact admission/currentness result and correct only the owning condition.
- Do not infer Ticket-set parallelism, worker scheduling, or a persistent queue from the existence of a Ready Ticket Set. Select only a currently admissible Ticket using canonical blockers, product dependencies, shared-workspace safety, and current repository evidence.

Do not invoke a disabled stage for stronger evidence. Verification yes includes final verifier-owned discovery; Verification no forbids final discovery/verdict/done, but Implementation yes still requires pre-implementation Heuristic and independent review. Preparation-only creates neither implementation nor verification authority.

## Invocation-local delivery checkpoint continuation

A checkpoint from implementation/verification `SUBAGENT` execution is a nonterminal invocation-local delivery message. Outer Main may release the protected next phase only after checking:

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
Checkpoint: PRE_RUNTIME | MATERIAL_TURN | PRE_PROGRESSION
Decision: CONTINUE | STEER | STOP
Authority / evidence anchor:
Bounded steering: None | <exact correction>
Reason:
```

`STEER` must identify the problematic checkpoint field, current authority/evidence anchor, why the protected phase cannot safely proceed unchanged, and the bounded correction. Vague preference-based steering is not sufficient.

Checkpoint review must not redesign the implementation diff from scratch, rerun all verifier flows, issue a Parent AC/whole-Ticket verdict, or convert a checkpoint into Adaptive defect classification. Do not forward a checkpoint as a user approval prompt. Do not create a checkpoint ledger or persistent state. A checkpoint is internal phase release under already established user authority, not the `/승인게이트` Run Contract release or any new Mandate/Scope/Spec/Ticket approval gate.

Adaptive delivery routing and verification triage wait for the exact terminal owner result. A checkpoint, candidate verdict, Parent steering decision, or partial observation is not a terminal implementation/verifier result.

Use public `checkpoint` with the exact kind and `release_checkpoint`. Parent continuation does not replace current plan review or erase authority/target drift. A plan refresh on release supplies `plan_review_path` to the common binding check; PAUSED permits safe read/analysis but no source mutation. Resumption/replacement preserves exact owner/currentness and actual service/effect settlement; no normal first-change reapproval is introduced.

## Invocation-local evidence economy

Pass this bounded instruction through each enabled delivery skill's existing `Additional User Instructions` input:

> Subject to the exact Ticket contract, the closed Run Contract, and current explicit user instructions, collect only evidence that can change admission, an authored flow result, target attribution/freshness, required cleanup/terminal closure, or the next authority route. Once those obligations are decidable, stop confidence-only duplicate evidence collection and emit the owning terminal result.

This does **not** weaken authored Verification flows, independent-verification requirements, counterexamples, ordering/interruption/persistence/UI/external boundaries, cleanup, Required Named Items, or the active Run Completion Predicate. It only prevents repeating the same claim across source/tests/browser or other modalities when the approved acceptance boundary/readback has already made the owning decision possible. Do not create evidence budgets, counters, modality quotas, extra report fields, or persistent evidence state.

## Preparation handoff

Before Implementation yes, or for explicit READY_EXECUTION_PLANS, invoke `ready-ticket-plan` when an actual independent current ADMIT is not already available for the required Ticket. Preserve exact Ticket/root, existing investigation and method navigation, current mode/model instructions and outside-root review output. Shared plans cover the impact of important producer/consumer decisions before dependent implementation, not a universal all-Ticket design gate.

Consume only actual `READY TICKET PLAN RESULT` and its `Plan Review` artifact. Forward the exact result as `plan_review_path`; the runtime recomputes current plan/common-plan/review/Ticket/authority identity on direct admission, assignment, child begin and affected resume. Planner/Heuristic intermediate output, JSON shape, past conversational approval or another Ticket's ADMIT is not admission. REVISE/EVIDENCE_NEEDED or PLAN_REVIEW_REQUIRED/PLAN_REVIEW_STALE/PLAN_NOT_ADMITTED returns to the affected preparation/evidence owner, not Adaptive final defect triage.

READY_EXECUTION_PLANS closes only with every explicitly required preparation Ticket current ADMIT and actual independent-review provenance. Partial useful plans or a smaller admitted subset cannot close it. Return the exact owner limits if independence/capability/evidence is unavailable; do not silently delegate or self-approve. Both delivery switches stay no and this terminal claims no implementation, verdict or done.

## Implementation handoff

Invoke implementation only when `Implementation: yes`.

Continue from implementation directly to final verification only when all of the following hold:

- `Verification: yes`;
- the current implementation report for the exact Ticket contains `Completion: COMPLETE`; and
- the canonical Ticket remains exact `Status: ready` for the next delivery owners.

Preserve exact actual implementation target/checkpoint, self-check evidence and optional plan/review context as verifier navigation, not final findings or verdicts.

BLOCKED/PARTIAL or unavailable implementation results do not silently become verification. Correct only their owning condition; re-enter after material candidate correction, changed authority or genuinely new evidence. A method-material correction starts at the affected preparation owner, while equivalent local repair stays with the worker/current ADMIT.

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

## Verification handoff

When Verification is yes, invoke `ready-ticket-verify` directly on the current stable ready target. Implementation yes supplies its exact COMPLETE target/self-check as navigation; Implementation no requires direct attribution of the already implemented target, not an inference from ready status. No new execution plan ADMIT is required for verification-only. Forward current required inputs from the discovered verifier, without synthesizing evidence or binding. Its current cycle owns mandatory scenarios plus a bounded material discovery frontier; no-lane/no-finding is not PASS.

Actual product-source/authority/runtime/readback drift invalidates affected evidence and requires fresh applicable observations. Exact declared method-context-only changes merely stale that navigation, unless the plan is itself an approved product target; do not force final verdict invalidation or new implementation preparation solely for method context. Undeclared files are conservatively product-target candidates until narrowly resolved.

## Verification terminal routing

Route from the exact verifier result fields, not a summarized label, implementation report or intermediate discovery/checkpoint:

```text
Verification Verdict: VERIFIED
Ticket Progression: COMPLETED
Ticket status after verification: done
  -> Ticket terminal delivery complete

Verification Verdict: VERIFIED
Ticket Progression: FAILED
  -> preserve actual observed status (even done); do not claim completed progression
  -> resolve the guarded progression/currentness failure under its owning authority

Verification Verdict: FAILED | INCONCLUSIVE
  -> classify with 06-verification-triage.md

No final Verification Verdict
  -> preserve the verifier's exact admission/capability/currentness result
  -> correct only its owning condition when current authority permits
  -> never invent an implementation/planning defect classification
```

Never reduce terminal completion to `VERIFIED -> done`; the canonical Ticket must actually be `done` after `Ticket Progression: COMPLETED`.

After one Ticket reaches `done`, re-read the complete current canonical Ticket denominator. The complete `done` denominator is a necessary progression fact, not automatic `CURRENT_INCREMENT_DELIVERED` success. Before emitting that terminal, Outer Main must also compare the approved current parent and validated Ticket Set, identify every parent-Spec/Behavior/UI obligation applicable to this Increment, confirm an existing Ticket acceptance boundary owns each one, and consume the owning result's actual current observation, authoritative readback, `Evidence limit`, and `Remaining uncertainty`. Do not include future, candidate, Non-Goal, or unrelated preserved obligations that do not apply to the current Increment.

## Corrective routing is the Adaptive default

Unless the current user explicitly requested `no re-entry`, `fail and report`, or equivalent, apply authority-based correction and re-enter the affected enabled owner after a material correction/new evidence:

```text
IMPLEMENTATION_DEFECT
  -> if Implementation yes: current reviewed method local repair by ready-ticket-implement
  -> material cause/owner/interface/persistence/readback change: affected ready-ticket-plan review before dependent implementation
  -> any changed target -> if Verification yes: fresh integrated ready-ticket-verify
  -> required stage disabled: return exact authority gap without bypass

VERIFICATION_MECHANISM_DEFECT
  -> correct only the actual integrated verifier/harness mechanism
  -> if Verification yes: fresh verifier-owned scenario/frontier/readback on stable target
  -> if Verification no: do not invoke the verifier

CONTRACT_OVERREACH
  -> re-enter IIS Adaptive Planning at the owning planning leaf
  -> To Tickets when only Ticket projection is wrong
  -> To Spec / Ask Matt when parent product meaning is wrong or incomplete
  -> fresh validated Ready Ticket(s)
  -> repeat only enabled stages; affected implementation method requires current review, changed verification target requires fresh integrated verification

CURRENT_INCREMENT_MISMATCH
  -> re-enter Scope Shaper against fresh actual product state
  -> current canonical planning route
  -> fresh Ready Ticket Set
  -> repeat only enabled stages; no stale result becomes current approval or PASS

INCONCLUSIVE
  -> obtain only missing evidence, operator condition, attributable target or verifier mechanism state
  -> continue only when that new evidence makes a valid next route available
```

Never turn an earlier failure into PASS after planning changes. Validate current authority and obtain fresh applicable owner evidence. No independent discovery-stage result or binding is required before the integrated verifier.

After a later Ticket or correction changes a product surface that can materially affect an earlier delivered obligation, current completion assessment uses new evidence only for the actually affected integration/preservation boundary. That boundary must be acceptance-owned and adjudicated through the relevant existing exact Ticket's authored verification and Scope/Non-Goals/cross-AC closure; Outer Main checks coverage and currentness but does not issue a second verdict. Keep unaffected evidence and prior `done` history intact; do not reset that history, infer permission for diagnostic re-verification of a `done` Ticket, or rerun unrelated flows. Explicit diagnostic authorization remains governed by the existing verifier contract. A historical PASS or `done` status cannot stand in for current readback at the affected boundary.

## Progress guard without retry machinery

Before repeating a planning or delivery owner, identify at least one material change:

- corrected planning/implementation candidate;
- changed canonical authority;
- newly attributable verification target or mechanism; or
- genuinely new evidence/external condition.

If the same artifact/target, same evidence, same finding, and same route would repeat without such a change, stop at the owning boundary and report the unresolved condition as whole-run incomplete. Do not add a numeric retry policy, persistent attempt ledger, or workflow state.

An explicit no-corrective-re-entry override stops cross-owner continuation after the current owner reports its terminal result/classification. It does not suppress normal local self-correction inside that owner before the terminal result, and it does not convert an unsatisfied Run Contract into success.

## Completion assessment and success continuation by Run Completion Boundary

A current Increment is fully delivered only after every current canonical Ticket in its approved Ready Ticket Set has reached exact `done` through the owning one-exact-Ticket verification lifecycle and every approved parent obligation applicable to that Increment is acceptance-owned in the existing Set and closed by that owner's current attributable evidence/readback. Do not pull future or otherwise non-applicable whole-Goal obligations into this boundary.

Apply the active Run Completion Boundary and current Mandate ceiling:

```text
READY_TICKET_SET
  -> should already have terminated at the planning ownership boundary
  -> Implementation and Verification must both be no

READY_EXECUTION_PLANS
  -> Implementation and Verification both no
  -> every exact required preparation Ticket has actual current independent ADMIT
  -> return actual READY TICKET PLAN RESULT/review; no product completion claim

CURRENT_INCREMENT_IMPLEMENTED
  -> requires Implementation yes and Verification no
  -> after the complete implementation denominator is COMPLETE, Run Contract satisfied
  -> Tickets remain under verifier-owned status; do not claim done
  -> no success re-entry into another Increment

CURRENT_INCREMENT_DELIVERED
  -> requires Verification yes
  -> after the complete done denominator closes, assess applicable parent-obligation ownership and current evidence/readback
  -> if every applicable obligation is owned and closed, Run Contract satisfied -> emit IIS ADAPTIVE RUN COMPLETE
  -> missing truthful ownership -> return the exact To Tickets or upstream planning gap; do not create an umbrella Ticket or second verifier
  -> existing owner but missing/stale/inconclusive evidence -> EVIDENCE_REQUIRED; do not infer success

NAMED_REQUIRED_ITEMS_DELIVERED
BOUNDED_OUTCOME_SATISFIED
MANDATE_OUTCOME_SATISFIED
  -> require fresh actual product state and attributable authoritative readback
  -> perform the completion assessment below
```

The shared closure check above is claim-sensitive. Direct runtime, operator, or external obligations require the actual current observation and authoritative readback their approved boundary names. `Not independently verifiable` or another limited PASS closes only the approved canonical facts or absence/reason it actually establishes; its `Evidence limit` and `Remaining uncertainty` cannot be widened into an unobserved result. Conversely, source, artifact, document, or structure obligations close by current canonical inspection when that is their approved boundary; do not demand invented runtime. Outer Main consumes the existing owner reports and readbacks without re-adjudicating exact Ticket ACs.

A current attributable readback that directly contradicts the Completion Predicate establishes that the predicate is **not satisfied**. It is not missing evidence, and acknowledging that fact is not a second AC/Ticket verdict. Do not require a fresh passing owner report merely to recognize non-completion, and do not relabel the observed contradiction as `EVIDENCE_REQUIRED`. Preserve the exact counterexample and existing acceptance owner; use only the corrective route current authority permits. If the user explicitly disabled that continuation, stop with the existing decision-provenance form, `Next allowed action: None`, and `Whole-run completion: no`. A settled no-mutation/no-re-entry instruction is not an unresolved material product choice; do not ask the user to choose it again or misreport it as a Mandate-ceiling gap.

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

- Adaptive Planning never becomes preparation, implementation or verification authority.
- Delivery owners never rewrite Scope/Spec/Ticket meaning to force admission or PASS.
- A preparation decision or internal discovery finding alone is never an Adaptive final defect classification or verifier verdict.
- Outer Main never invents deployment, credential, production/shared external mutation, destructive-action, or other missing authority.
- A material user-owned product trade-off outside current authority returns to the user.
- `done` belongs only to the verifier's guarded terminal progression.
- Verification no never permits final discovery/verdict/done; it does not disable required pre-implementation review.
- Candidate Named Items are not completion obligations; Required Named Items are not disposable.
- No phase, Ticket, or Increment may claim whole-run success before the active Completion Predicate is satisfied.
- This route is a thin handoff discipline, not a controller, scheduler, workflow database, approval engine, or generic Graph runtime.
