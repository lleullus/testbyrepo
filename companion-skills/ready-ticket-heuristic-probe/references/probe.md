# Ready Ticket Heuristic Probe Workflow

## 1. Invocation and execution mode

Bind:

- exact absolute Ticket path;
- current user instructions;
- optional implementation/candidate-target navigation;
- any explicit execution-mode instruction for this exact probe stage.

Execution mode rules:

```text
No explicit mode selection -> SUBAGENT
Explicit DIRECT selection -> DIRECT
Explicit SUBAGENT selection -> SUBAGENT
```

The top-level default requires no separate SUBAGENT opt-in. Apply the default or explicit user override, not task complexity, expected value, model capability, cost, lane count or available worker capacity. If required child capability is unavailable, return `SUBAGENT CAPABILITY UNAVAILABLE`; do not silently run DIRECT instead, and do not convert a DIRECT failure into SUBAGENT. The default applies only to top-level invocations, not delegated lane workers.

A delegated worker receives `Delegated Probe Worker: yes` and performs only its assigned lane. It does not delegate again.

## 2. Canonical admission and authority

Before any product/runtime action:

1. resolve the current installed `iis-workflow` skill only as the planning-authority locator;
2. follow its current To Tickets route and require the adjacent `validate_ticket.py`;
3. run that validator against the exact absolute Ticket and require exact `VALID`;
4. derive Ticket metadata, ACs, Scope, Non-Goals, Blockers, Verification flows, Behavior Authorities, UI authority and References from the validated Ticket;
5. resolve the exact current Parent Spec and applicable Behavior/UI authorities;
6. require normal delivery status exact `ready`;
7. bind the actual current implementation target from direct repository/runtime observation; and
8. record enough target identity to distinguish later drift without creating a retained probe identifier.

Return without product/runtime probing when admission cannot be established:

```text
HEURISTIC PROBE NOT STARTED
Ticket:
Reason:
Probe findings: Not issued
```

Structural `VALID` proves schema admission only. It does not establish product correctness, current target availability, heuristic materiality or any verifier verdict.

Implementation reports, test output, logs and candidate target descriptions are navigation/support unless the approved product contract makes that exact surface authoritative.

## 3. Heuristic method and purpose gate

Load the current installed `production-heuristic-probing` skill for the investigation method. Use its principles to:

- examine actual black-box behavior rather than trusting documented ideal behavior;
- prefer the smallest state-changing or behavior-distinguishing trigger before building complex machinery; and
- cross UI, modality, authentication, cache, network, provider, persistence or other boundaries when a current Ticket-derived question materially crosses them.

Apply the sibling `purpose-first-review` discipline before admitting a lane. A lane must materially protect the purpose of avoiding false delivery completion; mere curiosity, theoretical completeness or a cleaner test design is insufficient.

The heuristic method and purpose review do not create product authority. Ticket/Spec/Behavior/UI meaning remains controlling.

## 4. Probe Frontier Matrix

Review every authored Verification flow and every applicable authored conditional boundary once before deciding the frontier. Preserve authored labels and mappings for navigation; do not rewrite or strengthen them.

For each flow/boundary record:

```text
Probe Frontier Matrix Entry

Flow / boundary:
Contract / Behavior anchor:
Plausible false-completion or attribution path:
Observable consequence:
Authoritative readback:
Disposition: ADMIT_LANE | NO_DISTINCT_HEURISTIC_LANE
Reason:
```

Admit a lane only when all four conditions exist:

1. exact current product-contract anchor;
2. concrete plausible failure or false-attribution path;
3. material observable/canonical consequence; and
4. executable/inspectable current readback within existing authority.

Reject lane creation based only on:

- generic fuzzing or chaos testing;
- implementation-detail curiosity;
- future hardening or hypothetical extensibility;
- an unrelated security or infrastructure concern;
- a remote failure with no plausible current path;
- desire to use an available worker;
- arbitrary AC/file/module partitioning; or
- confidence-only duplication of an already decisive lane.

One lane may cover several authored flows when the same concrete failure path crosses them. Do not split one material path merely to create more workers.

If every entry is `NO_DISTINCT_HEURISTIC_LANE`, no runtime perturbation or worker dispatch is required. Finish after recording the bounded frontier and current target/authority checks.

## 5. Frontier report

Before the first product/runtime action or SUBAGENT assignment, emit an informational report:

```text
HEURISTIC PROBE FRONTIER REPORT

Ticket:
Execution Mode: DIRECT | SUBAGENT
Heuristic Probe Lead: Main
Ticket status:
Probe target:
Authority Snapshot: <Ticket + Parent Spec + applicable Behavior/UI current identities>
Target-stability check:
Heuristic method: production-heuristic-probing

Probe Frontier Matrix:
- <all authored flow/boundary entries>

Lane assignments: None | <lane -> worker>
Parallel-safe lanes: None | <lanes>
Sequential-only lanes: None | <lanes and reason>
External/operator conditions:
Cleanup boundaries:
Authority-required actions:
Execution disposition: PROCEED | AUTHORITY REQUIRED | BLOCKED
```

This is informational, not an approval gate. Continue authorized probing when `PROCEED`. If existing user/operator authority is actually required, return rather than suspending indefinitely.

## 6. DIRECT execution

In `DIRECT`, Main performs the Heuristic Probe Lead and executor roles for all admitted lanes.

For each lane:

1. confirm current Ticket/authority and target still match the frontier;
2. establish the smallest safe initial state needed for the lane;
3. exercise the most direct plausible trigger/readback first;
4. when material behavior appears, remove irrelevant conditions until the smallest reproducible trigger is established or the exact minimization limit is known;
5. capture actual observable behavior and authoritative readback;
6. record evidence limits rather than filling gaps with inference;
7. complete required cleanup/terminal state before moving to a lane whose evidence could otherwise be contaminated; and
8. stop once the lane's material question is decisively observed or bounded as unresolved.

Do not modify product source/config/tests to manufacture a finding or make probing easier.

## 7. SUBAGENT assignment, concurrency and fan-in

In `SUBAGENT`, Main remains Heuristic Probe Lead. Workers are exploration executors only.

### Dynamic assignments

Create workers only for admitted lanes that benefit from a separate context. There is no minimum, maximum-by-contract, fixed four-role team, AC roster, voting panel or mandatory wave count. Host concurrency is a capability limit, not a reason to invent or drop lanes.

Each assignment contains:

```text
HEURISTIC PROBE WORKER ASSIGNMENT

Ticket:
Project Root:
Target identity:
Probe lane:
Contract / Behavior anchor:
Plausible false-completion path:
Allowed product/runtime actions:
Authoritative readback:
Cleanup boundary:
Current user instructions:
Delegated Probe Worker: yes
```

Do not provide another worker's conclusion or an intended verdict before independent exploration when that would anchor the lane unnecessarily.

### Parallel-safety gate

Parallelize only when each lane has an isolated read/effect/cleanup surface. Typical parallel-safe cases include:

- read-only observations;
- separate disposable databases/files/directories;
- separate sessions/browser contexts/accounts explicitly authorized for testing;
- immutable candidate packets; or
- independent sandbox namespaces.

Serialize when lanes share or can interfere through:

- the same mutable database record or canonical file;
- the same reservation/order/session/account state;
- the same external idempotency key or one-shot operation;
- one process lifecycle or shared cache state whose mutation is material;
- cleanup that changes another lane's initial state; or
- a dependency where one lane establishes the next lane's required state.

Do not create a scheduler, queue, lease system or persistent worker registry to manage this. Main keeps only invocation-local assignments needed for the current fan-in.

### Worker result

Each worker returns:

```text
HEURISTIC PROBE WORKER RESULT

Ticket:
Probe Lane:
Actual Project Root:
Actual Target:
Worker identity / model:
Contract Anchor:
False-Completion Path:
Actions:
Minimal Trigger: None | <trigger>
Observed Behavior:
Authoritative Readback:
Direct Evidence:
Target Stability:
Cleanup / Terminal State:
Material Finding: None | <finding>
Evidence Limits:
Worker Completion: COMPLETE | PARTIAL | BLOCKED
```

A worker never returns AC verdicts, whole-Ticket verdicts, implementation-defect classifications or Ticket status mutations.

### Fan-in

Before using a worker result, Lead confirms actual root, Ticket, target and lane match the assignment. A report from another target is not partial evidence for this target.

Lead preserves an evidence-supported finding even when other workers did not observe it. Agreement and disagreement are not votes. Merge duplicate findings by common material trigger/root path without discarding distinct evidence limits.

Lead may issue one bounded follow-up when it materially narrows a trigger, resolves target attribution or closes a specific evidence gap. Do not create open-ended debate or confidence rounds.

## 8. Findings and minimal triggers

A **Material Finding** is a fresh attributable observation showing a concrete path that may matter to the approved Ticket outcome. It is not yet an AC/Ticket failure.

For each finding record:

```text
Finding:
Contract / Behavior anchor:
Minimal trigger:
Observed result:
Expected/authoritative comparison surface:
Direct evidence:
Target identity:
Cleanup/terminal state:
Remaining uncertainty:
```

Minimize toward the smallest material trigger by removing irrelevant inputs, state, steps or boundaries while preserving the observed material behavior. Stop minimization when further reduction would lose reproducibility, cross an authority boundary, become unsafe, or no longer answer the Ticket-derived question.

Do not relabel an interesting out-of-scope behavior as a defect simply because it was discovered. Preserve it only when necessary to explain why it is not a current material finding; do not create follow-up work automatically.

## 9. Target drift, action ambiguity and safety

### Target drift

The probe result is current only for its bound Ticket authority and implementation target. Material changes to Ticket, Parent Spec, applicable Behavior/UI authority, source/config/build/artifact/runtime checkpoint or relevant working-tree state invalidate supportive evidence that can no longer be attributed.

Preserve a directly observed contradiction only when its attribution remains exact and current. Otherwise report the evidence as stale/unattributable rather than carrying it forward.

### Mutation ambiguity

A transport/network failure during a mutation-capable action does not prove the action happened or did not happen. Do not immediately repeat it.

First read current authoritative state and any existing product-owned operation/readback surface. Repeat only when current evidence establishes the action did not occur and a new attempt remains authorized and safe. Otherwise finish the lane `PARTIAL` or `BLOCKED` with the exact ambiguity.

### Authority and safety

Existing exact Ticket/user authority is required for credential-bearing, production/shared, payment, message, deployment, destructive, irreversible, one-shot or duplicate-sensitive effects. Cross-layer heuristic exploration does not authorize access-control bypass, rate/protection bypass or a more privileged environment.

Use disposable/controlled targets where the approved contract permits them. Capture necessary evidence before cleanup, then restore/close the state required by the Ticket and current environment.

## 10. Completion and final result

`Probe Completion` has only these meanings:

- `COMPLETE` — every admitted lane reached a bounded conclusion/non-finding, all required worker results are attributable, cleanup/terminal conditions are closed, and target identity remains usable for the handoff;
- `PARTIAL` — some admitted lane could not finish, but current completed evidence and the unfinished boundary are exactly attributable and the environment is left in a known safe state;
- `BLOCKED` — canonical admission, required authority/capability, target attribution, safe action, or cleanup/terminal state prevents a valid handoff.

A finding does not make the probe itself fail. `COMPLETE` with one or more findings is normal.

Before a normal `ready` result can report `COMPLETE`, call Ready runtime `ready_probe_binding` exactly once after target-stability and cleanup closure. Choose a unique session-local output path outside Project Root; pass the exact Ticket/Project Root, the implementation `target_paths` that the verifier will bind, any declared generated-output paths, and every admitted lane as exactly one `lane-name=FINDING|NO_FINDING|EVIDENCE_LIMIT`. The runtime records current Ticket/Spec/Behavior/UI identities, authored Verification-flow denominator, target digest, lane denominator/terminal statuses, `probe_completion=COMPLETE`, and `cleanup=CLOSED`. Do not edit or “rebind” that JSON afterward; if authority/flow/target changes, rerun the Probe and create a new binding.

Return exactly one terminal result:

```text
READY TICKET HEURISTIC PROBE RESULT

Ticket:
Execution Mode: DIRECT | SUBAGENT
Heuristic Probe Lead: Main
Ticket status before probe:
Probe Target:
Authority Snapshot: <Ticket + Parent Spec + applicable Behavior/UI current identities>
Target Stability:
Heuristic Method: production-heuristic-probing

Probe Frontier Matrix:
- <entry summaries>

Worker Execution / Concurrency:
- DIRECT | <worker/lane terminals and concurrency used>

Material Findings:
- None | <findings>

Minimal Triggers:
- None | <finding -> trigger>

Direct Evidence:
Evidence Limits:
Cleanup / Terminal State:
Probe Machine Binding: <absolute session-local path outside Project Root> | diagnostic-not-required
Ticket status after probe: ready (unchanged) | <unchanged diagnostic status>
Verification status: NOT ADJUDICATED BY THIS SKILL
Probe Completion: COMPLETE | PARTIAL | BLOCKED
```

Do not use `PROBE_CLEAR`, `PASS`, `FAIL`, `SATISFIED`, `CONTRADICTED`, `VERIFIED`, `FAILED`, `IMPLEMENTATION_DEFECT` or another verifier/Adaptive classification as the probe completion result. A separate verifier decides the approved contract from fresh current evidence.

Stop after the terminal result. Do not automatically remediate implementation, invoke verification, mutate planning authority, create a Ticket, write `done`, or continue to another Increment.
