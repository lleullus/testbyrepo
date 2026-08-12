---
name: iis-goal-loop
description: Fulfill one exact approved IIS Spec by repeatedly reconciling its complete ready Ticket set against current product behavior until fresh whole-Spec verification passes.
---

# IIS Goal Fulfillment Loop

## Purpose

Complete the user's approved product Goal without turning the user into an IIS
operator. The loop is Ralph-style: keep the approved Spec and ready Ticket set as
the fixed completion contract, observe the current product, select one unmet
Acceptance Criterion, implement a bounded correction inside its existing Ticket,
reobserve, and repeat until fresh whole-Spec verification passes.

This skill is not a Controller runtime, workflow engine, state machine, planner,
or persistent process. It owns only the current invocation's orchestration.

## Activation And Inputs

Enter this loop only when there is active user intent to complete the product
Goal, not merely to plan it, inspect it, implement one explicit Ticket, or verify
one explicit Ticket. That intent may be an explicit request to complete an
already approved Spec, or the still-current completion intent carried by the IIS
entry router after the user has approved planning artifacts.

Require all of the following before mutation:

- one exact absolute canonical `Status: approved` Spec;
- the exact current `Project-Root`;
- the canonical sibling Ticket set produced for that Spec; and
- current user intent to complete the approved Goal.

Resolve and run the To Tickets set validator at
`../matt/skills/to-tickets/validate_ticket_set.py`, resolved from this skill's
canonical physical directory, against the exact Spec. A nonzero result means the
Ralph loop is not admitted. Return to the ordinary planning leaves to repair the
approved decomposition; do not invent a Ticket, silently widen an existing
Ticket, or create alternate planning state.

The Ticket set is discovered only from the approved Spec's canonical sibling
`tickets/` directory and the structural set validator. Do not create a Goal
manifest, run file, controller state, attempt ledger, database, registry, or
persistent queue.

## Fixed Goal Contract

The approved Spec remains the product Goal authority. Its Requirements,
Non-Goals, Implementation Constraints, adopted Behavior authorities, applicable
UI authority, and Verification Expectations are not rewritten by this loop.

Each ready Ticket is a delivery unit, not an implementation attempt. A Ticket
remains the same work unit across multiple implementation iterations until its
observable acceptance obligations are satisfied or planning authority must be
reopened.

The Ticket trace is interpreted as follows:

- `Parent outcome ordinal` identifies the current parent-Spec Verification
  Expectation the flow projects.
- `AC ordinals` identify the current Ticket Acceptance Criteria decided by that
  flow.
- `Behavior authority ordinals` identify the current Ticket Behavior authorities
  that supply semantic meaning to that flow.

Behavior is the semantic guardrail; ACs are the observable work queue. A
correction may satisfy an AC only while preserving every applicable mapped
Behavior authority, Ticket Non-Goal, parent-Spec constraint, and applicable UI
authority. These ordinals are positional locators only and never durable
identity.

A root cause, endpoint, parser, retry policy, file, helper, algorithm, or other
implementation mechanism is not part of the Goal denominator unless the approved
Spec already makes that exact mechanism normative.

## Ralph Reconciliation Cycle

Perform the following cycle while current evidence and Scope permit progress.
Do not ask the user whether to continue between iterations.

### 1. Fresh Working Observation

Re-read the exact approved Spec, complete ready Ticket set, mapped Behavior/UI
authorities, and current product/source. Build only an invocation-local working
assessment of the current Ticket ACs from their authored Verification flows and
current authoritative boundaries.

Use only these navigation meanings:

- `SATISFIED`: current direct observation shows the authored expected result;
- `UNSATISFIED`: current direct observation contradicts the authored obligation;
- `UNRESOLVED`: the current defined observation cannot yet establish either.

These navigation meanings are not independent Ticket verdicts, Goal evidence,
or persisted status. Tests, mocks, implementation narration, prior Ticket
verdicts, previous implementation results, and stale observations may help
locate work but do not replace a fresh current product/canonical observation.

If a flow is `Operator-assisted`, request operator involvement only when its
exact approved action and readback are actually needed to continue or complete
verification. The operator supplies the action/readback only; IIS interprets the
contract. A `Not independently verifiable` parent outcome has no completion
evidence path and therefore cannot yield `GOAL ACHIEVED`; return to planning for
an explicit completion-contract decision rather than pretending it passed.

### 2. Select One Unmet AC

Select one current `UNSATISFIED` or actionable `UNRESOLVED` AC whose correction
is already authorized by its exact ready Ticket. Prefer the earliest authored
parent outcome and Ticket/AC order when several choices are otherwise equally
useful. Do not create a root-cause queue or dynamic gap taxonomy.

The selected implementation packet consists only of:

- the exact ready Ticket;
- its exact current parent-outcome/AC/Behavior trace;
- the current direct observation that is not yet satisfied; and
- the existing Ticket Scope, Non-Goals, and adopted authorities.

The current observation is navigation context, not new Ticket authority.

### 3. Implement The Existing Ticket

Invoke `../implementation-lead/SKILL.md` through the host with the exact ready
Ticket and a host-provided invocation-local `Implementation Subagent` role. This
internal role exception exists only for this Ralph loop. It is never written to
`Worker:`, Ticket metadata, a sidecar, registry, capability, or durable state.
An explicit user request for Implementation Lead outside this loop continues to
require the ordinary user-designated role.

Implementation Lead owns technical diagnosis and implementation choices inside
the Ticket. Do not ask the user which endpoint, parser, fallback, retry policy,
file, algorithm, Worker, or internal correction to use.

A newly discovered technical cause does not create a new Ticket when correcting
it is already within the same Ticket Scope and required to make the same ACs
true. Reinvoke the same Ticket as many times as materially different in-Scope
corrections are justified by fresh current evidence.

### 4. Freshly Reobserve The Active Ticket

After every implementation result, freshly reobserve every AC of the active
Ticket at its authored product/canonical boundaries, not only the AC that
motivated the change. A regression in a previously satisfied AC becomes current
unfinished work immediately.

When every flow on the active Ticket is `Independent`, the separate
`../verification-lead/SKILL.md` may be invoked as a fresh independent checkpoint
using the exact Ticket and Project Root. Its `VERIFIED`, `FAILED`, or
`INCONCLUSIVE` result is useful current Ticket evidence but never completes the
parent Goal. Do not bypass that leaf for Operator-assisted or Not-independently-
verifiable flows.

### 5. Reconsider The Complete Ticket Set

When the active Ticket has no currently observed unmet AC, reread the complete
ready Ticket set and current affected product boundaries. Refresh any AC whose
boundary could have changed because of the implementation. Do not blindly rerun
costly unrelated external effects only to manufacture ceremony; final Goal
Verification will independently reobserve the full approved completion contract.

If any current Ticket AC is still unmet, return to step 2.

### 6. Fresh Whole-Spec Verification

Only when the complete Ticket set is provisionally satisfied, invoke
`../goal-verification-lead/SKILL.md` with the exact approved Spec, exact validated
Ticket set, and exact Project Root.

Implementation reports, candidate recipes, Ticket checkpoints, tests, prior
observations, and the Ralph working assessment are navigation hints only. The
Goal Verification Lead obtains fresh completion evidence independently.

- `GOAL VERIFIED` permits `GOAL ACHIEVED`.
- `GOAL FAILED` returns the failed parent outcome(s) to their mapped existing
  Ticket/AC ownership and the loop continues when an in-Scope correction exists.
- `GOAL INCONCLUSIVE` returns to the mapped Ticket when an in-Scope correction can
  restore the defined observation path; otherwise use the exact operator or user
  gate below.

No other result completes the Goal.

## Same-Ticket Repetition And No Progress

Do not repeat the same Ticket + same unmet AC set + same direct observation + same
correction with unchanged inputs. That is not Ralph progress.

Progress within the current invocation means at least one of:

- a fresh product observation changed materially;
- an AC moved toward or into `SATISFIED`;
- a previously hidden in-Scope implementation defect was directly established;
- a materially different in-Scope correction became justified; or
- a bounded Ticket obligation was actually closed without regressing another.

If the current invocation has an open Goal but no materially different in-Scope
correction, new direct evidence path, exact operator action, or product/scope
decision to request, stop this invocation as `GOAL OPEN — NO PROGRESS`. This is a
circuit breaker for the current attempt, not a claim that the Goal is impossible.
A later invocation starts from the same approved Spec, validated Ticket set, and
fresh current product state.

## Planning And Authority Gates

Do not dynamically author a new Ticket inside the loop. If a still-approved Spec
outcome has no valid owning ready Ticket, or the required mutation cannot fit an
existing Ticket without violating its Scope or Non-Goals, the approved
breakdown is defective. Return to the ordinary To Tickets planning leaf and its
normal user review. Do not widen Ticket authority in order to keep the loop
running.

Ask the user only for a real product, scope, completion-contract, or dangerous-
authority decision. Examples include changing the desired outcome, widening
Scope, choosing between incompatible product behaviors, approving deployment,
credential-bearing actions, payment/message effects, destructive actions, or
revising a defective delivery boundary.

Do not ask the user for implementation mechanics, Worker choice, whether to try
another in-Scope correction, whether to rerun safe local observation, or whether
to proceed to the next unfinished AC.

For an exact approved `Operator-assisted` path, report `OPERATOR ACTION REQUIRED`
only with the exact action, environment/target, and authoritative readback the
operator must supply. The operator never supplies the AC or Goal verdict.

## Completion And Public Result

The Goal has only two durable meanings in conversation: open or achieved. Do not
create a persisted Goal status.

Report one of:

```text
GOAL ACHIEVED
Spec: <exact approved Spec>
Evidence: <fresh Goal Verification Lead result summary>
User Action: None
```

```text
GOAL OPEN — PROGRESSED
Spec: <exact approved Spec>
Current unresolved Ticket/AC: <exact current ownership>
Current direct evidence: <fresh observation>
Last bounded action: <what changed>
User Action: None
```

```text
GOAL OPEN — NO PROGRESS
Spec: <exact approved Spec>
Current unresolved Ticket/AC: <exact current ownership>
Current direct evidence: <fresh observation>
Last bounded action: None | <last materially different correction>
User Action: None
```

Or the exact `USER DECISION REQUIRED` / `OPERATOR ACTION REQUIRED` gate with the
single decision/action needed. Never report Ticket readiness, implementation
completion, passing tests, a Ticket checkpoint, partial improvement, or absence
of pending implementation narration as Goal completion.

## Non-Goals

Do not create a controller runtime, background daemon, workflow database,
checkpoint store, persistent gap ID, attempt ledger, event log, replay engine,
claim/capability registry, generic DSL, or retained evidence capsule for this
loop. Do not encode project-specific diagnosis recipes into this skill merely
because an agent once missed a technical clue. Agent investigation quality is an
evaluation/tooling concern unless the IIS contract itself permits false
completion, authority violation, unsafe mutation, or an invalid loop boundary.
