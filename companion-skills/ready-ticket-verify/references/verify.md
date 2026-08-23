# Ready Ticket Verification Workflow

## 1. Direct-first invocation

Execution defaults to `DIRECT`, and `DIRECT` is the only currently supported verification topology. The current Main performs the verifier role for one exact Ticket and does not delegate verification, AC ownership or runtime verification to child workers.

Before verification:

1. Bind the exact Ticket and optional navigation inputs.
2. Confirm this invocation can directly access the Project Root, required product/canonical surfaces and caller-facing result path.
3. Carry current Additional User Instructions without allowing them to silently rewrite the Ticket or approved parent authority.
4. If the current user explicitly requests `SUBAGENT` verification, return `SUBAGENT VERIFICATION UNSUPPORTED` with no AC verdicts. Do not silently switch to DIRECT.
5. If this invocation cannot directly own the verifier role, return `DIRECT VERIFIER REQUIRED` with no AC verdicts.

The verifier emits the informational scenario report before product/runtime action, continues without waiting for approval when execution is authorized, emits material-turn reports only when adjudication can change, and ends with one `READY TICKET VERIFICATION RESULT`.

Do not create a verifier roster, parallel AC verifiers, nested verification workers or an implicit fallback topology inside this skill. Model capability, task difficulty, cost or worker availability never changes the execution topology automatically.

## 2. Admission and current authority

Before any runtime/product action:

1. Resolve the currently discovered `iis-workflow` skill only as the canonical planning-authority locator. Follow its current `### To Tickets` route target and require the adjacent `validate_ticket.py`.
2. Run that validator against the exact absolute Ticket path. Continue only when it returns exact `VALID`.
3. If the route/validator is unavailable, return `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`. If validation fails, return `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`. Do not issue AC verdicts or start product/runtime work.
4. After `VALID`, derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the Ticket itself.
5. Resolve parent Spec and referenced Behavior/UI authorities. Require canonical current paths, applicable authority and no unresolved contradiction.
6. Enumerate every current top-level AC once in authored order and every authored Verification flow once in authored order.
7. Confirm every AC is linked to at least one flow, every flow links at least one AC, and referenced Behavior ordinals remain current.
8. Preserve each flow's exact authored meaning. Do not infer a missing flow, remap ordinals from implementation shape, normalize a legacy flow or strengthen/relax a decision boundary.
9. Bind the exact current verification target from the validated Ticket plus direct repository/runtime observation: source/config/build/artifact/runtime checkpoint, actual entrypoint or canonical inspection target, acceptance surface and authoritative readback.

Caller-supplied candidate targets and implementation reports are navigation only. Structural `VALID` admits schema only; it never establishes semantic correctness, current target availability, runtime evidence or verdicts.

Return without AC verdicts when canonical admission, current authority, Ticket-to-parent projection or current target binding cannot be established.

```text
VERIFICATION NOT STARTED
Ticket:
Reason:
AC verdicts: Not issued
```

## 3. Semantic contract check

Before deriving or executing the runtime scenario, compare every current AC and mapped Verification flow against the approved parent outcome and applicable Behavior/UI meaning. Confirm that the authored observation/readback actually decides the material AC obligation rather than only a weaker proxy. When a concrete plausible false-positive or false-negative path could change the verdict, challenge it before execution.

Do not treat approval, structural `VALID`, ordinal closure, matching wording, tests or implementation narration as proof that the flow is semantically sufficient. Do not invent new requirements or strengthen the approved contract.

If a material semantic gap means the authored verification contract cannot decide the approved claim, stop before product/runtime action and return `VERIFICATION NOT STARTED` with the exact owning contract location, material claim, non-decisive observation or false-verdict path, and `AC verdicts: Not issued`. Verification does not repair that planning defect.

## 4. Status semantics

Normal first verification requires exact `Status: ready`.

- `draft` / `blocked`: do not start.
- `ready`: may progress to `done` only on final `VERIFIED` and successful guarded progression.
- `done`: only explicit diagnostic re-verification is allowed. Do not rewrite status or claim to reopen delivery authority.

If Ticket status or authored contract changes during a normal cycle, stop progression. Do not write `done` from a stale contract.

## 5. Verification target stability

Record enough current identity to attribute all evidence to one stable implementation target. Use an existing bounded identity such as current Git revision plus working-tree state, build/artifact identity, canonical document state or running version/checkpoint. Do not invent a persistent verification ID, retained-source store or workflow ledger.

The target source/config/build must remain stable throughout an authoritative cycle. Authored triggers may intentionally mutate disposable/product test state, but unrelated implementation/source/config mutation invalidates affected evidence and Ticket progression authority.

If target drift occurs:

- preserve already observed contradictions only when attribution remains exact and current;
- otherwise classify affected flow evidence as stale/unattributable;
- do not carry a prior PASS across the drift;
- re-establish a stable target and obtain fresh required observations before `VERIFIED`.

## 6. Integrated scenario ownership

After the semantic contract check finds no material gap that prevents the authored flow from deciding its approved claims, convert the authored Verification section into one integrated execution plan before any product/runtime action.

Treat each authored flow as one normative scenario block. Common setup, environment, disposable targets or cleanup may be coordinated only when flow meaning remains unchanged. Do not merge materially distinct flows or split one flow around implementation seams.

Before deriving execution steps, resolve each flow's `Parent outcome ordinal` against the approved parent Spec and confirm preservation of exact `Disposition`, `Independent verification required`, `Acceptance surface`, `External condition`, every authored conditional boundary, trigger/inspection target, acceptance boundary, expected result, authoritative readback, decision boundary and mapped Behavior authority.

A material projection mismatch returns `VERIFICATION NOT STARTED: TICKET/PARENT PROJECTION MISMATCH`; do not normalize the Ticket or author a compensating scenario.

### Scenario materiality gate

Freeze every authored flow and conditional boundary as the mandatory denominator. This gate never permits omission, weakening, merging or early termination of required coverage.

Add a derived positive variation, counterexample, boundary exercise or observation only when it materially tests an authored decision boundary, closes a concrete false-verdict path or prevents a concrete attribution error. Require a contract anchor and plausible failure path. Do not expand the scenario merely for exhaustiveness.

Reject expansion that invents a new trigger, precondition, Scope, acceptance surface or stricter/weaker result; requires unrelated product mutation; or obscures the core verification. Prefer the smallest sufficient scenario.

For each block keep authored contract and derived execution separate:

```text
Scenario Block:
Flow ordinal:

Authored Contract:
  <copy the validated Ticket flow's exact ordered label/value sequence>
  <preserve every validator-admitted optional boundary under its exact label and value>

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

Do not replace exact authored labels with convenience aliases or silently drop future validator-admitted fields.

## 7. Coverage matrices

Build invocation-local navigation matrices before execution. They are not persistent IDs or copied acceptance schema.

```text
AC Coverage Matrix:
AC 1 -> Flow 1
AC 2 -> Flow 2, 3

Behavior Authority Coverage Matrix:
Behavior 1 -> Flow 1, 3

Parent Outcome Mapping Matrix:
Flow 1 -> Parent outcome 1
Flow 2 -> Parent outcome 2
```

The matrices are navigation aids and do not replace the semantic contract check.

## 8. Scenario report

Before the first product/runtime action, emit:

```text
VERIFICATION SCENARIO REPORT

Ticket:
Execution Mode: DIRECT
Verifier: Main / DIRECT
Ticket status:
Verification target:
Target-stability check:
Environment:
External/operator conditions:
Semantic contract check: <no material gap found | exact blocking defect already returned before execution>

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
Absence-proof boundaries:
Preservation checks:
Cleanup / terminal conditions:
Authority-required actions:
Execution disposition: PROCEED | AUTHORITY REQUIRED | BLOCKED
```

The report is informational, not an approval gate. Continue safe authorized verification when `Execution disposition: PROCEED` without waiting for acknowledgement.

## 9. Evidence sufficiency and execution

The verifier directly performs each authored trigger or canonical inspection and directly captures authoritative readback for every required flow.

Evidence priority when applicable:

1. actual runtime / canonical acceptance-surface observation;
2. authoritative product/canonical readback;
3. rendered UI interaction/readback when UI is the acceptance surface;
4. deterministic fake/controlled-environment evidence when the contract permits it;
5. source/diff/unit tests as supporting explanation and regression evidence.

Passing implementation tests do not substitute for a Ticket-authored runtime/UI/provider/canonical readback. Conversely, do not invent runtime for a source/artifact/document/structure claim whose approved boundary is direct canonical inspection.

### Existence and current-state claims

Directly read the exact canonical/product target that decides the claim. Do not infer existence from a test name, source branch or implementation report when the current state is directly inspectable.

### Absence and retirement claims

Absence evidence must state its bounded universe. Derive that universe from the approved active product surface, Scope, preserved boundaries, entrypoints, package/config/runtime/storage authority and explicit historical exclusions.

Use the smallest set of direct inspection and targeted search needed to cover that universe. Record, as applicable:

```text
Absence claim:
Bounded active-surface universe:
Inspected entrypoints/config/package/runtime/storage surfaces:
Targeted identities/search terms:
Suspicious survivors directly inspected:
Explicit exclusions:
Conclusion:
```

Do not claim “nothing exists in the repository” from one directory, one grep, one config file or deleted-path status. Historical planning artifacts, tests, fixtures or documentation mentions are not active product survivors unless current authority makes them executable/product authority.

### Preservation claims

Establish the current canonical identity and authoritative value that must be preserved. When the authored verification trigger itself executes a mutation-capable path and preservation depends on no change across that action, capture the applicable before/after identity or readback. When the contract asks only for current preserved authority, do not invent historical telemetry merely to prove an unowned process history.

### Semantic and qualitative claims

When the AC requires grounding, causal reasoning, completeness, semantic depth, uncertainty, rendered meaning or another qualitative result, directly compare the approved source authority and produced result. Identify the actual passages/observations that establish the required relationship and the material distinction that prevents a shallow false positive.

Keywords, count checks, test names, schema presence, implementation narration or source plausibility can support but cannot replace semantic adjudication unless the approved contract explicitly makes that exact representation decisive.

### Process/history claims

If the approved contract makes a process step, external action, provider call or retained history itself the acceptance boundary, obtain that authorized evidence. If the contract deliberately makes only current canonical result authoritative, do not create a new run ledger, receipt or observability surface and do not fail the Ticket merely because unrequired history was not retained.

Exercise authored positive and material counterexample cases, including ordering, duplicate, interruption, timeout, stale identity, concurrency, refresh/reopen, partial external response, retry, Scope-excluded behavior or user-visible/canonical disagreement only where the Ticket makes them relevant.

## 10. Material verification turns

Emit a `VERIFICATION TURN REPORT` only when direct evidence creates a material change such as:

- declared target identity no longer matches the observed source/config/build/runtime target;
- current authority or Ticket-to-parent projection changes or becomes contradictory;
- an expected acceptance surface or authoritative readback is unavailable or materially different;
- a semantic-contract assumption becomes false because the observed target reveals that the authored readback is not actually decisive;
- an authored flow needs a bounded scenario amendment to preserve evidence capture without changing product meaning;
- evidence attribution changes a plausible flow result among `SATISFIED`, `CONTRADICTED` and `INCONCLUSIVE`;
- cleanup, terminal window, external/operator condition or guarded progression becomes materially limiting.

```text
VERIFICATION TURN REPORT

Ticket:
Turn:
Scenario block / flow:
Previous assumption:
New attributable evidence:
Material effect on semantic contract, execution or adjudication:
Affected AC / authority / target:
Safe work continuing:
Caller/operator action needed: NONE | USER/OPERATOR AUTHORITY
```

A bounded observation already inside the authored flow may be recorded as `SCENARIO AMENDMENT`. Do not use a turn report to invent a trigger, initial state, decision boundary, Scope or authority.

If new evidence establishes a material semantic gap in the authored verification contract before an authoritative verdict can be completed, stop rather than forcing the observed product into the old flow. Do not issue AC verdicts from a contract that can no longer decide them.

If required authority is unavailable, return the correct evidence limit instead of waiting in a live suspended state.

## 11. Disposition-specific execution

### Independent

Obtain fresh direct evidence from the authored acceptance boundary/readback. `Independent verification required: yes` cannot be closed by implementation narration, tests, source plausibility or prior verification.

### Operator-assisted

Execute the product-owned portion and use only the authored operator-owned action/evidence path for the operator portion. Missing credentials, operator evidence or naturally occurring external condition leaves the affected flow/AC `INCONCLUSIVE` unless direct contradiction exists.

### Not independently verifiable

Do not invent a fresh surface. Verify the approved absence/reason and only the current canonical facts the disposition permits. A limited PASS does not claim nonexistent direct observation. Judge semantic sufficiency relative to this approved disposition rather than demanding an unauthorized direct surface.

## 12. Flow and AC adjudication

For every authored flow assign exactly one result:

- `SATISFIED`: all required observable/readback conditions are established and no material semantic-contract or decision-boundary contradiction remains.
- `CONTRADICTED`: fresh attributable evidence directly violates the authored decision boundary.
- `INCONCLUSIVE`: required evidence, authority, terminal condition or current attribution could not be established without a direct contradiction.

For every top-level AC in authored order:

- `FAIL` if any required mapped flow is `CONTRADICTED` for that AC obligation.
- `PASS` only when all mapped obligations are `SATISFIED` under their dispositions and boundaries.
- otherwise `INCONCLUSIVE`.

Whole Ticket:

```text
all ACs PASS          -> VERIFIED
any AC FAIL           -> FAILED
otherwise             -> INCONCLUSIVE
```

A material semantic-contract defect discovered before valid adjudication is not an implementation `FAIL`; it is `VERIFICATION NOT STARTED` with no AC verdicts.

## 13. Scope, Non-Goals, cross-AC closure and cleanup

Before `VERIFIED`, directly check that the current product did not introduce or expose forbidden Scope/Non-Goal behavior relevant to the Ticket and that satisfying one AC did not contradict another AC or adopted Behavior/UI authority.

Complete every authored cleanup, absence window, process stop, disposable-target disposal and external-effect terminal condition required for attributable evidence.

A still-running duplicate-sensitive effect, incomplete cleanup or unfinished absence/ordering window prevents final `VERIFIED` when it affects the decision boundary. Capture necessary evidence before disposing of a temporary target.

## 14. Terminal status transition

Keep verification verdict and Ticket progression separate.

For normal first verification of `Status: ready`:

- `FAILED` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `INCONCLUSIVE` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `VERIFIED` -> attempt guarded progression only through the sequence below.

Before `ready -> done`:

1. Re-read the exact Ticket and require the verification target/source/config/build identity used for the verdict is still current and attributable.
2. Resolve the current canonical To Tickets validator through the same admission path and require exact `VALID`.
3. Re-resolve current parent Spec and adopted Behavior/UI authorities and require the same projection/currentness checks still hold with no unresolved material semantic-contract defect.
4. Require the Ticket is still the exact canonical `Status: ready` contract that was verified.
5. Perform one guarded targeted replacement of only the top metadata `Status: ready` line with `Status: done`. Reject stale content, concurrent edit, path drift or ambiguous status matches.
6. Immediately run the same validator and require exact `VALID`.

When all steps succeed, report `Ticket Progression: COMPLETED` and `Ticket status after verification: done`.

If the status write or post-write validation fails, preserve `Verification Verdict: VERIFIED` but report `Ticket Progression: FAILED` and the exact observed status/failure. Do not rewrite ACs, Verification flows, Spec, Scope, Behavior/UI authority or other planning meaning.

Diagnostic re-verification of `done` never rewrites status and reports `Ticket Progression: NOT APPLICABLE`.

## 15. No remediation loop

Verification ends with evidence and verdict. Do not automatically edit source, invoke `ready-ticket-implement`, create a follow-up Ticket, reopen planning or continue to a later Increment. The caller/user decides the next action.

## 16. Final report

```text
READY TICKET VERIFICATION RESULT

Ticket:
Execution Mode: DIRECT
Verifier: Main / DIRECT
Ticket status before verification:
Verification target:
Target stability:
Material turn reports: None | <concise list>

Semantic contract findings: None | <exact material gap and owning contract location>

Scenario report:
Executed scenario blocks:
Environment / external conditions:
Cleanup / terminal conditions:

Evidence sufficiency:
- Existence/current-state claims:
- Absence-proof boundaries:
- Preservation claims:
- Semantic/qualitative claims:
- Process/history evidence limits:

Flow results:
- Flow ordinal / parent outcome:
  AC ordinals:
  Result: SATISFIED | CONTRADICTED | INCONCLUSIVE
  Runtime / canonical observation:
  Authoritative readback:
  Evidence limit:

AC results:
- AC ordinal:
  Verdict: PASS | FAIL | INCONCLUSIVE
  Linked flows:
  Verifier evidence:
  Remaining uncertainty:

Scope / Non-Goals:
Cross-AC findings:
Implementation-report differences:

Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED
Ticket status after verification:
```
