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

The delegated verifier continues to own canonical admission, semantic contract check, complete authored Flow denominator, scenario authorship, runtime/canonical evidence, heuristic finding disposition, every Flow adjudication, every AC verdict, Scope/Non-Goals and cross-AC closure, whole-Ticket verdict and guarded status write. Parent Main does not perform a second verification pass.

### SUBAGENT checkpoint continuation

A checkpoint is a logical phase boundary. It is not a required live-wait primitive, direct-user approval gate or durable workflow state.

At a checkpoint:

1. delegated owner returns a complete checkpoint report to Parent Main;
2. it does not cross the named `Protected next phase` before Parent decision;
3. Parent returns exactly one decision:
   - `CONTINUE`: release the protected next phase;
   - `STEER`: provide a bounded correction with exact authority/evidence anchor; if decision-critical content changes, the verifier updates and resubmits the same checkpoint;
   - `STOP`: do not enter the protected phase and close with the applicable existing `VERIFICATION NOT STARTED | INCONCLUSIVE | terminal progression` owner contract;
4. only one delegated owner lane exists for the same Ticket/stage at a time;
5. do not repeat a checkpoint without material delta or create periodic progress checkpoints;
6. if checkpoint continuation capability is unavailable, return `SUBAGENT CAPABILITY UNAVAILABLE`;
7. never auto-fallback to `DIRECT`.

Continuation is harness-neutral: it may use live child yield/reply, same-session return/resume, or an attributable continuation invocation after confirming the prior child is inactive. A replacement continuation explicitly supersedes the prior worker and rechecks exact Ticket, target/current working-tree identity, previous checkpoint payload, Parent decision and baseline/currentness. The hard rule is: do not cross the protected next phase before Parent decision.

The verifier ends with one `READY TICKET VERIFICATION RESULT`. Checkpoint reports are nonterminal and do not themselves carry Adaptive defect classification.

## 2. Admission and current authority

Before any runtime/product action:

Skill reads and preparation artifact writing do not arm or enter execution. Explicit `begin_verify` or delegated assignment/begin starts admission only after one actual Ticket is selected. Current authority and actual target validation precede execution commit; a method plan/review is optional navigation, never a verification ADMIT prerequisite. `cancel_admission` fences only an in-flight unbound admission. Bound/uncertain execution stays with its current owner's closure/recovery path; orphan reservations require verified withdrawal/termination and no live work/uncertain effects before exact-identity recovery.


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

### Runtime enforcement boundary

After canonical/status/semantic/authority/projection gates and exact target resolution succeed, call `ready_guard begin_verify` with exact Ticket/Project Root, exact actual implementation `target_paths`, and only exact declared outside-root evidence outputs. No earlier exploration artifact/binding is required. Preserve the actual admission rejection; do not invent a machine-currentness diagnosis from prose.

Optional method navigation uses only `plan_review_path`; runtime resolves actually checked review/plans from that artifact, not arbitrary separately supplied plan paths. Product-required paths take precedence over method context. Do not require ADMIT to verify an already implemented target or synthesize a review merely for classification.

Continue only with returned `purpose: verify` and a bound target digest. Generic source/config/test/planning mutation and `ready_argv mutate` are forbidden. Use supported guarded inspection or structured `ready_argv execute` for ordinary runtime argv. Protected product drift enters PAUSED with reason TARGET_DRIFT and prevents stale VERIFIED. Authority drift, target drift and EFFECT_UNCERTAIN are distinct, and a parent CONTINUE cannot erase them.

Separate product-target identity from exact declared method-context navigation. Plan/review-only drift stales that navigation, not product evidence automatically; no write permission follows. A plan required by the approved product contract remains a product target. Undeclared new files are conservatively product changes until narrowly classified. File hashes do not prove runtime/DB/provider/permission currentness; obtain actual authoritative readback and required observation windows.

For delegated verification, Parent uses `assign_subagent` with `purpose: verify`; the worker uses `begin_delegated` with the same target inputs. Before actual scenario work use `checkpoint`, `kind: PRE_RUNTIME`; material and candidate VERIFIED closure use the same action with MATERIAL_TURN/PRE_PROGRESSION. Parent releases the exact pause through `release_checkpoint`; DIRECT current owner has no Parent ceremony but observes the same currentness/effect fence. PAUSED permits safe read/analysis, not source mutation or protected runtime action.

Replacement requires old dispatch revocation, actual work/service settlement, prior `suspend_worker`, Parent inactive confirmation and `replace_worker` one-use assignment. The new owner rechecks current authority/target and its scenario PRE_RUNTIME before dependent runtime work. Cancel receipt alone is not settlement; do not equate agent/job/session/assignment IDs. Parent STOP does not invent a verdict: the verifier owns its applicable terminal and `finalize_verification` closure.

Use native `hub start/logs/wait/stop` for one execution-owned ephemeral service with exact handle/generation, persist:false, detached:false and no automatic restart. Never adopt/stop shared existing services. Observe readiness and actual settlement; timeout can leave a live service. Stop/reap before terminal/suspend/replacement. Root exit/cancel receipt does not prove escaped descendants or external effects ended. Unsupported host surfaces remain explicit capability limitations.

The supported adapter uses an execution-UUID-unique service name and actual host resource `id`, `startedAt`, `restartCount` generation; preserve its returned handle and inspect stop/wait settlement. Names alone cannot adopt a later generation.

Mutation-capable scenario timeout/abort/transport loss can leave an applied effect even when local files are unchanged. Preserve EFFECT_UNCERTAIN and ownership; do not blind replay or claim rollback. `resolve_mutation` needs exact operation/effect surface and actual authoritative readback reference, with an authorized owner decision where local identity cannot decide. Unresolved effects remain protected after a blocked report.

The recovery request fields are `operation_id`, `effect_surface`, `evidence_reference`, `outcome`; exact current recovery-owner judgment and actual readback are required, not an arbitrary outcome string. Orphan admission recovery uses `recover_admission(project_root, ticket_path, reservation_id, recovery_evidence_reference)` only after the designated recovery owner establishes that exact admission ended/was withdrawn and no related live work/uncertain effects remain. Runtime compares the same reservation under lock; a handoff is not automatic host proof.


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

Checkpoint: NOT_APPLICABLE | PRE_RUNTIME
Protected next phase: NOT_APPLICABLE | FIRST_PRODUCT_OR_RUNTIME_ACTION
Checkpoint state: NOT_APPLICABLE | PARENT_CONTINUATION_REQUIRED
```

In `DIRECT`, the report is informational and has no Parent continuation. In `SUBAGENT`, `PRE_RUNTIME` is mandatory after semantic/scenario closure and before the first product/runtime action; the delegated verifier does not cross `FIRST_PRODUCT_OR_RUNTIME_ACTION` before Parent `CONTINUE`. Parent reviews authored Flow/AC denominator completeness, heuristic-finding coverage, authoritative readback strength, Scope and obvious target/authority mismatch only; Parent does not execute the flows or issue AC verdicts.

Call `ready_guard checkpoint` with `kind: PRE_RUNTIME` for the delegated report and wait for exact Parent `release_checkpoint`. Use the same public action with MATERIAL_TURN and PRE_PROGRESSION at their defined boundaries; no normal implementation-first-change checkpoint is implied.

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
Proposed continuation direction:

Checkpoint: NOT_APPLICABLE | MATERIAL_TURN
Protected next phase: NOT_APPLICABLE | <exact protected phase>
Checkpoint state: NOT_APPLICABLE | PARENT_CONTINUATION_REQUIRED
Work permitted before continuation: safe read/analysis only while PAUSED; no protected runtime action
```

A bounded observation already inside the authored flow may be recorded as `SCENARIO AMENDMENT`. Do not use a turn report to invent a trigger, initial state, decision boundary, Scope or authority.

In `DIRECT`, the report remains informational and verifier-owned execution continues under current authority. In `SUBAGENT`, the report becomes a `MATERIAL_TURN` checkpoint only when the changed evidence can alter adjudication or safe progression; after returning it, do not perform work that depends on the changed direction before Parent continuation. `STEER` that changes decision-critical content requires an updated checkpoint before protected work resumes.

If new evidence establishes a terminal blocker or material semantic gap that prevents authoritative adjudication, do not create an unnecessary checkpoint: return the applicable existing `VERIFICATION NOT STARTED`, `FAILED` or `INCONCLUSIVE` terminal result. Checkpoints are for cases that can continue after bounded resynchronization, not periodic progress or terminal blockers.

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

For normal delivery verification of `Status: ready`:

- `FAILED` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `INCONCLUSIVE` -> keep `ready`; `Ticket Progression: NOT APPLICABLE`.
- `VERIFIED` -> attempt guarded progression only through the sequence below.

For `SUBAGENT`, after all Flow adjudications and AC candidate verdicts are closed, Scope/Non-Goals and cleanup are closed, and candidate whole-Ticket verdict is `VERIFIED`, return this checkpoint before final `VERIFIED` emission or status mutation:

```text
VERIFICATION PRE-PROGRESSION CHECKPOINT

Ticket:
Execution Mode: SUBAGENT
Verifier:
Verification target:
Target stability:
Candidate whole-Ticket verdict: VERIFIED

Flow closure:
- <every authored Flow and candidate result>

AC closure:
- <every AC and candidate verdict>

Heuristic finding dispositions:
Scope / Non-Goals closure:
Cross-AC closure:
Evidence limits:
Cleanup / terminal conditions:
Ticket status currently observed:

Checkpoint: PRE_PROGRESSION
Protected next phase: FINAL_VERIFIED_AND_GUARDED_READY_TO_DONE
Checkpoint state: PARENT_CONTINUATION_REQUIRED
```

Parent reviews only obvious closure errors: missing authored Flow/AC, `INCONCLUSIVE` evidence paired with candidate `VERIFIED`, missing heuristic disposition or Scope/Non-Goals closure, incomplete cleanup, target/status drift, or direct internal contradiction. Parent does not rerun runtime verification or issue its own verdict. `FAILED` and `INCONCLUSIVE` candidates have no `PRE_PROGRESSION` checkpoint and terminate without `done` mutation.

On Parent `CONTINUE`, the delegated verifier rechecks currentness and performs the existing guarded progression. On `STEER`, it reopens only the bounded Flow/evidence/closure identified by Parent and resubmits `PRE_PROGRESSION` if the candidate remains `VERIFIED`. Parent may use `STOP` at `PRE_PROGRESSION` only when current authority, target currentness, current user instruction, evidence closure, or progression authority means candidate `VERIFIED` can no longer be finalized. On that `STOP`, the delegated verifier re-adjudicates the candidate under that exact evidence limit and emits the existing terminal `READY TICKET VERIFICATION RESULT` with `Verification Verdict: INCONCLUSIVE`, `Ticket Progression: NOT APPLICABLE`, and `Ticket status after verification: ready`; it performs no `done` mutation. Parent Main does not issue or substitute that verdict.

Every terminal verdict closes the bound verification execution through `ready_guard finalize_verification`; do not leave the guard active after emitting a terminal result. `FAILED` and `INCONCLUSIVE` finalize with `Ticket Progression: NOT APPLICABLE` and perform no status mutation.

Before candidate `VERIFIED` on normal `ready`:

1. Re-read the exact Ticket and require the verification target/source/config/build identity used for the verdict is still current and attributable.
2. Resolve the current canonical To Tickets validator through the same admission path and require exact `VALID`.
3. Re-resolve current parent Spec and adopted Behavior/UI authorities and require the same projection/currentness checks still hold with no unresolved material semantic-contract defect.
4. Require the Ticket is still the exact canonical `Status: ready` contract that was verified.
5. Call `ready_guard finalize_verification` with the exact verification execution and `verdict: VERIFIED`. `Perform one guarded targeted replacement` remains the progression invariant: the runtime rechecks target/authority currentness, performs the only allowed top-metadata `Status: ready` -> `Status: done` replacement, and immediately requires exact `VALID` post-write validation. Do not perform this mutation through generic file tools.

When the runtime reports success, report `Ticket Progression: COMPLETED` and `Ticket status after verification: done`.

If the guarded write or post-write validation fails, preserve `Verification Verdict: VERIFIED` but report `Ticket Progression: FAILED` and the exact observed status/failure. Do not rewrite ACs, Verification flows, Spec, Scope, Behavior/UI authority or other planning meaning.

The finalizer preserves bytes/mode except the one top-metadata status, records exact before/candidate intent, uses status-only compare-and-swap atomic replacement and validates the actual canonical Ticket path after writing. Only its exact expected candidate is exempted as the intended authority transition; other authority/source drift still blocks. On failure it conditionally restores ready only if candidate bytes, owner and authority still match. Do not overwrite an external edit, infer success from a done string, or drop a reservation before durable progression/intent recovery closes. Report actual status and exact recovery limit even when verdict is VERIFIED, progression FAILED and bytes remain done.

Diagnostic re-verification of `done` still calls `finalize_verification`, never rewrites status, and reports `Ticket Progression: NOT APPLICABLE`.

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
Heuristic finding dispositions: None | <finding -> disposition>
Material turn reports: None | <concise list>
Checkpoint decisions:
- PRE_RUNTIME: CONTINUE | STEERED_THEN_CONTINUE | STOP | NOT_APPLICABLE
- MATERIAL_TURN: None | <turn -> decision>
- PRE_PROGRESSION: CONTINUE | STEERED_THEN_CONTINUE | STOP | NOT_APPLICABLE

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

When final `INCONCLUSIVE` is caused specifically by an authority/evidence-attribution/target-currentness boundary, or when a `VERIFIED` evidence verdict cannot complete guarded progression, append the same `Decision / Governing authority / Observed condition / Effect / Next allowed action` provenance fields. Do not append them to a normal evidence-complete `FAILED` verdict merely because the product contradicted the Ticket.
