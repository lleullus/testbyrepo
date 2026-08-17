---
name: iis-adaptive-planning
description: Use only when the user explicitly requests IIS Adaptive Planning, IIS 어댑티브 플래닝, an adaptive IIS mode, or explicitly continues a current Adaptive Planning Mandate. Run the existing IIS planning semantics and canonical artifacts under a standing user-delegated planning mandate so clear recommendations can be adopted without repeated approval prompts, current Increments can be reshaped and planning leaves re-entered when evidence changes, and verification failures can be routed by authority instead of being blindly treated as implementation defects. Never activate for ordinary IIS, Ask Matt, To Spec, To Tickets, implementation, verification, or status-only requests.
---

# IIS Adaptive Planning

## Purpose

Run an **opt-in alternate operating mode** for IIS Planning without replacing or modifying Baseline IIS.

Preserve the current IIS product-planning semantics, authority owners, canonical artifact schemas, validators, and terminal Ready Ticket boundary. Add only these Adaptive behaviors:

1. establish a user-authorized Planning Mandate;
2. satisfy eligible repeated planning confirmations through standing delegated confirmation when the mandate resolves the decision;
3. reshape the current Increment and re-enter the correct planning leaf when new evidence makes the current shape materially worse;
4. classify later verification problems by authority and route them to implementation, verification setup, or planning instead of forcing a test pass.

Do not turn IIS into a controller, delivery orchestrator, workflow database, approval engine, agent-governance framework, or generic safety layer.

## Required current authority

At the start of every Adaptive planning run:

1. Load the currently discovered `iis-workflow` skill.
2. Resolve its current Scope Shaper, Ask Matt, To Spec, and To Tickets route targets.
3. Read the applicable current leaf before performing that leaf.
4. Use the current canonical templates, validators, path rules, authority ownership, and product-contract semantics from those sources.
5. Apply only the explicit Adaptive Delta defined in [references/00-baseline-coexistence.md](references/00-baseline-coexistence.md) and [references/03-adaptive-routing.md](references/03-adaptive-routing.md).

Do not copy a remembered Baseline schema into this skill or treat an older package copy as current IIS authority.

Read these references before the corresponding work:

- always: [references/00-baseline-coexistence.md](references/00-baseline-coexistence.md)
- mandate creation/update: [references/01-mandate-contract.md](references/01-mandate-contract.md)
- delegated decisions and confirmations: [references/02-delegated-decision-policy.md](references/02-delegated-decision-policy.md)
- routing and re-entry: [references/03-adaptive-routing.md](references/03-adaptive-routing.md)
- any Increment change: [references/04-increment-reshaping.md](references/04-increment-reshaping.md)
- any durable artifact write: [references/05-artifact-contract.md](references/05-artifact-contract.md)
- a verification result used as planning evidence: [references/06-verification-triage.md](references/06-verification-triage.md)
- terminal or user-return report: [references/07-terminal-report.md](references/07-terminal-report.md)

## Activation

Activate only when the current user authority clearly selects this mode, for example:

- `IIS Adaptive Planning으로 진행해`
- `IIS 어댑티브 모드로 계획해`
- an explicit instruction to continue one exact current Adaptive Planning Mandate
- explicit adoption of an Adaptive Planning Mandate proposed in the current conversation

Installation, an old Adaptive artifact, a past Adaptive session, a general preference for automation, or an ordinary `IIS workflow` request is not activation.

If Adaptive activation is absent, do not ask whether the user wants Adaptive. Leave the request to Baseline IIS.

A read-only status request remains read-only even when an Adaptive Mandate exists. Use the current Baseline state-check/Observatory contract and STOP.

## Adaptive Planning Mandate

Before the first Adaptive planning mutation, normalize the user's current authority into the mandate contract in [references/01-mandate-contract.md](references/01-mandate-contract.md).

The mandate establishes:

- Desired Product Outcome and why it matters
- ordered Decision Priorities
- Hard Constraints
- Non-Goals
- delegated reshaping and planning-decision authority
- Return-to-User Boundary
- project/planning-unit applicability

Do not demand a form-filling ceremony. If the user's natural-language instruction establishes these sufficiently, record the mandate and proceed. Ask only when a material product choice cannot be resolved from current authority and the mandate.

The mandate delegates **planning judgment only**. It never creates implementation, verification, deployment, credential, external-effect, destructive-action, worker-roster, or production authority.

## Standing delegated confirmation

In Adaptive mode, the user's explicit adoption of the mandate is standing authority for eligible downstream planning confirmations.

A candidate may use standing delegated confirmation only when all of the following are true:

1. it remains inside the current mandate and canonical parent authority;
2. current evidence and ordered priorities yield one materially preferred product result;
3. no Return-to-User Boundary is triggered;
4. no unresolved authority conflict remains;
5. the current leaf's non-approval admission, semantic, artifact, validation, and evidence requirements are satisfied; and
6. the gate is not one of the exact special gates preserved as direct-user-only in the Adaptive Delta.

When these conditions hold, do not ask for a redundant per-artifact approval. Complete the canonical confirmation/status transition and record its provenance as `DELEGATED_RECOMMENDATION` in the Adaptive trace.

Do **not** describe that event as an explicit user approval. The user authorized the decision policy; the agent made the delegated recommendation under that authority.

If the conditions do not hold, return the smallest material decision to the user. Do not weaken the contract merely to avoid a question.

## Adaptive planning loop

For the current planning unit:

1. establish current canonical planning state and current product evidence;
2. establish or revalidate mandate applicability;
3. route by the current `iis-workflow` admission rules;
4. perform the current canonical leaf with the Adaptive Delta;
5. validate every canonical artifact with the current canonical validator/review contract;
6. compare the resulting planning shape with the mandate, parent authority, and fresh evidence;
7. choose exactly one disposition:
   - `CONTINUE_CURRENT_ROUTE`
   - `RESHAPE_INCREMENT`
   - `RETURN_TO_ASK_MATT`
   - `RETURN_TO_SPEC_PROJECTION`
   - `RETURN_TO_TICKET_PROJECTION`
   - `RETURN_TO_USER`
   - `CURRENT_INCREMENT_PLANNING_COMPLETE`
8. for a nonterminal planning disposition, re-enter the correct existing IIS leaf without inventing a new leaf;
9. when one approved Spec and its validated complete Ready Ticket Set exist for the current Increment, report completion and STOP.

Do not use retry counters, a workflow ledger, persistent controller state, or agent scheduling to implement this loop. It is a planning judgment loop in the current request/context plus durable planning artifacts.

## Reshaping

Treat an Increment as the current best construction hypothesis, not as an immutable product promise.

When the mandate delegates reshaping, Adaptive may split, merge, reorder, replace, shrink, defer, drop unsupported future scope, insert a required durable foundation, or supersede an unconsumed planning unit when fresh evidence makes that shape materially better.

Use [references/04-increment-reshaping.md](references/04-increment-reshaping.md). Preserve current IIS lineage rules and unique work slugs. Never rewrite an immutable Scope revision or a delivered `done` history.

A reshape is not permission to change the user's product intent, Hard Constraints, Non-Goals, or a material trade-off that remains genuinely unresolved.

## Spec and Ticket projection

To Spec and To Tickets remain projection stages, not places to invent product meaning.

- If accurate Spec writing needs a new product decision, return to Ask Matt or Scope Shaper.
- If Ticket decomposition requires strengthening/weakening product meaning, return upstream.
- If the approved result projects cleanly, use standing delegated confirmation rather than asking for a redundant review.
- Keep the canonical `SPEC.md`, Ticket schema, status vocabulary, Behavior/UI authority adoption, Verification flow schema, and validators exactly as current IIS defines them.

## Verification evidence and re-entry

Adaptive Planning may consume a fresh exact result from the separate `ready-ticket-verify` lifecycle as evidence. It does not replace or rewrite the verifier verdict.

Classify the underlying problem using [references/06-verification-triage.md](references/06-verification-triage.md):

- `IMPLEMENTATION_DEFECT`
- `VERIFICATION_MECHANISM_DEFECT`
- `CONTRACT_OVERREACH`
- `CURRENT_INCREMENT_MISMATCH`
- `INCONCLUSIVE`

Never infer `CONTRACT_OVERREACH` merely because a requirement is difficult or expensive. Trace the requirement to current product authority.

If planning authority changes a contract, do not turn an earlier failed result into PASS. Validate the new planning artifacts and require fresh verification in the separate delivery lifecycle.

Adaptive Planning itself does not implement or verify Tickets. A caller may perform those separate actions only when the user's current request independently authorizes them.

## Artifacts

Always preserve the current canonical IIS artifact set. Adaptive does not replace Scope, Work Package, Increment, Behavior/UI authority, Spec, Ticket, or validator outputs.

Additionally keep only the minimal Adaptive companion provenance described in [references/05-artifact-contract.md](references/05-artifact-contract.md):

- `ADAPTIVE-PLANNING-MANDATE.md`
- `ADAPTIVE-PLANNING-TRACE.md` only when material delegated decisions, reshaping, verification triage, or user-return decisions exist

Never inject Adaptive-only metadata into canonical IIS artifacts merely for convenience.

## Hard boundaries

Do not:

- activate Adaptive for Baseline requests;
- edit Baseline skills, templates, or validators as part of Adaptive operation;
- auto-enable adversarial consensus or choose its Challenger;
- bypass a special direct-user-only gate preserved by the Adaptive Delta;
- turn repository/runtime truth into product authority by itself;
- implement outside approved current scope to satisfy a test;
- delete/relax an approved contract merely to produce PASS;
- rewrite delivered history;
- create a controller, scheduler, retry engine, approval state machine, agent registry, generic permission DSL, or evidence database;
- add planning ceremony solely in the name of generic agent control, security, or safety.

Concrete host/tool permission boundaries still apply to the concrete actions they govern, but they do not become IIS product-planning machinery.

## Terminal boundary

Adaptive Planning ends at the same current-Increment product as Baseline IIS: one approved Spec and its validated complete Ready Ticket Set.

Report using [references/07-terminal-report.md](references/07-terminal-report.md), then STOP.

Do not automatically implement, verify, plan the next provisional Increment, or declare the whole product complete merely because current Increment planning completed.
