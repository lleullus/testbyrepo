---
name: ready-ticket-verify
description: "Verify one existing IIS Ready Ticket against a stable current implementation target, adjudicate every authored Verification flow and AC, and own the guarded terminal done transition. The default top-level path assigns the exact Ticket to one delegated verifier worker; DIRECT execution is allowed only when explicitly requested."
---

# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket from fresh current product/canonical evidence.

The verifier worker owns the complete authored Verification-flow denominator, every AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket verdict and guarded `ready -> done` progression. Outer Main owns assignment, current user-instruction handoff, report reception, terminal-result integrity and the caller-facing response; it does not become a second verification authority.

Before work, read [references/verify.md](references/verify.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

## Execution topology

Top-level default execution mode is `SUBAGENT`.

- `SUBAGENT`: Outer Main assigns the exact Ticket to exactly one verifier worker.
- `DIRECT`: Outer Main performs the verifier-worker role only when the user explicitly requests it in the current request.

For `SUBAGENT`:

1. Confirm the current host can start one non-blocking child worker with access to the Project Root, parent-directed messages and a terminal result.
2. Pass the exact Ticket, optional navigation inputs, Additional User Instructions and `Delegated Worker: yes` in one complete assignment.
3. A worker receiving `Delegated Worker: yes` performs verification directly and never delegates this skill again.
4. If the required child/message/result capability is unavailable, report `SUBAGENT CAPABILITY UNAVAILABLE`.
5. Never silently fall back to `DIRECT`.
6. Do not create a verifier roster, split AC ownership across workers, or run multiple independent verification scenarios for one Ticket.

## Canonical admission gate

Before any product/runtime action, resolve the currently discovered `iis-workflow` skill only as the canonical planning-authority locator, follow its current `### To Tickets` route target and require the adjacent `validate_ticket.py`. Run that validator against the exact Ticket.

- Unavailable route/validator: `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`.
- Validator result other than exact `VALID`: `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`.
- Structural `VALID` admits schema only; the verifier worker must still perform semantic, authority, projection and current-target checks in `references/verify.md`.

## Ticket status gate

- Normal first verification input is exact `Status: ready`.
- `draft` or `blocked` does not enter verification and receives no AC verdicts.
- `done` permits only explicit diagnostic re-verification. Diagnostic re-verification never reopens or rewrites status.
- `FAILED` or `INCONCLUSIVE` leaves a normal `ready` Ticket at `ready`.
- A normal `ready` Ticket changes to `done` only after final `VERIFIED` on a stable target and the guarded progression succeeds.

## Scenario ownership

The verifier worker alone authors one integrated scenario before any product/runtime action. It preserves every authored Verification flow as a distinct normative scenario block and keeps the exact authored label/value contract separate from derived execution steps.

Before deriving execution, resolve each flow's current `Parent outcome ordinal` against the approved parent Spec and preserve disposition, independent-verification requirement, acceptance surface, external condition and every authored conditional boundary without strengthening, weakening or borrowing meaning from another outcome.

For every flow, predeclare the evidence and conditions for:

- `SATISFIED`
- `CONTRADICTED`
- `INCONCLUSIVE`

Do not relax or rewrite those criteria after observing results.

## Scenario report and material turns

Before the first product/runtime action, produce `VERIFICATION SCENARIO REPORT`.

- In `SUBAGENT`, send it to the direct parent non-blocking and continue safe authorized verification without waiting for acknowledgement or approval.
- In `DIRECT`, report it to the caller as informational output and continue unless a genuine authority/operator condition requires stopping.

Send `VERIFICATION TURN REPORT` only when target identity, authority mapping, scenario execution, evidence attribution or an expected authoritative readback changes materially enough to affect flow adjudication or safe terminal progression. Routine progress, normal command output and confidence-only updates are not report events.

When unresolved caller/operator/external authority is required, do not create a suspended live workflow. Return the correct `VERIFICATION NOT STARTED`, `INCONCLUSIVE` or terminal progression result with exact evidence limits.

## Disposition handling

### Independent

The verifier worker directly executes the authored trigger or canonical inspection and obtains fresh attributable authoritative readback. `Independent verification required: yes` cannot be satisfied by implementation narration, source plausibility, test names or prior evidence.

### Operator-assisted

Preserve the authored operator-owned acceptance path. Verify the product-owned portion and only the required operator evidence. Missing operator evidence produces `INCONCLUSIVE`, not an invented product defect.

### Not independently verifiable

Do not create a new verification surface. Confirm the approved absence/reason and only the evidence allowed by the authored disposition.

## Evidence and verdicts

Runtime/acceptance-surface observation and authoritative readback are load-bearing when the Ticket defines them. Implementation reports, source shape, mocks, logs, tests or prior verification are navigation/support only unless the Ticket explicitly makes that exact target the acceptance boundary.

The source/config/build target must remain stable throughout the authoritative cycle. Unrelated target drift makes affected PASS evidence stale or unattributable and requires fresh applicable observation.

The verifier worker assigns exactly one result to every authored flow and one verdict to every current top-level AC in authored order.

```text
Flow result: SATISFIED | CONTRADICTED | INCONCLUSIVE
AC verdict: PASS | FAIL | INCONCLUSIVE
Whole Ticket: VERIFIED | FAILED | INCONCLUSIVE
```

- Every AC `PASS` -> `VERIFIED`
- Any AC `FAIL` -> `FAILED`
- Otherwise -> `INCONCLUSIVE`

## Terminal `done` transition

For a normal `Status: ready` Ticket, the verifier worker may attempt `Status: done` only after:

1. every authored Verification flow has an attributable final result;
2. every current AC is `PASS`;
3. no unresolved material evidence conflict, authority gate, target drift or cleanup/terminal-condition gap remains;
4. the verification target remains current and attributable;
5. the exact Ticket passes the same current canonical validator again as exact `VALID`;
6. current parent Spec / Behavior / UI authority and Ticket-to-parent projection checks still hold;
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
