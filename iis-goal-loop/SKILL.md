---
name: iis-goal-loop
description: Fulfill one exact approved IIS Spec by repeatedly reconciling its complete ready Ticket set against current product behavior until fresh whole-Spec verification passes.
---

# IIS Goal Fulfillment Loop

## Purpose

Complete the user's approved product Goal without turning the user into an IIS
operator. The loop is Ralph-style: keep the approved Spec and ready Ticket set as
the fixed completion contract, observe the current product, act on current
in-Scope evidence inside the active Ticket, allow bounded same-Ticket implementation
overlap when it is useful and safe, converge to a settled current product, and
repeat fresh Ticket/whole-Spec verification until the Goal passes.

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

When the approved Scope/Spec/Ticket explicitly says the current work preserves,
replaces, rebuilds, or migrates an existing product capability, the bounded
predecessor implementation and its currently used product boundaries are relevant
navigation before Ralph concludes that an external dependency is unavailable or
that no in-Scope correction remains. Inspect only the predecessor surfaces needed
to understand the explicitly preserved capability; its implementation details,
policy, schema, fallback strategy, or historical behavior do not become new
product authority unless the approved contract already adopts them. This is not a
license for broad legacy archaeology or for treating any nearby old repository as
a compatibility requirement.

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
re-triggering a product effect. Failure of one endpoint, representation, transport,
tool, or readback establishes only that exact failed boundary. Do not promote it
to dependency-wide unavailability while another materially relevant representation
or authoritative readback is already identified by the approved contract, current
product/config/source, or other current direct evidence. Inspect only those bounded
known alternatives needed for the obligation; do not invent arbitrary fallbacks or
perform broad endpoint discovery. If a known usable representation exists but the
current product does not support or reach it where the Ticket requires the outcome,
treat that as candidate current in-Scope product/integration work rather than an
external-dependency conclusion.

Execute a trigger for working observation only when it is safe
local/disposable/repeatable, or when existing exact authority covers the action,
target, readback, cleanup, and non-duplication boundary. Do not re-run payment,
message, deployment, destructive, irreversible, shared-production,
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
Ticket. When the user supplied current-conversation `Implementation Subagent`
role bindings, reservations, ordering, consumption timing, or concurrency limits,
use those exact constraints; otherwise Ralph may use host-provided invocation-local
`Implementation Subagent` roles for the currently active Ticket. Do not
pre-consume a role the user reserved for a later correction by using it for
initial fan-out, and do not infer another role merely because the same configured
model/agent is available. A separate user designation is required when the same
configured model/agent is to serve a different IIS role. These bindings constrain
current-invocation scheduling only and never become Ticket metadata, a role queue,
or durable worker identity.

Within those user-supplied constraints, Ralph may have more than one same-Ticket
Implementation Lead invocation active when current evidence justifies additional
in-Scope work, the host supports it, and concurrent mutation can preserve current
user/concurrent changes and all safety/authority boundaries. Before adding another
invocation, Ralph accounts for the useful work already known to be in flight and
does not knowingly duplicate materially the same implementation work against
materially the same current evidence merely to increase concurrency. This is
current-invocation scheduling judgment, not an assignment registry or durable
identity rule. Concurrency is not itself progress; do not add an invocation when
its expected coordination, duplication, or edit-contention cost outweighs the
useful critical path overlap. When safe beneficial non-duplicative overlap is
unclear, serial execution is the fallback. Except for properties the user
explicitly fixed, the exact number, timing, and technical allocation of
invocations remain implementation-owned and are not planning or verification
semantics.

When a fresh qualifying observation materially refines, confirms, or contradicts
work already being performed by an active same-Ticket implementation invocation,
and the host can communicate with that invocation, give the observation to that
existing invocation first. Do not open a duplicate invocation or consume another
user-reserved implementation role merely because the finding arrived separately.
The active role must recheck current source and may revise or abandon its current
diagnosis. This is useful-work continuity inside the current invocation, not
defect/AC/file ownership; a materially distinct safe correction may still justify
another invocation under the rules above.

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
continues to require the ordinary user-designated role. Crossing one of those
freshness boundaries does not erase a still-current user role designation: Ralph
may make a new invocation with the same designated role when that remains allowed
by the user's current-conversation conditions, but it must not treat the prior
invocation's technical context or source facts as current.

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
can treat the Ticket as provisionally satisfied, start an authoritative Ticket
Verification cycle, or enter whole-Spec Goal Verification after all required
Ticket cycles, all current-Ralph implementation mutation for the active Ticket
must finish. Any earlier Ticket Verification Lead/Runner cycle that overlapped
that mutation must have quiesced: every Runner must have returned or been
host-confirmed stopped, and every Runner-started product effect must have reached
its authored terminal/cleanup boundary or be established unable to mutate the
target. Do not start the settled fresh reobservation or a new authoritative
verification cycle while an earlier navigation-only Runner or one of its
still-running effects can still change the target being evaluated. Ralph then
reviews the resulting current project as one combined product, confirms that the
settled changes remain inside the Ticket Scope and preserve current user/concurrent
changes without an unresolved integration conflict, and freshly reobserves every
AC of the active Ticket at its authored product/canonical boundaries. A regression
in a previously satisfied AC becomes current unfinished work immediately.

The shared-acquisition rule from step 1 applies to this settled post-mutation
reobservation: one fresh execution/readback may decide several linked AC
observations, but every AC remains separately classified and no observation from
before or during the mutation interval may be reused as current post-mutation
evidence.

When the active Ticket is provisionally satisfied and every authored flow on that
Ticket is `Independent`, invoke the separate `../verification-lead/SKILL.md`
before Ralph treats that Ticket as verified for progression. This requirement
applies to every such Ticket, including the last or only Ticket immediately before
whole-Spec Goal Verification. Goal Verification is not a substitute for this
Ticket-level streaming feedback cycle. Pass through the current-conversation
user-designated `Verification Runner` bindings and consumption conditions when
present; otherwise Verification Lead may use its host-provided invocation-local
Runner roles. `VERIFIED` permits Ralph to leave/close the Ticket for navigation
only when no product/source mutation overlapped that Verification Lead/Runner
cycle. It never completes the parent Goal. `FAILED` returns to the same Ticket;
`INCONCLUSIVE` remains current unfinished work and is handled by correction, an
exact operator/environment/authority action or gate, or another defined evidence
path.

When Verification Lead forwards a qualifying current finding from a fresh Runner
before the cycle finishes, Ralph may immediately act on it under steps 2 and 3
instead of waiting for the remaining Runner assignments or final aggregate. Other
still-safe Runner observations may continue and Verification Lead may forward
additional qualifying findings. Only Ralph decides whether a finding justifies
same-Ticket implementation or belongs at an operator, environment, or authority
gate, and only Ralph decides whether and when to invoke more same-Ticket
implementation within the user's role bindings and consumption conditions. When
a finding materially refines work already in flight, apply step 3's existing-
invocation-first rule instead of consuming another reserved role merely because a
separate Runner found it. Neither Runner nor Verification Lead dispatches mutation
or remediates product code itself.

If any current-Ralph product/source mutation begins after a Ticket Verification
Lead/Runner cycle starts, the whole cycle immediately loses Ticket-progression
authority. Still-safe Runner observations may remain navigation, but before a new
authoritative cycle Ralph must let all current Ticket mutation finish, let every
Runner from the overlapped cycle return or be host-confirmed stopped, and ensure
every Runner-started product effect has reached its authored terminal/cleanup
boundary or is established unable to mutate the target. Ralph then reviews the
combined current project, freshly reobserves every AC of the active Ticket, and
obtains a new Verification Lead cycle with fresh Runner invocations. Do not carry
forward earlier PASS rows or an earlier aggregate across that mutation boundary.

Do not skip required Independent Ticket Verification because the Ticket is the
last/only Ticket or because replaying an expensive, one-shot, destructive,
credential-bearing, production, or duplicate-sensitive effect would be unsafe.
Prefer a fresh read of already-current authoritative state/readback when the
Ticket contract permits it; otherwise coordinate one valid safe acquisition that
can serve genuinely linked observations, serialize relevant Runner work when
needed for attribution/effect safety, or accept `INCONCLUSIVE` with the exact
environment/operator/authority evidence limit when required Independent evidence
cannot be obtained safely. Do not leap directly to Goal Verification to avoid this
cycle. Mixed/non-independent flows remain under Ralph provisional observation and
final Goal Verification because the Independent Ticket Verification route cannot
adjudicate them.

### 5. Reconsider The Complete Ticket Set

When the active Ticket has no currently observed unmet AC, reread the complete
ready Ticket set and current affected product boundaries. Refresh any AC whose
boundary could have changed because of the implementation. Do not blindly rerun
costly unrelated external effects only to manufacture ceremony; final Goal
Verification will independently reobserve the full approved completion contract.

If any current Ticket AC is still unmet, return to step 2.

### 6. Fresh Whole-Spec Verification

Only when the complete Ticket set is provisionally satisfied, every applicable
all-Independent Ticket has a current non-overlapped `VERIFIED` Ticket Verification
cycle, and all implementation/verification mutation-capable effects are quiescent,
invoke `../goal-verification-lead/SKILL.md` with the exact approved Spec, exact
validated Ticket set, exact Project Root, and the current-conversation
user-designated `Verification Runner` bindings/conditions when present.

Implementation reports, candidate recipes, Ticket checkpoints, tests, prior
Runner observations, prior Ticket-verification evidence, and the Ralph working
assessment are navigation hints only. Goal Verification Lead uses new fresh Runner
invocations and obtains whole-Spec completion evidence independently. It is the
quiescent final barrier, not another streaming remediation stage.

- `GOAL VERIFIED` permits `GOAL ACHIEVED`.
- `GOAL FAILED` must identify the exact failed obligation and current candidate
  Ticket/Verification-flow/AC ownership, or exact `None` when no ready Ticket owns
  the required mutation. Continue the mapped existing Ticket when an in-Scope
  correction exists; `None` returns to ordinary Ticket planning instead of
  widening authority.
- `GOAL INCONCLUSIVE` must identify the exact evidence-limited obligation and the
  same current ownership information. It terminates only that Goal Verification
  invocation; it is not Goal completion, product impossibility, dependency-wide
  unavailability, or by itself permission to end Ralph. For each non-PASS
  obligation, Ralph immediately re-enters current bounded resolution: continue the
  mapped existing Ticket when an in-Scope correction can restore the observation
  path; otherwise determine whether another currently known contract-admitted
  authoritative readback/direct observation, exact operator/environment/authority
  action, or required planning/user decision remains. Only the exact owning gate
  may stop further automatic work.

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

Before `GOAL OPEN — NO PROGRESS`, perform an invocation-local bounded
 evidence/correction closure audit over every currently known materially relevant
 path admitted by the approved contract or current product boundary. Confirm that
 there is no materially different in-Scope correction, no safe direct observation
 or authoritative readback still available, no exact operator/environment/authority
 action that could restore evidence, and no required product/scope decision. A
 path is not exhausted merely because its first endpoint, representation,
 transport, tool, or readback failed. Do not turn this audit into broad repository
 discovery, arbitrary endpoint hunting, a durable path registry, or a scheduler.

Only when the current invocation has an open Goal and that bounded audit closes
 every such path may Ralph stop this invocation as `GOAL OPEN — NO PROGRESS`. This
 is a circuit breaker for the current attempt, not a claim that the Goal is
 impossible. A later invocation starts from the same approved Spec, validated
 Ticket set, and fresh current product state.

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

A host-known required Implementation Lead, Implementation Subagent, Verification
Lead, Goal Verification Lead, Verification Runner invocation, or Runner-started
product effect that is still active, waiting for a required current reply, or still
capable of producing authorized current evidence/correction is an unexhausted path.
Ralph may send a concise nonterminal progress update while such work continues, but
must not close the current invocation with a Goal result or `GOAL OPEN — NO
PROGRESS` merely because another required role/effect has not returned yet. This is
invocation-local host awareness only; do not persist a task registry, queue, or
scheduler.

`GOAL OPEN — PROGRESSED` is a nonterminal progress report when authorized automatic
work remains in the current invocation. It is not a handoff of due-now work to the
user. When a report says `User Action: None`, Ralph continues executing every
remaining authorized evidence/correction path in the current invocation; do not
instruct the user to resume later, retry when a dependency recovers, wait for a
background task, or perform an unspecified next step. If automatic progress truly
cannot continue, use only the already-defined exact `GOAL OPEN — NO PROGRESS`,
`USER DECISION REQUIRED`, `OPERATOR ACTION REQUIRED`, planning, environment, or
authority boundary that actually owns the stop.

Keep implementation checks and completion evidence visibly separate in every
progress or public result. Test/build/lint counts may be reported as implementation
checks, but they never fill `Current direct evidence:` or final `Evidence:` and do
not outrank current CLI/product/persistence/rendered/canonical authoritative
readback. If current direct evidence cannot be obtained, report the exact evidence
limit instead of substituting a passing test count or Worker narration.

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
