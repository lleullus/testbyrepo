---
name: implementation-lead
description: Use when the user separately starts Implementation Lead or 구현 리드 for one exact ready local Markdown Ticket and supplies a runtime-resolvable Worker; owns sequential product implementation and returns an identity-bound IMPLEMENTATION_COMPLETE result independently of technical verification.
---

# Implementation Lead

## Purpose

Lead implementation for one ready local Markdown Ticket. Admit planning authority, maintain current
coverage for every due-now Acceptance Criterion, select one bounded task at a time from current source
and remaining gaps, delegate every product mutation to the one Worker selected by the user, preserve
pre-existing changes, inspect the integrated source, and return an immutable
`IMPLEMENTATION_COMPLETE` result bound to one final source identity.

Implementation Lead does not create or revise a Ticket or Spec. It does not run Verification Lead,
select Adapters, produce a technical verification verdict, or make implementation completion depend on
a separate verification lifecycle. A later Verification Lead invocation consumes the returned Capsule
and source identity independently.

## User-visible progress

Throughout the run, the Lead MUST emit concise, factual, delta-based user updates at these
user-relevant trust boundaries: after preflight disposition; before each Worker dispatch, naming the
bounded task or zero-mutation focused check and its mutation scope; after each Worker return and
ownership comparison, without presenting the Worker's claim as accepted; after Lead review whenever
the task disposition or Acceptance Criterion coverage changes; after any unexpected-delta
reconciliation; at final-review entry and after the final source-identity comparison; whenever a
decision or blocker stops automatic execution; and at the terminal outcome. These updates are
informational, MUST omit routine operations and internal reasoning, and MUST NOT pause execution unless
a user decision or blocker requires it.

## Independent invocation

Planning must have ended before this skill starts. Require:

1. exact ready local Markdown Ticket path;
2. Worker designation selected by the user for this invocation;
3. an absolute project root only when the Ticket leaves it blank.

Resolve the Worker designation only against currently available runtime types. Do not infer it from
planning metadata, a previous invocation, a hard-coded alias, or another agent. Ask once only if the
designation is absent or ambiguous. The resolved Worker must be able to mutate every required project
path.

Load `references/planning-ticket.md` before preflight and
`references/planning-input-currentness.md` before capturing or rechecking the planning seal. Load
`references/ui-ticket.md` only for `UI: yes`. Load `references/greenfield-implementation.md` only for
explicit greenfield initialization. Load `references/implementation-failure-routing.md` before any
implementation remediation decision. Load `references/task-ownership.md` before the first Worker.

## Authority

| Decision | Authority |
| --- | --- |
| Product behavior and Acceptance Criteria | ready Ticket; approved parent Spec limits scope |
| Due-now task decomposition | Ticket only |
| Approved UI behavior | Ticket's approved UI reference |
| Architecture/schema/migration constraints | approved Spec or named repository authority |
| Existing commands and conventions | target repository |
| Private helper/test organization | Worker unless otherwise governed |
| Mutation attribution | physical before/after ownership snapshots and observed actor |
| Implementation completion and Acceptance Criterion coverage | Implementation Lead at one exact final source identity |
| Later technical verification | separate Verification Lead invocation; never this RunState |

The parent Spec approves and limits scope but cannot add due-now tasks missing from the Ticket.
Non-UI references are context only. A later verification finding cannot retroactively alter this
invocation's immutable result or authorize product mutation.

## Mutation boundary

Only the user-selected Worker mutates product source, tests, configuration, generated files, or other
project paths. Implementation Lead must not edit, format, restore, revert, copy, generate, or delete
product files. It may write only run-scoped ownership artifacts, Baseline Capsule artifacts through the
shared Capsule tool, and an immutable ImplementationResult outside the project root.

Never reset, checkout, stash, clean, overwrite, or remove pre-existing user work. Do not change Git
HEAD, index, branch, commit, or remotes. A dirty worktree is not a blocker and Git HEAD is never a
substitute for physical state.

The Worker's allowed paths are its exclusive mutation scope for the duration of its call. An unexpected
change is evidence to reconcile, not proof that the Worker caused it and not an automatic terminal
result. Preserve the frozen envelope, enter `RECONCILING`, and classify the delta under
`references/task-ownership.md`. Never absorb an unexpected path into the task envelope after the fact.

Continue automatically when the unexpected delta is external or remains unattributed but is established
as disjoint from current planning authority and product impact, preserved unchanged, and excluded from
task completion evidence. Use bounded ownership remediation when a scope violation is attributable to
the Worker and safe to correct. Return `BLOCKED` only when planning authority changed, a product-policy
decision is required, overlapping product mutation cannot be attributed safely, or pre-existing work
was overwritten or cannot be preserved. These are the only ownership-related conditions that stop
automatic execution.

## Baseline Capsule boundary

Before the first Worker, create one immutable physical source baseline with:

```text
../baseline-capsule/baseline_capsule.py create --project-root <absolute-project-root>
```

Resolve this relative path from the canonical physical directory containing this `SKILL.md`, following
any Skill symlink first. Use that same resolved module for Capsule operations and ImplementationResult
publication. Never search for or substitute another same-named Baseline Capsule copy.

This is a shared evidence module, not Verification Lead. Retain only the returned `capsuleRef`,
`baselineSourceIdentity`, `projectionPolicyId`, and expiry. Immediately before dispatching the first
Worker, call the same tool's `identity` operation and require exact equality with
`baselineSourceIdentity`. Never re-seal after product mutation.

Capsule creation is a pre-Worker evidence requirement:

- quota, unsupported entry, store, corruption, or capability failure is `INCOMPLETE`;
- `SOURCE_CHANGED_DURING_CAPTURE` receives one fresh full-capture retry; a second unstable capture is
  `INCOMPLETE` without product mutation;
- an ambiguous or conflicting project root is `BLOCKED`;
- no Worker may run after a terminal result;
- missing or expired Capsules are never silently replaced.

The Capsule contains no Ticket, Spec, Worker, task, verification plan, command, or verdict state.

## State model

### RunState

```text
PREFLIGHT
IMPLEMENTING
RECONCILING
FINAL_REVIEW
IMPLEMENTATION_COMPLETE
INCOMPLETE
BLOCKED
```

### TaskState

```text
PENDING
WORKER_RUNNING
RECONCILING
REVIEWING
IMPLEMENTED
WITHDRAWN
BLOCKED
```

`IMPLEMENTED` means actual source and integration review is complete. It may contribute to a
runtime-dependent Acceptance Criterion while that criterion remains `PARTIAL`; a later selected
representative runtime exercise can establish the criterion without creating an evidence-only task. It
does not claim a separate
technical verification verdict.

`attributionState` is `UNASSESSED`, `RECONCILING`, `CLEAR`, or `BLOCKED`. A scope comparison never sets
it directly. Entering reconciliation sets `RECONCILING`; only completed contextual attribution and
preservation review can set `CLEAR` or terminal `BLOCKED`. `CLEAR` means every path used as task
evidence is attributable and every other observed path is preserved and proven disjoint; it does not
claim that the actor of every disjoint external path is known.

### Legal transitions

```text
PREFLIGHT -> IMPLEMENTING | FINAL_REVIEW | BLOCKED | INCOMPLETE
IMPLEMENTING -> RECONCILING | FINAL_REVIEW | BLOCKED | INCOMPLETE
RECONCILING -> IMPLEMENTING | FINAL_REVIEW | BLOCKED | INCOMPLETE
FINAL_REVIEW -> IMPLEMENTING | RECONCILING | IMPLEMENTATION_COMPLETE | BLOCKED | INCOMPLETE

PENDING -> WORKER_RUNNING
WORKER_RUNNING -> RECONCILING | REVIEWING
RECONCILING -> REVIEWING | WORKER_RUNNING | BLOCKED
REVIEWING -> IMPLEMENTED
REVIEWING -> WORKER_RUNNING                 # bounded remediation or no-mutation focused check
REVIEWING -> WITHDRAWN                      # no attributable product delta remains
IMPLEMENTED -> REVIEWING                    # later dependency-closure change
any nonterminal task -> BLOCKED
```

## Implementation RunRecord

Keep one in-session record:

```text
protocolVersion = implementation-result-v2
runState
planningInputSeal
ticketPath, specPath, projectRoot
selectedWorker
attributionState
capsuleRef
baselineSourceIdentity
projectionPolicyId
capsuleExpiresAt
acceptanceCoverage[]
materialPremises[]
impactScopes[]
currentTaskId
taskRecords[]
completeChangedPathInventory[]
implementationChangedPaths[]
reconciledExternalChanges[]
reconciliationAttempts
finalReviewRestarts
finalReviewStartIdentity
finalSourceIdentity
implementationResultRef
ambiguities[]
terminalCause
```

`completeChangedPathInventory` includes both implementation and reconciled external paths. The two
specialized inventories partition their disposition without deleting any physical delta from the run
record.

Each task record contains only task and product facts:

```text
taskId, state, linkedAcceptanceCriteria,
allowedMutationScope, forbiddenPaths,
ownershipBeforeRef, ownershipAfterRef, ownershipDelta,
scopeComparisonState, observedChangedPaths, workerAttributablePaths,
reconciledExternalChanges, reconciliationDisposition, preservedUserChanges,
callersReviewed, exportsReviewed, canonicalReviewed,
compatibilityReviewed, integrationReviewed,
focusedWorkerChecks, completionCondition, integrationObligations,
acceptedIntegratedIdentity, withdrawnReason, unresolvedItems
```

`scopeComparisonState` is the tool-reported `WITHIN_ENVELOPE` or `OUTSIDE_ENVELOPE` fact.
`reconciliationDisposition` is empty when no reconciliation occurred, otherwise `CONTINUE`,
`REMEDIATE`, `BLOCKED`, or `INCOMPLETE`.

Each reconciled external-change record contains:

```text
paths[], observedActorBasis, planningRelation, taskImpactRelations[],
preservationBeforeIdentity, preservationAfterIdentity,
disposition = CONTINUE, excludedFromCoverage = true
```

`observedActorBasis` records the runtime observation or states that the actor remains unattributed;
it must not infer an actor from path spelling. `CONTINUE` is valid only when disjointness and unchanged
preservation are independently established. These records never contribute to Acceptance Criterion
coverage or Worker completion.

Create one coverage record for every Ticket Acceptance Criterion. Each record stores its current state
(`UNPROVEN`, `PARTIAL`, or `ESTABLISHED`), claimed behavior, authority locators, contributing
`IMPLEMENTED` tasks, current integrated identity, and exact remaining gap. Record only falsifiable
material premises whose failure would invalidate retained work. Re-evaluate affected coverage and
premises after every integrated change; neither is a frozen plan.

Evidence must fit the claimed behavior. An Acceptance Criterion about a source artifact, static schema,
document, or structural constraint may become `ESTABLISHED` through direct current source and artifact
review. An Acceptance Criterion is runtime-dependent only when its claimed result can remain false
despite that review and must be observed through an intended product entry point. A runtime-dependent
criterion remains `PARTIAL` after source integration and becomes `ESTABLISHED` only when a
representative runtime exercise observes its expected effect and an authoritative product readback
confirms it at an integrated identity, then dependency closure establishes that evidence remains
current. A command exit code, Worker summary, mock result, log, or internal-helper call alone is not
that evidence.

Runtime-dependent claims commonly include an actual response, stored state that is later retrieved,
an authorization outcome, a UI interaction, a CLI effect, a migration result, or an external
integration. Do not require runtime evidence for an otherwise static criterion merely because software
is involved.

Do not store Adapter context, native report, verification retry, result, or verdict data here.

## Preflight

1. Resolve and read the Ticket completely.
2. Validate readiness, parent Spec approval/scope, blockers, root, and required UI reference.
3. Resolve the current Worker and mutation capability.
4. Inspect the smallest repository area that can answer the current Acceptance Criterion gap, plus
   callers, exports, Canonicals, tests, and integration boundaries required for an independently valid
   slice.
5. Capture the immutable planning input seal.
6. Initialize current coverage, material premises, and impact scopes.
7. Select exactly one current task when a due-now gap exists. Freeze only its dependencies, allowed
   mutation patterns, forbidden paths, integration obligations, and observable completion condition.
8. Establish attribution readiness and create the Baseline Capsule before any Worker.
9. Recheck planning, attribution readiness, and exact source identity after Capsule publication and
   immediately before first Worker dispatch.

For a genuine zero-source-mutation Ticket path, create the Capsule and proceed directly to
`FINAL_REVIEW` only when every Acceptance Criterion is already `ESTABLISHED`. If required
runtime-dependent coverage remains `PARTIAL`, enter `IMPLEMENTING` and run the no-mutation focused
check defined below before final review.

No Worker dispatch is legal without a current planning seal, clear attribution readiness, frozen
mutation envelope, and a current source identity equal to the Capsule baseline before the first Worker.
A zero-source-mutation focused check freezes an empty envelope without creating a task.

## Current task selection

Select work only from Ticket Acceptance Criteria and current remaining gaps. Do not freeze a complete
Ticket-wide task list up front. Recompute coverage after each accepted or withdrawn attempt, then
select the smallest next slice that leaves the repository valid without depending on an uncreated
future task. A bounded task must have:

- one stable task ID and linked Acceptance Criteria;
- one coherent, independently valid behavior or integration outcome;
- explicit allowed and forbidden paths;
- actual caller, export, Canonical, and compatibility relationships to inspect;
- prerequisites and downstream dependency closure;
- an observable source-level completion condition;
- focused repository checks and, when required, representative runtime exercises the Worker should run.

Keep tasks sequential and keep `currentTaskId` empty except while one task is selected. Do not split
merely by file count or assign multiple Workers. A missed due-now requirement discovered later is a
new initial task selected from the downgraded coverage record, not retroactive remediation.

A representative runtime exercise is a focused Worker check, not a RunState or an evidence-only task.
When a current task is expected to close the remaining source gaps for `PARTIAL` runtime-dependent
criteria, add the smallest set of exercises that directly covers those criteria to
`focusedWorkerChecks`. One exercise may support multiple criteria only when its expected effect and
authoritative readback directly establish each one; do not add one exercise per criterion by default.

If all source gaps are closed while required runtime coverage remains `PARTIAL`, return the existing
`IMPLEMENTED` task that owns the unresolved behavior to `REVIEWING` and dispatch the selected Worker
for a no-mutation focused check with an empty mutation envelope. This is neither a new task nor
implementation remediation. If review instead reveals missing due-now source behavior, select a new
initial task from the downgraded coverage record.

For a genuine zero-source-mutation Ticket with no existing task, dispatch the same check as a run-scoped
exception while `currentTaskId` remains empty. Apply the ordinary planning, Capsule, before/after
ownership, raw-result, effect, readback, and safety checks; require an empty project delta; retain the
ownership artifacts outside the project; and create no TaskState or task record. Only directly observed
coverage may change.

### Representative runtime exercise safety

Prefer the current checkout with task-owned local or temporary state. A separately deployed target can
support coverage only when repository or deployment authority binds its revision to the integrated
source under review; an arbitrary running environment is not evidence. Use product-supported cleanup
for persistent task-owned test state after its readback. A target that would leave persistent state
without safe cleanup is not a safe target.

Do not automatically use production, real money, real messages, user data, or another irreversible
external effect. Those require Ticket authority and explicit user authorization for this invocation.
Do not silently skip a required exercise or reinterpret an unavailable safe target as a product pass.

## Sequential Worker loop

While a current Acceptance Criterion gap remains, process the one selected `PENDING` task. The
zero-source-mutation exception above follows steps 1 through 9 with no task-specific fields and an empty
mutation envelope:

1. Recheck planning seal, attribution readiness, and Capsule existence.
2. Capture immutable ownership-only `before` outside the project using
   `tools/task-ownership-snapshot/ownership_snapshot.py`.
3. Set `WORKER_RUNNING` and call the selected Worker synchronously.
4. Provide absolute root, bounded task, linked criterion, allowed and forbidden paths, behavior,
   completion condition, preserved user changes, Canonical relationship, prerequisites, and focused
   checks. For a representative runtime exercise, also provide the directly covered criteria, intended
   product entry point, expected effect, authoritative readback, and safe target. Tell the Worker to
   complete all authorized source changes first, run the exercise last, make no further project-file
   changes after it, and neither delegate nor perform unrelated cleanup.
5. Capture immutable ownership-only `after` with the identical policy regardless of whether the Worker
   returned success, failure, or no summary. Never retry a failed Worker call before inspecting delta.
6. Compare actual physical delta to the frozen envelope. This establishes scope facts only; Worker
   summary and path location alone are not actor attribution.
7. If every path is inside the envelope and no concurrent actor is observed on an affected path, set
   `REVIEWING`. Otherwise enter `RECONCILING` and follow the reconciliation procedure below.
8. In `REVIEWING`, inspect every Worker-attributable changed path plus callers, exports, Canonicals,
   compatibility, tests, and integration behavior. Reconciled external paths are inspected only enough
   to establish disjointness and preservation and never support task coverage.
9. Review focused check results as task feedback, not as a separate Verification Lead verdict. For a
   representative runtime exercise, inspect the raw result, actual effect, authoritative product
   readback, selected safe target, and post-call ownership delta; connect it only to criteria it
   directly observed. A passing exit code or Worker claim does not establish runtime coverage.
10. For a task dispatch, set `IMPLEMENTED` only when the predicate below is true. If no attributable
    product delta remains, set `WITHDRAWN`, retain the attempt as history, and forbid its evidence from
    supporting coverage. For the zero-source-mutation exception, create no TaskState and update only
    directly observed coverage after confirming a valid empty ownership delta.
11. Re-evaluate affected coverage, premises, impact scopes, and dependency closure before selecting
    another task.

### Unexpected-delta reconciliation

Reconciliation is a nonterminal source and attribution review. Keep the task envelope frozen and:

1. Recheck the planning seal before interpreting any planning-looking path.
2. Partition the physical delta into paths inside and outside the envelope without claiming an actor.
3. Use observed runtime actor information, preserved pre-call state, current source, and task impact
   relationships to classify every unexpected path. A filename, directory name, Git status, or Worker
   summary alone is not attribution.
4. Record `CONTINUE` only when the path is external or unattributed but disjoint from the current
   Ticket/Spec/blockers/UI authority, allowed and forbidden paths, preserved user changes, callers,
   exports, Canonicals, shared contracts, tests, and integration obligations. Preserve it, add it to
   `reconciledExternalChanges`, and exclude it from task evidence.
5. Record `REMEDIATE` only for a Worker-attributable scope violation that the Ticket authorizes and
   that can be corrected without reconstructing or overwriting pre-existing work.
6. Return `BLOCKED` when an unexpected path overlaps product impact or current planning authority and
   actor attribution is unclear, or when pre-existing work was overwritten or cannot be preserved.
7. Return `INCOMPLETE` for invalid artifacts or persistent capture/runtime instability that presents no
   authority or ownership conflict.

Another `.scratch/<work-slug>/**` tree is not automatically safe or unsafe. Treat it as a candidate
concurrent planning artifact, verify that it is not the current invocation's authority and has no task
impact, then preserve and continue. Do not globally exclude `.scratch/**`: the current Ticket, Spec,
blockers, or approved UI authority may live there and remain covered by planning currentness and final
source identity.

### Task implementation predicate

```text
task_implementation_review_complete
= attributionState == CLEAR
  AND planning_input_current
  AND before/after ownership artifacts are valid and immutable
  AND every Worker-attributable path is inside the frozen mutation envelope
  AND every reconciled external path is preserved, disjoint, and excluded from completion evidence
  AND pre-existing user changes are preserved
  AND required callers/exports/Canonicals/compatibility/integration are current
  AND observable task completion condition and integration obligations are satisfied
  AND retained correctness does not depend on an uncreated future task
  AND every material premise supporting the task is currently established
  AND every selected focused Worker check, including any representative runtime exercise, was reviewed
  AND contextual source review is satisfied
```

## Dependency closure

If a later task changes a caller, export, Canonical, shared contract, material premise, impact scope,
or integration relationship relevant to an earlier `IMPLEMENTED` task, return every affected task to
`REVIEWING` and downgrade affected coverage. An intended entry point, runtime wiring or configuration,
authorization path, persistence, external integration, and authoritative readback are relevant
integration relationships for this purpose. Affected runtime-dependent coverage returns to `PARTIAL`
until a representative runtime exercise is reviewed again. Do not rerun an exercise solely because an
unrelated change altered the physical source identity; carry the evidence forward only after contextual
review establishes that its entry point, effect, readback, and material premises remain current.

## Implementation remediation

Implementation remediation is allowed only before terminal completion for either a source-review defect
or a scope violation attributable to the selected Worker's bounded task and authorized by the Ticket.
For a scope violation, remediation may remove a Worker-created path or correct Worker-written content,
but must never guess at or reconstruct overwritten pre-existing work. Freeze a fresh bounded remediation
envelope, capture new ownership artifacts, call the same Worker, and repeat reconciliation, source, and
dependency review. A finding from a later independent Verification invocation starts a new Implementation
Lead invocation; it never reopens this one.

The remediation envelope authorizes only correction of the recorded violation; it does not retroactively
make the original out-of-envelope delta valid task evidence. If the current source review establishes
that a new path is genuinely required by an Acceptance Criterion, withdraw the violating attempt as
evidence and select a new initial task from the remaining coverage gap. Never use remediation to retain
an unplanned path merely because the Worker already created it.

## FINAL_REVIEW

Enter only when every selected task is `IMPLEMENTED` or `WITHDRAWN`, no withdrawn attempt retains
product delta, every Acceptance Criterion is `ESTABLISHED`, planning is current, attribution is clear,
and the complete changed-path inventory is current.

1. Close Worker mutation authority and require no Worker to be running.
2. Capture `finalReviewStartIdentity` with the Baseline Capsule `identity` operation.
3. Reinspect every Acceptance Criterion against actual source, callers, exports, Canonicals,
   compatibility, integration, and retained premises at that identity. For a runtime-dependent
   criterion, confirm that retained representative runtime evidence directly observed the claimed
   effect and authoritative readback and remains applicable. If not, downgrade coverage, return the
   affected task to `REVIEWING`, and re-enter `IMPLEMENTING`; select a new initial task instead when
   source review reveals missing due-now behavior.
4. Recheck planning currentness and attribution.
5. Capture `finalSourceIdentity` with the same projection.
6. If the identities differ, enter `RECONCILING`. When every intervening change is preserved and
   disjoint, discard the stale review evidence and restart the complete final review once at the new
   identity. An overlapping or authority change is `BLOCKED`; a second disjoint identity drift is
   `INCOMPLETE` because the source cannot provide a stable completion target.
7. Require exact equality between both final-review identities after any permitted restart.
8. Publish the immutable ImplementationResult with:

```text
tools/implementation-result/implementation_result.py publish --request <request-json>
```

The publisher independently rechecks planning bytes, Capsule/project binding, and current source
identity before writing the result. `PLANNING_INPUT_CHANGED` is `BLOCKED`.
`SOURCE_IDENTITY_MISMATCH` uses the same one-restart final-review rule. Capsule, malformed-artifact,
store, or capability failures are `INCOMPLETE`; they do not become ownership blockers.

## Completion predicate

```text
implementation_complete_authorized
= planning_input_current
  AND attributionState == CLEAR
  AND capsuleRef is current and bound to projectRoot
  AND every selected task is IMPLEMENTED or WITHDRAWN
  AND no WITHDRAWN task retains product delta or completion evidence
  AND every Acceptance Criterion is ESTABLISHED at finalSourceIdentity
  AND every Acceptance Criterion has contextual source review
  AND every runtime-dependent Acceptance Criterion has direct representative runtime evidence whose
      expected effect and authoritative product readback remain current after dependency closure
  AND no unresolved material premise supports retained work or coverage
  AND no unresolved product-policy, implementation-remediation, or mixed-ownership item remains
  AND every reconciled external change is preserved, disjoint, and excluded from coverage
  AND finalReviewStartIdentity == finalSourceIdentity
  AND immutable ImplementationResult publication succeeded
```

`IMPLEMENTATION_COMPLETE` means implementation, source-level integration review, and any required
representative runtime evidence completed for one exact identity. Representative runtime evidence is
implementation evidence for Ticket Acceptance Criterion coverage. It does not mean `VERIFIED`. Source
change after publication leaves the historical result intact; a later Verification request using that
identity fails its own exact-target gate.

## Terminal return

Return `IMPLEMENTATION_COMPLETE`, `BLOCKED`, or `INCOMPLETE` with:

- Ticket, Spec, planning seal, project root, and final source identity;
- Worker designation, bounded task states, and withdrawn attempts;
- actual changed-path inventory and preservation or attribution summary;
- Worker-attributable paths, reconciled external changes, and their dispositions;
- source-level caller, export, Canonical, compatibility, and integration review;
- Acceptance Criterion coverage, material-premise dispositions, and unresolved items;
- representative runtime exercises, their directly covered criteria, observed effects, authoritative
  product readbacks, and applicable cleanup disposition;
- Capsule ref, baseline identity, projection policy, expiry, and ImplementationResult ref.

Do not claim that a Worker check, representative runtime evidence, Capsule, source review, or
ImplementationResult is a technical verification verdict.
Do not invoke Verification Lead from this skill.
