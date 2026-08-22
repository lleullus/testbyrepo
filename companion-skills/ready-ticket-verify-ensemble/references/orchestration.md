# Ready Ticket Ensemble Verification Orchestration

## 1. Canonical meaning and topology boundary

This reference changes only how one exact Ready Ticket verification is executed. It does not create a different verification meaning.

Main applies the current sibling DIRECT verifier's canonical rules for:

- canonical validator admission and Ticket status;
- current parent Spec and Behavior/UI authority;
- semantic contract checking without inventing stronger meaning;
- stable target attribution;
- authored Verification-flow preservation;
- evidence sufficiency and disposition handling;
- `SATISFIED | CONTRADICTED | INCONCLUSIVE`;
- `PASS | FAIL | INCONCLUSIVE`;
- `VERIFIED | FAILED | INCONCLUSIVE`;
- Scope/Non-Goals, cross-AC and cleanup closure;
- guarded `ready -> done`; and
- no automatic remediation or planning continuation.

Do not inherit the sibling skill's DIRECT-only child topology. In this skill, analysts are advisory read-only roles under Main-owned verification authority. Main itself executes the frozen product/runtime actions and owns the resulting raw evidence packet.

## 2. Purpose-first materiality discipline

The ensemble exists to reduce false `VERIFIED` results caused by weak reasoning at two transformations:

```text
approved contract -> material proof obligations
raw evidence -> supported product meaning
```

Do not manufacture objections merely because four analysts are available. Main admits a blocking or decision-relevant objection only when it contains:

1. an exact Ticket/Spec/Behavior/UI contract anchor;
2. a concrete plausible state, observation gap or evidence-attribution condition;
3. a causal path to a false `SATISFIED`, false `CONTRADICTED`, wrong AC verdict or unsafe progression; and
4. material impact on an approved product claim, evidence attribution or terminal safety.

Preference, style, a theoretically better check, remote hypothetical, duplicate wording or a non-material difference is not an objection. After a question is decisively closed, stop adding confidence-only duplicate checks.

## 3. Wave 0 — Main admission and target snapshot

Main performs this wave directly before any child assignment.

### 3.1 Canonical admission

Follow the sibling DIRECT verifier's current canonical admission path:

1. resolve the current `iis-workflow` skill as the To Tickets authority locator;
2. locate the adjacent `validate_ticket.py`;
3. run it against the exact absolute Ticket and require exact `VALID`;
4. derive all Ticket authority fields from that validated Ticket;
5. resolve exact parent Spec and adopted Behavior/UI authority; and
6. enforce the current Ticket status semantics.

No analyst result can cure failed canonical admission.

### 3.2 Stable target packet

Record a bounded current target packet sufficient to attribute every report and later evidence. Include what applies:

```text
Verification Invocation:
Ticket path:
Ticket SHA / canonical identity:
Parent Spec path and SHA:
Behavior/UI authority paths and SHAs:
Project Root:
Workspace ID:
Git branch / revision:
Working-tree identity:
Build/artifact identity:
Runtime version/checkpoint:
Canonical acceptance surfaces:
External/operator conditions:
```

Use current existing identities. Do not create a retained verification ID, repository file, workflow state or evidence ledger.

### 3.3 Assignment identities

Create invocation-local assignment labels for the four analyst roles. Preserve:

- assignment ID;
- logical role;
- actual worker identity when returned;
- target packet identity;
- phase (`PREFLIGHT`, `POST_RUN`); and
- terminal report status.

These values remain in Main's current context only.

## 4. Wave 1 — Independent analyst preflight

Assign all four roles from [role-contracts.md](role-contracts.md).

### 4.1 Independence

- Give each role the same exact authority/target packet.
- Give only the evidence allowed by that role.
- Do not provide another role's conclusions, Main's suspected defect or an intended verdict.
- Prefer four simultaneous child contexts.
- With only two independent contexts, run two roles and then the other two; do not disclose first-batch results to the second batch.
- Do not use one continuing context for several roles when it retains prior role conclusions.

### 4.2 Read-only boundary

All Wave 1 roles are read-only. They may inspect authorized repository, artifact, runtime-description or canonical documents only as their role permits. They may not trigger product effects, modify files, change Ticket status, invoke implementation, or delegate.

### 4.3 Report identity gate

Before using any report, Main confirms:

- assignment ID and role match;
- actual Project Root matches;
- exact Ticket matches;
- actual target fingerprint matches the Wave 0 packet; and
- report terminal status and mandatory fields are present.

A successful report from another target is not partial evidence. Discard it for this verification.

## 5. Wave 2 — Main preflight fan-in and scenario freeze

### 5.1 Invocation-local objection table

Main converts material analyst findings into this table:

```text
Objection ID:
Origin role / worker:
AC / Flow / authority:
Exact contract anchor:
Concrete condition or false-verdict path:
Causal path:
Material effect:
Evidence or inference:
Status: OPEN | CLOSED | UNRESOLVED
Closure basis:
```

Do not count supporting or opposing workers.

### 5.2 Objection admission

Use the purpose-first materiality discipline. Record `NOT ESTABLISHED` analyst concerns as attempted challenges, not open objections.

An analyst finding does not become authority merely because it is detailed. Main reopens the exact anchor and confirms that the finding concerns current approved meaning.

### 5.3 Objection closure

An `OPEN` material objection closes only through one of:

1. exact higher/current authority showing that the alleged obligation or premise is not part of the contract;
2. fresh direct evidence establishing that the concrete false-verdict path cannot hold on the current target;
3. one bounded targeted rebuttal that identifies and disproves the finding's exact premise with attributable authority/evidence; or
4. the originating role, after receiving the new exact authority/evidence, explicitly withdrawing the finding.

Other workers' disagreement, confidence, majority or silence is not closure.

Allow at most one targeted rebuttal round per objection in this invocation. If the objection remains materially disputed, classify it `UNRESOLVED`; do not create a debate loop.

### 5.4 Preflight disposition

Do not start Main's product/runtime execution when any of the following remains:

- material semantic-contract defect that prevents the authored flow from deciding an approved claim;
- current Ticket/parent/Behavior/UI projection contradiction;
- decision-critical target or authoritative-readback boundary unresolved;
- unauthorized, unsafe or currently unexecutable authored action; or
- target packet drift.

Return without AC verdicts:

```text
VERIFICATION NOT STARTED
Execution Mode: ENSEMBLE
Ticket:
Reason:
Open / unresolved material objections:
AC verdicts: Not issued
```

### 5.5 Scenario freeze

When no blocking objection remains, Main authors and freezes one integrated scenario using every authored Verification flow in order. Preserve exact authored labels and boundaries, then state:

```text
Flow ordinal:
Authored contract:
Setup:
Exact Main actions / canonical inspections:
Evidence capture points:
Bounded absence universe, when applicable:
Preservation checks, when applicable:
Cleanup / terminal condition:
SATISFIED evidence condition:
CONTRADICTED evidence condition:
INCONCLUSIVE evidence condition:
```

Derived checks may close a concrete false-verdict or attribution path, but may not invent a new trigger, product requirement, acceptance surface or stricter result.

### 5.6 Informational preflight report

Before Main execution, emit:

```text
ENSEMBLE VERIFICATION PREFLIGHT REPORT

Ticket:
Execution Mode: ENSEMBLE
Main verifier:
Target packet:
Analyst roles / worker identities:
Material objections: None | <closed/open summary>
Scenario blocks:
Authoritative readbacks:
Absence / preservation boundaries:
Main execution actions:
Cleanup / terminal conditions:
Authority-required actions:
Execution disposition: PROCEED | AUTHORITY REQUIRED | BLOCKED
```

This is informational, not an approval gate. Continue when `PROCEED` and current authority permits the frozen actions.

## 6. Wave 3 — Main direct execution

Main performs the frozen scenario directly on the exact target. This is the only product/runtime execution path in the ensemble lifecycle.

### 6.1 Single execution ownership

- No analyst executes the trigger or owns runtime mutation.
- Main does not delegate a separate execution runner.
- Main may coordinate common setup/cleanup across authored flows only when the frozen scenario preserves their meaning.
- Main captures raw observations, authoritative readbacks, evidence limits and cleanup/terminal state before adjudication.

### 6.2 Target and action gate

Before each material action, Main confirms the actual root and current target still match the frozen target packet. A mismatch stops execution; do not choose another root, revision, environment or path to bypass the mismatch.

For each flow Main records:

```text
Flow ordinal:
Target before:
Actions actually performed:
Exact command/interaction/canonical inspection:
Raw observation/output:
Authoritative readback anchors:
Artifact/screenshot references:
Missing evidence:
Directly observed contradiction:
Cleanup / terminal condition:
Target after:
Unrelated target drift:
```

This Main-owned packet is raw verification evidence. Do not pre-label it with flow/AC/Ticket verdicts before Wave 4 review.

### 6.3 State-changing uncertainty

A network/transport failure during a mutation-capable Main action does not prove success or failure and does not prove anything about the target files/data.

Do not immediately repeat the same action. Main first reads current authoritative state and any existing operation history that the contract already provides.

- If fresh readback establishes the action definitely did not occur and a repeat remains authorized/safe, Main may perform a new explicit attempt after recording that state check.
- If execution or duplicate effect cannot be determined, affected flow evidence is `INCONCLUSIVE`.
- Do not add a new ledger merely to resolve the uncertainty.

## 7. Wave 4 — Independent post-run evidence review

Return Main's raw evidence packet to all four logical analyst roles.

Prefer resuming the exact role worker. When resumption is unavailable, start a fresh isolated worker for that logical role with only:

- its original assignment;
- its own preflight report;
- the frozen target/scenario;
- Main's raw execution evidence; and
- no other role conclusions or Main tentative verdict.

Each role performs only its post-run responsibilities from [role-contracts.md](role-contracts.md).

Use the same report identity and material-objection rules as Wave 1/2.

## 8. Wave 5 — Main final adjudication

### 8.1 Evidence attribution gate

Before adjudication, require:

- same exact target or explicitly attributable authored state transition;
- every required evidence capture point accounted for;
- no stale evidence carried across unrelated source/config/build/Ticket drift;
- required cleanup and terminal windows complete; and
- every material post-run objection closed or classified.

If the Ticket, parent authority or implementation target materially changed after Wave 0, do not reuse analyst agreement. Before Main execution, return `VERIFICATION NOT STARTED: ENSEMBLE TARGET CHANGED`. During/after Main execution, classify affected flows `INCONCLUSIVE` unless a direct attributable contradiction remains current.

### 8.2 Flow truth table

Main applies this order for each authored flow:

```text
Fresh attributable evidence directly violates the authored decision boundary
  -> CONTRADICTED

A required observation/readback, target attribution, material objection,
cleanup or terminal condition remains unresolved without direct contradiction
  -> INCONCLUSIVE

All authored obligations are established by decisive current evidence,
with no material semantic or decision-boundary contradiction
  -> SATISFIED
```

Worker labels never substitute for this Main-owned determination.

### 8.3 AC and Ticket truth tables

```text
Any required mapped flow CONTRADICTED for the AC obligation
  -> AC FAIL

All mapped obligations SATISFIED
  -> AC PASS

Otherwise
  -> AC INCONCLUSIVE
```

```text
All ACs PASS          -> VERIFIED
Any AC FAIL           -> FAILED
Otherwise             -> INCONCLUSIVE
```

Do not convert a semantic-contract defect into an implementation `FAIL`. A preflight contract defect receives no AC verdicts. A post-run evidence/readback insufficiency that prevents a decisive result yields `INCONCLUSIVE` unless direct evidence contradicts the authored boundary.

### 8.4 Scope and terminal closure

Before `VERIFIED`, Main directly reconciles Scope, Non-Goals, cross-AC obligations, Behavior/UI authority, cleanup, duplicate-sensitive effects and terminal windows using the current target.

## 9. Guarded Ticket progression

For a normal `Status: ready` Ticket, Main attempts `ready -> done` only after final `VERIFIED` and the sibling DIRECT verifier's full guarded progression sequence:

1. re-read exact Ticket and current target identity;
2. require current canonical validator exact `VALID`;
3. re-resolve current parent Spec and adopted Behavior/UI authority;
4. require no unresolved material objection, drift or cleanup gap;
5. require the exact unchanged canonical `Status: ready` contract;
6. guarded targeted replacement of only the top metadata status line; and
7. immediate exact `VALID` post-write validation.

Keep verdict and progression separate. If the write or post-write validation fails, preserve `Verification Verdict: VERIFIED` and report `Ticket Progression: FAILED` with exact current status.

A diagnostic re-verification of `done` never rewrites status.

## 10. Errors and bounded retries

### 10.1 Read-only analyst transport error

Main may retry the same exact read-only assignment with the same role, target and allowed evidence up to three times. Do not change paths/options as a retry. A changed assignment is a new experiment and must be labeled as such.

### 10.2 Analyst report defect

A malformed, incomplete or internally inconsistent report is a completed tool/application result, not a transport error. Do not blindly rerun it. Mark the role `UNRESOLVED` or issue at most one targeted correction assignment naming only the missing required fields while preserving the same target and role question.

### 10.3 Session/context error

If the host returns an expired/unknown child session or workspace identity, reopen/reinitialize the relevant context and use the new explicit identifier. Do not continue sending the stale identifier and do not infer a server restart.

### 10.4 Retry exhaustion

When the safe retry/correction boundary is exhausted, stop and report:

```text
Confirmed state:
- successful calls and actual targets

Failure boundary:
- failed call, exact error and error layer

Established facts:
- facts supported by successful target-matched results

Unconfirmed:
- facts not established because of the failure

Next safe action:
- exact minimal read retry, context reinitialization or state readback
```

## 11. Final report

Return one concise fan-in result. Do not dump every worker transcript.

```text
READY TICKET VERIFICATION RESULT

Ticket:
Execution Mode: ENSEMBLE
Main verifier identity:
Ticket status before verification:
Verification target:
Target stability:

Team execution:
- CONTRACT_INTERPRETER: <worker / terminal>
- ORACLE_CHALLENGER: <worker / terminal>
- EVIDENCE_ARCHITECT: <worker / terminal>
- SEMANTIC_MATERIALITY_REVIEWER: <worker / terminal>
- Main execution: DIRECT
- Concurrency used:

Preflight:
- Material objections opened:
- Objections closed and basis:
- Unresolved objections:

Scenario and evidence:
- Executed scenario blocks:
- Environment / external conditions:
- Absence / preservation boundaries:
- Cleanup / terminal conditions:
- Evidence limits:

Flow results:
- Flow ordinal / parent outcome:
  AC ordinals:
  Result: SATISFIED | CONTRADICTED | INCONCLUSIVE
  Runtime / canonical observation:
  Authoritative readback:
  Material analyst finding and resolution:
  Remaining uncertainty:

AC results:
- AC ordinal:
  Verdict: PASS | FAIL | INCONCLUSIVE
  Linked flows:
  Main verifier evidence:
  Remaining uncertainty:

Scope / Non-Goals:
Cross-AC findings:
Implementation-report differences:

Verification Verdict: VERIFIED | FAILED | INCONCLUSIVE
Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED
Ticket status after verification:
```
