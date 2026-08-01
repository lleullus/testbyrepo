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
bounded task and mutation scope; after each Worker return and ownership comparison, without presenting
the Worker's claim as accepted; after Lead review whenever the task disposition or Acceptance Criterion
coverage changes; at final-review entry and after the final source-identity comparison; whenever a
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
| Source-level implementation completion | Implementation Lead at one exact final source identity |
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

The Worker's allowed paths are exclusive mutation scope for the duration of its call. After the first
Worker, an unexplained external edit or overwritten intermediate state is mixed ownership: stop
`BLOCKED` for reconciliation. Do not widen a mutation envelope after observing an unexpected change.

## Baseline Capsule boundary

Before the first Worker, create one immutable physical source baseline with:

```text
../baseline-capsule/baseline_capsule.py create --project-root <absolute-project-root>
```

This is a shared evidence module, not Verification Lead. Retain only the returned `capsuleRef`,
`baselineSourceIdentity`, `projectionPolicyId`, and expiry. Immediately before dispatching the first
Worker, call the same tool's `identity` operation and require exact equality with
`baselineSourceIdentity`. Never re-seal after product mutation.

Capsule creation is a pre-Worker evidence requirement:

- quota, unsupported entry, store, corruption, or capability failure is `INCOMPLETE`;
- changing source, unclear ownership, or a root conflict is `BLOCKED` for reconciliation;
- no Worker may run after either result;
- missing or expired Capsules are never silently replaced.

The Capsule contains no Ticket, Spec, Worker, task, verification plan, command, or verdict state.

## State model

### RunState

```text
PREFLIGHT
IMPLEMENTING
FINAL_REVIEW
IMPLEMENTATION_COMPLETE
INCOMPLETE
BLOCKED
```

### TaskState

```text
PENDING
WORKER_RUNNING
REVIEWING
IMPLEMENTED
WITHDRAWN
BLOCKED
```

`IMPLEMENTED` means actual source and integration review is complete. It does not claim a separate
technical verification verdict.

### Legal transitions

```text
PREFLIGHT -> IMPLEMENTING | FINAL_REVIEW | BLOCKED | INCOMPLETE
IMPLEMENTING -> FINAL_REVIEW | BLOCKED | INCOMPLETE
FINAL_REVIEW -> IMPLEMENTATION_COMPLETE | IMPLEMENTING | BLOCKED | INCOMPLETE

PENDING -> WORKER_RUNNING -> REVIEWING -> IMPLEMENTED
REVIEWING -> WORKER_RUNNING                 # bounded implementation remediation only
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
ownershipState
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
finalReviewStartIdentity
finalSourceIdentity
implementationResultRef
ambiguities[]
terminalCause
```

Each task record contains only task and product facts:

```text
taskId, state, linkedAcceptanceCriteria,
allowedMutationScope, forbiddenPaths,
ownershipBeforeRef, ownershipAfterRef, ownershipDelta,
observedChangedPaths, preservedUserChanges,
callersReviewed, exportsReviewed, canonicalReviewed,
compatibilityReviewed, integrationReviewed,
focusedWorkerChecks, completionCondition, integrationObligations,
acceptedIntegratedIdentity, withdrawnReason, unresolvedItems
```

Create one coverage record for every Ticket Acceptance Criterion. Each record stores its current state
(`UNPROVEN`, `PARTIAL`, or `ESTABLISHED`), claimed behavior, authority locators, contributing
`IMPLEMENTED` tasks, current integrated identity, and exact remaining gap. Record only falsifiable
material premises whose failure would invalidate retained work. Re-evaluate affected coverage and
premises after every integrated change; neither is a frozen plan.

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
8. Establish ownership and create the Baseline Capsule before any Worker.
9. Recheck planning, ownership, and exact source identity after Capsule publication and immediately
   before first Worker dispatch.

For a genuine zero-mutation Ticket path, create the Capsule and proceed directly to `FINAL_REVIEW`.
No Worker dispatch is legal without a current planning seal, clear ownership, frozen task envelope,
and a current source identity equal to the Capsule baseline.

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
- focused repository checks the Worker should run.

Keep tasks sequential and keep `currentTaskId` empty except while one task is selected. Do not split
merely by file count or assign multiple Workers. A missed due-now requirement discovered later is a
new initial task selected from the downgraded coverage record, not retroactive remediation.

## Sequential Worker loop

While a current Acceptance Criterion gap remains, process the one selected `PENDING` task:

1. Recheck planning seal, ownership, and Capsule existence.
2. Capture immutable ownership-only `before` outside the project using
   `tools/task-ownership-snapshot/ownership_snapshot.py`.
3. Set `WORKER_RUNNING` and call the selected Worker synchronously.
4. Provide absolute root, bounded task, linked criterion, allowed and forbidden paths, behavior,
   completion condition, preserved user changes, Canonical relationship, prerequisites, and focused
   checks. Tell the Worker not to delegate or perform unrelated cleanup.
5. Capture immutable ownership-only `after` with the identical policy.
6. Compare actual physical delta to the frozen envelope. Worker summary is non-authoritative.
7. If ownership is clear, set `REVIEWING` and inspect every changed path plus callers, exports,
   Canonicals, compatibility, tests, and integration behavior.
8. Review focused command results as task feedback, not as a separate Verification Lead verdict.
9. Set `IMPLEMENTED` only when the predicate below is true. If no attributable product delta remains,
   set `WITHDRAWN`, retain the attempt as history, and forbid its evidence from supporting coverage.
10. Re-evaluate affected coverage, premises, impact scopes, and dependency closure before selecting
    another task.

### Task implementation predicate

```text
task_implementation_review_complete
= ownershipState == CLEAR
  AND planning_input_current
  AND before/after ownership artifacts are valid and immutable
  AND actual delta is inside the frozen mutation envelope
  AND pre-existing user changes are preserved
  AND required callers/exports/Canonicals/compatibility/integration are current
  AND observable task completion condition and integration obligations are satisfied
  AND retained correctness does not depend on an uncreated future task
  AND every material premise supporting the task is currently established
  AND focused Worker checks were reviewed
  AND contextual source review is satisfied
```

## Dependency closure

If a later task changes a caller, export, Canonical, shared contract, material premise, impact scope,
or integration relationship relevant to an earlier `IMPLEMENTED` task, return every affected task to
`REVIEWING` and downgrade affected coverage. Reinspect current source and transition it back to
`IMPLEMENTED` only after source-level review.

## Implementation remediation

Implementation remediation is allowed only before terminal completion and only for a defect discovered
during source review that is attributable to the selected Worker's bounded task and authorized by the
Ticket. Freeze a fresh bounded envelope, capture new ownership artifacts, call the same Worker, and
repeat source and dependency review. A finding from a later independent Verification invocation starts
a new Implementation Lead invocation; it never reopens this one.

## FINAL_REVIEW

Enter only when every selected task is `IMPLEMENTED` or `WITHDRAWN`, no withdrawn attempt retains
product delta, every Acceptance Criterion is `ESTABLISHED`, planning is current, ownership is clear,
and the complete changed-path inventory is current.

1. Close Worker mutation authority and require no Worker to be running.
2. Capture `finalReviewStartIdentity` with the Baseline Capsule `identity` operation.
3. Reinspect every Acceptance Criterion against actual source, callers, exports, Canonicals,
   compatibility, integration, and retained premises at that identity.
4. Recheck planning currentness and ownership.
5. Capture `finalSourceIdentity` with the same projection.
6. Require exact equality between both final-review identities.
7. Publish the immutable ImplementationResult with:

```text
tools/implementation-result/implementation_result.py publish --request <request-json>
```

The publisher independently rechecks planning bytes, Capsule/project binding, and current source
identity before writing the result.

## Completion predicate

```text
implementation_complete_authorized
= planning_input_current
  AND ownershipState == CLEAR
  AND capsuleRef is current and bound to projectRoot
  AND every selected task is IMPLEMENTED or WITHDRAWN
  AND no WITHDRAWN task retains product delta or completion evidence
  AND every Acceptance Criterion is ESTABLISHED at finalSourceIdentity
  AND every Acceptance Criterion has contextual source review
  AND no unresolved material premise supports retained work or coverage
  AND no unresolved product-policy, implementation-remediation, or mixed-ownership item remains
  AND finalReviewStartIdentity == finalSourceIdentity
  AND immutable ImplementationResult publication succeeded
```

`IMPLEMENTATION_COMPLETE` means implementation and source-level integration review completed for one
exact identity. It does not mean `VERIFIED`. Source change after publication leaves the historical
result intact; a later Verification request using that identity fails its own exact-target gate.

## Terminal return

Return `IMPLEMENTATION_COMPLETE`, `BLOCKED`, or `INCOMPLETE` with:

- Ticket, Spec, planning seal, project root, and final source identity;
- Worker designation, bounded task states, and withdrawn attempts;
- actual changed-path inventory and preservation or ownership summary;
- source-level caller, export, Canonical, compatibility, and integration review;
- Acceptance Criterion coverage, material-premise dispositions, and unresolved items;
- Capsule ref, baseline identity, projection policy, expiry, and ImplementationResult ref.

Do not claim that a Worker check, Capsule, source review, or ImplementationResult is a technical
verification verdict. Do not invoke Verification Lead from this skill.
