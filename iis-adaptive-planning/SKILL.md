---
name: iis-adaptive-planning
description: Use only when the user explicitly requests IIS Adaptive Planning, IIS 어댑티브 플래닝, an adaptive IIS mode, or explicitly continues a current Adaptive Planning Mandate. Run the existing IIS planning semantics and canonical artifacts under a standing user-delegated planning mandate and one closed invocation-local Run Contract so clear recommendations can be adopted without repeated approval prompts, required and candidate named work remain distinct, delivery stages and whole-run completion remain explicit, current Increments can be reshaped and planning leaves re-entered when evidence changes, and verification failures can be routed by authority instead of being blindly treated as implementation defects. Never activate for ordinary IIS, Ask Matt, To Spec, To Tickets, implementation, verification, or status-only requests.
---

# IIS Adaptive Planning

## Purpose

Run an **opt-in alternate operating mode** for IIS Planning without replacing or modifying Baseline IIS.

Preserve the current IIS product-planning semantics, authority owners, canonical artifact schemas, validators, and terminal Ready Ticket boundary. Add only these Adaptive behaviors:

1. establish a user-authorized Planning Mandate;
2. close one invocation-local Adaptive Run Contract that preserves required/candidate item meaning, independent delivery-stage authority, and whole-run completion before mutation;
3. satisfy eligible repeated planning confirmations through standing delegated confirmation when the mandate resolves the decision;
4. reshape the current Increment and re-enter the correct planning leaf when new evidence makes the current shape materially worse;
5. classify later verification problems by authority and route them to implementation, verification setup, or planning instead of forcing a test pass; and
6. after current-Increment planning closes, return the Ready Ticket Set and closed Run Contract to the current invocation's Outer Main, which applies the independently closed Implementation and Verification fields.

Do not turn IIS into a controller, delivery orchestrator, workflow database, approval engine, agent-governance framework, or generic safety layer.

## Single-entry invocation and Outer Main

There is no separately invokable Adaptive Run skill. `Run` in **Adaptive Run Contract** means the lifetime of the current explicit Adaptive invocation initiated through this one `iis-adaptive-planning` skill.

The **Outer Main** is the main agent handling that current explicit Adaptive invocation. It owns only Run Contract closure and carry-forward, phase routing from exact owner results, fresh completion assessment, and the final caller-facing result. It does not become a second planning, implementation, or verification authority: current IIS leaves retain product-planning authority, `ready-ticket-implement` retains implementation authority, and `ready-ticket-verify` retains verification verdict and guarded `done` authority. When Outer Main enters that skill's sole-verifier role, it acts as that exact owner for the verification phase and returns to Adaptive routing after the terminal result.

This is a thin invocation-local handoff role, not a persistent controller, scheduler, queue, retry ledger, workflow database, or new product-authority layer.

## Required current authority

At the start of every Adaptive planning run:

1. Load the currently discovered `iis-workflow` skill.
2. Resolve its current Scope Shaper, Ask Matt, To Spec, and To Tickets route targets.
3. Read the applicable current leaf before performing that leaf.
4. Use the current canonical templates, validators, path rules, authority ownership, and product-contract semantics from those sources.
5. Apply only the explicit Adaptive Delta defined in [references/00-baseline-coexistence.md](references/00-baseline-coexistence.md), [references/03-adaptive-routing.md](references/03-adaptive-routing.md), and the invocation-closure/completion discipline in [references/09-run-contract.md](references/09-run-contract.md).

Do not copy a remembered Baseline schema into this skill or treat an older package copy as current IIS authority.

Read these references before the corresponding work:

- always: [references/00-baseline-coexistence.md](references/00-baseline-coexistence.md)
- always before the first mutation and at every whole-run terminal decision: [references/09-run-contract.md](references/09-run-contract.md)
- mandate creation/update: [references/01-mandate-contract.md](references/01-mandate-contract.md)
- delegated decisions and confirmations: [references/02-delegated-decision-policy.md](references/02-delegated-decision-policy.md)
- routing and re-entry: [references/03-adaptive-routing.md](references/03-adaptive-routing.md)
- any Increment change: [references/04-increment-reshaping.md](references/04-increment-reshaping.md)
- any durable artifact write: [references/05-artifact-contract.md](references/05-artifact-contract.md)
- a verification result used as planning evidence: [references/06-verification-triage.md](references/06-verification-triage.md)
- terminal or user-return report: [references/07-terminal-report.md](references/07-terminal-report.md)
- current-Increment delivery/corrective handoff and explicit stop overrides: [references/08-delivery-continuation.md](references/08-delivery-continuation.md)

## Activation

Activate only when the current user authority clearly selects this mode, for example:

- `IIS Adaptive Planning으로 진행해`
- `IIS 어댑티브 모드로 계획해`
- an explicit instruction to continue one exact current Adaptive Planning Mandate
- explicit adoption of an Adaptive Planning Mandate proposed in the current conversation

Installation, an old Adaptive artifact, a past Adaptive session, a general preference for automation, or an ordinary `IIS workflow` request is not activation.

If Adaptive activation is absent, do not ask whether the user wants Adaptive. Leave the request to Baseline IIS.

A read-only status request remains read-only even when an Adaptive Mandate exists. Use the current Baseline state-check/Observatory contract and STOP.

## Adaptive Run Contract

Before the first Adaptive planning mutation, close and render the compact invocation contract in [references/09-run-contract.md](references/09-run-contract.md) using [templates/ADAPTIVE-RUN-CONTRACT.template.md](templates/ADAPTIVE-RUN-CONTRACT.template.md).

The Run Contract establishes:

- Goal Outcome for this invocation;
- Required Named Items;
- Candidate Named Items;
- Required Item Policy: `EXACT_REQUIRED_SET` | `REQUIRED_FLOOR` | `NONE_REQUIRED`;
- Implementation: `yes` | `no`;
- Verification: `yes` | `no`;
- Run Completion Boundary: `READY_TICKET_SET` | `CURRENT_INCREMENT_IMPLEMENTED` | `CURRENT_INCREMENT_DELIVERED` | `NAMED_REQUIRED_ITEMS_DELIVERED` | `BOUNDED_OUTCOME_SATISFIED` | `MANDATE_OUTCOME_SATISFIED`;
- one observable Completion Predicate;
- Authoritative Readback;
- Run Contract Approval Gate: `required` | `not_required`; and
- Source Authority.

Auto-fill every field current user authority, the applicable Mandate, canonical planning authority, or inspectable facts determine. A fully derived `CLOSED` form normally proceeds without another approval prompt. The only Run Contract-local exception is an affirmative `/승인게이트` modifier on the current explicitly active Adaptive invocation: set `Run Contract Approval Gate: required`, render the exact `CLOSED` form, and STOP before the first planning or delivery mutation until the user directly approves that rendered contract. Without that modifier, set `Run Contract Approval Gate: not_required` and proceed normally.

`/승인게이트` does not activate Adaptive by itself and does not change Goal Outcome, required/candidate meaning, delivery stages, completion meaning, Mandate authority, or any Baseline leaf approval. Standing delegation cannot satisfy this gate. If the user materially revises the decision-critical Run Contract meaning while responding, re-close and re-render the revised contract before requesting direct approval again; leaf-local planning or delivery changes inside the approved contract do not create another approval gate.

If a material field remains unresolved, mark the form `USER_INPUT_REQUIRED`, ask only for the smallest field whose different answers would change required scope, candidate freedom, delivery stages, success continuation, or completion meaning, and STOP before mutation. Do not ask the user to repeat settled fields or decide an inspectable fact.

Required Named Items and Candidate Named Items may coexist. Do not collapse a mixed assignment into one list-wide label, move a Required Named Item into the Candidate list, or treat a Candidate Named Item as a completion obligation without current user authority.

Implementation and Verification are independent invocation fields. Preserve explicit `do not implement` and `do not verify` overrides. `Verification: no` never permits a verifier call, a `done` claim, or a delivered/outcome boundary that still requires verification.

When explicit Adaptive activation supplies no narrower stop override and no broader named-item or outcome terminal, close the default current-Increment execution envelope as `Implementation: yes`, `Verification: yes`, and `Run Completion Boundary: CURRENT_INCREMENT_DELIVERED`, subject to the Required-item coverage invariant and Mandate Continuation Authority ceiling in `references/09-run-contract.md`. Do not force this current-Increment terminal when current authority already assigns a broader outcome or when required-item coverage is unknown or partial.

Do not let a planning leaf STOP, one implementation report, one Ticket, or one current Increment stand in for whole-run completion unless the closed Run Completion Boundary and Completion Predicate say so.

The Run Contract is invocation-local authority, not a third durable companion artifact or workflow state. Carry its decision-critical fields through planning, delivery, corrective re-entry, and success re-entry. Record only a material closure/revision in the Adaptive trace when later interpretation requires it.

## Adaptive Planning Mandate

Before the first Adaptive planning mutation, also normalize the user's current authority into the mandate contract in [references/01-mandate-contract.md](references/01-mandate-contract.md).

The mandate establishes:

- Desired Product Outcome and why it matters
- ordered Decision Priorities
- Hard Constraints
- Non-Goals
- delegated reshaping and planning-decision authority
- Continuation Authority ceiling: `CURRENT_INCREMENT` | `BOUNDED_OUTCOME` | `MANDATE_OUTCOME`
- Return-to-User Boundary
- project/planning-unit applicability

Do not demand a form-filling ceremony. If the user's natural-language instruction establishes these sufficiently, record the mandate and proceed. Ask only when a material product choice cannot be resolved from current authority and the mandate.

The Mandate fixes how to judge a good plan and the **maximum authorized success-continuation ceiling**. The Run Contract fixes what this invocation must preserve and what exact predicate ends it. If the Run Completion Boundary needs broader continuation than the stored ceiling and the current instruction explicitly grants it, revise/adopt the Mandate before mutation. Otherwise return the exact authority gap. Never silently stop early or expand authority.

The mandate delegates **planning judgment only**. It never turns Adaptive Planning into implementation or verification authority and never grants deployment, credential, external-effect, destructive-action, worker-roster, or production authority. Under explicit Adaptive activation, Outer Main defaults `Implementation: yes` and `Verification: yes` unless the user independently overrides either field; execution remains owned by the delivery skills.

## Standing delegated confirmation

In Adaptive mode, the user's explicit adoption of the mandate is standing authority for eligible downstream planning confirmations.

A candidate may use standing delegated confirmation only when all of the following are true:

1. it remains inside the current mandate, closed Run Contract, and canonical parent authority;
2. current evidence and ordered priorities yield one materially preferred product result;
3. no Return-to-User Boundary is triggered;
4. no unresolved authority conflict remains;
5. the current leaf's non-approval admission, semantic, artifact, validation, and evidence requirements are satisfied; and
6. the gate is not one of the exact special gates preserved as direct-user-only in the Adaptive Delta.

When these conditions hold, do not ask for a redundant per-artifact approval. Complete the canonical confirmation/status transition and record its provenance as `DELEGATED_RECOMMENDATION` in the Adaptive trace.

When adversarial consensus is explicitly active, activation and exact Challenger designation remain direct-user-only. Before the first Challenger invocation, apply the pre-consensus Intent Anchor finalization in `references/02-delegated-decision-policy.md`: when current user authority, the adopted Mandate, closed Run Contract, applicable canonical authority, and direct facts determine one faithful current Intent Anchor, the delegated-decision test passes, and no Return-to-User Boundary, authority conflict, separately required disclosure expansion, or explicit current request for direct Anchor review exists, finalize that Anchor as `DELEGATED_RECOMMENDATION` and invoke the exact designated Challenger without a user round-trip. Otherwise return only the smallest unresolved Anchor, authority, or disclosure decision. After `ADVERSARIAL CONSENSUS REACHED` for the latest complete candidate, Ask Matt alone performs the post-consensus authority-delta review against the current user conversation, adopted Mandate, closed Run Contract, current finalized Intent Anchor, applicable canonical authority, and direct facts. If the delta is `NONE`, the delegated-decision test still passes, no Return-to-User Boundary or authority conflict exists, and no material candidate change occurred after the Challenger's final review, standing delegation may satisfy the final integrated approval as `DELEGATED_RECOMMENDATION` and continue to To Spec. `MATERIAL` or `UNCERTAIN` authority delta returns only the exact decision to the user. To Spec consumes that finalized result; it does not re-run the authority-delta review.

This post-consensus finalization is leaf-local. It does not revise the Run Contract Goal Outcome, Required Named Items, delivery stages, Run Completion Boundary, or Completion Predicate unless current user authority independently changes those outer-run fields.

Do **not** describe a delegated confirmation or delegated post-consensus finalization as an explicit user approval. The user authorized the decision policy; the agent made the delegated recommendation under that authority.

If the conditions do not hold, return the smallest material decision to the user. Do not weaken the contract merely to avoid a question.

## Adaptive planning loop

For the current planning unit:

1. establish current canonical planning state and current product evidence;
2. establish or revalidate Mandate applicability and the closed Run Contract;
3. route by the current `iis-workflow` admission rules;
4. perform the current canonical leaf with the Adaptive Delta;
5. validate every canonical artifact with the current canonical validator/review contract;
6. compare the resulting planning shape with the Mandate, Run Contract, parent authority, and fresh evidence;
7. choose exactly one disposition:
   - `CONTINUE_CURRENT_ROUTE`
   - `RESHAPE_INCREMENT`
   - `RETURN_TO_ASK_MATT`
   - `RETURN_TO_SPEC_PROJECTION`
   - `RETURN_TO_TICKET_PROJECTION`
   - `RETURN_TO_USER`
   - `CURRENT_INCREMENT_PLANNING_COMPLETE`
8. for a nonterminal planning disposition, re-enter the correct existing IIS leaf without inventing a new leaf;
9. when one approved Spec and its validated complete Ready Ticket Set exist for the current Increment, report **planning phase** completion and STOP at the IIS Planning ownership boundary; and
10. return that exact owner result to Outer Main, which compares it with the active delivery-stage fields, Run Completion Boundary, and Completion Predicate before declaring whole-run success or continuing.

Do not use retry counters, a workflow ledger, persistent controller state, or agent scheduling to implement this loop. It is a planning judgment loop in the current request/context plus durable planning artifacts and one invocation-local Run Contract.

## Reshaping

Treat an Increment as the current best construction hypothesis, not as an immutable product promise.

When the mandate delegates reshaping, Adaptive may split, merge, reorder, replace, shrink, defer, drop unsupported future scope, insert a required durable foundation, or supersede an unconsumed planning unit when fresh evidence makes that shape materially better.

Use [references/04-increment-reshaping.md](references/04-increment-reshaping.md). Preserve current IIS lineage rules and unique work slugs. Never rewrite an immutable Scope revision or a delivered `done` history.

A reshape is not permission to change the user's product intent, Hard Constraints, Non-Goals, a material trade-off that remains genuinely unresolved, Required Named Items, Required Item Policy, delivery-stage limits, or the active Completion Predicate. Required Named Items remain whole-run obligations even when split across multiple Increments. Candidate Named Items may be replaced/deferred/dropped only under current Mandate authority and evidence.

## Spec and Ticket projection

To Spec and To Tickets remain projection stages, not places to invent product meaning.

- If accurate Spec writing needs a new product decision, return to Ask Matt or Scope Shaper.
- If Ticket decomposition requires strengthening/weakening product meaning, return upstream.
- For Spec/Ticket projection, use the current Baseline leaf's self-review/adoption guard and do not add a redundant Adaptive approval ceremony.
- Keep the canonical `SPEC.md`, Ticket schema, status vocabulary, Behavior/UI authority adoption, Verification flow schema, and validators exactly as current IIS defines them.
- Do not force all multi-Increment Run Contract obligations into one current Spec or Ticket Set. Project exactly one current Increment while preserving the outer whole-run obligations.

## Verification evidence and re-entry

Adaptive Planning may consume a fresh exact result from the separate `ready-ticket-verify` lifecycle as evidence. It does not replace or rewrite the verifier verdict.

Classify the underlying problem using [references/06-verification-triage.md](references/06-verification-triage.md):

- `IMPLEMENTATION_DEFECT`
- `VERIFICATION_MECHANISM_DEFECT`
- `CONTRACT_OVERREACH`
- `CURRENT_INCREMENT_MISMATCH`
- `INCONCLUSIVE`

Never infer `CONTRACT_OVERREACH` merely because a requirement is difficult or expensive. Trace the requirement to current product authority.

If planning authority changes a contract, do not turn an earlier failed result into PASS. Validate the new planning artifacts and require fresh verification when Verification remains enabled.

Adaptive Planning itself does not implement or verify Tickets. Outer Main invokes the separately discovered `ready-ticket-implement` only when `Implementation: yes` and `ready-ticket-verify` only when `Verification: yes`, following each skill's current execution-mode contract. Delivery defaults to DIRECT; Adaptive never auto-selects or falls back to SUBAGENT, and implementation SUBAGENT is used only when the current user explicitly selected it for that stage. Use [references/08-delivery-continuation.md](references/08-delivery-continuation.md); do not insert a new approval prompt merely because ownership changes.

If an enabled delivery lifecycle produces a material implementation, verification-mechanism, contract, or current-Increment defect, corrective routing/re-entry is the Adaptive default after an actual correction or new evidence, unless the user explicitly requested no corrective re-entry/fail-and-report. Adaptive owns only planning correction/reshaping; implementation and verification remain owned by the separate delivery skills. A disabled stage is an authority boundary, not a failure to be bypassed.

## Post-delivery completion assessment and success re-entry

A successful current Increment may trigger a new Adaptive planning cycle only after:

1. its current canonical Tickets are actually `done`;
2. Verification was enabled;
3. the active Run Completion Boundary remains unsatisfied and requires broader success continuation; and
4. the Mandate Continuation Authority ceiling permits that continuation.

`CURRENT_INCREMENT_IMPLEMENTED` is an implementation-only terminal and never triggers success re-entry.

Before selecting anything next, inspect fresh actual product state and compare the active Completion Predicate against current authoritative readback. Do not infer success continuation from `done` status alone, and do not consume the existing Work Package list or Provisional Construction Horizon as an execution queue.

Choose exactly one completion-assessment disposition:

- `RUN_CONTRACT_SATISFIED` — the active Required Named Items, bounded outcome, or Mandate outcome predicate is satisfied in fresh actual product state; stop the Adaptive invocation and report Run Contract completion.
- `NEXT_INCREMENT_REQUIRED` — the active predicate is not yet satisfied and current authority can determine that more construction is required; re-enter Scope Shaper against fresh actual state so it selects exactly one new current Increment.
- `USER_DECISION_REQUIRED` — the active predicate is not yet satisfied but a material user-owned trade-off remains after applying current authority and priorities; return only that decision to the user.
- `EVIDENCE_REQUIRED` — current attributable evidence cannot determine whether the active predicate is satisfied or whether more construction is required; obtain only the missing authoritative readback or operator/external evidence and do not infer completion, product defect, or Scope Shaper re-entry.

`NEXT_INCREMENT_REQUIRED` never names the next WP/INC from a prior plan by default. Scope Shaper may preserve, split, merge, reorder, replace, or discard provisional structure under its current rules. Completion is judged against the active observable predicate, not by exhausting a roadmap or provisional horizon.

For `NAMED_REQUIRED_ITEMS_DELIVERED`, inspect every Required Named Item against delivered canonical authority and actual product readback. Candidate Named Items do not block completion. A Ticket title or historical plan mention is not completion evidence.

Continuation Authority is the success-continuation ceiling and does not grant implementation or verification authority. The closed Implementation and Verification fields govern the current invocation's delivery stages.

## Artifacts

Always preserve the current canonical IIS artifact set. Adaptive does not replace Scope, Work Package, Increment, Behavior/UI authority, Spec, Ticket, or validator outputs.

Additionally keep only the minimal Adaptive companion provenance described in [references/05-artifact-contract.md](references/05-artifact-contract.md):

- `ADAPTIVE-PLANNING-MANDATE.md`
- `ADAPTIVE-PLANNING-TRACE.md` only when material delegated decisions, Run Contract classifications/revisions, reshaping, verification triage, success re-entry/completion, or user-return decisions exist

The rendered Run Contract remains invocation-local and is not a required third companion file.

Never inject Adaptive-only metadata into canonical IIS artifacts merely for convenience.

## Hard boundaries

Do not:

- activate Adaptive for Baseline requests;
- begin planning or delivery mutation before the Run Contract is `CLOSED`;
- collapse mixed Required/Candidate Named Items into one list-wide meaning;
- invoke implementation when Implementation is `no`;
- invoke verification or claim `done` when Verification is `no`;
- claim whole-run completion before the active Completion Predicate is satisfied;
- close a Run Completion Boundary broader than the Mandate ceiling without explicit current authority;
- edit Baseline skills, templates, or validators as part of Adaptive operation;
- auto-enable adversarial consensus or choose its Challenger;
- bypass a special direct-user-only gate preserved by the Adaptive Delta;
- turn repository/runtime truth into product authority by itself;
- implement outside approved current scope to satisfy a test;
- delete/relax an approved contract merely to produce PASS;
- rewrite delivered history;
- create a controller, scheduler, retry engine, approval state machine, agent registry, generic permission DSL, evidence database, or persistent Run Contract state;
- add planning ceremony solely in the name of generic agent control, security, or safety.

Concrete host/tool permission boundaries still apply to the concrete actions they govern, but they do not become IIS product-planning machinery.

## Terminal boundary

Adaptive Planning ends at the same current-Increment product as Baseline IIS: one approved Spec and its validated complete Ready Ticket Set.

Report the result as `IIS ADAPTIVE PLANNING PHASE COMPLETE` using [references/07-terminal-report.md](references/07-terminal-report.md), then STOP at the planning ownership boundary.

`STOP` here is the **IIS Planning owner boundary**, not necessarily the end of the current Adaptive invocation. Do not implement or verify **as IIS Planning** merely because current Increment planning completed. Return the Ready Ticket Set and closed Run Contract to Outer Main; this owner STOP is not an invocation STOP.

Outer Main applies Implementation and Verification independently and emits `IIS ADAPTIVE RUN COMPLETE` only when the active Run Completion Boundary and Completion Predicate are actually satisfied. `CURRENT_INCREMENT_IMPLEMENTED` stops after the complete implementation denominator without verifier progression. Broader delivery or outcome boundaries require the exact enabled stages and current Mandate ceiling.

Do not plan the next provisional Increment or declare the whole product complete merely because current Increment planning completed. A broader success continuation begins only after the current Increment is actually delivered, the active Run Contract requires it, and the Mandate ceiling permits it; even then Scope Shaper selects the next current Increment from actual state rather than consuming a provisional plan.
