---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, require a current COMPLETE Ready Ticket heuristic-probe handoff for normal ready verification, semantically check that its authored AC/Verification flow can meaningfully decide the approved product claims, adjudicate every authored Verification flow and AC from fresh verifier-owned evidence, and own the guarded terminal done transition. Execution defaults to DIRECT, and DIRECT is the only currently supported verification topology."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket directly from fresh current product/canonical evidence.

The current Main is the sole verifier. It owns semantic preflight, the complete authored Verification-flow denominator, every AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket verdict and guarded `ready -> done` progression. It does not delegate this verification authority to a child worker.

Before work, read [references/verify.md](references/verify.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Required for normal delivery verification of `Status: ready`:

- Heuristic Probe Result / Evidence: `<current READY TICKET HEURISTIC PROBE RESULT for this exact Ticket/authority/implementation target>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

## Execution topology

Execution defaults to `DIRECT`, and `DIRECT` is the only currently supported verification topology.

- The current Main performs the complete verifier role in this invocation.
- Do not assign this skill, any AC, or any Verification flow to a child verifier and do not create a verifier roster or parallel verification scenarios.
- If the current user explicitly requests `SUBAGENT` verification, return `SUBAGENT VERIFICATION UNSUPPORTED` without issuing AC verdicts. Do not silently run DIRECT instead.
- Do not infer another execution mode from model capability, task difficulty, cost or worker availability and do not silently fall back to another verification topology.
- If the current invocation cannot directly own the caller-facing verifier role, return `DIRECT VERIFIER REQUIRED` without issuing AC verdicts.

## Canonical admission gate

Before any product/runtime action, resolve the currently discovered `iis-workflow` skill only as the canonical planning-authority locator, follow its current `### To Tickets` route target and require the adjacent `validate_ticket.py`. Run that validator against the exact Ticket.

- Unavailable route/validator: `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`.
- Validator result other than exact `VALID`: `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`.
- Structural `VALID` admits schema only; the verifier must still perform semantic, authority, projection and current-target checks in `references/verify.md`.

Before deriving runtime execution, semantically compare every AC and mapped Verification flow against the approved parent/Behavior/UI meaning. Confirm that the authored observation/readback actually decides the material AC obligation rather than only a weaker proxy, and challenge concrete plausible false-positive or false-negative paths when they could change the verdict. If the authored verification contract has a material semantic gap, stop before runtime action and report the exact planning-contract defect without issuing AC verdicts. Do not repair, strengthen or normalize planning meaning inside verification.

## Ticket status gate

- Normal delivery verification input is exact `Status: ready`.
- `draft` or `blocked` does not enter verification and receives no AC verdicts.
- `done` permits only explicit diagnostic re-verification. Diagnostic re-verification never reopens or rewrites status.
- `FAILED` or `INCONCLUSIVE` leaves a normal `ready` Ticket at `ready`.
- A normal `ready` Ticket changes to `done` only after final `VERIFIED` on a stable target and the guarded progression succeeds.

## Required heuristic probe gate

Normal delivery verification of a `ready` Ticket requires one current terminal result from `ready-ticket-heuristic-probe` before verifier product/runtime execution.

Require all of the following:

1. exact same canonical Ticket;
2. `Probe Completion: COMPLETE`;
3. Probe `Authority Snapshot` still matches the current Ticket, Parent Spec and applicable Behavior/UI authorities;
4. Probe target is the same current implementation target the verifier binds;
5. Probe cleanup/terminal state is closed and no material source/config/build/runtime drift occurred after the probe.

Return without AC verdicts when the gate cannot be established:

- missing result: `VERIFICATION NOT STARTED: REQUIRED HEURISTIC PROBE RESULT MISSING`;
- `PARTIAL`, `BLOCKED`, malformed or otherwise non-complete result: `VERIFICATION NOT STARTED: HEURISTIC PROBE GATE INCOMPLETE`;
- stale Ticket/authority/target/cleanup attribution: `VERIFICATION NOT STARTED: HEURISTIC PROBE RESULT STALE`.

Probe findings are navigation/counterexample seeds, not flow or AC verdicts and not automatic implementation defects. `Material Findings: None` is not PASS evidence. Where a finding is material and current, the verifier incorporates it into its own scenario and obtains verifier-owned current evidence. A probe result never satisfies `Independent verification required: yes` by itself.

Explicit diagnostic re-verification of an already `done` Ticket does not require this normal delivery gate unless the current user explicitly asks for a fresh heuristic probe as part of that diagnostic.

## Scenario ownership

The verifier authors one integrated scenario before any product/runtime action. It preserves every authored Verification flow as a distinct normative scenario block and keeps the exact authored label/value contract separate from derived execution steps.

Before deriving execution, resolve each flow's current `Parent outcome ordinal` against the approved parent Spec and preserve disposition, independent-verification requirement, acceptance surface, external condition and every authored conditional boundary without strengthening, weakening or borrowing meaning from another outcome.

For every flow, predeclare the evidence and conditions for:

- `SATISFIED`
- `CONTRADICTED`
- `INCONCLUSIVE`

Do not relax or rewrite those criteria after observing results.

## Scenario report and material turns

Before the first product/runtime action, produce `VERIFICATION SCENARIO REPORT` to the caller as informational output and continue unless a genuine authority/operator condition requires stopping. It is not an approval gate.

Produce `VERIFICATION TURN REPORT` only when target identity, authority mapping, scenario execution, evidence attribution or an expected authoritative readback changes materially enough to affect flow adjudication or safe terminal progression. Routine progress, normal command output and confidence-only updates are not report events.

When unresolved caller/operator/external authority is required, do not create a suspended live workflow. Return the correct `VERIFICATION NOT STARTED`, `INCONCLUSIVE` or terminal progression result with exact evidence limits.

## Disposition handling

### Independent

The verifier directly executes the authored trigger or canonical inspection and obtains fresh attributable authoritative readback. `Independent verification required: yes` cannot be satisfied by implementation narration, source plausibility, test names or prior evidence.

### Operator-assisted

Preserve the authored operator-owned acceptance path. Verify the product-owned portion and only the required operator evidence. Missing operator evidence produces `INCONCLUSIVE`, not an invented product defect.

### Not independently verifiable

Do not create a new verification surface. Confirm the approved absence/reason and only the evidence allowed by the authored disposition.

## Evidence sufficiency

Runtime/acceptance-surface observation and authoritative readback are load-bearing when the Ticket defines them. Implementation reports, source shape, mocks, logs, tests or prior verification are navigation/support only unless the Ticket explicitly makes that exact target the acceptance boundary.

Match evidence to the actual claim:

- **Existence/state:** directly read the exact canonical or product target that decides the claim.
- **Absence/retirement:** define the bounded active-surface universe authorized by the contract and inspect the relevant entrypoints/config/package/runtime/storage surfaces; do not turn a narrow search into an unbounded repository-wide absence claim.
- **Preservation:** establish the current authoritative identity/readback and, when the verification trigger itself could mutate the deciding state, obtain the applicable pre/post evidence rather than inferring preservation from narration.
- **Semantic/qualitative result:** directly compare the source authority and produced result for the required meaning, grounding, causal connection, uncertainty or other authored quality boundary; keywords, test names and plausible source shape do not substitute.
- **Process/history claim:** require process/history evidence only when the approved acceptance contract makes it load-bearing; do not invent a ledger or retained evidence surface to make verification easier.

The source/config/build target must remain stable throughout the authoritative cycle. Unrelated target drift makes affected PASS evidence stale or unattributable and requires fresh applicable observation.

The verifier assigns exactly one result to every authored flow and one verdict to every current top-level AC in authored order.

```text
Flow result: SATISFIED | CONTRADICTED | INCONCLUSIVE
AC verdict: PASS | FAIL | INCONCLUSIVE
Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE
```

- Every AC `PASS` -> `VERIFIED`
- Any AC `FAIL` -> `FAILED`
- Otherwise -> `INCONCLUSIVE`

## Terminal `done` transition

For a normal `Status: ready` Ticket, the verifier may attempt `Status: done` only after:

1. every authored Verification flow has an attributable final result;
2. every current AC is `PASS`;
3. no unresolved material semantic-contract defect, evidence conflict, authority gate, target drift or cleanup/terminal-condition gap remains;
4. the verification target remains current and attributable;
5. the exact Ticket passes the same current canonical validator again as exact `VALID`;
6. current parent Spec / Behavior / UI authority and Ticket-to-parent projection checks still hold; and
7. the exact Ticket is still the same canonical `Status: ready` contract immediately before the write.

Then perform one guarded targeted replacement of only the top metadata `Status: ready` line with `Status: done` and require immediate exact `VALID` post-write validation.

Keep `Verification Verdict` separate from `Ticket Progression`. A `VERIFIED` verdict remains the evidence verdict if the guarded write or post-write validation fails; report `Ticket Progression: FAILED` without pretending delivery progression completed.

## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries or workflow runtime merely to ease verification.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require existing exact authority.
- Do not automatically invoke implementation or IIS planning after the result.
