
# Ready Ticket Verify

## Purpose and authority

Verify one exact IIS Ready Ticket from fresh current product/canonical evidence. The Main verifier always owns the complete authored Verification-flow denominator, every AC verdict, cross-AC reconciliation, Scope/Non-Goals verification, the whole-Ticket verdict, and the caller-facing result.

Optional AC Runtime Auditors are concurrent read-only observers of the Main verifier's single integrated runtime execution. They never replace Main coverage, run a separate verification scenario, trigger product behavior, modify product state/source, or own AC/Ticket verdicts.

Before work, read [references/verify.md](references/verify.md) in full. When `AC Runtime Auditor Count` is greater than `0`, also read [references/ac-runtime-auditors.md](references/ac-runtime-auditors.md) in full.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Verification Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities, and References from the validated Ticket itself. Optional target/report inputs never override the Ticket or current repository/runtime observation.

AC Runtime Auditor Configuration:

```text
AC Runtime Auditor Count: 0 .. <current top-level AC count>
Default: 0 only when no AC runtime audit was requested and no count was supplied
Selection: AUTO_BY_MATERIAL_RISK | EXPLICIT
Default when Count > 0 and no Selection was supplied: AUTO_BY_MATERIAL_RISK
Explicit AC Ordinals: None | <comma-separated unique current AC ordinals>
Default Model: None | <exact caller/user-designated model for selected auditors>
Default Reasoning Depth: None | <exact caller/user-designated depth for selected auditors>
Per-AC Overrides:
- AC Ordinal: <selected ordinal>
  Model: None | <exact caller/user-designated model>
  Reasoning Depth: None | <exact caller/user-designated depth>
```

## Canonical admission gate

Before any product/runtime action, resolve the current discovered `iis-workflow` skill only as the canonical planning-authority locator, follow its current `### To Tickets` route target, and require the adjacent `validate_ticket.py`. Run that current validator against the exact Ticket. Do not copy validator logic into this skill, use a remembered path, or normalize a legacy Ticket locally.

- Validator unavailable or route target unresolved: `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`.
- Validator result is not exact `VALID`: `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`.
- A structural `VALID` result admits the Ticket schema only; Main must still perform the current semantic/authority checks in [references/verify.md](references/verify.md) before scenario authoring.

## Ticket status gate

- Normal first verification input is exact `Status: ready`.
- `draft` or `blocked` does not enter verification; report the exact admission/status problem without issuing AC verdicts.
- `done` is already a terminal delivery marker. Only an explicit caller/user request to re-verify a `done` Ticket may run a diagnostic fresh verification cycle. Diagnostic re-verification does not reopen or rewrite Ticket status.
- A normal `ready` Ticket changes to `done` only after this skill establishes final `VERIFIED` on a stable target and safely performs the targeted status transition.
- `FAILED` or `INCONCLUSIVE` leaves a normal `ready` Ticket at `ready`.

## Main-only scenario ownership

The Main verifier alone authors the integrated verification scenario before any product/runtime action. AC Runtime Auditors do not co-author or pre-approve it.

The integrated scenario is one execution plan containing the Ticket's exact authored Verification flows as distinct scenario blocks. For each flow, preserve the validated Ticket's exact ordered label/value contract without renaming, dropping, merging, or collapsing fields. This includes the current canonical core fields such as `Independent verification required` and `Acceptance surface` plus every authored validator-admitted conditional boundary under its exact label. Keep this authored contract separate from Main's derived execution steps. Do not merge materially distinct flows or split one flow merely for execution convenience.

Before deriving any scenario action, resolve each flow's current `Parent outcome ordinal` against the approved parent Spec and confirm the Ticket flow preserves the parent outcome's disposition, independent-verification requirement, acceptance surface, external condition, and authored conditional boundaries without strengthening, weakening, or borrowing meaning from another outcome. A material projection mismatch is `VERIFICATION NOT STARTED`, not a scenario-repair opportunity.

For every flow, predeclare the evidence and the conditions that will produce:

- `SATISFIED`
- `CONTRADICTED`
- `INCONCLUSIVE`

Do not relax or rewrite those criteria after observing results.

## Scenario report before execution

Before the first product/runtime action, report `VERIFICATION SCENARIO REPORT` to the caller. The report is informational, not an automatic approval ceremony. Continue with safe authorized verification unless the next action genuinely requires caller/operator/external authority.

The report must include:

- exact Ticket and verification-target identity;
- environment and external/operator conditions;
- every authored Verification-flow scenario block with authored-contract trace and derived execution;
- AC coverage matrix, Behavior Authority coverage matrix, and Parent Outcome mapping matrix;
- positive and material counterexample coverage;
- ordering/interruption/persistence/UI/external-effect boundaries when authored;
- authoritative readbacks and evidence-capture points;
- cleanup/terminal conditions;
- selected AC Runtime Auditor count, ACs, selection reasons, and requested bindings;
- any authority-bearing action that cannot proceed automatically.

## Runtime execution and concurrent AC audit

After the scenario report and before the first runtime/product action:

1. Resolve the configured AC Runtime Auditor roster.
2. Start every selected auditor concurrently so each can observe the same Main execution from its initial state onward.
3. Do not silently reduce the requested count, replace an explicit requested binding, or convert missing concurrency into post-hoc review. If the exact requested auditor agent/configuration is successfully started before runtime, binding admission is closed; later self-reported model/depth/runtime metadata or display labels are diagnostic only and cannot require re-audit, downgrade the Ticket verdict, or block `ready -> done`.
4. Confirm each selected auditor has the required same-execution evidence visibility for its assigned AC from initial state through relevant transient events, authoritative readbacks, pre-cleanup evidence, and terminal assessment. Successful start alone is insufficient when indispensable evidence is not observable.
5. If the requested concurrent observer capacity or required evidence visibility cannot be provided, report `AC RUNTIME AUDIT CAPABILITY UNAVAILABLE` before starting the authoritative runtime execution. Do not substitute late/post-hoc review or wave execution.
6. Main then executes the integrated scenario once and owns all product triggers, canonical inspection, runtime actions, evidence capture, and cleanup.
7. Auditors may inspect the same live/readback/evidence surfaces read-only, report material evidence gaps or contradictions while Main is still executing, and return terminal AC-scoped evidence assessments.
8. Main independently checks load-bearing auditor claims and combines them with direct Main observations before any verdict.

Use the current host's native concurrency, communication, lifecycle, and terminal-result mechanisms and standing governance. Do not define or duplicate host-specific transport protocol in this skill.

## Disposition handling

### Independent

Main directly executes the authored trigger or canonical inspection and obtains the authoritative readback. An `Independent verification required: yes` flow cannot be satisfied without fresh attributable independent evidence from the current verification cycle.

### Operator-assisted

Preserve the authored operator-owned acceptance path. Main verifies the product-owned parts and the required operator evidence. Missing operator evidence produces `INCONCLUSIVE`, not an invented product defect.

### Not independently verifiable

Do not create a new verification surface. Confirm the approved absence/reason and only the current evidence the authored disposition permits. Do not claim independently observed product behavior that the contract declares unavailable.

## Evidence and freshness

Runtime/acceptance-surface observation and authoritative readback are load-bearing evidence when the Ticket defines them. Implementation reports, implementation auditors, test names, source shape, mocks, logs, or prior verification are navigation/support only unless the Ticket explicitly makes that exact canonical target the acceptance boundary.

The verification source/config/build target must remain stable for an authoritative Ticket verdict. Authored scenario actions may mutate their disposable/product test state as part of the verification flow, but unrelated source/config/build mutation or target drift during the cycle makes affected evidence stale or unattributable. Do not carry a prior PASS row across such drift; re-establish a stable target and obtain fresh evidence.

## Verdict ownership

Main assigns exactly one flow result to every authored Verification flow and exactly one verdict to every current top-level AC in authored order.

Flow result:

```text
SATISFIED | CONTRADICTED | INCONCLUSIVE
```

AC verdict:

```text
PASS | FAIL | INCONCLUSIVE
```

Whole-Ticket verdict:

```text
VERIFIED      # every AC PASS
FAILED        # one or more AC FAIL
INCONCLUSIVE  # no AC FAIL, but at least one AC INCONCLUSIVE
```

AC Runtime Auditor assessments never become verdicts by vote, majority, model rank, or count. Main resolves material conflicts from current authoritative evidence.

## Terminal `done` transition

For a normal `Status: ready` Ticket, Main may attempt `Status: done` only after:

1. every authored Verification flow has an attributable final result;
2. every current AC is `PASS`;
3. every requested AC Runtime Auditor returned a terminal assessment or the configuration was Count `0`;
4. no unresolved material evidence conflict, authority gate, target drift, or cleanup/terminal-condition gap remains;
5. the verification target remains current and attributable;
6. the exact Ticket is re-read and passes the same current canonical validator again as exact `VALID`;
7. the current parent Spec / Behavior / UI authority and Ticket-to-parent projection checks still hold;
8. the exact Ticket is still the same canonical `Status: ready` contract immediately before the write.

Then perform one guarded targeted replacement of only the top metadata `Status: ready` line with `Status: done` and immediately require the same current canonical validator to return exact `VALID` on the resulting Ticket. Do not modify ACs, Verification flows, Spec, Scope, Behavior/UI authority, or other planning meaning.

Keep `Verification Verdict` separate from `Ticket Progression`. A `VERIFIED` verdict remains the evidence verdict even if the guarded status write or post-write validation fails; in that case report `Ticket Progression: FAILED` and the exact observed status/failure without pretending terminal delivery progression completed.

A diagnostic re-verification of an already `done` Ticket never changes status, even if the diagnostic result is `FAILED` or `INCONCLUSIVE`; report the contradiction and required separate reopen/planning authority instead.

## Safety and non-goals

- Do not remediate implementation during verification.
- Do not edit product source/config/tests to manufacture expected behavior.
- Do not reinterpret missing evidence as success or failure.
- Do not add product observability, test hooks, routes, sessions, ledgers, evidence stores, verifier registries, or workflow runtime merely to make verification easier.
- Safe local execution and read-only canonical inspection need no extra ceremony.
- Credential-bearing, shared/production, payment, message, deployment, destructive, irreversible, one-shot, or duplicate-sensitive actions require existing exact authority; otherwise preserve the authored path and return the correct evidence limit/`INCONCLUSIVE`.
- Do not automatically invoke implementation or IIS planning after a verification result.

## Final report

Report:

```text
READY TICKET VERIFICATION RESULT

Ticket:
Ticket status before verification:
Verification target:
Target stability:

Scenario report:
Executed scenario blocks:
Environment / external conditions:
Cleanup / terminal conditions:

Flow results:
- Flow ordinal / parent outcome:
  AC ordinals:
  Result: SATISFIED | CONTRADICTED | INCONCLUSIVE
  Runtime / canonical observation:
  Authoritative readback:
  Evidence limit:

AC Runtime Auditor Configuration:
Count:
Selection:
Selected ACs:
Requested auditor configuration / spawn admission:
Terminal assessments:

AC results:
- AC ordinal:
  Verdict: PASS | FAIL | INCONCLUSIVE
  Linked flows:
  Main evidence:
  Auditor evidence assessment:
  Remaining uncertainty:

Scope / Non-Goals:
Cross-AC findings:
Implementation-report differences:

Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED
Ticket status after verification:
```
