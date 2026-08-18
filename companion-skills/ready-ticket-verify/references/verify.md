# Ready Ticket Verification Workflow

## 1. Admission and current authority

Before any runtime/product action:

1. Resolve the current discovered `iis-workflow` skill only as the canonical planning-authority locator. Follow its current `### To Tickets` route target and require the adjacent `validate_ticket.py`. Do not invoke IIS planning, hard-code a remembered validator path, or copy validator rules into this skill.
2. Run that current validator against the exact absolute Ticket path. Continue only when it returns exact `VALID`. If the route/validator is unavailable, return `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`; if validation fails, return `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`. Do not issue AC verdicts or start product/runtime work.
3. After `VALID`, read the exact Ticket and derive its `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities, and References from the Ticket itself. Any caller-supplied candidate target or implementation report is navigation only and cannot override these values.
4. Resolve the parent Spec and referenced Behavior/UI authorities from the validated Ticket. Require the Ticket path, `Project-Root`, parent Spec, blockers, and adopted authorities to remain canonical, current, applicable, and nonconflicting. A current authority contradiction stops verification before scenario authoring or AC verdicts.
5. Enumerate every current top-level AC once in authored order and every authored Verification flow once in authored order.
6. Confirm every AC is linked by current ordinal to at least one Verification flow, every flow links at least one AC, every referenced Behavior ordinal is current, and the authored Behavior Authority set is covered as required by the current canonical contract.
7. Preserve each Verification flow's exact authored product meaning. Do not infer a missing flow, remap ordinals from implementation shape, normalize a legacy flow, or strengthen/relax a decision boundary.
8. Bind the exact current verification target from the validated Ticket plus direct current repository/runtime observation: source/config/build/artifact/runtime checkpoint, actual entrypoint or canonical inspection target, acceptance surface, and authoritative readback. A candidate target from the caller is only a hint and must be rejected or corrected when stale or inconsistent.

Structural `VALID` admits the current Ticket schema only; it never establishes semantic mapping, current target availability, runtime evidence, or verdicts.

Return `VERIFICATION NOT STARTED` without AC verdicts when canonical admission, current authority, Ticket-to-parent projection, or current verification-target binding cannot be established before product execution.

```text
VERIFICATION NOT STARTED
Ticket:
Reason:
AC verdicts: Not issued
```

## 2. Status semantics

Normal first verification requires exact `Status: ready`.

- `draft` / `blocked`: do not start.
- `ready`: authoritative verification may progress to `done` only on final `VERIFIED`.
- `done`: only explicit diagnostic re-verification is allowed. Do not rewrite status or claim to reopen delivery authority.

If the Ticket status or authored contract changes during a normal verification cycle, stop progression. Do not write `done` from a stale contract.

## 3. Verification target stability

Record enough current identity to attribute all evidence to one stable implementation target. Use an existing bounded identity such as current Git revision plus working-tree state, build/artifact identity, canonical document state, or running version/checkpoint. Do not invent a persistent verification ID, digest system, retained-source store, or workflow ledger.

The target source/config/build must remain stable throughout an authoritative cycle. Authored verification triggers may intentionally mutate disposable/product test state, but unrelated implementation/source/config mutation invalidates affected evidence and Ticket progression authority.

If such drift occurs:

- preserve already observed contradictions only when their attribution remains exact and current;
- otherwise classify affected flow evidence as stale/unattributable;
- do not carry a prior PASS across the drift;
- re-establish a stable target and run fresh required observations before `VERIFIED`.

## 4. Main authors the integrated scenario alone

Main converts the authored Verification section into one integrated execution plan. AC Runtime Auditors are not started yet and do not contribute to scenario authoring.

Treat each authored Verification flow as one normative scenario block. Common setup, environment, disposable targets, or cleanup may be coordinated across blocks when that does not change flow meaning, but do not merge materially distinct flows or split a flow around implementation seams.

Before deriving execution steps for a flow, resolve its current `Parent outcome ordinal` against the approved parent Spec and directly confirm the Ticket flow preserves the mapped parent outcome's exact `Disposition`, `Independent verification required`, `Acceptance surface`, `External condition`, and every authored conditional-boundary label/value. Also confirm the Ticket's trigger/inspection target, acceptance boundary, expected observable result, authoritative readback, decision boundary, and mapped Behavior authorities preserve the parent meaning without adding a new precondition or stricter result. A material mismatch returns `VERIFICATION NOT STARTED: TICKET/PARENT PROJECTION MISMATCH`; do not normalize the Ticket or author a compensating scenario.

### Scenario materiality gate

Freeze every authored Verification flow and authored conditional boundary as the mandatory verification denominator before considering discretionary scenario expansion. This gate never permits omission, weakening, merging, or early termination of required flow, boundary, or evidence coverage.

For this gate, derive verification purpose only from the current canonical Ticket contract, its mapped parent outcome, and applicable Behavior/UI authority. Do not substitute broader product intent, implementation preference, or reviewer intuition.

Add a derived positive variation, counterexample, boundary exercise, or extra observation only when it materially tests an authored acceptance/decision boundary or prevents a concrete plausible false verdict or evidence-attribution error. Require an identifiable contract anchor and a plausible failure path. Do not add cases merely because they are theoretically possible, implementation-interesting, or make the scenario appear more exhaustive. If no additional material case exists beyond the authored obligations, add none and continue with the mandatory denominator.

Reject a discretionary expansion when it would invent a new trigger, precondition, Scope, acceptance surface, or stricter/weaker result; require unrelated product mutation; or add complexity/context that materially obscures or destabilizes the core verification. Among remaining purpose-preserving options, prefer the smallest sufficient scenario.

For each block keep the authored contract and Main-derived execution separate:

```text
Scenario Block:
Flow ordinal:

Authored Contract:
  <copy the validated Ticket flow's exact ordered label/value sequence without renaming, dropping, merging, or collapsing any field>
  <preserve every validator-admitted optional boundary under its exact authored label and value>

Derived Execution Plan:
  Setup:
  Runtime / canonical inspection actions:
  Positive case:
  Material counterexamples:
  Evidence capture points:
  Cleanup / terminal condition:
  SATISFIED condition:
  CONTRADICTED condition:
  INCONCLUSIVE condition:
```

Do not replace exact authored labels with convenience aliases such as `Trigger / inspection target` or collapse multiple optional boundaries into one generic field. The current canonical core includes `Independent verification required` and `Acceptance surface`; both must remain visible in the authored contract. Preserve any future validator-admitted authored field as part of that exact contract rather than silently dropping it.

## 5. Coverage matrices and runtime-auditor selection

Build current navigation matrices from the validated authored mapping before execution. They are invocation-local navigation only, not persistent IDs or a copied acceptance schema.

```text
AC Coverage Matrix:
AC 1 -> Flow 1
AC 2 -> Flow 2, 3
...

Behavior Authority Coverage Matrix:
Behavior 1 -> Flow 1, 3
...

Parent Outcome Mapping Matrix:
Flow 1 -> Parent outcome 1
Flow 2 -> Parent outcome 2
...
```

`AC Runtime Auditor Count` may be `0` through the current top-level AC count.

- If no audit was requested and no count was supplied, use `0`.
- Count greater than the AC count is invalid.
- One selected auditor owns exactly one unique current AC ordinal.
- `EXPLICIT`: selected unique ordinals must exactly match the requested Count.
- `AUTO_BY_MATERIAL_RISK`: Main selects exactly Count unique ACs after the complete integrated scenario is authored.

For automatic selection, prefer ACs with greater material risk or observation complexity, such as:

- multiple mapped Verification flows or strong cross-AC coupling;
- ordering, concurrency, retry, duplicate, lifecycle, interruption, persistence, terminal, or identity semantics;
- externally visible/irreversible effects or difficult cleanup;
- operator/external conditions that can create false positive/negative judgments;
- UI interaction or multi-layer authoritative readback;
- weak or easily confused readback/attribution surfaces;
- implementation-time findings that make direct evidence attribution especially important.

Selection changes observation density only. Main still verifies every AC.

## 6. Binding policy

A caller/user may designate a default exact Model and Reasoning Depth for all selected AC Runtime Auditors and may provide exact per-AC overrides. A per-AC override applies only to that selected AC; otherwise the supplied default applies. Preserve every supplied exact binding and do not silently substitute another value.

When neither a default nor an applicable per-AC exact binding was supplied for a selected AC, a current host-provided invocation-local observer role may be used. Model identity alone never grants verdict or broader authority.

Before runtime execution, confirm the host can start the full selected observer Count concurrently with every explicit requested auditor agent/configuration. If the exact requested agent/configuration cannot be started or the full concurrent observer capacity cannot be provided, report the exact configuration/capability problem before the first runtime/product action. Do not silently reduce Count or turn missing observers into post-hoc review. Once an exact requested auditor agent/configuration is successfully started, binding admission is closed: later auditor self-reported model/depth/runtime metadata or display labels are diagnostic only and cannot invalidate the slot, require re-audit, downgrade `VERIFIED`, or block the Ticket `ready -> done` transition.

## 7. Report the scenario before execution

Emit the following before the first runtime/product action:

```text
VERIFICATION SCENARIO REPORT

Ticket:
Ticket status:
Verification target:
Target-stability check:
Environment:
External/operator conditions:

Scenario Blocks:
- <all authored Verification flows in authored order>

AC Coverage Matrix:
- <AC -> flow mapping>
Behavior Authority Coverage Matrix:
- <Behavior authority -> flow mapping>
Parent Outcome Mapping Matrix:
- <flow -> current parent outcome mapping>

Positive / Counterexample Coverage:
Ordering / interruption / persistence / UI / external-effect boundaries:
Authoritative readbacks:
Evidence-capture points:
Cleanup / terminal conditions:

AC Runtime Auditor Count:
Selection: AUTO_BY_MATERIAL_RISK | EXPLICIT
Selected ACs:
Selection reasons:
Requested bindings:

Authority-required actions:
Execution disposition: PROCEED | AUTHORITY REQUIRED | BLOCKED
```

This is a report, not an automatic approval gate. Safe local execution and read-only canonical inspection continue. Pause only for a genuinely authority-bearing action or missing required operator/external condition.

## 8. Start auditors, then Main starts runtime

After the scenario report and immediately before the first product/runtime action:

1. Start every configured AC Runtime Auditor concurrently.
2. Give each auditor the complete Main-authored integrated scenario plus its one assigned AC, mapped flows, applicable authority, expected evidence/readbacks, and the stable verification target.
3. Confirm all required auditors are active/attached before Main performs the first runtime action.
4. For every selected AC, complete the same-execution evidence-visibility preflight from [ac-runtime-auditors.md](ac-runtime-auditors.md): required initial-state, transient-event, authoritative-readback, pre-cleanup evidence, and distinct terminal-result visibility must be available for that exact Main execution. A started but evidence-blind observer does not satisfy requested coverage.
5. If any selected AC lacks required visibility, report `AC RUNTIME AUDIT CAPABILITY UNAVAILABLE` and do not start the authoritative runtime execution. Do not substitute late/post-hoc review or wave execution.
6. Main then executes the integrated scenario. Auditors observe; they do not trigger or replay scenario actions themselves.

A late-started observer that missed required initial-state or earlier runtime evidence does not satisfy the requested AC runtime-audit coverage unless all missed evidence remains directly and unambiguously attributable from the same live execution.

## 9. Main runtime-first execution

Main directly performs the authored product trigger or canonical inspection and directly captures the authoritative readback for every required flow.

Evidence priority when applicable:

1. actual runtime / canonical acceptance-surface observation;
2. authoritative product/canonical readback;
3. rendered UI interaction/readback when UI is the acceptance surface;
4. deterministic fake/controlled environment evidence when the contract permits it;
5. source/diff/unit tests as supporting explanation and regression evidence.

Passing implementation tests does not substitute for a Ticket-authored runtime/UI/provider/canonical readback. Conversely, do not invent runtime for a source/artifact/document/structure claim whose approved acceptance boundary is direct canonical inspection.

Exercise all applicable authored positive and material counterexample cases. Examples include reverse completion ordering, duplicate/repeated observation, interruption, timeout, stale identity, concurrent first use, refresh/reopen, partial external response, retry vs re-observation, Scope-excluded behavior, or user-visible/canonical disagreement — only where the Ticket contract makes them relevant.

## 10. Intermediate auditor findings during Main execution

AC Runtime Auditors may report a material finding while Main is still executing when it can change safe evidence capture or prevent a false verdict. Examples:

- required initial state for the assigned AC was not actually established;
- Main is about to pass the terminal observation point without capturing an authored readback;
- observed identity/order/terminal state conflicts with the assigned AC;
- evidence is not attributable to the declared target or current scenario step;
- a required negative/absence window has not reached its authored terminal condition;
- current evidence for the assigned AC is incomplete even though the scenario is about to move on.

Main owns the response. The auditor does not perform the missing trigger or modify the scenario/runtime itself.

If a bounded extra observation is already inside the authored flow and does not change initial state, trigger meaning, decision boundary, or external authority, Main may capture it and record a `SCENARIO AMENDMENT` note.

If satisfying a finding would require a new product trigger, materially different initial state, stronger/weaker decision boundary, Scope expansion, or new external/destructive authority, do not silently extend the scenario. Report the material amendment/authority problem and rerun the affected flow from a valid fresh state when allowed; otherwise classify it `INCONCLUSIVE`.

## 11. Disposition-specific execution

### Independent

Main must obtain fresh direct evidence from the authored acceptance boundary/readback. `Independent verification required: yes` cannot be closed by implementation narration, tests, prior auditor output, or source plausibility.

### Operator-assisted

Execute the product-owned portion and use only the authored operator-owned action/evidence path for the operator portion. Lack of operator credentials or a naturally occurring external condition is not automatically a product defect. Missing required operator evidence leaves the affected flow/AC `INCONCLUSIVE`.

### Not independently verifiable

Do not invent a fresh surface. Verify the approved absence/reason and only the current canonical facts/evidence that the disposition actually permits. A limited PASS means the authored no-independent-surface contract is not contradicted; it does not claim a nonexistent direct product observation.

## 12. AC Runtime Auditor fan-in

Before final AC verdicts, collect the terminal assessment from every requested AC Runtime Auditor. Main verifies decision-critical auditor claims directly against current evidence.

Auditor assessment categories are advisory evidence classifications, not AC verdicts:

```text
EVIDENCE SUFFICIENT
CONTRADICTION OBSERVED
EVIDENCE INSUFFICIENT
STALE / UNATTRIBUTABLE
```

No vote, majority, model rank, or number of agreeing auditors can override the authored decision boundary or current authoritative evidence.

If an auditor reports a material contradiction or attribution problem, Main directly reopens the exact relevant evidence/readback. If the conflict cannot be resolved on the stable target, the affected AC cannot be PASS.

If a requested auditor disappears or cannot return an attributable terminal assessment after authoritative execution has started, do not silently reduce Count. Main may still report `FAILED` when Main direct evidence already establishes an AC contradiction; otherwise the requested observation coverage is incomplete, so the whole Ticket cannot be `VERIFIED` and is `INCONCLUSIVE`.

## 13. Flow and AC adjudication

For every authored flow assign exactly one result:

- `SATISFIED`: all required observable/readback conditions for that flow's disposition are established and no decision-boundary contradiction remains.
- `CONTRADICTED`: fresh attributable evidence directly violates the authored decision boundary.
- `INCONCLUSIVE`: required evidence/authority/terminal condition/current attribution could not be established without a direct contradiction.

For every top-level AC in authored order:

- `FAIL` if any required mapped flow is `CONTRADICTED` for that AC obligation.
- `PASS` only when all mapped required flow obligations for that AC are `SATISFIED` under their dispositions and applicable boundaries.
- otherwise `INCONCLUSIVE`.

Whole Ticket:

```text
all ACs PASS          -> VERIFIED
any AC FAIL           -> FAILED
otherwise             -> INCONCLUSIVE
```

## 14. Scope, Non-Goals, and cross-AC closure

Before `VERIFIED`, Main directly checks that the executed current product did not introduce or expose forbidden Scope/Non-Goal behavior relevant to the Ticket and that satisfying one AC did not contradict another AC or adopted Behavior/UI authority.

Do not use source search alone when the Ticket defines an observable runtime/user boundary.

## 15. Cleanup and terminal conditions

Complete every authored cleanup, absence window, process stop, disposable-target disposal, and external-effect terminal condition required to attribute the evidence safely.

A still-running duplicate-sensitive effect, incomplete cleanup that can change the target, or unfinished absence/ordering window prevents final `VERIFIED` when it affects the authored decision boundary.

Capture necessary authoritative evidence before disposing of a temporary target. Narration about an already-destroyed target does not replace a missing raw/current readback.

## 16. Terminal status transition

Keep verification verdict and Ticket progression as separate results.

For normal first verification of `Status: ready`:

- `FAILED` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `INCONCLUSIVE` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `VERIFIED` -> attempt terminal progression only through the guarded sequence below.

Before `ready -> done`:

1. Re-read the exact Ticket from disk and require the verification target/source/config/build identity used for the verdict is still current and attributable.
2. Resolve the current canonical To Tickets validator through the same admission path and run it again against the exact Ticket; require exact `VALID`.
3. Re-resolve the current parent Spec and adopted Behavior/UI authorities and require the same Ticket-to-parent projection/currentness checks still hold.
4. Require the Ticket is still the exact canonical `Status: ready` contract that was verified. If any contract/status/path/currentness check changed, do not write `done`; report `Ticket Progression: FAILED` with the exact stale/currentness reason.
5. Perform one guarded targeted replacement of only the top metadata `Status: ready` line with `Status: done`. Reject stale content, concurrent edit, path drift, or ambiguous/multiple status matches rather than broad rewriting.
6. Immediately run the same current canonical validator on the resulting Ticket and require exact `VALID`.

When steps 1-6 succeed, report `Ticket Progression: COMPLETED` and `Ticket Status: done`.

If the status write or post-write validation fails, preserve the already-established `Verification Verdict: VERIFIED` but report `Ticket Progression: FAILED` and the exact observed Ticket status/failure. Do not claim terminal delivery progression succeeded and do not rewrite any AC, Verification flow, Spec, Scope, Behavior/UI authority, or other planning meaning to repair it.

Diagnostic re-verification of `done` never rewrites status and reports `Ticket Progression: NOT APPLICABLE`. A diagnostic `FAILED`/`INCONCLUSIVE` is reported as a current contradiction that requires separate reopen/planning authority.

## 17. No remediation loop

Verification ends with evidence and verdict. Do not automatically edit source, invoke `ready-ticket-implement`, create a follow-up Ticket, reopen planning, or continue to a later Increment. The caller/user decides the next action.
