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
   -> one unmet Ticket AC
   -> same-Ticket bounded Implementation Lead iteration
   -> active-Ticket reobservation
   -> safe independent transition checkpoint when useful
   -> repeat
-> fresh whole-Spec Goal Verification
-> GOAL ACHIEVED only after GOAL VERIFIED
```

The Ralph completion unit is exactly one bounded approved Spec. The architecture intentionally has no controller runtime, persistent Goal state, attempt ledger, gap registry, replay engine, dynamic Ticket queue, persistent trace identity, or initiative fan-in engine.

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

Invariant: a Ticket is a delivery unit, not one implementation attempt. Ralph continues on current unmet ACs and does not mistake a bounded correction for Goal completion.

Closure:

- A newly discovered technical cause inside the existing Ticket Scope remains the same Ticket.
- After implementation, every AC of the active Ticket is freshly reobserved so a regression becomes unfinished work immediately.
- The complete Ticket set is reconsidered before whole-Spec verification.
- Same Ticket + same unmet set + same observation + same correction with unchanged inputs is not progress; the current invocation may end `GOAL OPEN — NO PROGRESS` without declaring the Goal impossible.
- A later invocation starts from the approved Spec, validated Ticket set, and fresh current product state.

Primary contracts/tests:

- `iis-goal-loop/SKILL.md`
- `tests/test_iis_goal_loop_contract.py`
- `tests/test_ralph_semantics_fixture.py`

### 4. Completion Boundary — PROVED

Invariant: only fresh whole-Spec verification can close a supported Goal.

Closure:

- Implementation Lead cannot issue an AC verdict or `VERIFIED`.
- Thin Verification Lead owns one Ticket verdict only.
- Ralph provisional `SATISFIED` is navigation only.
- Transition checkpoints never complete the parent Goal.
- Goal Verification uses fresh admissible current evidence and has the only `GOAL VERIFIED` authority.

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

Invariant: the user chooses product meaning, Scope, completion meaning, and dangerous authority; IIS owns implementation mechanics and iteration.

Closure:

- Ralph does not ask whether to continue between ACs or corrections.
- Endpoint, parser, fallback, retry/backoff, file, algorithm, Worker, internal Ticket mechanics, and ordinary in-Scope correction choice are implementation-owned.
- The user is asked only for a real product decision, Scope/completion-contract change, or dangerous/external authority.
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
- Positional ordinals require re-review when their authored items reorder or change semantically.
- Complete ready Ticket-set planning is required before Ralph starts; partial dynamic Ticket admission is intentionally unsupported.
- Ralph does not persist a Goal-achieved marker or mutate Tickets to become workflow state. A later semantic delta must go through current planning/Ticket review; a new bounded work slug is the clean default for post-completion product deltas when preserving the old work as history matters.
- The structural validator cannot mechanically prove every semantic stale-projection fact without introducing stronger identity/version machinery or rejecting valid decomposition. Current semantic admission is therefore model-mediated under explicit authored authority rules.

Why accepted:

Adding attempt ledgers, Goal state, generations, persistent Ticket-set manifests, semantic hashes, replay state, or controller databases would materially increase stale-state, lifecycle, migration, and user-ceremony costs while not improving the supported bounded Goal's final correctness enough to justify the control-plane complexity.

## Core Freeze Admission

After the stale Spec-to-Ticket semantic-freshness gate and this closure audit pass the repository verification gates, the IIS core is frozen.

A future issue may reopen core architecture only when **all** of the following are true:

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

If any condition is false, the issue is classified as agent competence/evaluation, project-specific implementation, environment/operator condition, an accepted trade-off, or out-of-range capability. It does not justify another IIS core patch.

## Explicit Non-Reasons To Break The Freeze

Do not modify IIS core merely because:

- an agent missed a useful field, endpoint, helper, source location, or root cause;
- a different technical correction would have been better;
- an iteration was inefficient or repeated work after a fresh invocation;
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
