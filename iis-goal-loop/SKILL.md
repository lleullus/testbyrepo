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
canonical physical directory, against the exact Spec with
`--require-completable`. A nonzero result means the Ralph loop is not admitted.
For an ordinary decomposition/readiness defect, return to the ordinary planning
leaves to repair it; do not invent a Ticket, silently widen an existing Ticket,
or create alternate planning state. When admission fails because a parent Spec
outcome is `Not independently verifiable`, stop before mutation and request only
the completion-contract decision: establish an Independent acceptance path,
approve an Operator-assisted action/readback, or keep the work as an explicit
leaf delivery that does not claim automatic Goal completion.

The Ticket set is discovered only from the approved Spec's canonical sibling
`tickets/` directory and the structural set validator. Do not create a Goal
manifest, run file, controller state, attempt ledger, database, registry, or
persistent queue.

Before any mutation, freshly revalidate the current authority chain. The exact
Spec must still be `Status: approved`. Every Spec-adopted Behavior authority must
resolve from the exact Project Root to the same canonical project-local authority
path, remain readable and `Status: approved`, retain the adopted Scope, and not
conflict with the Spec. Any applicable UI authority must still resolve to the
same canonical target and remain approved, complete, in-scope, and nonconflicting.
A current authority-chain drift is a planning/admission defect, not product
failure; return to the owning planning leaf before mutation instead of silently
adopting the changed meaning.

Also revalidate the current Spec-to-Ticket semantic projection before mutation.
Every ready Ticket's Acceptance Criteria, Scope, Non-Goals, Verification flows,
and applicable Behavior/UI authorities must still be compatible with the current
approved Spec rather than a previously approved meaning at the same work path.
The structural validator closes exact outcome-flow projection fields, but the
Ralph admission must also reject any remaining semantic stale projection that
would require the Ticket to implement, preserve, exclude, or verify a different
product contract. Return that Ticket to ordinary To Tickets review; do not mutate
from stale authority or infer that an unchanged `Status: ready` keeps it current.

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

When one current authored product execution or authoritative readback naturally
decides several AC observations, acquire that shared boundary once and classify
each linked AC separately from the same fresh result. Share an acquisition only
when the authored flows actually use that same trigger/input, relevant state, and
authoritative readback, or when one execution directly produces every required
linked observation. Distinct inputs, states, branches, lifecycle boundaries, or
readbacks remain distinct acquisitions; do not infer equivalence merely because
the ACs concern nearby product behavior. Do not rerun an identical safe effect
merely to manufacture one execution per AC. This is acquisition sharing only: it
creates no combined AC verdict, observation cache, retained evidence, or reusable
currentness. Any product/source mutation after the acquisition invalidates it for
the next working observation.

Prefer reading an already-current authoritative product state or readback over
re-triggering a product effect. Execute a trigger for working observation only
when it is safe local/disposable/repeatable, or when existing exact authority
covers the action, target, readback, cleanup, and non-duplication boundary. Do not
re-run payment, message, deployment, destructive, irreversible, shared-production,
credential-bearing, one-shot, or duplicate-sensitive effects merely to refresh
Ralph navigation. If fresh observation requires such an effect, keep the item
`UNRESOLVED` or request the exact approved operator action. Do not consume a
one-shot Operator-assisted action during provisional observation when the final
Goal Verification can safely use that action/readback once.

If a flow is `Operator-assisted`, request operator involvement only when its
exact approved action and readback are actually needed to continue or complete
verification. The operator supplies the action/readback only; IIS interprets the
contract. A `Not independently verifiable` parent outcome is rejected by Ralph
admission before mutation and never reaches the reconciliation cycle.

### 2. Act On Current In-Scope Evidence

When fresh current evidence shows that implementation is still required inside
the exact active ready Ticket, Ralph may invoke Implementation Lead without
inventing a new Ticket, queue, root-cause registry, or other planning state. The
current observations that justify implementation are navigation only; they do not
add, strengthen, split, or reorder Ticket authority.

An implementation invocation receives only what is currently needed to work
inside that existing Ticket boundary:

- the exact ready Ticket;
- its exact current parent-outcome/AC/Behavior trace;
- the current direct observations relevant to the in-Scope work being attempted;
- current preservation or regression observations when materially relevant; and
- the existing Ticket Scope, Non-Goals, and adopted authorities.

Do not serialize the working observations, turn them into a gap registry, or carry
them across a later invocation as current state.

### 3. Implement The Existing Ticket

Invoke `../implementation-lead/SKILL.md` through the host with the exact ready
Ticket and host-provided invocation-local `Implementation Subagent` roles for the
currently active Ticket. Ralph may have more than one same-Ticket Implementation
Lead invocation active when current evidence justifies additional in-Scope work,
the host supports it, and concurrent mutation can preserve current user/concurrent
changes and all safety/authority boundaries. Serial execution remains a fully
valid fallback. The exact number, timing, and technical allocation of those
invocations are implementation-owned and are not planning or verification
semantics.

Within that exact active Ticket and current Ralph invocation, a role may be
resumed for later materially different work only when its retained context
remains bounded, relevant, and likely to reduce technical rediscovery. If
retained context is noisy, oversized, materially contradicted, no longer relevant,
or likely to cost more than fresh technical rehydration, reinvoke a fresh role
instead. Retained context may shorten technical rediscovery only; every
Implementation Lead entry must freshly revalidate the current
Ticket/Spec/Behavior/UI authority, Project Root, semantic compatibility,
user/concurrent changes, feasibility, and current source before mutation. Prior
feasibility, source facts, implementation narration, or observations never remain
current merely because a role context was resumed or another same-Ticket role is
already active.

If reliable resumption is unavailable or fresh rehydration is preferable under
the bounded-context rule above, reinvoke a fresh role without changing Ralph
semantics. Never resume an implementation role across a Ticket change, entry into
whole-Spec Goal Verification, a user/operator/planning gate,
`GOAL OPEN — NO PROGRESS`, the end of the current Ralph invocation, or a later
Goal-verification return to a Ticket that Ralph had already left. This internal
role exception exists only for this Ralph loop. It is never written to `Worker:`,
Ticket metadata, a sidecar, session registry, capability, assignment ledger, or
durable state. An explicit user request for Implementation Lead outside this loop
continues to require the ordinary user-designated role.

Implementation Lead owns technical diagnosis and implementation choices inside
the Ticket. Do not ask the user which endpoint, parser, fallback, retry policy,
file, algorithm, Worker, technical allocation, or internal correction to use.

A newly discovered technical cause does not create a new Ticket when correcting
it is already within the same Ticket Scope and required to make the same authored
obligations true. Reinvoke the same Ticket as many times as materially different
in-Scope changes are justified by fresh current evidence. A resumed role must
revise or abandon an earlier diagnosis when fresh current evidence contradicts
it; role continuity never authorizes repetition of the same change against
unchanged inputs.

### 4. Converge And Freshly Reobserve The Active Ticket

Individual Implementation Lead results are current implementation information,
not independent evidence. While another authorized same-Ticket product/source
mutation remains in flight, Ralph does not need to stop the useful work merely to
perform a full Ticket reobservation after each individual result. Before Ralph
can treat the Ticket as provisionally satisfied, start a transition-verification
invocation that may authorize leaving it, or enter whole-Spec Goal Verification,
all current-Ralph implementation mutation for the active Ticket must finish.
Ralph then freshly reobserves every AC of the active Ticket at its authored
product/canonical boundaries. A regression in a previously satisfied AC becomes
current unfinished work immediately.

The shared-acquisition rule from step 1 applies to this settled post-mutation
reobservation: one fresh execution/readback may decide several linked AC
observations, but every AC remains separately classified and no observation from
before or during the mutation interval may be reused as current post-mutation
evidence.

When the active Ticket is provisionally satisfied and Ralph is about to leave it
for a different Ticket, use the separate `../verification-lead/SKILL.md` as the
default transition checkpoint when every flow on the active Ticket is
`Independent` and the authored verification can be performed safely without
replaying an expensive, one-shot, destructive, credential-bearing, production,
or duplicate-sensitive effect. `VERIFIED` permits moving to another Ticket only
when no product/source mutation from the current Ralph invocation overlapped that
Verification Lead invocation. `FAILED` returns to the same Ticket;
`INCONCLUSIVE` remains current unfinished work and is handled by correction,
exact operator action, or the authority gate.

When that Verification Lead reports an admissible direct contradiction before
its invocation finishes, Ralph may immediately act on the current observation
under steps 2 and 3 instead of waiting for the verifier to finish every remaining
flow. The Verification Lead may continue other still-safe observations and may
report additional current contradictions; only Ralph decides whether and when to
invoke more same-Ticket implementation. The verifier never dispatches mutation or
remediates product code itself. Any implementation started during the verifier
invocation triggers the mutation-overlap rule below, so that in-flight verifier
can help locate unfinished work but cannot authorize a Ticket transition.

If any current-Ralph product/source mutation begins after a transition
Verification Lead invocation starts, that invocation immediately loses authority
to move Ralph out of the active Ticket. Its still-safe observations may remain
navigation, but Ralph must first let the current Ticket's mutation settle, freshly
reobserve every AC of the active Ticket against the resulting current product,
and then obtain a new fresh Verification Lead invocation before leaving the
Ticket. Do not carry forward earlier PASS rows or an earlier aggregate across
that mutation boundary.

Do not run this checkpoint merely for ceremony when the active Ticket is the last
remaining Ticket and fresh whole-Spec Goal Verification will run immediately, or
when the checkpoint would materially duplicate an unsafe/non-repeatable effect.
In those cases keep the provisional observation as navigation, record the
invocation-local reason for skipping the checkpoint, and rely on final Goal
Verification for completion evidence. Any current-Ralph implementation mutation
must still be finished before whole-Spec Goal Verification begins. A Ticket-level
checkpoint never completes the parent Goal. Do not bypass the thin verifier for
mixed/non-independent flows; those flows stay under Ralph provisional observation
and final Goal Verification.

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
- `GOAL FAILED` must identify the exact failed obligation and current candidate
  Ticket/Verification-flow/AC ownership, or exact `None` when no ready Ticket owns
  the required mutation. Continue the mapped existing Ticket when an in-Scope
  correction exists; `None` returns to ordinary Ticket planning instead of
  widening authority.
- `GOAL INCONCLUSIVE` must identify the exact evidence-limited obligation and the
  same current ownership information. Return to the mapped Ticket only when an
  in-Scope correction can restore the defined observation path; otherwise use the
  exact operator, planning, or user gate below.

No other result completes the Goal.

## Same-Ticket Repetition And No Progress

Do not repeat the same Ticket + materially unchanged current observations + the
same attempted implementation with unchanged inputs. Starting or resuming another
Worker does not turn that repetition into progress. This applies whether the
current Ticket work is serial or overlapping.

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

## Supported Range

This Ralph loop completes exactly one bounded approved Spec and its canonical
sibling Ticket set. `GOAL ACHIEVED` means only that exact Spec Goal is currently
verified. It must never be promoted to completion of a parent Scope Shaper
initiative, sibling Work Package set, release program, or multi-Spec initiative.
For initiative-scale work, complete only the explicitly selected bounded Work
Package/Spec under this loop and report any remaining initiative scope separately;
do not invent fan-in orchestration or silently reduce the user's initiative-level
completion unit to the first finished package.

## Non-Goals

Do not create a controller runtime, background daemon, workflow database,
checkpoint store, persistent gap ID, dispatch queue, Worker/assignment ledger,
attempt ledger, event log, replay engine, claim/capability registry, generic DSL,
or retained evidence capsule for this loop. Concurrent same-Ticket execution is
host invocation behavior, not a stored scheduler. Do not encode project-specific
diagnosis recipes into this skill merely
because an agent once missed a technical clue. Agent investigation quality is an
evaluation/tooling concern unless the IIS contract itself permits false
completion, authority violation, unsafe mutation, or an invalid loop boundary.
