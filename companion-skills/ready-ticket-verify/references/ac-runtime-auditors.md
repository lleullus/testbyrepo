# AC Runtime Auditor Contract

## 1. Role

An AC Runtime Auditor is an optional concurrent read-only observer attached to the Main verifier's single integrated runtime execution for exactly one unique current top-level AC.

The auditor does not author the scenario, execute a separate scenario, trigger product behavior, mutate product/source state, decide an AC verdict, decide the Ticket verdict, or replace Main verification coverage.

The purpose of adding auditors is to increase observation density and catch AC-specific evidence gaps, contradictions, attribution mistakes, or terminal-condition mistakes while Main is still executing the same scenario.

## 2. Roster size and AC assignment

`AC Runtime Auditor Count` may be `0` through the current top-level AC count.

- Count `0`: no auditor contexts are created.
- Count `1..N`: create exactly Count auditors.
- One auditor receives exactly one unique current AC ordinal.
- Do not assign two auditors to the same AC in this initial contract.
- Main still verifies every AC regardless of Count.

Selection modes:

### `EXPLICIT`

The caller/user supplies the exact unique AC ordinals. Their count must exactly equal `AC Runtime Auditor Count`.

### `AUTO_BY_MATERIAL_RISK`

Main selects exactly Count unique ACs only after Main has completed the integrated scenario and AC coverage matrix. Selection must be explained in the Scenario Report.

Prefer ACs where a second simultaneous observer is most likely to prevent a false verdict: cross-flow coupling, concurrency/ordering, lifecycle/interruption/persistence, terminal/absence windows, identity/ownership, complex authoritative readback, UI interaction, external/operator conditions, or strong cross-AC coupling.

## 3. Binding policy

Resolve each selected AC from the caller/user configuration:

```text
Default Model: None | <exact model>
Default Reasoning Depth: None | <exact depth>
Per-AC Override: None | <exact selected-AC model/depth>
Resolved AC binding: <per-AC override, otherwise default, otherwise host-provided invocation-local>
```

- If the caller/user supplied an exact default or per-AC Model and/or Reasoning Depth, preserve that exact binding.
- A per-AC override applies only to that selected AC; otherwise use the supplied default.
- Do not substitute a nearby model, different depth, or arbitrary host default for an explicitly supplied binding.
- When neither default nor applicable per-AC exact binding was supplied, Main may use a current host-provided invocation-local observer role.
- Model identity or reasoning depth never expands auditor authority.

Before Main begins the first product/runtime action, the host must be able to start the full requested Count concurrently with every exact requested auditor agent/configuration. If it cannot, do not silently reduce Count, start late observers as a substitute, or convert the request into post-hoc review. Successful start of the exact requested auditor agent/configuration closes binding admission; later self-reported model/depth/runtime metadata or display labels are non-authoritative diagnostics and cannot invalidate the auditor slot, require re-audit, change Main's verdict, or block `ready -> done`.

### Same-execution evidence visibility preflight

Before Main's first product/runtime action, confirm for each selected AC that its auditor can actually inspect the evidence surfaces needed to audit the same Main execution from the required initial state through attributable terminal evidence. For the assigned AC, establish all applicable capabilities:

- the final Main-authored scenario and assigned mapped flows are available before execution;
- required initial-state evidence is visible before the relevant trigger;
- transient runtime/UI/process events can be observed directly or through timely Main-captured evidence from that exact execution;
- authoritative readbacks, IDs, timestamps, exit results, screenshots/DOM/state captures, or equivalent evidence can be inspected read-only when required;
- evidence needed before cleanup/state replacement is available to the auditor before it becomes unattributable;
- Main can receive one distinct terminal assessment for that assigned AC.

This is evidence-visibility admission, not a second model/binding check. A successfully started auditor that cannot observe indispensable assigned-AC evidence does not provide the requested runtime-audit coverage. If any selected AC lacks required same-execution visibility, report `AC RUNTIME AUDIT CAPABILITY UNAVAILABLE` before authoritative runtime starts. Do not substitute late attachment, wave execution, or post-hoc log review for requested concurrent observation.

## 4. Assignment package

Every auditor receives:

```text
AC RUNTIME AUDIT ASSIGNMENT

Ticket:
Project Root:
Verification target:
Integrated scenario:
Assigned AC ordinal:
Exact AC text:
Mapped Verification flows:
Applicable Behavior authorities:
Applicable UI authority:
Relevant scenario blocks / steps:
Required initial states:
Required observable results:
Forbidden / contradictory results:
Authoritative readbacks:
Applicable ordering / interruption / persistence / UI / external boundaries:
Cross-AC dependencies:
Evidence locations / live surfaces:
Requested Model / Reasoning Depth:
Read-only and non-authority boundaries:
```

Give the auditor the final Main-authored scenario. Do not ask the auditor to redesign it or pre-judge likely defects.

## 5. Start timing and lifecycle

Start all selected auditors after `VERIFICATION SCENARIO REPORT` and before Main's first product/runtime action.

Each auditor remains attached until every mapped flow and claim-specific condition that can affect its assigned AC has reached an attributable terminal observation, or until the verification cycle is cancelled/invalidated.

An auditor may finish before unrelated later scenario blocks only when all evidence and cross-AC dependencies relevant to its assigned AC are already closed and cannot be changed by later authored steps.

A late-started auditor does not satisfy requested coverage if it missed a required initial state or transient event and that evidence is not still directly attributable from the same Main execution.

## 6. Observation authority

An auditor may:

- read the Ticket, parent Spec, mapped Behavior/UI authority, and the final integrated scenario;
- inspect Main's live output, logs, screenshots, DOM/state captures, canonical readbacks, process exit results, IDs, timestamps, and other evidence surfaces needed for the assigned AC;
- independently re-read safe current authoritative state/readback when that read itself does not trigger or mutate product behavior;
- inspect bounded source/configuration facts only to verify current target/evidence attribution;
- report material evidence gaps, contradictions, stale attribution, or missing terminal conditions to Main while the scenario is still running;
- return one terminal AC-scoped evidence assessment.

An auditor must not:

- execute the scenario trigger or replay a product action;
- invoke mutation-capable runtime commands merely to obtain independent evidence;
- create its own disposable verification run;
- modify product source/config/tests, persisted product state, Git state, Ticket, Spec, or authority files;
- repair implementation or add observability;
- change Main's scenario;
- decide `PASS`, `FAIL`, `INCONCLUSIVE`, `VERIFIED`, `FAILED`, or Ticket progression;
- spawn another verification role or establish a second verification authority.

If a required readback cannot be safely inspected read-only by the auditor, use Main-captured evidence and report any attribution limitation instead of triggering a second run.

## 7. What the auditor checks

For its assigned AC, the auditor tracks every mapped Verification flow through the same Main execution and asks:

- Was the authored initial state actually established before the relevant trigger?
- Did Main execute the exact authored trigger/inspection target rather than an implementation substitute?
- Was the acceptance boundary actually reached?
- Was the authoritative readback captured before cleanup or state transition made it unavailable?
- Are the observed target identity, request/run identity, ordering source, timestamps, terminal state, and persistence identity attributable to this exact scenario execution?
- Did every required observable result occur?
- Did any forbidden/contradictory result occur?
- Was an absence/negative condition observed through its authored terminal window rather than inferred early?
- Were interruption, retry, duplicate, concurrency, ordering, lifecycle, persistence, UI interaction, or external-effect boundaries exercised when applicable?
- Did another AC's scenario step mutate a shared state in a way that changes the assigned AC evidence or contradicts it?
- Is Main about to leave a scenario block while required assigned-AC evidence is still missing?

The auditor is not trying to produce a second full Ticket review. Keep work bounded to the assigned AC, its mapped flows, their necessary authority, and material cross-AC dependencies.

## 8. Intermediate material findings

Send an intermediate finding only when it can materially change safe evidence capture, current scenario execution, or the eventual AC judgment.

```text
AC RUNTIME AUDIT FINDING

AC Ordinal:
Mapped Flow:
Scenario step / evidence anchor:
Finding type: EVIDENCE GAP | CONTRADICTION | ATTRIBUTION RISK | TERMINAL-CONDITION GAP | CROSS-AC CONFLICT
Authority / decision boundary:
Observed evidence:
Why it is material now:
Main action needed: REVIEW | CAPTURE BEFORE CONTINUING | DECISION / AUTHORITY REQUIRED | NONE
```

Examples worth interrupting Main for:

- an authored readback has not been captured and the scenario is about to destroy/replace that state;
- the current run identity does not match the evidence Main is recording;
- an absence window has not yet reached its terminal condition;
- the assigned AC requires a second mapped flow that Main is about to omit;
- a forbidden state is directly visible;
- a later shared-state mutation will make current evidence unattributable.

Do not spam routine progress, stylistic observations, source-quality suggestions, or implementation refactors.

## 9. Main response to a finding

Main owns all action. The auditor does not execute the remedy.

Main may:

- capture an already-authored missing readback;
- pause before an irreversible/terminal step;
- re-check a bounded current identity/state;
- record a scenario amendment that stays inside the authored flow;
- classify evidence as insufficient/stale;
- rerun an affected flow from a fresh valid state when the authored contract and authority permit it;
- stop for an actual authority gate.

If fixing the gap would change product meaning, add a new trigger, expand Scope, or invent an acceptance surface, Main must not use the auditor finding to rewrite the contract.

## 10. Terminal evidence assessment

After all relevant assigned-AC evidence is closed, return:

```text
AC RUNTIME AUDIT RESULT

AC Ordinal:
Exact AC text:
Verification target:
Mapped Verification flows observed:
Scenario steps observed:
Required initial states observed:
Required results observed:
Forbidden-result checks:
Authoritative readbacks inspected:
Ordering / interruption / persistence / UI / external boundaries observed:
Cross-AC findings:
Evidence gaps:
Target/currentness limitations:
Requested auditor configuration:
Spawn admission: STARTED | FAILED
Host diagnostic metadata: <optional; non-authoritative>

Assessment:
EVIDENCE SUFFICIENT | CONTRADICTION OBSERVED | EVIDENCE INSUFFICIENT | STALE / UNATTRIBUTABLE

Evidence anchors:
Remaining uncertainty:
AC verdict: Not owned by this auditor
Ticket verdict: Not owned by this auditor
```

Assessment meaning:

- `EVIDENCE SUFFICIENT`: the auditor found the required assigned-AC evidence set complete and attributable, with no observed contradiction. Main still owns PASS.
- `CONTRADICTION OBSERVED`: the auditor directly observed evidence that appears to violate an authored boundary. Main must verify the load-bearing evidence before FAIL.
- `EVIDENCE INSUFFICIENT`: required evidence/terminal condition/readback was not established, without a direct contradiction.
- `STALE / UNATTRIBUTABLE`: evidence cannot be reliably tied to the stable verification target/current Main execution.

## 11. Main fan-in rules

- Main must receive or classify the terminal result for every requested auditor before final Ticket verdict.
- A requested auditor that fails to start, disappears, or misses indispensable transient evidence is not silently treated as Count reduction. If Main direct evidence already establishes `FAILED`, that contradiction remains usable; otherwise incomplete requested audit coverage prevents `VERIFIED` and yields whole-Ticket `INCONCLUSIVE`. A self-reported model/depth/runtime-metadata difference after successful exact requested spawn is not a start failure, disappearance, or evidence gap and cannot by itself prevent `VERIFIED` or `done`.
- Main independently verifies every decision-critical auditor claim.
- Auditor agreement is not a vote.
- `EVIDENCE SUFFICIENT` cannot override Main's direct contradiction.
- `CONTRADICTION OBSERVED` cannot become AC FAIL until Main verifies the current evidence against the authored decision boundary.
- An unresolved material conflict between Main evidence and auditor evidence prevents the affected AC from PASS.

## 12. Freshness and cancellation

If unrelated source/config/build mutation invalidates the Main verification target, auditors stop treating existing observations as progression evidence. Still-safe read-only work may finish only as navigation.

If Main cancels or restarts the verification cycle, old auditor assessments do not transfer as PASS evidence to the new cycle. New authoritative execution requires current attributable evidence and, when Count is nonzero, a newly attached configured auditor roster for that execution.

Do not create a persistent auditor registry, evidence cache, cycle database, run ledger, or assignment store to manage this lifecycle.
