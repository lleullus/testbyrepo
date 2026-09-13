# Ready Ticket Verification Workflow

## 1. Subagent-only invocation

At top level, Parent Main dispatches exactly one task with `authorityProfile: iis-ready-verifier/v1`, the selected verifier model/effort, and the complete assignment below. Do not supply caller `outputSchema` or `schemaMode`; the host profile owns the strict terminal schema. There is no `DIRECT` verifier mode, same-Main semantic-verdict/finalizer path, verifier roster, or capability-based topology fallback. If the required subagent capability is unavailable, return `SUBAGENT CAPABILITY UNAVAILABLE` with no product/runtime/status mutation.

The delegated verifier owns the whole verifier core and never delegates it again. Its assignment binds:

```text
Ticket:
Candidate Verification Target:
Implementation Report / Evidence:
Execution Plan / Review: None | <exact optional outside-root plan_review_path>
Known Coverage Findings: None | <exact prior Coverage result and relevant correction/new evidence>
Additional User Instructions:
Delegated Verifier: yes
```

The actual caller resolves [verify SKILL.md](../SKILL.md) and [references/verify.md](verify.md) from the current pinned IIS bundle and includes both exact readable paths in that assignment, with an instruction to read them before work and apply only the delegated verifier core. A role name or the caller's read/summary is not a substitute. Keep `Delegated Verifier: yes`; bind the exact inputs and required evidence/report locations under this contract, and instruct the worker to return the existing admission failure or its host terminal after all applicable authored obligations, readback, settlement and cleanup are handled. It must not remediate implementation, dispatch Coverage or finalize. These are assignment instructions, not additional terminal-schema fields.

For an Adaptive invocation, receive its unchanged Common original sources block from [the shared source assignment](../../../iis-adaptive-planning/templates/SHARED-SOURCE-ASSIGNMENT.template.md). Read the bound originals before accepting caller framing and use them in the existing semantic projection check; a caller's narrower test suggestion cannot redefine success. Preserve exact Ticket scope, existing admission returns and the host terminal schema. Standalone verification retains its existing authority inputs without requiring Adaptive activation.

The delegated verifier owns canonical admission, semantic contract check, complete authored Flow denominator, scenario authorship, runtime/canonical evidence, finding disposition, every Flow adjudication, every AC verdict, Scope/Non-Goals and cross-AC closure, and the whole-Ticket semantic verdict. It never owns the status write. Parent Main does not perform a second verification pass.

### SUBAGENT terminal fan-in and settlement

The verifier runs one invocation-local evidence cycle and returns exactly one terminal `READY TICKET VERIFICATION RESULT`. There are no IIS verification checkpoints, release decisions, execution leases, or persistent verifier sessions.

1. exactly one delegated verifier owns the same Ticket/stage at a time;
2. the verifier captures the immutable verification binding before product/runtime scenario action;
3. normal scenario progress and settled command failures stay inside that invocation;
4. if target identity, effect partition, or authority becomes unattributable, the verifier terminates with the applicable `VERIFICATION NOT STARTED | FAILED | INCONCLUSIVE` result rather than waiting for Parent continuation;
5. after fixing the semantic verdict, the verifier emits its exact terminal result and exits successfully; it does not seal a verdict record;
6. OMP captures non-forgeable finalization authority only for that exact successful Ready Verify terminal return and delivers one opaque terminal handle;
7. for VERIFIED from ready, Parent obtains one read-only Coverage terminal before success submission under §14; for other results, existing non-progressing finalization remains. Parent submits only the applicable exact host-delivered handle and never extracts or recreates verdict authority.

After successful background verifier dispatch, Parent Main does not poll normal progress or completion. It does not call `hub wait`, `hub jobs`, `hub list`, or `hub inbox`, send a status request, or duplicate repository/runtime inspection solely to observe the verifier. It stands by once and lets the host-delivered terminal result wake it; routing and `ready_finalize` begin only from that exact result.

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

Freeze every authored flow and conditional boundary as the mandatory scenario, adjudication and report denominator. This gate never permits omission from that denominator, weakening, or merging materially distinct flows. After a decisive attributable failure, §9 may leave only information-value-negative remaining work unexecuted and explicitly `INCONCLUSIVE`; it never permits `VERIFIED` without all contract-required execution and sufficient fresh evidence for every applicable flow.

Add a derived positive variation, counterexample, boundary exercise or observation only when it materially tests an authored decision boundary, closes a concrete false-verdict path or prevents a concrete attribution error. Require a contract anchor and plausible failure path. Do not expand the scenario merely for exhaustiveness.

Do not introduce or change product obligations, supported conditions, Scope, acceptance surfaces or decision criteria. Preserve every authored mandatory flow and explicit initial condition. Within the approved usage and existing action authority, a derived variation of data, entity identity or execution order may exercise the same obligation when a current implementation-grounded failure path makes that variation material. Such a variation supplements, rather than replaces, the authored flow. Do not expand into unrelated mutation or exhaustive coverage; prefer the smallest sufficient scenario.

For every material finding discovered while grounding/executing this scenario or supplied through navigation (including a prior Coverage result), reopen its current contract anchor and assign one verifier-owned disposition. A concrete path rejected using current evidence is recorded with that evidence; do not require a failure reproduction for a hypothesis already decisively refuted.

```text
Finding Disposition:
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

Navigation never substitutes for fresh verifier-owned evidence. Prefer the safely minimized trigger; same-cycle evidence directly obtained by this verifier can support both discovery and adjudication without repeating a risky effect. The verifier's final judgment remains independent from prior implementation narration/self-check.

### Scenario challenges and known findings

The separate additional implementation-path frontier search belongs to `ready-ticket-coverage` after a successful terminal. Do not add a mandatory separate frontier pass to this verifier cycle. Continue grounding each flow's discrimination in the actual entrypoint, deciding state/effect and authoritative readback, and resolve every known material counterexample under the existing evidence rules. Source/schema inspection selects discriminating execution; it does not replace runtime evidence.

For an authorized scenario challenge, preserve initial state and target identity, use the smallest sufficient trigger, and capture primary output/readback before cleanup. Keep observed facts separate from inference; transport failure does not decide mutation outcome. Stop trigger minimization when it loses reproducibility, crosses authority, becomes unsafe or no longer answers the contract question. Record the exact contract anchor, actions, observed result, authoritative comparison, primary evidence, identity, cleanup state and uncertainty. Agreement is not evidence. Required risky/external/one-shot actions retain current Ticket/user authority; the verifier never delegates or expands that authority.

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

For runtime claims, ground `Nearest nonconforming state` in a concrete failure of a current implementation assumption, `Discriminating observation` in the actual result that differs between conforming and failing implementations, and `Sensitivity activation` in the initial state and execution that exposes that difference. Do not select only total non-operation when current evidence supports a material implementation that succeeds on the chosen happy path but fails during another reachable use covered by the same obligation. If that implementation would also pass the proposed observation, choose the smallest authorized activation and readback that distinguishes it. Do not invent a counterexample quota or require speculative cases without a current contract and implementation anchor.

Use the existing Derived Execution Plan fields to make clear why the selected current observation or real execution is sufficient to distinguish the flow's `SATISFIED`, `CONTRADICTED`, and `INCONCLUSIVE` conditions. Choose that evidence from the authored obligation and current changes to code, data volume or distribution, configuration, runtime, shared state, owners, and read paths; do not turn this choice into a separate exhaustive independence audit. Common setup and same-cycle verifier-owned evidence may support multiple flows only when each flow's initial conditions, contract-required actions, observation window, and decision boundary are actually satisfied. If later scenario work changes shared state or another premise on which earlier evidence depended, refresh the affected observation under the existing target-attribution and cross-AC rules.

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
Execution Mode: SUBAGENT
Verifier: <delegated verifier identity>
Ticket status:
Verification target:
Target-stability check:
Environment:
External/operator conditions:
Semantic contract check: <no material gap found | exact blocking defect already returned before execution>
Known material counterexamples: None | <scenario-discrimination challenges / supplied findings and their current basis>
Findings / proposed verifier dispositions: None | <finding -> disposition>

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

The report is informational and records the immutable binding captured before scenario execution. No Parent release/checkpoint is required. Parent does not execute the flows or issue AC verdicts; it receives only the eventual terminal verifier result.

## 9. Evidence sufficiency and execution

The verifier directly obtains the smallest sufficient fresh, attributable evidence for every authored flow whose verification remains required under the verdict-specific rules below. Preserve every contract-required action, initial condition, acceptance boundary, observation window and terminal condition. Freshness alone does not require replaying an earlier setup or trigger.

Use current authoritative canonical/product inspection when it fully decides the authored obligation. Execute the necessary real path when the obligation requires behavior, transition, ordering, persistence, performance or an external effect that current-state inspection cannot establish. Use full end-to-end execution when the contract requires that connection or a narrower observation would miss a material false-verdict path; do not choose it merely for freshness.

Use changes to code, configuration, data volume or distribution, runtime, shared state, owners and read paths to determine which conditions and observations are necessary, not as permission to carry a prior `PASS` or omit current evidence. Do not require a separate exhaustive proof of independence for every flow. File-diff absence, prior `PASS` and implementation narration do not close a current flow. Every authored flow remains in the scenario and terminal adjudication denominator whether satisfied by current inspection, by necessary real execution, or explicitly left `INCONCLUSIVE` after a decisive failure.

Evidence priority when applicable:

1. actual runtime / canonical acceptance-surface observation;
2. authoritative product/canonical readback;
3. rendered UI interaction/readback when UI is the acceptance surface;
4. real execution in an authorized disposable/controlled environment when it exercises the approved implementation, entrypoint, state/effect, lifecycle, and readback;
5. source/diff/unit tests and supporting doubles as explanation/navigation, not proof of a boundary they replace.

A mock, stub, canned response, seeded success state, or surrogate readback cannot prove the actual acceptance boundary it substitutes for. A double for an ancillary dependency need not invalidate observations of an unrelated real boundary; never claim the double's replaced boundary was verified. Test format or disposable location alone does not invalidate evidence that actually exercises and observes the required real path. Required provider/external effects need their approved effect readback, not merely internal success or HTTP acceptance.

Directly inspect an artifact, source, document, schema, plan, or simulator when that actual deliverable is the original approved result, faithful to parent authority and current user instructions; do not demand invented runtime or claim unobserved external/product effects. Apply §3 to a flow that substitutes for required meaning rather than repairing it inside verification. If a valid real boundary is unavailable, preserve `INCONCLUSIVE` unless attributable evidence establishes contradiction; neither unknown nor contradiction becomes fake success.

For runtime claims, use the existing `Nearest nonconforming state`, `Discriminating observation`, and `Sensitivity activation` to determine whether this run actually exercised the required boundary. Do not mark a flow `SATISFIED` without the declared discriminating readback and its sensitivity activation; passing implementation tests or source-only mechanism shape cannot substitute.

A successful happy-path execution does not satisfy an affected flow while a current, contract-anchored material counterexample remains unresolved. Obtain the discriminating runtime evidence, or dismiss the path using current evidence that it is unreachable, already handled or outside the approved obligation; dismissing a hypothesis does not replace otherwise required runtime execution. If required decisive evidence cannot be obtained, keep the affected flow `INCONCLUSIVE`; an attributable contradiction makes it `CONTRADICTED`. Lack of authority or evidence is not itself a product failure. Apply the existing flow-to-AC adjudication and failure-aware continuation rules below without adding a new verdict.

### Failure-aware ordering and continuation

After semantic preflight and binding capture, order scenario work without changing authored dependencies, initial state, ordering, shared-state or one-shot-effect meaning: first establish target/authority/attribution, then execute and observe the cheapest decisive flow or same-cause group, then reclassify remaining work under this section before starting another setup, long wait or separate external action, and finally perform the remaining required acceptance flows. Do not batch an unrelated high-cost or effectful trigger with cheaper potentially decisive checks in a way that prevents this evidence-driven continuation decision. Common setup, environment and cleanup may be reused only when flow meaning remains intact.

A first failure is not by itself a stop condition. Only after fresh attributable evidence directly contradicts an authored decision boundary and thereby fixes at least one AC `FAIL` and whole-Ticket `FAILED`, classify remaining work as follows:

- continue same-setup observations that cheaply establish other uses of the same failed assumption;
- continue observations that can change failure validity, target attribution, cause/implementation owner or the bounded correction span;
- finish every started product/external effect's required settlement, authoritative readback and cleanup;
- finish authored ordering, absence-window or terminal-condition work needed to make the observed failure itself valid;
- execute the user's requested diagnostic scope only when current Additional User Instructions explicitly require all-item diagnosis; the ordinary request to verify a whole Ticket is not such a request;
- when information value is uncertain but the observation is cheap, perform it before deciding;
- leave unexecuted a flow unrelated to the established failure when it requires new setup, a long wait or a separate external action and cannot realistically change verdict, attribution, correction span or required cleanup. This is the default cost boundary, not optional extra coverage.

All of the following are required for such non-execution: the contradiction is bound to the current target; it alone fixes whole-Ticket `FAILED`; the omitted flow has no realistic path to change the failure's validity, attribution, correction span or mandatory cleanup; and the report records the omission and material basis. Every authored Flow/AC remains in the reporting and adjudication denominator by receiving an explicit result; that denominator does not require every flow to execute after a decisive failure. Never copy an earlier target's PASS or infer PASS for an unexecuted flow. This rule cannot select `INCONCLUSIVE` merely because required reachable execution is expensive, and it never narrows the work required for `VERIFIED`.

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

For scenario work still required by the failure-aware continuation rule, obtain the fresh observations needed to decide authored positive and material counterexample cases, including ordering, duplicate, interruption, timeout, stale identity, concurrency, refresh/reopen, partial external response, retry, Scope-excluded behavior or user-visible/canonical disagreement only where the Ticket makes them relevant. A single same-cycle setup, action or readback may decide more than one flow or case when it fully activates and discriminates each authored boundary; do not repeat it solely because the obligations are separate. Do not omit a contract-required trigger, condition, observation window, terminal condition or cleanup.

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

A bounded `SCENARIO AMENDMENT` may refine derived execution or add a discriminating variation permitted by §6 without changing authored obligations or weakening decision criteria. Record a material amendment under this section's existing reporting threshold before executing the added action; routine adjustments do not require a new report or approval.

Continue only within the captured stable/effect partition and existing authority. If the required variation cannot remain within those boundaries, or changed evidence makes the binding stale or attribution unsafe, terminate with the applicable `VERIFICATION NOT STARTED`, `FAILED` or `INCONCLUSIVE` result and exact evidence limit, preserving the condition needed for a fresh invocation. Do not wait for Parent continuation, patch an immutable binding, or carry PASS evidence across the drift.

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
- `INCONCLUSIVE`: required evidence, authority, terminal condition or current attribution could not be established without a direct contradiction, or the flow was not executed under the decisive-failure continuation rule and carries its exact material stop basis.

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

Complete every authored cleanup, absence window, process stop, disposable-target disposal and external-effect terminal condition required for attributable evidence. Decisive failure never permits abandoning settlement, readback or cleanup for an effect already started.

A still-running duplicate-sensitive effect, incomplete cleanup or unfinished absence/ordering window prevents final `VERIFIED` when it affects the decision boundary and prevents `FAILED` when needed to make the contradiction attributable. Capture necessary evidence before disposing of a temporary target.

## 14. Terminal semantic result and caller-owned status transition

Keep semantic verification and Ticket progression separate. The delegated verifier owns the semantic result; OMP owns opaque terminal authority; the caller owns post-success Coverage fan-in and the narrow `ready_finalize` invocation, not a second verdict.

For every normal delivery verification captured from `Status: ready`, the verifier fixes one semantic verdict and returns one terminal `READY TICKET VERIFICATION RESULT` with `Verifier Ticket Progression: PENDING CALLER FINALIZATION`. This applies to `VERIFIED`, `FAILED`, and `INCONCLUSIVE`. The verifier never writes `done`, invokes `ready_finalize`, calls `seal_verdict`, or creates a verdict record.

Before emitting semantic `VERIFIED`, the verifier must still ensure within its evidence cycle that:

1. every authored Flow has an attributable final result;
2. every current AC is `PASS`;
3. Scope/Non-Goals, finding dispositions, cleanup, and terminal conditions are closed;
4. no unresolved material semantic-contract defect or evidence conflict remains;
5. the source/config/build target used for the verdict remains attributable to the captured stable target; and
6. no unresolved external-effect settlement gap prevents required evidence from being decisive.

For `FAILED`, require at least one fresh attributable `CONTRADICTED` flow that fixes an AC `FAIL`; keep every authored flow and AC in the report; mark any permitted unexecuted flow and its mapped unresolved obligation `INCONCLUSIVE`, never `PASS`; and complete related cheap observations plus every readback, settlement and cleanup needed to make the failure valid. Uncertainty confined to unrelated permitted omissions does not replace the already established whole-Ticket `FAILED`.

Use whole-Ticket `INCONCLUSIVE` only when current evidence does not establish a direct product contradiction and required authority, environment, readback, terminal condition or attribution is missing. Cost alone is not a basis, and a reachable required observation may not be left unattempted under this verdict.

The readable terminal verifier result includes:

```text
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Stable Target Paths: ["<exact absolute path>", "..."]
Scenario Effect Paths: [] | ["<exact absolute path>", "..."]
Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Verifier Ticket Progression: PENDING CALLER FINALIZATION | NOT APPLICABLE
Observed Ticket Status: ready | done | <actual>
```

OMP accepts finalization authority only from the exact successful terminal result of the delegated Ready Verify worker. Parent Main first applies the caller-owned post-success Coverage sequence below, then calls `ready_finalize({ terminal_handle: "<exact host-delivered handle>" })` only when permitted. It supplies no semantic verdict, binding path/SHA, Ticket, bundle, protocol, or reconstructed payload. Terminal text, copied fields, a fabricated handle, or another caller/session's handle has no authority; an exact retry of the same accepted handle returns the same captured result without another status write.

`ready_finalize` obtains the verifier verdict and binding provenance only from host-owned terminal metadata and rechecks current loaded bundle/protocol identity, current authority, stable target, and canonical Ticket validation. It does not rerun or reinterpret semantic verification.

For an original `ready` binding:

- `FAILED` or `INCONCLUSIVE` -> no status mutation; caller reports the finalizer's non-progressing result.
- `VERIFIED` -> only the finalizer may perform the exact top-metadata `Status: ready` -> `Status: done` compare-and-swap and exact post-write validation.
- unknown/foreign/malformed terminal authority or stable target/authority/Ticket/bundle/protocol drift -> no progression; semantic `VERIFIED` stays `VERIFIED` when readable provenance is available.
- a provenance-free current `done` state is diagnostic, not a new completion.

The finalizer preserves bytes/mode except the one status token, uses exact compare-and-swap atomic replacement, and conditionally restores only this call's exact candidate when post-write validation fails and authority/stable target remain unchanged. It must not overwrite an external edit or infer fresh completion from a `done` string.

Diagnostic re-verification captured from `done` is semantic/diagnostic only and reports `Verifier Ticket Progression: NOT APPLICABLE`; it never reopens or rewrites status.

### Caller-owned post-success Coverage

For normal ready-to-done VERIFIED only, the finalization-owning caller dispatches one independent `ready-ticket-coverage` worker after verifier settlement. Forward exact Ticket/parent/Behavior/UI/user authority, the completed verifier report and primary evidence, and existing target/binding identities. Keep the opaque handle private to the caller. Coverage uses the current applicable user-selected model/effort policy, returns one ordinary read-only terminal, has no verifier authority profile, and never delegates. If Adaptive Outer Main is the caller it performs this step directly; no second verify wrapper or duplicate Coverage invocation is added.

COMPLETE with no unresolved material finding or evidence gap permits submission of that original handle while target/authority remain current. A material finding, PARTIAL/BLOCKED or failed/missing Coverage result withholds success submission: preserve VERIFIED and actual Ticket status, report Coverage result/limits and `Finalization: not called`, and route to the existing verification/correction or contract owner. No response or incomplete review is not no-finding. Do not invent a finalizer return or new semantic verdict. FAILED/INCONCLUSIVE and diagnostic non-progressing terminals skip normal-success Coverage and keep existing finalization.

Supplementary execution/adjudication needs a fresh verifier invocation, binding and terminal, never resumption or edits to an ended result. Forward the finding as navigation; the fresh verifier owns current decisive evidence and every applicable Flow/AC, not just one extra test. Changed source/config/effect paths cannot be patched into the old binding or inherit old PASS. Remediation remains subject to existing implementation/plan authority; a standalone verification request does not authorize automatic repair. Follow-up Coverage uses the new exact report, checks prior gap resolution and materially affected scope, and does not repeat unrelated investigation. No redispatch of the same finding/evidence without a material change or an unattempted authorized discriminating observation.

This adds a real caller procedure, not mechanical Coverage enforcement by the finalizer. Keep opaque handles, terminal schema, binding and guarded status write unchanged. The full read-only investigation/finding/result contract belongs to `ready-ticket-coverage`; no Coverage store, validator or lifecycle is added.

## 15. No remediation loop

Verification ends with evidence and verdict. Do not automatically edit source, invoke `ready-ticket-implement`, create a follow-up Ticket, reopen planning or continue to a later Increment. The caller/user decides the next action.

## 16. Final report

```text
READY TICKET VERIFICATION RESULT

Ticket: <exact absolute canonical Ticket path, byte-for-byte equal to structured `ticket_path`; never a title, basename or relative path>
Execution Mode: SUBAGENT
Verifier: <delegated verifier identity>
Ticket status before verification:
Verification target:
Target stability:
Verification Binding: <exact outside-root path>
Verification Binding SHA256: <sha256>
Stable Target Paths: ["<exact absolute path>", "..."]
Scenario Effect Paths: [] | ["<exact absolute path>", "..."]
Finding dispositions: None | <finding -> disposition>
Material turn reports: None | <concise list>

Semantic contract findings: None | <exact material gap and owning contract location>

Scenario report:
Executed scenario blocks: <each authored flow -> fresh observation or execution used | not executed after decisive failure, with material basis>
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
  Evidence limit: <including `not executed after decisive failure` and the material basis when applicable>

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

`Executed scenario blocks` treats a sufficient fresh canonical/product inspection or explicitly identified same-cycle verifier-owned evidence as completed verification work for that flow; it is neither a skip nor prior-`PASS` carry-over. Record the concrete observation under that flow's existing `Runtime / canonical observation` and `Authoritative readback`. Reserve `not executed after decisive failure` for the §9 cost boundary and leave that flow `INCONCLUSIVE`.

Render both path lists as whitespace-free compact JSON arrays exactly matching the structured arrays, including order and empty `[]` (equivalent to JSON separators `(',', ':')`). Across the complete report, each reserved top-level identity/result label in the template appears exactly once; nested scenario, flow or evidence sections must use different labels rather than repeat `Ticket:`, `Verification Binding:`, `Verification Binding SHA256:`, `Stable Target Paths:`, `Scenario Effect Paths:`, `Verification Verdict:`, `Verifier Ticket Progression:` or `Observed Ticket Status:`.

The delegated verifier returns the report through one strict host terminal `yield` whose data uses schema `iis-ready-verifier-terminal/v1` and exact fields `project_root`, `ticket_path`, `verification_binding`, `verification_binding_sha256`, `stable_target_paths`, `scenario_effect_paths`, `verification_verdict`, `ticket_progression`, `observed_ticket_status`, and `report`. Every field must equal the corresponding readable report/binding fact; `report` contains the complete text above. Text-only narration, a caller output schema, or copied task output does not create finalization authority.

The delegated verifier stops at this report and exits successfully. OMP validates and privately persists that exact terminal result, then delivers its opaque handle to Parent Main. Parent applies §14 post-success Coverage, submits only the eligible exact handle to `ready_finalize`, and appends its actual `Verification Verdict`, `Ticket Progression`, `Progression Basis`, `Ticket Status After`, host provenance and progression detail. When Coverage withholds submission, report the exact review and `Finalization: not called` instead. The verifier report contains no transferable finalization credential.

When final `INCONCLUSIVE` is caused specifically by an authority/evidence-attribution/target-currentness/effect-settlement boundary, or when a `VERIFIED` evidence verdict cannot complete caller finalization, append the same `Decision / Governing authority / Observed condition / Effect / Next allowed action` provenance fields. Do not append them to a normal evidence-complete `FAILED` verdict merely because the product contradicted the Ticket.
