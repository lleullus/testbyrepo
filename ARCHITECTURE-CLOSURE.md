# IIS Architecture Closure

Status: frozen after the verification gates in this document pass.

This document closes the finite architecture review surface for the current IIS design. It is not a runtime artifact, planning authority, Goal state, or workflow ledger. Its purpose is to stop open-ended core hardening: future review asks whether a reproducible counterexample overturns one of the finite conclusions below, rather than searching indefinitely for any imaginable imperfection.

## Frozen Architecture

The supported architecture is:

```text
Scope Shaper
-> Ask Matt / Behavior Design / UI authority as applicable
   -> optional explicit-only Adversarial Planning Consensus when the user requests it and names the exact Challenger
   -> current latest-candidate consensus + final user approval when that gate is active
-> approved Spec
-> complete ready Ticket set
-> Ralph Goal Fulfillment Loop
   -> current observation
   -> default first implementation dispatch uses one Lead / one Subagent unless the user fixes another schedule
   -> ordered Implementation Subagent bindings are reusable precedence, not one-use slots
   -> same-Ticket Implementation Lead work as current evidence or exact user scheduling justifies
   -> earlier all-Independent Tickets that Ralph must leave run Ticket Verification before transition
      -> Verification Lead owns AC verdicts/aggregate
      -> fresh Verification Runner(s) perform actual observation
      -> qualifying Runner finding may reach Ralph before remaining observation finishes
      -> Ralph may start authorized same-Ticket remediation immediately
   -> mutation overlap invalidates that whole Ticket-verification cycle for progression
      -> do not spawn new Runner work merely to finish invalidated old coverage
      -> useful already-active observation may remain navigation; otherwise stop at the next host boundary
   -> after quiescence Ralph performs lightweight integration/authority preflight, not a duplicate full AC acquisition
   -> earlier Independent Ticket -> fresh Ticket Verification; mixed/non-independent Ticket -> Ralph fresh AC reobservation
   -> last/only all-Independent Ticket -> fresh whole-Spec Goal Verification directly unless the user requested a separate Ticket verdict
-> after all required transition checks and mutation-capable effects are quiescent, fresh whole-Spec Goal Verification with new fresh Runner(s)
-> GOAL ACHIEVED only after GOAL VERIFIED
```

The Ralph completion unit is exactly one bounded approved Spec. Ralph may overlap
same-Ticket implementation under exact user scheduling, or under Lead-owned
scheduling when current evidence and the useful-work tradeoff justify it. Exact
user-authored role binding, reusable ordering, reservation, one-shot/usage limits,
consumption timing, and concurrency timing constrain Lead scheduling; only
properties the user left unspecified remain Lead-owned. Live scheduling updates are
event-driven: no role repeatedly rereads the whole conversation to prove freshness,
and repair changes future duties rather than replaying already-completed mutation.
Verification observation is separated from verdict authority: fresh Verification
Runner roles observe, while Verification Lead and Goal Verification Lead
adjudicate. Mutation or another material evidence/currentness/attribution/used-role
authority delta invalidates the affected verification cycle; unrelated future
scheduling changes do not. The architecture intentionally has no controller
runtime, persistent Goal state, attempt ledger, Runner/Worker registry, assignment
queue, evidence cache, replay engine, dynamic Ticket queue, persistent trace
identity, or initiative fan-in engine.

## Classification Meanings

- `PROVED`: the current authored contracts plus regression coverage close the architecture failure class when those contracts are faithfully followed.
- `ACCEPTED TRADE-OFF`: a real limitation remains, but removing it would cost more in state, complexity, ceremony, or authority risk than the supported Goal requires. The limitation is not a reason to patch core again.
- `OUT OF SUPPORTED RANGE`: IIS does not claim this completion capability. The architecture must prevent narrower success from being mislabeled as completion of that unsupported unit.

## Finite Failure-Class Closure

### 1. Goal Authority — PROVED

Invariant: the exact approved Spec is the Goal completion authority; current product/canonical observation outranks implementation narration, Ticket status, tests, and historical execution results.

Closure:

- Planning produces one approved Spec with current-final-evaluable normative obligations.
- Ticket completion, implementation completion, passing tests, partial improvement, and one Ticket `VERIFIED` cannot complete the parent Goal.
- Goal Verification freshly evaluates every Spec Verification Expectation plus the remaining Global Contract obligations.
- Only all-PASS `GOAL VERIFIED` permits user-facing `GOAL ACHIEVED`.
- Current Behavior/UI authority-chain drift blocks Goal admission or final verification instead of silently changing the Goal denominator.

Primary contracts/tests:

- `matt/skills/to-spec/SKILL.md`
- `iis-goal-loop/SKILL.md`
- `goal-verification-lead/SKILL.md`
- `tests/test_goal_verification_lead_contract.py`
- `tests/test_iis_goal_loop_contract.py`

### 2. Ticket Ownership And Spec Projection — PROVED

Invariant: Ralph may mutate only through a current ready Ticket whose Scope/Non-Goals/AC/Verification/Behavior/UI projection remains compatible with the current approved Spec.

Closure:

- `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` are current positional locators, not durable identities.
- The structural validator closes path/status, ordinal ranges, exact disposition/surface/external-condition combinations, conditional-boundary projection, and declared Behavior-authority adoption.
- To Tickets owns semantic projection review and requires a semantically edited mapped item to return the Ticket to `draft` and be reviewed again.
- Ralph independently revalidates current Spec-to-Ticket semantic compatibility before mutation. An unchanged `Status: ready` is not sufficient when the Ticket still represents a previously approved meaning at the same work path.
- If current Goal Verification finds an unmet obligation with no ready Ticket owner, Ralph returns to ordinary Ticket planning instead of widening a Ticket.

Deliberate structural-validator boundary:

The validator does **not** decide semantic equivalence of prose fields such as a refined Ticket trigger or acceptance boundary. Exact string equality would reject valid solution-independent decomposition, as demonstrated by active examples. Semantic stale-projection detection therefore remains an authored planning/Ralph admission responsibility. A future model occasionally missing that semantic fact is an agent-quality/evaluation issue unless the authored contract itself permits stale mutation.

Primary contracts/tests:

- `matt/skills/to-tickets/SKILL.md`
- `matt/skills/to-tickets/validate_ticket.py`
- `iis-goal-loop/SKILL.md`
- `tests/test_ticket_validator.py`
- `tests/test_iis_goal_loop_contract.py`

### 3. Ralph Repetition And Regression Recovery — PROVED

Invariant: a Ticket is a delivery unit, not one implementation attempt. Ralph owns
same-Ticket iteration and invocation timing while the authored Ticket remains the
fixed delivery authority; implementation overlap never substitutes for fresh
post-mutation observation or final verification.

Closure:

- A newly discovered technical cause inside the existing Ticket Scope remains the same Ticket.
- Current-conversation user role binding, reusable ordering, reservation, explicit one-shot/usage/rotation conditions, consumption timing, and concurrency timing constrain Ralph scheduling. A role reserved for later remediation is not consumed for initial fan-out merely to increase concurrency; properties the user did not fix remain implementation-owned.
- Ordered Implementation Subagent bindings are reusable precedence, not one-use slots. Every new dispatch reapplies the authored order from the top; a returned invocation is eligible again unless the user actually ended its eligibility. Retained-context reuse is a separate optimization, so stale context causes a fresh invocation of the same higher-priority binding rather than automatic advancement to the next binding.
- The default first implementation dispatch is one Lead / one Subagent when the user did not fix another initial schedule. A maximum-concurrency increase or another available binding is capacity, not an immediate-overlap instruction.
- Fresh Verification Runner observation may surface a qualifying current contradiction or Ticket-owned implementation/integration/surface/readback absence before the remaining Runner work finishes. Verification Lead forwards the finding; Ralph alone decides whether to start same-Ticket remediation, while Runner and Lead remain non-remediating.
- When a fresh finding materially refines work already active in a same-Ticket implementation invocation, Ralph feeds the finding to that existing invocation first rather than duplicating the work or consuming another reserved role. This is invocation-local useful-work continuity, not persistent defect/AC/file ownership.
- Under Lead-owned scheduling, an additional same-Ticket Implementation Lead invocation requires materially distinct useful work and a positive overlap tradeoff. An exact user-authored immediate-overlap instruction overrides only the default wait and Lead-owned efficiency preference; it does not widen Ticket Scope or product/dangerous authority.
- Scheduling repair is prospective: product-authorized mutation produced by an otherwise eligible implementation binding at the wrong authored order/timing remains current product state and is not rolled back, ceremonially repeated, or reassigned merely to reconstruct preferred history. This does not preserve Scope-exceeding, wrong-role, unauthorized-dangerous-effect, or user-rejected mutation. Ralph reobserves current state and dispatches only genuinely unfinished work under the current authored order.
- An observed scheduling delta is sent once, delta-only, to affected active roles: changed scheduling fact, effective boundary, and unchanged Ticket/Scope/AC/Behavior/UI/user intent. Unaffected roles receive no update and no full conversation/history is resent.
- Every Implementation Lead entry freshly rechecks current authority, source, feasibility, and concurrent changes before mutation. Its implementation-stage product checks are minimum focused liveness/integration checks for changed or integration-affected routes, not a rehearsal of the complete independent browser/state/lifecycle/AC matrix.
- For a settled all-`Independent` Ticket, Ralph performs a lightweight integration/authority preflight rather than a duplicate full-AC acquisition. Verification Lead is the first settled full-AC observer when Ralph must leave that Ticket; mixed/non-independent Tickets retain Ralph fresh AC reobservation because Ticket Verification cannot adjudicate those flows.
- An earlier all-`Independent` Ticket that Ralph must leave runs Ticket Verification before transition. A last/only all-`Independent` Ticket goes directly to fresh whole-Spec Goal Verification after quiescence/lightweight preflight unless the user explicitly requested a separate Ticket verdict; Goal Verification remains the first settled independent full observer and reports exact Ticket/flow/AC ownership on non-PASS.
- Mutation overlapping a Ticket Verification Lead/Runner cycle invalidates the whole cycle for progression. An unrelated scheduling change does not. After invalidation, no new Runner assignment exists merely to finish the old roster/coverage; already-active observation continues only for a materially distinct current correction or exact user-requested continuation, otherwise stop is requested. After quiescence Ralph follows the appropriate fresh observer path rather than forcing both Ralph full-AC reobservation and a new Ticket Verification cycle.
- A prospective Runner withdrawal/future-assignment change does not retroactively discard attributable evidence obtained while the Runner was validly admitted unless the user rejects that prior observation, the Runner was never eligible, or product/source currentness, coverage, attribution, target/effect safety, or other evidence meaning changed.
- One endpoint/representation/transport/readback failure establishes only that boundary. A dependency-wide conclusion requires closure of currently known materially relevant contract-admitted alternatives; an alternate may diagnose reachability or candidate integration work but cannot silently satisfy an exact authored representation unless the approved contract permits equivalence. A known usable representation that the current product fails to support is candidate same-Ticket product/integration work.
- A bounded Runner assignment decomposes observation only; it never defines or narrows authored verification coverage. Caller preference cannot remove a required boundary or make a surrogate surface equivalent.
- A decision not to attempt a required boundary is an evidence limit, not evidence of dependency unavailability. Safety/authority limits leave that obligation unresolved or `INCONCLUSIVE` unless the approved contract itself admits a sufficient current readback or equivalent surface.
- `GOAL INCONCLUSIVE` ends only its Goal Verification invocation. Before `GOAL OPEN — NO PROGRESS`, Ralph closes every currently known bounded evidence/correction path; the first failed endpoint/tool/readback does not exhaust a path.
- A later invocation starts from the approved Spec, validated Ticket set, and fresh current product state.

Primary contracts/tests:

- `iis-goal-loop/SKILL.md`
- `tests/test_iis_goal_loop_contract.py`
- `tests/test_ralph_semantics_fixture.py`

### 4. Completion Boundary — PROVED

Invariant: only fresh whole-Spec verification can close a supported Goal.

Closure:

- Implementation Lead cannot issue an AC verdict or `VERIFIED`.
- Verification Runner performs fresh bounded observation only. Verification Lead owns Ticket AC verdicts/aggregate; Goal Verification Lead owns whole-Spec row verdicts/aggregate and is the only leaf that may return `GOAL VERIFIED`.
- Runner reports are never votes. Neither Lead may derive a verdict by majority, consensus, model agreement, or counting Runner labels; conflicting raw observations are resolved against the bounded authoritative boundary or remain `INCONCLUSIVE`.
- Disposable verification targets must yield attributable raw authoritative readback before cleanup. If only Runner narration remains after the target is gone, that narration cannot supply `PASS`.
- A Ticket Verification Lead/Runner cycle overlapped by current-Ralph mutation cannot authorize progression, regardless of an earlier PASS observation or aggregate. After quiescence the stale cycle is never reused; Ralph follows the single appropriate fresh observer path for the Ticket's position/disposition.
- Ralph provisional `SATISFIED`, lightweight post-mutation preflight, implementation checks, test counts, Worker narration, and mutation-overlapped observations are navigation only and never fill final completion evidence.
- An earlier all-Independent Ticket that Ralph must leave receives Ticket Verification and its `VERIFIED` result is navigation/progression only. The last/only all-Independent Ticket may skip that separate verdict because Goal Verification immediately provides the first settled independent full observation; this does not weaken whole-Spec completion authority.
- Goal Verification starts only after every earlier required Ticket transition check and all mutation-capable effects are quiescent. It uses new fresh Runner invocations, is not another streaming remediation stage, and has the only `GOAL VERIFIED` authority.

Primary contracts/tests:

- `implementation-lead/SKILL.md`
- `verification-lead/SKILL.md`
- `goal-verification-lead/SKILL.md`
- `tests/test_goal_verification_lead_contract.py`
- `implementation-lead/tests/contract/test_skill_contract.py`
- `verification-lead/tests/test_contract.py`

### 5. Failure And Inconclusive Routing — PROVED

Invariant: a non-PASS Goal result returns to current authorized ownership or an exact gate; it never creates authority by inference.

Closure:

- Final `FAIL`/`INCONCLUSIVE` identifies the exact obligation and current candidate Ticket/Verification-flow/AC ownership, or exact `None`.
- A mapped in-Scope correction returns to the same existing Ticket.
- `None` returns to ordinary Ticket planning rather than widening Scope.
- Operator evidence limits produce the exact operator action/readback gate.
- Product/scope/completion-contract changes return to the user-owned planning decision boundary.

Primary contracts/tests:

- `goal-verification-lead/SKILL.md`
- `iis-goal-loop/SKILL.md`
- `tests/test_goal_verification_lead_contract.py`
- `tests/test_iis_goal_loop_contract.py`

### 6. User Authority Boundary — PROVED

Invariant: the user chooses product meaning, Scope, completion meaning, dangerous authority, and any explicit execution-role binding/consumption constraints they choose to supply; IIS owns only the implementation/orchestration mechanics the user left unspecified.

Closure:

- Ralph does not ask whether to continue between ACs or corrections.
- Endpoint, parser, fallback, retry/backoff, file, algorithm, internal Ticket mechanics, and ordinary in-Scope correction choice remain implementation-owned unless the approved product contract already makes one normative.
- Explicit current-conversation Adversarial Planning Challenger / Implementation Subagent / Implementation Research Agent / Verification Runner role designations and the user's authored ordering, reusable precedence, reservation, one-shot/usage/rotation, exact consumption timing, and concurrency timing remain binding. Model identity alone is not a role, and the same configured model/agent serves another IIS role only under a separate user designation for that role.
- Exact user-authored implementation timing outranks Lead-owned efficiency preference. Lead tradeoff judgment applies only to scheduling properties the user left open; it is not authority to silently serialize or reorder an exact current instruction. If exact immediate overlap cannot be executed as authored, Ralph returns the exact concrete `ORCHESTRATION CONFLICT`; efficiency/coordination preference alone is never a conflict reason.
- Live orchestration reconciliation is event-driven. No Lead or subordinate repeatedly rereads the full user conversation merely to prove currentness; when an actual new delta arrives, only the affected scheduling delta is applied. Each affected active role receives one concise delta-only update and unrelated roles receive none. If the host knows a newer direction exists but cannot observe enough content, only the affected new dispatch/mutation/progression blocks.
- The user is asked only for a real product decision, Scope/completion-contract change, dangerous/external authority, an explicitly requested Intent Anchor confirmation before adversarial review, or another decision that the approved contract actually assigns to the user; already supplied execution-role intent is not reopened for ceremony.
- Operator-assisted paths delegate action/readback only; the operator does not interpret ACs or supply verdicts.

Primary contracts/tests:

- `matt/skills/ask-matt/SKILL.md`
- `iis-goal-loop/SKILL.md`
- `iis-workflow/SKILL.md`
- `tests/test_iis_goal_loop_contract.py`

### 7. Safety And External Effects — PROVED

Invariant: fresh observation must not manufacture evidence by replaying unauthorized or duplicate-sensitive effects.

Closure:

- Ralph prefers an already-current authoritative state/readback over re-triggering a product effect.
- Working observation does not replay payment, message, deployment, destructive, irreversible, credential-bearing, shared-production, one-shot, or duplicate-sensitive effects merely for navigation.
- When an earlier all-Independent Ticket requires Ticket Verification before Ralph leaves it, effect cost does not waive that transition check: use current authoritative readback when valid, one attributable shared acquisition when authored boundaries genuinely match, serialized Runner observation where needed, or exact `INCONCLUSIVE`/operator-environment-authority gating. A last/only all-Independent Ticket still receives fresh independent observation through Goal Verification rather than paying a second Ticket-level cycle first.
- Same-Ticket implementation overlap is permitted only while concurrent mutation can preserve current user/concurrent changes and every existing safety/authority boundary; unsafe or duplicate-sensitive work remains serial or gated unless the user has already supplied exact authority for the effect itself.
- A Verification Lead/Runner cycle invalidated by mutation cannot authorize progression or manufacture additional effect authority. Do not create new old-cycle Runner work after invalidation; already-active navigation continues only for distinct correction value or exact user-requested continuation, while already-started effects still reach their authored cleanup/terminal boundary.
- One endpoint/representation failure does not prove dependency-wide unavailability; only bounded contract-admitted/current-product alternatives are considered, with no arbitrary fallback hunting.
- Goal Verification treats a fresh current read as fresh evidence when the contract permits it and re-triggers only when the approved contract and exact safety authority require it.
- Operator-assisted effects preserve exact action, target, readback, cleanup, and non-duplication boundaries.

Primary contracts/tests:

- `iis-goal-loop/SKILL.md`
- `goal-verification-lead/SKILL.md`
- `verification-lead/SKILL.md`
- `tests/test_iis_goal_loop_contract.py`
- `tests/test_goal_verification_lead_contract.py`
- `verification-lead/tests/pilot/test_representative_pilots.py`

### 8. Routing And Completion Unit — PROVED For Bounded Spec; Initiative Fan-In OUT OF SUPPORTED RANGE

Invariant: explicit leaf intent remains leaf intent; one bounded Spec success is never promoted to a larger completion unit.

Closure:

- Explicit planning, one-Ticket implementation, one-Ticket verification, and explicit whole-Spec verification routes keep their own terminal boundaries.
- An explicit To Spec request does not withdraw or bypass an active user-requested adversarial-consensus gate. To Spec owns the direct admission: exact Challenger binding, confirmed Intent Anchor, current latest-candidate consensus, and post-consensus final integrated user approval are required while that gate remains active.
- The adversarial planning gate is explicit-only and model-auto-invocation-disabled. It adds no ordinary-path Challenger call; after consensus, Behavior/UI authority and the integrated shared understanding may receive their final approval in one user response.
- Broad end-to-end bounded product completion enters Ralph only after ordinary planning has produced the approved Spec and validated complete ready Ticket set.
- Scope Shaper retains initiative-scale entry precedence.
- Ralph completes exactly one bounded approved Spec.
- A Work Package `GOAL ACHIEVED` cannot be promoted to parent initiative, sibling Work Packages, multi-Spec release, or program completion.

Out of supported range:

- automatic multi-Spec/initiative fan-in completion.

This unsupported range is deliberate. Do not add an initiative controller or durable fan-in state unless the user explicitly reopens the architecture for that new capability.

Primary contracts/tests:

- `iis-workflow/SKILL.md`
- `iis-goal-loop/SKILL.md`
- `tests/test_iis_entry_routing_contract.py`
- `tests/test_iis_goal_loop_contract.py`

### 9. State, Restart, And Historical Efficiency — ACCEPTED TRADE-OFF

Invariant: correctness is reconstructed from current planning authority and current product state rather than persisted orchestration history.

Accepted limitations:

- No durable attempt history means a later invocation may rediscover or retry a technical correction.
- `NO PROGRESS` is invocation-local and does not prove Goal impossibility.
- Same-Ticket concurrent implementation can create stale planned work, edit contention, or wasted Worker effort. Every invocation therefore rechecks current source before mutation and stale work becomes no-op/revised work. When scheduling is left to Ralph, it avoids knowingly duplicating materially the same in-flight work and may serialize when overlap is not useful. When the user fixed exact immediate overlap, that Lead-owned efficiency preference does not override the instruction; only an actual Scope/role/authority impossibility remains a blocking boundary.
- Event-driven live reconciliation deliberately gives up repeated proof-of-currentness checks. The accepted benefit is lower context noise and less instruction drift: no role repeatedly rereads the full conversation, and only an actually observed scheduling delta is propagated to affected future work.
- Ordered reusable bindings may cause the same configured implementation role to be invoked repeatedly across distinct corrections. That is intentional; one-use behavior exists only when the user authored it. Persistent usage counters or slot ledgers are rejected because they would convert conversational precedence into stale orchestration state.
- Prospective scheduling repair accepts that a historically misassigned but authorized mutation may remain in the current product. The architecture pays for fresh reobservation of the resulting product, not ceremonial rollback/replay through the preferred role, because replay would add mutation, context, and verification churn without improving current product authority.
- A Verification Lead/Runner cycle overlapped by implementation may still surface useful current observations, but its aggregate cannot authorize Ticket progression. The efficiency rule stops creating new old-cycle assignments after invalidation and requests stop for already-active observation that has no distinct correction value; already-started effects still reach their authored terminal/cleanup boundary. This may delay discovery of a non-distinct defect until the fresh authoritative cycle, but avoids paying known-stale broad coverage twice.
- Settled all-Independent success paths intentionally use one full observer per transition boundary: Ralph performs only lightweight integration/authority preflight, an earlier Ticket uses Ticket Verification, and the last/only Ticket uses Goal Verification directly unless the user requested a separate Ticket verdict. The accepted risk is that a defect Ralph could have found in a redundant pre-verifier full scan is instead found by the verifier; the benefit is removal of an entire duplicate browser/runtime/persistence acquisition without weakening verdict authority.
- Implementation Lead intentionally limits product checks to changed/integration-affected gross liveness rather than pre-running the full independent browser/viewport/state/lifecycle/AC matrix. Some defects therefore move to the independent verifier that already owns complete coverage; this is accepted because duplicate full-matrix execution adds context and runtime cost without adding independent verdict authority.
- A prospective Runner withdrawal does not invalidate already attributable evidence solely to make historical roster use match future scheduling. This may preserve evidence from a Runner that will no longer receive work, but only while the observation remains current, attributable, safe, and not explicitly rejected by the user.
- Bounded evidence/correction closure before `NO PROGRESS` may spend additional investigation time on already-known contract-admitted paths. The search remains bounded to current authority/product/predecessor evidence rather than becoming arbitrary endpoint discovery or a persistent path registry.
- Positional ordinals require re-review when their authored items reorder or change semantically.
- Complete ready Ticket-set planning is required before Ralph starts; partial dynamic Ticket admission is intentionally unsupported.
- Ralph does not persist a Goal-achieved marker or mutate Tickets to become workflow state. A later semantic delta must go through current planning/Ticket review; a new bounded work slug is the clean default for post-completion product deltas when preserving the old work as history matters.
- The structural validator cannot mechanically prove every semantic stale-projection fact without introducing stronger identity/version machinery or rejecting valid decomposition. Current semantic admission is therefore model-mediated under explicit authored authority rules.

Why accepted:

The streaming overlap trades some invocation duplication and concurrent-edit risk for a shorter useful-work critical path while preserving a settled fresh-verification barrier. Ralph does not add a scheduler database, dispatch ledger, Worker identity system, or persistent finding queue to manage that overlap. Adding attempt ledgers, Goal state, generations, persistent Ticket-set manifests, semantic hashes, replay state, or controller databases would materially increase stale-state, lifecycle, migration, and user-ceremony costs while not improving the supported bounded Goal's final correctness enough to justify the control-plane complexity.

## Recorded User-Directed Architecture Evolution

On 2026-08-13 the user explicitly chose to evolve the supported Ralph execution
model from a strictly serial implementation/reobservation/verification cadence to
bounded same-Ticket streaming remediation. This is an intentional architecture
generation change, not a faithful-contract counterexample and not a change
admitted through either contract-preserving optimization lane below. It changes
when implementation may run: fresh verification observation may surface a
qualifying direct contradiction or concrete current Ticket-owned
implementation/integration/surface/readback absence before the remaining
observation work finishes; Ralph may start current authorized same-Ticket
implementation immediately, and additional same-Ticket implementation may overlap
when current evidence, useful work already in flight, user role-consumption
constraints, host capability, preservation, safety, and authority boundaries permit
it.

The user-directed evolution did **not** change product authority, Ticket Scope,
AC/Verification denominators, verdict authority, `GOAL VERIFIED` authority, or the
requirement for fresh current evidence. Verification observation used fresh Runner
leaves while Verification Lead / Goal Verification Lead alone adjudicated verdicts.
Runner reports were not votes, and user-designated role binding/consumption timing
was preserved rather than inferred from model identity. The architecture added no
persistent scheduler, finding queue, assignment ledger, Runner/Worker identity
system, evidence cache, or controller. At that generation, mutation overlap was
followed by a combined-project review, Ralph full active-Ticket reobservation, and a
new Ticket Verification cycle after quiescence. The later efficiency generation
below supersedes only that redundant observer sequence; mutation-invalidated
progression authority and the fresh independent barrier remain unchanged.

A 2026-08-14 follow-up then required Ticket Verification even for the last/only
all-Independent Ticket before Goal Verification. That historical generation bought
an extra streaming feedback cycle at the cost of a duplicate settled observation.
The later efficiency generation below supersedes that last/only extra cycle: earlier
Tickets still verify before Ralph leaves them, while the last/only Independent
Ticket uses fresh Goal Verification as its first settled independent full observer.

The same follow-up preserves explicit user role binding and consumption timing
through Ralph, so a verification-designated role cannot be consumed as
implementation research and a role reserved for later remediation is not silently
spent on initial fan-out. Model identity alone never changes that binding.

It also tightens evidence convergence: `GOAL INCONCLUSIVE` ends only the current
final-verification invocation; Ralph must close currently known bounded
contract-admitted evidence/correction paths before `NO PROGRESS`, one failed
endpoint/representation does not establish dependency-wide unavailability, and an
explicitly preserved predecessor is bounded navigation rather than inherited
product authority. Runner reports carry attributable raw readback rather than
vote-like verdict authority, host-known required work still in flight is an
unexhausted path, and `User Action: None` cannot hand executable due-now work back
to the user. A returned or host-confirmed stopped/unproductive invocation clears
only that liveness blocker; Ralph still closes any remaining bounded evidence or
correction path before a terminal result.

A further 2026-08-14 user-directed generation change makes user-intent retention
and low-context orchestration load explicit architecture priorities. The user
rejected safety hardening that repeatedly re-injects the full conversation,
reopens already supplied execution intent, or adds agent calls merely to prove
freshness, because that extra context can itself cause instruction drift. Live
orchestration is therefore event-driven: absent an actually observed new user or
canonical delta, execution continues without a new orchestration checkpoint. When
a delta arrives, each affected active role receives exactly one concise delta-only
update with the changed scheduling fact/effective boundary and unchanged Ticket,
Scope, AC, Behavior/UI, and user intent; unaffected roles receive nothing. If the
host knows a newer direction exists but cannot observe enough of it, only the
affected new dispatch, mutation, or progression decision blocks.

The same generation fixes ordered implementation-role semantics. User-authored
ordering is reusable precedence rather than implicit one-shot slot consumption.
Every new same-Ticket dispatch starts from the top of the still-eligible order; a
returned role is eligible again, and stale retained context causes fresh
rehydration of that same binding rather than automatic promotion of the next one.
One-shot use, usage limits, rotation, reservation, or retirement exist only when
the user actually authored them. The default first implementation dispatch remains
one Lead / one Subagent when timing is unspecified, while maximum concurrency is
capacity rather than a command to fan out. Conversely, an exact user-authored
immediate-overlap instruction outranks Ralph's Lead-owned efficiency preference;
that preference applies only to timing/concurrency the user left open. If exact
immediate overlap cannot be executed because of a concrete binding/work/mutation/
authority conflict, Ralph returns that exact `ORCHESTRATION CONFLICT` rather than
silently serializing or substituting a different role.

Scheduling repair is prospective under this generation. If an otherwise eligible
implementation binding already completed product-authorized mutation at the wrong
authored order or timing, IIS preserves that current product result, reobserves it,
and reapplies the correct order only to genuinely unfinished future work. It does
not roll back or replay the same correction through the preferred role merely to
repair history. Scope-exceeding, wrong-role, unauthorized-dangerous-effect, or
user-rejected mutation is not protected by this rule. This avoids extra mutation,
repeated context loading, and unnecessary invalidation of later verification.

Planning receives the same intent-preserving treatment. Adversarial Planning
Consensus remains explicit-only and requires the exact user-designated Challenger;
model auto-invocation is disabled. An active gate cannot be bypassed by an explicit
To Spec request: current latest-candidate consensus and the post-consensus final
integrated user approval are required until the user explicitly withdraws the
gate. Intent Anchor confirmation is one deliberate pre-review approval; routine
repository-disclosure approval is not added. A second and final user response may
jointly approve the consensus-post shared understanding and any completed new or
changed Behavior/UI authority. No mandatory live-Challenger smoke or generic
multi-agent council is added to ordinary IIS execution.

Verification invalidation is also narrowed to evidence meaning rather than mere
orchestration-file movement. Product/source mutation and changes that materially
affect authored coverage, currentness, attribution, target/effect safety, or the
validity of a Runner's role at the time of observation invalidate affected evidence.
A prospective Runner withdrawal or future-assignment change does not retroactively
discard evidence obtained while that Runner was validly admitted when the evidence
remains current, attributable, safe, and not explicitly rejected by the user.
Future implementation-role ordering/concurrency changes or other unrelated
scheduling changes likewise do not discard attributable evidence by themselves.

Rejected alternatives for this generation are: implicit one-use role slots;
persistent role-usage counters or scheduling ledgers; repeated whole-conversation
freshness rereads by every Lead/Subagent/Runner; extra agents used only as
freshness/safety sentinels; mandatory live adversarial smoke without an exact user
designation; historical rollback/replay merely to reconstruct preferred dispatch
order; silently serializing an exact user-fixed overlap for Lead convenience; and
invalidating already-valid evidence solely to make future Runner scheduling look
historically consistent. These alternatives increase context, state, ceremony, or
rework without better preserving the user's current bounded Goal.

A subsequent 2026-08-14 efficiency generation removes duplicate observation work
that contributed no additional verdict authority. After mutation quiescence an
all-`Independent` Ticket no longer pays both a Ralph full-AC acquisition and a
Verification Lead full-AC acquisition: Ralph performs a lightweight integration/
authority preflight and the verifier is the first settled full observer. Mixed or
non-independent Tickets retain Ralph fresh AC reobservation because no Ticket
Verification Lead can adjudicate those flows.

The same efficiency generation restores direct final verification for the last or
only all-`Independent` Ticket. Earlier Independent Tickets still obtain Ticket
Verification before Ralph leaves them, preserving the transition/regression barrier.
For the last/only Ticket, fresh Goal Verification immediately supplies the first
settled independent full observation and exact non-PASS Ticket/flow/AC candidate
ownership, so a preceding Ticket Verification cycle is omitted unless the user
explicitly requested that separate Ticket-level verdict. Whole-Spec `GOAL VERIFIED`
authority and final fresh evidence are unchanged.

Mutation-invalidated streaming verification is also bounded by usefulness. The
invalidated cycle never receives new Runner assignments merely to complete its old
roster/coverage. Already-active observation continues only when it can materially
surface a distinct current correction or the user explicitly required continuation;
otherwise stop is requested at the next host-controllable boundary. Already-started
product effects still reach terminal/cleanup. After quiescence Ralph selects exactly
one required fresh observer path rather than stacking Ralph full-AC observation and
Ticket Verification again.

Implementation Lead likewise stops short of rehearsing independent verification.
It checks changed/integration-affected routes for minimum gross product liveness and
obvious broken integration, while the complete browser/viewport/state/lifecycle/AC
matrix remains with Verification Lead or Goal Verification Lead. The accepted
tradeoff is that some defects appear first in the independent verifier instead of a
redundant pre-verification scan; the benefit is lower wall time, lower context load,
and fewer duplicate browser/effect acquisitions without moving verdict authority.

Rejected efficiency alternatives are impacted-only final verification, evidence
caching across mutation, verifier-context reuse as evidence, skipping earlier Ticket
transition verification, weakening whole-Spec Goal Verification, or adding a
scheduler/ledger to optimize dispatch. The admitted change removes only duplicate
success-path acquisition/cycles and low-value invalidated work while preserving the
fresh authoritative observer that actually decides progression.

The five-condition Core Freeze Admission below governs issue-driven hardening of
a frozen architecture generation. An explicit user instruction to deliberately
replace the supported architecture may start a new generation, but it must be
recorded as such, preserve the user's accepted authority/safety boundaries, pass
the repository verification gates, and then re-freeze. This recorded evolution
must not be cited as permission for ordinary latency complaints or agent-quality
variance to bypass the freeze.

## Contract-Preserving Execution Optimization Boundary

The freeze protects IIS authority, evidence, completion, state, and orchestration semantics; it does not require deliberately repeating the same admissible invocation-local work. A proposed optimization is **not** an architecture reopen only when it fits exactly one lane below and satisfies every condition in that lane. If any condition fails, treat the proposal as an architecture change and apply the ordinary Core Freeze Admission rules below.

**Lane A — Monotonic Deduplication Refinement**

This lane permits removing duplicate acquisition of an already-authorized current boundary while preserving every authored obligation. All of the following are required:

- one execution or authoritative readback already directly supplies the current observation needed by every linked obligation;
- every AC or verification obligation remains separately classified or verdict-bearing; no denominator row disappears, merges, or inherits another row's verdict;
- distinct inputs, relevant states, branches, lifecycle boundaries, or authoritative readbacks remain distinct acquisitions;
- any product/source mutation invalidates the prior acquisition for the next current observation;
- the governed expensive acquisition count is weakly reduced or unchanged; the refinement never adds a compensating replay merely to support the optimization;
- no persistent cache, retained evidence, identity system, ledger, runtime, controller, or durable state is introduced; and
- when the sharing conditions do not hold, execution falls back to the ordinary separate fresh acquisition with unchanged semantics.

Shared fresh observation acquisition in the Ralph loop is the canonical admitted example: it shares only one genuinely identical fresh boundary and never shares an AC verdict or post-mutation currentness.

**Lane B — Conditional Invocation-Local Locality Optimization**

This lane permits retaining bounded technical working context only to reduce cold rediscovery. It is not claimed to be a monotonic wall-clock improvement. All of the following are required:

- Goal, Spec, Ticket, Behavior/UI authority, observation, verification, and completion semantics remain unchanged;
- retained context is current-invocation technical working memory only and never authority, evidence, feasibility, current-source truth, or completion state;
- every mutation entry still freshly revalidates the complete current authority/source/feasibility boundary required by the owning contract;
- reuse is limited to the same active Ticket and is discarded across Ticket change, whole-Spec verification, user/operator/planning gates, `GOAL OPEN — NO PROGRESS`, or invocation end;
- if retained context is noisy, oversized, materially contradicted, no longer relevant, or likely to cost more than fresh technical rehydration, the host uses a fresh role instead without changing semantics;
- if reliable resumption is unavailable, the baseline fresh invocation remains fully supported;
- no persistent session registry, cache, identity system, ledger, runtime, controller, or durable workflow state is introduced; and
- regression coverage proves the freshness/disposal boundaries while the performance claim remains limited to the structurally removed cold rediscovery unless separate telemetry establishes more.

Bounded Same-Ticket Implementation Subagent continuation is the canonical admitted example. Its benefit is fewer cold technical rediscoveries when reuse is actually cheaper; its escape hatch preserves the original fresh-invocation baseline when reuse is not beneficial.

This boundary is deliberately narrow. It does **not** admit impacted-only AC reobservation, verifier-context reuse, evidence caching, semantic hashes, persistent attempt history, workflow/session managers, controller state, or any optimization that changes who owns a decision, what must be freshly observed, or what can complete a Goal.

## Core Freeze Admission

After the stale Spec-to-Ticket semantic-freshness gate and this closure audit pass the repository verification gates, the IIS core is frozen.

A contract-preserving execution optimization admitted by the boundary above does not reopen architecture semantics. Any other future issue may reopen core architecture only when **all** of the following are true:

1. **Faithful-contract counterexample** — the problem is reproducible even when the current authored contracts are followed, not merely when an agent overlooks evidence or reasons poorly.
2. **Architecture-general** — it is not a project-, site-, parser-, endpoint-, library-, model-, or environment-specific problem.
3. **Material failure class** — the consequence is at least one of:
   - false `GOAL ACHIEVED`;
   - unauthorized mutation or Scope expansion;
   - dangerous/duplicate external effect;
   - IIS deciding a user-owned product/Scope/authority decision;
   - a valid supported bounded Goal being structurally impossible to complete; or
   - mutation being authorized through the wrong current Ticket or authority.
4. **Invariant repair** — the fix strengthens one of the finite failure classes above rather than encoding a project-specific diagnosis recipe.
5. **Complexity test** — the fix does not introduce a new status taxonomy, persistent state, identity system, ledger, runtime, generic workflow DSL, or controller mechanism unless the user explicitly chooses to reopen the architecture and accepts that trade-off.

If any condition is false and the proposal also fails the Contract-Preserving Execution Optimization Boundary, the issue is classified as agent competence/evaluation, project-specific implementation, environment/operator condition, an accepted trade-off, or out-of-range capability. It does not justify another IIS core patch.

## Explicit Non-Reasons To Break The Freeze

Do not modify IIS architecture semantics merely because:

- an agent missed a useful field, endpoint, helper, source location, or root cause;
- a different technical correction would have been better;
- an iteration was inefficient or repeated work after a fresh invocation; inefficiency alone never permits an architecture change, and only an optimization that independently passes the strict boundary above may reduce that duplication;
- a project needs a parser, retry, fallback, storage, or deployment-specific rule;
- a Ticket could have been decomposed more elegantly while the approved outcome remains completable;
- an unsupported initiative fan-in capability would be convenient;
- a test or operational pilot reveals agent-quality variance without a faithful-contract architecture counterexample.

## Verification Gates For Freeze

The freeze is valid only after all of these pass on the same working tree:

```text
python3 -B run_tests.py
python3 phase8_removal_census.py --repo-root /home/user01/project/iis-skills --state-root /home/user01/.local/state/opencode --installed-skill-root /home/user01/.codex/skills --config-root /home/user01/.config/opencode
git diff --check
installed iis-workflow/SKILL.md byte-identical to repository iis-workflow/SKILL.md
```

The operational Ralph pilot remains useful empirical evidence, but a model failing to find the best correction is not by itself a reason to break this architecture freeze. The pilot may break the freeze only when it demonstrates a faithful-contract counterexample admitted by the five rules above.
