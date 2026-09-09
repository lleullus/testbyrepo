# Ready Ticket Verification Workflow

## 1. Subagent-first invocation

Top-level execution defaults to `SUBAGENT`. Use `DIRECT` only when the current user explicitly selects it for this exact verification stage. Do not require a separate SUBAGENT opt-in.

- `DIRECT`: under that explicit stage override, the current Main owns the complete verifier core for one exact Ticket.
- `SUBAGENT`: exactly one delegated verifier owns the whole verifier core; do not split ACs/flows, create a verifier roster, run parallel verifiers or delegate again.
- Apply the default or explicit user override without capability-based topology changes or automatic fallback. Required `SUBAGENT` capability failure returns `SUBAGENT CAPABILITY UNAVAILABLE` with no product/runtime/status mutation.
- The default applies only to top-level invocations. A worker assigned `Delegated Verifier: yes` performs the verifier core itself and never delegates it again.

Before verification, bind the exact Ticket and optional navigation inputs, carry current Additional User Instructions without silently rewriting authority, and confirm access to the required Project Root/product/canonical surfaces. A `SUBAGENT` assignment includes:

```text
Ticket:
Candidate Verification Target:
Implementation Report / Evidence:
Execution Plan / Review: None | <exact optional outside-root plan_review_path>
Additional User Instructions:
Delegated Verifier: yes
```

The delegated verifier continues to own canonical admission, semantic contract check, complete authored Flow denominator, scenario authorship, runtime/canonical evidence, heuristic finding disposition, every Flow adjudication, every AC verdict, Scope/Non-Goals and cross-AC closure, the whole-Ticket semantic verdict and its immutable verdict record. It never owns the status write. Parent Main does not perform a second verification pass; after passive terminal fan-in it owns the separate `ready_finalize` call using the exact verdict-record identity.

### SUBAGENT terminal fan-in and settlement

The delegated verifier runs one invocation-local evidence cycle and returns one terminal `READY TICKET VERIFICATION RESULT`. There are no IIS verification checkpoints, release decisions, execution leases, or persistent verifier sessions.

1. exactly one delegated verifier owns the same Ticket/stage at a time;
2. the verifier captures the immutable verification binding before product/runtime scenario action;
3. normal scenario progress and settled command failures stay inside that invocation;
4. if target identity/effect partition/authority changes enough that the captured binding is no longer attributable, the verifier terminates with the applicable `VERIFICATION NOT STARTED | FAILED | INCONCLUSIVE` result rather than waiting for Parent continuation;
5. after fixing the semantic verdict, the verifier calls `ready_contract seal_verdict` for that exact binding/verdict and returns the resulting verdict-record path/SHA;
6. Parent receives only the terminal semantic result, does not substitute or recreate a verdict, and invokes `ready_finalize` with the exact verdict-record path/SHA;
7. never auto-fallback between `SUBAGENT` and `DIRECT`.

After successful background verifier dispatch, Parent Main does not poll normal progress or completion. It does not call `hub wait`, `hub jobs`, `hub list` or `hub inbox`, send a status request, or duplicate repository/runtime inspection solely to observe the verifier. It yields/stands by once and lets the host-delivered async terminal result wake it; routing and `ready_finalize` begin only from that exact terminal result.

A single bounded diagnostic snapshot is allowed only for an explicit current user status request, cancellation/stop request, host-reported timeout/failure, malformed or missing expected terminal delivery, or a real need to establish verifier replacement/settlement. If the verifier is normally running, Parent returns to passive terminal fan-in without periodic monitoring.

If the verifier process must be replaced, the caller/host must first establish actual prior worker/process settlement before starting another verifier on the same mutable worktree/effect surface. A cancel receipt or session/job ID is not settlement evidence. A fresh verifier invocation captures a fresh binding.

## 2. Admission and current authority

Before any runtime/product action:

Skill reads and preparation artifact writing do not arm or enter execution. After one actual Ticket is selected, canonical/semantic/authority/target preflight resolves the exact stable implementation targets and exact scenario-effect paths. `ready_contract capture_verification` then creates the immutable outside-root binding used by this verifier invocation. A method plan/review is optional navigation, never a verification ADMIT prerequisite. No verification execution/session/reservation/admission lifecycle is created.


1. Resolve the current pinned bundle's canonical To Tickets `validate_ticket.py`, the same validator identity used by Ready runtime. The discovered `iis-workflow` route is navigation within that bundle; never probe historical source or another client home for a substitute validator.
2. Run that validator against the exact absolute Ticket path. Continue only when it returns exact `VALID`.
3. If the route/validator is unavailable, return `VERIFICATION NOT STARTED: CANONICAL VALIDATOR UNAVAILABLE`. If validation fails, return `VERIFICATION NOT STARTED: CANONICAL TICKET INVALID`. Do not issue AC verdicts or start product/runtime work.
4. After `VALID`, derive `Status`, `Parent-Spec`, `Project-Root`, `UI`, Acceptance Criteria, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities and References from the Ticket itself.
5. Resolve parent Spec and referenced Behavior/UI authorities. Require canonical current paths, applicable authority and no unresolved contradiction.
6. Enumerate every current top-level AC once in authored order and every authored Verification flow once in authored order.
7. Confirm every AC is linked to at least one flow, every flow links at least one AC, and referenced Behavior ordinals remain current.
8. Preserve each flow's exact authored meaning. Do not infer a missing flow, remap ordinals from implementation shape, normalize a legacy flow or strengthen/relax a decision boundary.
9. Bind the exact current verification target from the validated Ticket plus direct repository/runtime observation: source/config/build/artifact/runtime checkpoint, actual entrypoint or canonical inspection target, acceptance surface and authoritative readback.

Caller-supplied targets, execution plans/reviews, implementation reports and exploration assistance are navigation only. Bind the actual current target directly. Structural `VALID` admits schema only; it never establishes semantic correctness, current target availability, runtime evidence or verdicts. Existing implemented ready targets need no new implementation plan.

Return without AC verdicts when canonical admission, current authority, Ticket-to-parent projection or current target binding cannot be established.

```text
VERIFICATION NOT STARTED
Ticket:
Reason:
Decision: VERIFICATION NOT STARTED
Governing authority: ready-ticket-verify / <stable admission, semantic, authority, or target-binding rule>
Observed condition: <smallest directly established condition that prevented verifier admission/adjudication>
Effect: verifier-owned product/runtime execution and AC verdict issuance do not continue from this state
Next allowed action: <exact owner/caller action needed for a fresh valid verification attempt, or None>
AC verdicts: Not issued
```

The provenance fields explain the exact owner result, such as `CANONICAL TICKET INVALID` or `TICKET/PARENT PROJECTION MISMATCH`, rather than replacing it. If only a tool/transport/protocol failure is established, report that failure without inferring a missing file, permission or product condition.

## 3. Semantic contract check

Before deriving or executing the runtime scenario, compare every current AC and mapped Verification flow against the approved parent outcome, applicable Behavior/UI meaning, and relevant current user instructions supplied through the existing handoff. Confirm that the authored observation/readback decides the material approved obligation rather than a weaker proxy or a fake replacing its required boundary. Ticket wording alone cannot authorize that substitution. Challenge concrete plausible false-positive or false-negative paths that could change the verdict; preserve the exact Ticket scope rather than importing unrelated outer Goal work.

Do not treat approval, structural `VALID`, ordinal closure, matching wording, tests or implementation narration as proof that the flow is semantically sufficient. Do not invent new requirements or strengthen the approved contract.

If a material semantic gap means the authored verification contract cannot decide the approved claim, stop before product/runtime action and return `VERIFICATION NOT STARTED` with the exact owning contract location, material claim, non-decisive observation or false-verdict path, and `AC verdicts: Not issued`. Verification does not repair that planning defect.

## 4. Status semantics

Normal delivery verification requires exact `Status: ready`.

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

### Stateless verification boundary

After canonical/status/semantic/authority/projection gates and exact target resolution succeed, call `ready_contract capture_verification` with exact Ticket/Project Root, exact `stable_target_paths`, exact `scenario_effect_paths`, and optional `plan_review_path`. The tool validates current authority, rejects stable/effect overlap and protected authority/method effect paths, and creates an immutable outside-root binding with exact path/SHA. Preserve the actual capture failure; do not invent a machine-currentness diagnosis from prose.

Optional method navigation uses only `plan_review_path`; the binding records the exact review bytes and checked plan paths as navigation/method context. Product-required paths take precedence over method context. Do not require ADMIT to verify an already implemented target or synthesize a review merely for classification.

After capture, use host-native inspection/read/CLI/service surfaces. Verification must not edit product source/config/tests/planning artifacts to manufacture success. Settled nonzero command results are ordinary verifier evidence and do not create generic workflow uncertainty. The stable implementation target remains immutable for attribution; scenario-effect paths may change only as predeclared by the authored scenario.

Separate product-target identity from exact declared method-context navigation. Plan/review-only drift stales navigation, not product evidence automatically; no write permission follows. A plan required by the approved product contract remains a product target. Undeclared new files are conservatively product changes until narrowly classified. File hashes do not prove runtime/DB/provider/permission currentness; obtain actual authoritative readback and required observation windows.

There are no delegated Ready assignments, begin calls, checkpoints, pause/release actions, or verifier execution IDs. Parent/caller owns only worker process lifecycle and terminal fan-in. Replacement requires actual old-worker/process/service settlement before a fresh verifier touches the same mutable worktree/effect surface; cancel receipt alone is not settlement.

Use host-native service/process facilities when a scenario requires them. Preserve exact returned handle/generation where available, never adopt/stop shared existing services without authority, observe readiness and actual settlement, and complete authored cleanup before terminal verdict. A timeout can leave a live service; root exit/cancel receipt does not prove escaped descendants or external effects ended.

Mutation-capable scenario timeout/abort/transport loss can leave an applied external/product effect even when local files are unchanged. Do not blind replay or claim rollback. Continue with the authored authoritative readback, cleanup, and evidence path. If readback establishes applied/not-applied, adjudicate from that fact; if settlement or attribution remains unknown, affected evidence is `INCONCLUSIVE` and any verdict depending on it cannot be `VERIFIED`. No generic execution-uncertainty phase, recovery operation, reservation, or mutation-resolution state is created.


## 6. Integrated scenario ownership

After the semantic contract check finds no material gap that prevents the authored flow from deciding its approved claims, convert the authored Verification section into one integrated execution plan before any product/runtime action.

Treat each authored flow as one normative scenario block. Common setup, environment, disposable targets or cleanup may be coordinated only when flow meaning remains unchanged. Do not merge materially distinct flows or split one flow around implementation seams.

Before deriving execution steps, resolve each flow's `Parent outcome ordinal` against the approved parent Spec and confirm preservation of exact `Disposition`, `Independent verification required`, `Acceptance surface`, `External condition`, every authored conditional boundary, trigger/inspection target, acceptance boundary, expected result, authoritative readback, decision boundary and mapped Behavior authority.

A material projection mismatch returns `VERIFICATION NOT STARTED: TICKET/PARENT PROJECTION MISMATCH`; do not normalize the Ticket or author a compensating scenario.

### Scenario materiality gate

Freeze every authored flow and conditional boundary as the mandatory denominator. This gate never permits omission, weakening, merging or early termination of required coverage.

Add a derived positive variation, counterexample, boundary exercise or observation only when it materially tests an authored decision boundary, closes a concrete false-verdict path or prevents a concrete attribution error. Require a contract anchor and plausible failure path. Do not expand the scenario merely for exhaustiveness.

Reject expansion that invents a new trigger, precondition, Scope, acceptance surface or stricter/weaker result; requires unrelated product mutation; or obscures the core verification. Prefer the smallest sufficient scenario.

For every material finding from this verifier's current discovery cycle or optional navigation, reopen its current contract anchor and assign one verifier-owned disposition:

```text
Heuristic Finding Disposition:
- REPRODUCED
- CURRENT_READBACK_CONFIRMED
- OUT_OF_SCOPE
- UNATTRIBUTABLE
- SUPERSEDED_BY_CURRENT_TARGET
```

- `REPRODUCED`: the verifier safely exercises the finding's minimized trigger on the current target and captures fresh authoritative evidence.
- `CURRENT_READBACK_CONFIRMED`: a current direct canonical/product readback independently establishes the material behavior without repeating an unsafe or unnecessary trigger.
- `OUT_OF_SCOPE`: current authority does not make the observed behavior part of this Ticket's claim; do not fail or expand the Ticket for it.
- `UNATTRIBUTABLE`: the finding cannot be tied decisively to the current target/authority; it is not a FAIL. If the missing attribution is required to decide an authored flow, that flow remains `INCONCLUSIVE`.
- `SUPERSEDED_BY_CURRENT_TARGET`: current target/authority changed so the old finding no longer describes the object being verified; do not carry it forward.

Navigation never substitutes for fresh verifier-owned evidence. Prefer the safely minimized trigger; same-cycle evidence directly obtained by this verifier can support both discovery and adjudication without repeating a risky effect. Current Main in DIRECT keeps its final judgment independent from prior implementation narration/self-check.

### Bounded post-implementation frontier

Review every authored flow and applicable conditional boundary for realistic false-completion/attribution paths in the actual implementation, separately from the mandatory scenario. Start from original purpose/current entrypoints and alternate owners, order/partial effects and weak readbacks, not just the reviewed plan's diagnosis. A lane requires a current contract anchor, reachable concrete path, material consequence and executable/inspectable discriminating readback. Dismiss unreachable, out-of-scope or already-handled hypotheses with exact evidence; the original unfixed symptom is a purpose failure even if pre-existing.

For admitted exploration, preserve initial state and target identity, make the smallest authorized trigger, minimize one irrelevant dimension at a time where safe, and capture primary output/readback before cleanup. Keep observed facts separate from inference; transport failure does not decide mutation outcome. Preserve each lane's material finding, attributable no-finding or exact evidence limit without forcing a finding count. No distinct lane/no finding is not PASS and never removes any authored obligation. A same-cycle finding becomes CONTRADICTED only through its actual affected flow/AC decision boundary.

Stop minimization when further reduction loses reproducibility, crosses authority, becomes unsafe or stops answering the contract question. Keep a compact finding record: exact contract/flow anchor, minimal trigger/actions, observed result, authoritative comparison/readback, primary evidence, current target identity, cleanup/terminal state and remaining uncertainty. Where assistance is explicitly permitted, isolate read/effect/cleanup state; serialize shared records, idempotency keys, service lifecycles or dependency-sensitive observations. Agreement is not evidence and one attributable contradiction is not discarded by majority.

Required risky/external/one-shot actions retain current Ticket/user authority; do not bypass protection to make a trigger. A verifier may use bounded assistance only when the current stage explicitly permits delegation; the default one-verifier/no-redelegation contract does not secretly create a worker roster. Assistance is navigation and the final verifier owns fresh decisive evidence. These principles are self-contained; no external methodology installation is required.

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
  Nearest nonconforming state:
  Discriminating observation:
  Sensitivity activation:
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
Execution Mode: DIRECT | SUBAGENT
Verifier: Main / DIRECT | <delegated verifier identity>
Ticket status:
Verification target:
Target-stability check:
Environment:
External/operator conditions:
Semantic contract check: <no material gap found | exact blocking defect already returned before execution>
Heuristic frontier: <material lanes or no distinct lane, with bounded rationale>
Heuristic findings / proposed verifier dispositions: None | <finding -> disposition>

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

Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Stable Target Paths: <exact list>
Scenario Effect Paths: <exact list>
```

In both `DIRECT` and `SUBAGENT`, the report is informational and records the immutable binding captured before scenario execution. No Parent release/checkpoint is required. Parent does not execute the flows or issue AC verdicts; in SUBAGENT it receives only the eventual terminal verifier result.

## 9. Evidence sufficiency and execution

The verifier directly performs each authored trigger or canonical inspection and directly captures authoritative readback for every required flow.

Evidence priority when applicable:

1. actual runtime / canonical acceptance-surface observation;
2. authoritative product/canonical readback;
3. rendered UI interaction/readback when UI is the acceptance surface;
4. real execution in an authorized disposable/controlled environment when it exercises the approved implementation, entrypoint, state/effect, lifecycle, and readback;
5. source/diff/unit tests and supporting doubles as explanation/navigation, not proof of a boundary they replace.

A mock, stub, canned response, seeded success state, or surrogate readback cannot prove the actual acceptance boundary it substitutes for. A double for an ancillary dependency need not invalidate observations of an unrelated real boundary; never claim the double's replaced boundary was verified. Test format or disposable location alone does not invalidate evidence that actually exercises and observes the required real path. Required provider/external effects need their approved effect readback, not merely internal success or HTTP acceptance.

Directly inspect an artifact, source, document, schema, plan, or simulator when that actual deliverable is the original approved result, faithful to parent authority and current user instructions; do not demand invented runtime or claim unobserved external/product effects. Apply §3 to a flow that substitutes for required meaning rather than repairing it inside verification. If a valid real boundary is unavailable, preserve `INCONCLUSIVE` unless attributable evidence establishes contradiction; neither unknown nor contradiction becomes fake success.

For runtime claims, use the existing `Nearest nonconforming state`, `Discriminating observation`, and `Sensitivity activation` to determine whether this run actually exercised the required boundary. Do not mark a flow `SATISFIED` without the declared discriminating readback and its sensitivity activation; passing implementation tests or source-only mechanism shape cannot substitute.

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
Material effect:
Affected AC / authority / target:
Binding impact: NONE | STALE_OR_UNATTRIBUTABLE
Verifier action: CONTINUE WITH SAME BINDING | TERMINATE FOR FRESH VERIFICATION
```

A bounded observation already inside the authored flow may be recorded as `SCENARIO AMENDMENT`. Do not use a turn report to invent a trigger, initial state, decision boundary, Scope or authority.

When the changed evidence does not alter the captured stable/effect partition or authority identity, the verifier may continue in the same invocation. When it makes the binding stale or attribution unsafe, terminate with the applicable `VERIFICATION NOT STARTED`, `FAILED` or `INCONCLUSIVE` result and exact evidence limit. Do not wait for Parent continuation, patch an immutable binding, or carry PASS evidence across the drift.

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

## 14. Terminal semantic result and caller-owned status transition

Keep verification verdict and Ticket progression separate. The verifier owns the semantic result and immutable verdict record; the caller owns only the narrow status transition.

For every normal delivery verification captured from `Status: ready`, the verifier fixes one semantic verdict, calls `ready_contract seal_verdict` with the exact binding path/SHA and verdict, then returns one terminal `READY TICKET VERIFICATION RESULT` with both immutable identities and `Ticket Progression: PENDING CALLER FINALIZATION`. This applies to `VERIFIED`, `FAILED`, and `INCONCLUSIVE`. The verifier never writes `done` and never invokes `ready_finalize`.

Before sealing and emitting semantic `VERIFIED`, the verifier must still ensure within its evidence cycle that:

1. every authored Flow has an attributable final result;
2. every current AC is `PASS`;
3. Scope/Non-Goals, heuristic finding dispositions, cleanup and terminal conditions are closed;
4. no unresolved material semantic-contract defect or evidence conflict remains;
5. the source/config/build target used for the verdict remains attributable to the captured stable target; and
6. no unresolved external-effect settlement gap prevents required evidence from being decisive.

`seal_verdict` accepts only binding path/SHA, semantic verdict and an optional outside-root verdict path. It rereads the immutable binding, copies Ticket/bundle/protocol identity from it, and atomically creates a mode-`0600` non-overwritable verdict record. The verifier does not supply those copied identities. If sealing fails, report the exact tool/evidence failure; do not emit a normal finalizable terminal result or ask the caller to reconstruct the record.

The terminal verifier result includes:

```text
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Verification Verdict Record: <exact outside-root path>
Verification Verdict Record SHA256: <sha256>
Stable Target Paths: <exact list>
Scenario Effect Paths: <exact list>
Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Ticket Progression: PENDING CALLER FINALIZATION | NOT APPLICABLE
Observed Ticket Status: ready | done | <actual>
```

In `SUBAGENT`, Parent Main consumes this terminal result and calls `ready_finalize(verdict_path, verdict_sha256)` without supplying a semantic verdict. In `DIRECT`, Main first completes and seals the verifier result and then performs the same call as a distinct caller step. `ready_finalize` obtains the verdict only from the immutable record and rechecks record/binding SHA, their exact identity relationship, the current loaded bundle/protocol, current authority, stable target and canonical Ticket validation. It does not rerun or reinterpret semantic verification.

For an original `ready` binding:

- `FAILED` or `INCONCLUSIVE` -> no status mutation; caller reports the finalizer's non-progressing result.
- `VERIFIED` -> only the finalizer may perform the exact top-metadata `Status: ready` -> `Status: done` compare-and-swap and exact post-write validation.
- stable target/authority/Ticket/bundle/protocol drift -> finalizer reports progression `FAILED`; semantic `VERIFIED` stays `VERIFIED`.
- a current `done` Ticket matching the same captured ready candidate without attributable prior finalizer provenance is `ALREADY_DONE_MATCHING_BINDING`, not a new completion.

The finalizer preserves bytes/mode except the one status token, uses exact compare-and-swap atomic replacement, and conditionally restores only this call's exact candidate when post-write validation fails and authority/stable target remain unchanged. It must not overwrite an external edit or infer fresh completion from a `done` string.

Diagnostic re-verification captured from `done` is semantic/diagnostic only. The verifier still seals its verdict record but reports `Ticket Progression: NOT APPLICABLE`; caller finalization, if invoked for normalized reporting, never rewrites status.

## 15. No remediation loop

Verification ends with evidence and verdict. Do not automatically edit source, invoke `ready-ticket-implement`, create a follow-up Ticket, reopen planning or continue to a later Increment. The caller/user decides the next action.

## 16. Final report

```text
READY TICKET VERIFICATION RESULT

Ticket:
Execution Mode: DIRECT | SUBAGENT
Verifier: Main / DIRECT | <delegated verifier identity>
Ticket status before verification:
Verification target:
Target stability:
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Verification Verdict Record: <exact outside-root path>
Verification Verdict Record SHA256: <sha256>
Stable Target Paths: <exact list>
Scenario Effect Paths: <exact list>
Heuristic finding dispositions: None | <finding -> disposition>
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
Verifier Ticket Progression: PENDING CALLER FINALIZATION | NOT APPLICABLE
Observed Ticket Status: ready | done | <actual>
```

The delegated verifier stops at this report. The caller then passes the exact `Verification Verdict Record` path/SHA to `ready_finalize` and appends that exact result as a separate finalization record: `Ticket Progression`, `Progression Basis`, `Ticket Status After`, verdict-record provenance, and any exact progression detail. DIRECT follows the same semantic-result/seal-then-finalization sequence in one Main invocation.

When final `INCONCLUSIVE` is caused specifically by an authority/evidence-attribution/target-currentness/effect-settlement boundary, or when a `VERIFIED` evidence verdict cannot complete caller finalization, append the same `Decision / Governing authority / Observed condition / Effect / Next allowed action` provenance fields. Do not append them to a normal evidence-complete `FAILED` verdict merely because the product contradicted the Ticket.
