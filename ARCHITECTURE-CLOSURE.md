# IIS Architecture Closure

Status: frozen after the verification gates in this document pass.

This document closes the finite architecture review surface for the current IIS design. It is not a runtime artifact, planning authority, Goal state, or workflow ledger. Its purpose is to stop open-ended core hardening: future review asks whether a reproducible counterexample overturns one of the finite conclusions below, rather than searching indefinitely for any imaginable imperfection.

## Frozen Architecture

The supported architecture is:

```text
Scope Shaper
-> Ask Matt / Behavior Design / UI authority as applicable
-> approved Spec
-> complete ready Ticket set
-> Ralph Goal Fulfillment Loop
   -> current observation
   -> same-Ticket Implementation Lead work as current evidence justifies
   -> every provisionally satisfied all-Independent Ticket runs Ticket Verification, including last/only
      -> Verification Lead owns AC verdicts/aggregate
      -> fresh Verification Runner(s) perform actual observation
      -> qualifying Runner finding may reach Ralph before remaining observation finishes
      -> Ralph may start authorized same-Ticket remediation immediately
   -> mutation overlap invalidates that whole Ticket-verification cycle for progression
   -> quiescence + combined current-project review + fresh full active-Ticket reobservation
   -> a new Verification Lead cycle with fresh Runner(s) must verify the Ticket
   -> repeat
-> after all required Ticket cycles and mutation-capable effects are quiescent, fresh whole-Spec Goal Verification with new fresh Runner(s)
-> GOAL ACHIEVED only after GOAL VERIFIED
```

The Ralph completion unit is exactly one bounded approved Spec. Ralph may overlap
same-Ticket implementation when current evidence and user role-consumption
constraints permit it. Verification observation is separated from verdict
authority: fresh Verification Runner roles observe, while Verification Lead and
Goal Verification Lead adjudicate. A mutation-overlapped Ticket-verification cycle
cannot authorize progression. User-designated role binding and consumption timing
constrain Lead scheduling; unspecified grouping/count/timing/concurrency remains
Lead-owned. The architecture intentionally has no controller runtime, persistent
Goal state, attempt ledger, Runner/Worker registry, assignment queue, evidence
cache, replay engine, dynamic Ticket queue, persistent trace identity, or
initiative fan-in engine.

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
- Current-conversation user role binding, reservation, ordering, and consumption timing constrain Ralph scheduling. A role reserved for later remediation is not consumed for initial fan-out merely to increase concurrency; properties the user did not fix remain implementation-owned.
- Fresh Verification Runner observation may surface a qualifying current contradiction or Ticket-owned implementation/integration/surface/readback absence before the remaining Runner work finishes. Verification Lead forwards the finding; Ralph alone decides whether to start same-Ticket remediation, while Runner and Lead remain non-remediating.
- When a fresh finding materially refines work already active in a same-Ticket implementation invocation, Ralph feeds the finding to that existing invocation first rather than duplicating the work or consuming another reserved role. This is invocation-local useful-work continuity, not persistent defect/AC/file ownership.
- Additional same-Ticket Implementation Lead invocation is allowed only when current evidence justifies materially distinct useful work and concurrent mutation can preserve current user/concurrent changes plus safety/authority boundaries. Concurrency is not progress; serial fallback remains valid when coordination, duplication, or edit-contention cost dominates.
- Every Implementation Lead entry freshly rechecks current authority, source, feasibility, and concurrent changes before mutation. If the approved work explicitly preserves/rebuilds an existing capability, its bounded predecessor implementation is navigation for the currently used product boundary, not inherited product authority.
- Every provisionally satisfied all-Independent Ticket runs Ticket Verification, including the last/only Ticket. Goal Verification does not replace this streaming correction stage.
- Mutation overlapping a Ticket Verification Lead/Runner cycle invalidates the whole cycle for progression. After all current mutation settles, every overlapped Runner/effect must quiesce; Ralph reviews the combined current project, freshly reobserves every AC, and only a new Verification Lead cycle with fresh Runner invocation(s) may verify the Ticket.
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
- A Ticket Verification Lead/Runner cycle overlapped by current-Ralph mutation cannot authorize progression, regardless of an earlier PASS observation or aggregate; after quiescence a fresh full-Ticket reobservation and new Runner cycle are required.
- Ralph provisional `SATISFIED`, implementation checks, test counts, Worker narration, and mutation-overlapped observations are navigation only and never fill final completion evidence.
- Every provisionally satisfied all-Independent Ticket, including the last/only Ticket, must receive Ticket Verification. Its `VERIFIED` result is navigation/progression only and never completes the parent Goal.
- Goal Verification starts only after required Ticket Verification cycles and all mutation-capable effects are quiescent. It uses new fresh Runner invocations, is not another streaming remediation stage, and has the only `GOAL VERIFIED` authority.

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
- Explicit current-conversation Implementation Subagent / Implementation Research Agent / Verification Runner role designations, ordering, reservation, consumption timing, and concurrency constraints remain binding. Model identity alone is not a role, and the same configured model/agent serves another IIS role only under a separate user designation for that role.
- The user is asked only for a real product decision, Scope/completion-contract change, dangerous/external authority, or another decision that the approved contract actually assigns to the user; already supplied execution-role intent is not reopened for ceremony.
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
- Required Independent Ticket Verification is not skipped because replaying an effect would be unsafe or duplicative. Use current authoritative readback when valid, one attributable shared acquisition when authored boundaries genuinely match, serialized Runner observation where needed, or exact `INCONCLUSIVE`/operator-environment-authority gating.
- Same-Ticket implementation overlap is permitted only while concurrent mutation can preserve current user/concurrent changes and every existing safety/authority boundary; unsafe or duplicate-sensitive work remains serial or gated.
- A Verification Lead/Runner cycle that continues safe navigation after mutation starts cannot authorize progression and cannot manufacture additional effect authority.
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
- Same-Ticket concurrent implementation can create stale planned work, edit contention, or wasted Worker effort; every invocation therefore rechecks current source before mutation, Ralph avoids knowingly duplicating materially the same in-flight work, stale work becomes no-op/revised work, and Ralph may serialize whenever overlap is not useful or safe.
- A Verification Lead/Runner cycle overlapped by implementation may continue to surface useful current observations, but its aggregate cannot authorize Ticket progression; Ralph must wait for or host-confirmedly stop every overlapped Runner and wait for any Runner-started product effect to reach its authored terminal/cleanup boundary or become unable to mutate the target before settled reobservation/new authoritative verification. The residual wait plus a fresh cycle are deliberate costs paid for a non-overlapping evidence boundary.
- The last/only all-Independent Ticket now pays a Ticket Verification cycle before whole-Spec Goal Verification. That duplicate-observation cost is intentional because Ticket Verification is the streaming correction engine; effect cost is mitigated with current readback, valid shared acquisition, serialization, or `INCONCLUSIVE`, not by deleting the feedback stage.
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

The user-directed evolution does **not** change product authority, Ticket Scope,
AC/Verification denominators, verdict authority, `GOAL VERIFIED` authority, or the
requirement for fresh current evidence. Verification observation uses fresh Runner
leaves while Verification Lead / Goal Verification Lead alone adjudicate verdicts.
Runner reports are not votes, and user-designated role binding/consumption timing is
preserved rather than inferred from model identity. The architecture adds no
persistent scheduler, finding queue, assignment ledger, Runner/Worker identity
system, evidence cache, or controller. Any mutation overlapping a Ticket
Verification Lead/Runner cycle invalidates the whole cycle for progression; all
current implementation must settle, every overlapped Runner/effect must quiesce,
Ralph must review the combined current project and freshly reobserve the full active
Ticket, and a new Verification Lead cycle with fresh Runner invocation(s) must run
before the Ticket is treated as verified. Whole-Spec Goal Verification begins only
after all required Ticket cycles and mutation-capable effects are quiescent, and it
uses new fresh Runner invocation(s) as a final non-streaming barrier.

A 2026-08-14 follow-up closes the last/only-Ticket feedback gap exposed by that
streaming generation. The older optimization that skipped Ticket Verification
when Goal Verification followed immediately is no longer valid once Ticket
Verification is the streaming discovery/remediation engine. Every provisionally
satisfied all-Independent Ticket therefore runs Ticket Verification, including the
last or only Ticket. The extra cycle before Goal Verification is an accepted cost;
duplicate-effect cost is reduced with current authoritative readback, valid shared
acquisition, serialized Runner observation, or an exact `INCONCLUSIVE` evidence
limit rather than by skipping the feedback stage.

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
