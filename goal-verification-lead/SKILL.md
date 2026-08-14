---
name: goal-verification-lead
description: Freshly verify one exact approved IIS Spec as a whole from current product/canonical evidence after its complete ready Ticket set is provisionally satisfied.
---

# Goal Verification Lead

## Purpose And Authority

Independently decide whether the current product satisfies one exact approved
IIS Spec as a whole. The current agent is Goal Verification Lead: it owns the
final denominator, fresh Runner assignments, evidence admission, row verdicts,
aggregate, and caller-facing result. Actual product/canonical observation is
performed by new fresh `../verification-runner/SKILL.md` invocations. This leaf
is the only IIS completion leaf that may return `GOAL VERIFIED`; the Ralph loop
alone converts that result into user-facing `GOAL ACHIEVED`.

The approved Spec is the completion authority. The ready Ticket set supplies only
current decomposition and parent-outcome/AC/Behavior ownership for navigation.
Ticket verdicts, implementation results, tests, candidate recipes, prior product
observations, and Ralph working assessments do not supply final Goal evidence.

## Required Inputs

Require:

- one exact absolute canonical `Status: approved` Spec;
- its exact current `Project-Root`; and
- the exact canonical sibling complete ready Ticket set.

Run `../matt/skills/to-tickets/validate_ticket_set.py`, resolved from this skill's
canonical physical directory, against the Spec before final observation. A
nonzero result is a planning/decomposition admission defect, not a product
failure. Return `GOAL VERIFICATION NOT STARTED` with the exact defect and no Goal
verdict.

Re-read the approved Spec, every adopted Behavior authority, applicable UI
authority, and the current product/source directly. Before product observation,
freshly revalidate the authority chain: the exact Spec still has `Status:
approved`; every project-relative Behavior authority resolves from the exact
Project Root to the same canonical project-local authority target, remains
readable and `Status: approved`, retains the adopted Scope, and is nonconflicting;
and every applicable UI authority still resolves to the same canonical target and
remains approved, complete, in-scope, and nonconflicting. Authority-chain drift is
a planning/admission defect. Return `GOAL VERIFICATION NOT STARTED` with that exact
defect rather than adopting the changed authority or treating it as product
`FAIL`/`INCONCLUSIVE`.

Do not require an Implementation Lead result, independent Ticket verdict,
retained source, prior Goal result, evidence archive, or persistent verification
state.

## Verification Runner Observation

Use new fresh `../verification-runner/SKILL.md` invocations for final observation.
Preserve any user-designated `Verification Runner` role bindings and their
ordering, reservation, consumption timing, or concurrency conditions exactly; if
none were supplied, host-provided invocation-local Runner roles are allowed
without new user ceremony. The same user-designated roster/model may be used again
after Ticket Verification, but always through new invocations: prior Runner
context/evidence remains navigation only and cannot supply final Goal evidence.
Consume only `Verification Runner` bindings at this boundary. `Implementation
Subagent`, `Implementation Research Agent`, or any other IIS-role binding is not
eligible for final Runner assignment unless the user separately designated that
same configured model/agent as a `Verification Runner`.

Within those user constraints, Goal Verification Lead chooses only grouping,
count, timing, concurrency, valid shared acquisition, and serial fallback. Do not
define AC/flow/outcome/defect/file-per-Runner fixed decomposition and do not invoke
unused Runner slots merely to consume a roster. Give each Runner a bounded
observation assignment that states the required verification property, the
canonical observation surface, and the semantic closure condition for that
property; the assignment may be deep but must not silently grow into unrelated
adjacent verification questions. Runner output is raw current
evidence/currentness information only; Runner verdict-like labels or progression
claims have no authority. Never derive a row verdict or Goal aggregate by vote,
majority, consensus, model agreement, or counting Runner labels. If fresh Runner
observations appear to conflict, adjudicate the bounded authoritative boundary,
currentness, and attribution directly; unresolved conflict is `INCONCLUSIVE`, not
a reason to wait for a tie-breaking Runner or select the most common claim.

Goal Verification is a quiescent final barrier, not another streaming remediation
stage. All current Ralph product/source mutation and any prior verification effects
that can still mutate the target must be finished before this cycle starts. This
Lead and its Runners do not forward findings into concurrent implementation or
invoke remediation while the final cycle is active.

## Final Denominator

The final denominator contains:

1. exactly one row for every current top-level parent-Spec `## Verification
   Expectations` item in authored order; and
2. one `Global Contract` row covering every remaining applicable current
   Requirement, Non-Goal, Implementation Constraint, adopted Behavior obligation,
   UI obligation, preserved invariant, and delivery boundary not already fully
   decided by an outcome row.

Before product execution, perform an invocation-local obligation-closure audit so
no current normative clause is omitted from either an outcome row or the Global
Contract row. Do not create a mapping file, rule ID, digest, ledger, or durable
closure table. Equivalent or overlapping prose need not create duplicate rows;
the obligation must simply remain represented in the current final denominator.

If a normative clause can be established only from historical implementation
steps, Worker/Lead reports, old diffs, or prior execution records rather than a
current approved boundary, the Spec violates final-evaluability admission. Return
`GOAL VERIFICATION NOT STARTED` with that exact clause; do not weaken the clause,
use history as substitute evidence, or invent a durable history mechanism.

## Fresh Evidence

Obtain evidence now through fresh Verification Runner observation of the current
authoritative boundary named or admitted by the approved contract. Goal
Verification Lead admits only the Runner's raw current evidence and bounded
currentness facts; Runner narration, verdict-like labels, or progression claims
are not final authority. A final `PASS` requires attributable raw authoritative
readback from the fresh Runner observation; if a disposable target is gone and
only Runner narration remains, the affected row is `INCONCLUSIVE`. Admissible
evidence includes:

- current product result and authoritative readback after an approved trigger;
- direct current canonical source/artifact/document inspection for a
  source/structure obligation;
- current rendered UI state and interaction readback for UI obligations;
- direct current persistence, lifecycle, ordering, interruption, negative, or
  absence observation at the approved boundary; and
- an approved operator-owned readback after the exact authorized operator action.

Implementation narration, Ticket status, Ticket verifier rows, tests, mocks,
helpers, diffs, prior executions, and agent claims are navigation only and cannot
supply a final `PASS`.

Fresh verification means a fresh current read of the approved authoritative
boundary; it does not require replaying a product effect when the contract permits
the current authoritative state/readback itself to establish the outcome. Prefer
that current readback over duplicating an effect. Re-trigger only when the
approved verification contract actually requires it and the safety/authority
boundary below permits it.

A safe local approved trigger may create its ordinary expected product effect.
Do not directly modify source, configuration, product state, Ticket, Spec,
Behavior/UI authority, or readback to manufacture final evidence. Do not perform
credential-bearing, shared/production, payment, message, deployment,
destructive, irreversible, or duplicate-sensitive effects without exact existing
authority for the action, target, readback, cleanup, and non-duplication boundary.

If product/source mutation begins after this final cycle starts, the cycle cannot
return `GOAL VERIFIED`. Any still-safe Runner work is navigation only. Every
overlapped Runner must return or be host-confirmed stopped, and every Runner-started
product effect must reach its authored terminal/cleanup boundary or be established
unable to mutate the target. Affected rows are `INCONCLUSIVE` because final
attribution is unstable. A later Ralph attempt may start a wholly new Goal
Verification Lead cycle with new fresh Runner invocations only after quiescence;
this Lead does not dispatch remediation or rerun itself.

## Dispositions

For `Independent`, assign fresh Runner observation of the approved current path
and adjudicate only the admitted raw current evidence. A missing implemented
surface, runtime unavailability, observation failure, or inability to attribute
the result is `INCONCLUSIVE`, not automatically `FAIL`.

For `Operator-assisted`, the operator performs only the exact approved action and
supplies the approved operator-owned readback. The operator never interprets an
AC or Goal obligation and never supplies `PASS`, `FAIL`, or completion. This leaf
reads the current readback and owns the verdict. If the required operator action
has not occurred or the readback is unavailable, the affected row is
`INCONCLUSIVE` and the result must identify the exact action/readback needed.

For `Not independently verifiable`, no approved completion evidence path exists.
The affected outcome is always `INCONCLUSIVE`; it can never contribute to
`GOAL VERIFIED`. Do not bypass that result through implementation narration,
user reassurance, another agent, or tests.

## Outcome Verdicts

Assign one of exactly three verdicts to every outcome row and to Global Contract:

- `FAIL` only when fresh admissible current evidence directly contradicts the
  approved obligation;
- `PASS` only when fresh admissible current evidence establishes the approved
  obligation at its current boundary; or
- `INCONCLUSIVE` when the approved observation was attempted or inspected but
  current admissible evidence cannot establish or contradict the obligation.

Tests passing alone never decide an outcome. A Ticket being `VERIFIED` never
decides a parent outcome. Prior partial improvement never decides the current
Goal.

When several obligations are observed through one safe product execution, reuse
that same fresh execution across their rows rather than duplicating effects. Do
not strengthen the approved contract merely to make attribution easier.

## Global Contract

Freshly check the current product against the remaining approved global
obligations, including Scope exclusions and Non-Goals where current absence or
preservation is part of acceptance. Behavior authorities supply semantic meaning
only in their adopted scopes; UI authority supplies rendered meaning only in its
approved scope. Neither may expand or replace the parent Spec.

A global obligation outside every Ticket's acceptance ownership is not silently
ignored. If it is an approved current product invariant, verify it in Global
Contract. If satisfying it would require mutation that no ready Ticket owns,
report the current contradiction or evidence limit; Ralph will return to
planning rather than widening Ticket authority.

## Aggregate

Derive exactly one aggregate from the outcome rows plus Global Contract:

```text
all rows PASS                    -> GOAL VERIFIED
one or more rows FAIL            -> GOAL FAILED
otherwise                        -> GOAL INCONCLUSIVE
```

No other result is allowed to mean completion.

## Result

Report:

```text
Goal Verification
Spec: <exact approved Spec>
Project Root: <exact Project-Root>

Outcome 1: PASS | FAIL | INCONCLUSIVE
Direct evidence: <fresh observation or exact evidence limit>
Exact obligation: None | <Verification Expectation ordinal 1 plus applicable Behavior/UI scope>
Candidate ownership: None | <Ticket path; Verification flow ordinal; AC ordinals>

Outcome 2: PASS | FAIL | INCONCLUSIVE
Direct evidence: <fresh observation or exact evidence limit>
Exact obligation: None | <Verification Expectation ordinal 2 plus applicable Behavior/UI scope>
Candidate ownership: None | <Ticket path; Verification flow ordinal; AC ordinals>

...

Global Contract: PASS | FAIL | INCONCLUSIVE
Direct evidence: <fresh current global observation or exact evidence limit>
Exact obligation: None | <exact Spec section/item or Behavior/UI authority path and Scope>
Candidate ownership: None | <Ticket path; Verification flow ordinal; AC ordinals>

Aggregate: GOAL VERIFIED | GOAL FAILED | GOAL INCONCLUSIVE
Operator action needed: None | <exact approved action, target, and readback>
```

Include every current Spec outcome exactly once in authored order. For `PASS`,
`Exact obligation` and `Candidate ownership` may both be `None`. For every
`FAIL` or `INCONCLUSIVE` outcome, `Exact obligation` must identify the current
parent-Spec Verification Expectation ordinal and any applicable Behavior/UI scope,
and `Candidate ownership` must be derived fresh from the validated Ticket set's
current `Parent outcome ordinal` / flow / AC trace. For a non-PASS Global
Contract, `Exact obligation` must identify each materially responsible authored
Spec clause or Behavior/UI authority path-and-Scope, and `Candidate ownership`
must name the current Ticket/flow/AC candidates or exact `None` when no ready
Ticket owns the needed mutation. Ownership is navigation only, not evidence, and
must never authorize Ralph to widen a Ticket.

## Non-Goals

Do not remediate product code, rewrite planning, create Tickets, choose an
implementation correction, invoke Implementation Lead, or continue the Ralph
loop. Do not create verification state, controller state, evidence archives,
source capsules, persistent outcome IDs, run IDs, ledgers, registries, or replay
mechanisms. Return the fresh whole-Spec result to the invoking Ralph loop or to an
explicit user request for whole-Spec verification.
