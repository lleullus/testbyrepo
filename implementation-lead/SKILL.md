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

Implementation Lead does not create or revise a Ticket or Spec, select an
external verification system, or produce an independent general technical
certification. Implementation completion is self-contained in this run.

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
`references/completion-record-v3.md` before classifying Evidence Requirements or publishing. Load
`references/ui-ticket.md` only for a current `UI_IMPLEMENTATION` dispatch under `UI: yes`. Load
`references/greenfield-implementation.md` when current scope inspection finds
required target readiness absent and first product/package/application artifacts due. Load
`references/implementation-failure-routing.md` before any implementation remediation decision. Load
`references/task-ownership.md` before the first Worker.

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

The parent Spec approves and limits scope but cannot add due-now tasks missing from the Ticket.
Non-UI references are context only. A later bug report or review finding cannot
retroactively alter this invocation's immutable result or authorize product mutation.

## Mutation boundary

Only the user-selected Worker mutates product source, tests, configuration, generated files, or other
project paths. Implementation Lead must not edit, format, restore, revert, copy, generate, or delete
product files. It may write only run-scoped ownership artifacts, Baseline Capsule artifacts through the
shared Capsule tool, source-bound disposable execution materializations, and an immutable
ImplementationResult outside the project root. A materialization is non-product runtime state, uses the
same bounded source projection as `finalSourceIdentity`, has owner-only access where supported, and is
removed after observation and readback. It never authorizes a project-root mutation.

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

This is the immutable source-baseline support module. Retain only the returned `capsuleRef`,
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
runtime-dependent Acceptance Criterion while that criterion remains `PARTIAL`; the Lead-owned final
representative runtime exercise can establish it without creating an evidence-only task. It does not claim a separate
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
REVIEWING -> WORKER_RUNNING                 # bounded implementation remediation
REVIEWING -> WITHDRAWN                      # no attributable product delta remains
IMPLEMENTED -> REVIEWING                    # later dependency-closure change
any nonterminal task -> BLOCKED
```

## Implementation RunRecord

Keep one in-session record:

```text
protocolVersion = implementation-result-v3
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
completionRecord
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

For a selected task, record its current dispatch `frontendMode`, classification basis, and any resolved
active `ima2-front` path/base directory in that task record's existing `integrationObligations`, and
echo the mode with its required direct reads, renderer conditions, commands, expected effects, and
readbacks in that task record's existing `focusedWorkerChecks`. When an existing `IMPLEMENTED` task
returns to `REVIEWING` for bounded remediation, reuse those same fields on its owning task record. These
are task facts, not new RunState, TaskState, task-record fields, manifest, lifecycle, or result protocol.

For a genuine zero-source-mutation path, create no TaskState, task record, or task fields. Keep any
provisional check context invocation-local. Final source or runtime evidence is recorded at run level in
`completionRecord`; do not create an artificial task merely to hold evidence.

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

Create one coverage record for every mechanically parsed top-level Ticket Acceptance Criterion. Each
record stores its stable one-based `criterionIndex`, exact `criterionRawSha256`, current state
(`UNPROVEN`, `PARTIAL`, or `ESTABLISHED`), claimed behavior, one or more `SOURCE` or `RUNTIME` Evidence
Requirements, authority locators, contributing `IMPLEMENTED` tasks, current integrated identity, and
exact remaining gap. Record only falsifiable material premises whose failure would invalidate retained
work. Re-evaluate affected coverage and premises after every integrated change; neither is a frozen
plan.

Evidence must fit the claimed behavior. An Acceptance Criterion about a source artifact, static schema,
document, or structural constraint may become `ESTABLISHED` through direct current source and artifact
review. An Acceptance Criterion is runtime-dependent only when its claimed result can remain false
despite that review and must be observed through an intended product entry point. A runtime-dependent
requirement remains `PARTIAL` after source integration and becomes `ESTABLISHED` only when
Implementation Lead directly performs a representative runtime exercise on the final candidate,
observes its expected effect, and obtains the required authoritative product readback. A command exit
code, Worker summary, mock result, log, provisional Worker runtime check, or internal-helper call alone
is not that evidence.

Runtime-dependent claims commonly include an actual response, stored state that is later retrieved,
an authorization outcome, a UI interaction, a CLI effect, a migration result, or an external
integration. Do not require runtime evidence for an otherwise static criterion merely because software
is involved.

## Preflight

1. Resolve and read the Ticket completely.
2. Validate readiness, parent Spec approval/scope, blockers, root, and required UI reference.
3. Resolve the current Worker and mutation capability.
4. Inspect the smallest repository area that can answer the current Acceptance Criterion gap, plus
   callers, exports, Canonicals, tests, and integration boundaries required for an independently valid
   slice.
5. Classify current target readiness for the Ticket scope. Do not use root emptiness or Ticket wording.
   If first product/package/application artifacts are required, apply the scope-level initialization
   admission reference before selecting work.
6. Capture the immutable planning input seal.
7. Initialize current coverage, material premises, and impact scopes.
8. Select exactly one current task when a due-now gap exists. Freeze only its dependencies, allowed
   mutation patterns, forbidden paths, integration obligations, and observable completion condition.
9. Establish attribution readiness and create the Baseline Capsule before any Worker.
10. Recheck planning, attribution readiness, and exact source identity after Capsule publication and
   immediately before first Worker dispatch.

For a genuine zero-source-mutation Ticket path, create the Capsule and proceed directly to
`FINAL_REVIEW` when every source requirement is `ESTABLISHED` and each runtime requirement has an
authoritative entry point, expected effect, readback mode, and safe execution target ready for the
Lead-owned final exercise. Runtime coverage remains `PARTIAL` until that final exercise succeeds.

No Worker dispatch is legal without a current planning seal, clear attribution readiness, frozen
mutation envelope, and a current source identity equal to the Capsule baseline before the first Worker.
A zero-source-mutation path freezes no Worker envelope and creates no task.

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
- focused repository checks and any provisional runtime checks useful as implementation feedback.

Keep tasks sequential and keep `currentTaskId` empty except while one task is selected. Do not split
merely by file count or assign multiple Workers. A missed due-now requirement discovered later is a
new initial task selected from the downgraded coverage record, not retroactive remediation.

### Frontend dispatch classification

`frontendMode` is a current-dispatch classification, not a RunState, TaskState, task record, manifest,
or result protocol. Recompute it when selecting every bounded task and frontend remediation dispatch.
It has exactly these values:

```text
NONE
ENGINEERING_ONLY
UI_IMPLEMENTATION
```

The mode changes the selected Worker's dispatch contract, not Worker selection. It creates no Addon,
dedicated frontend Worker, or separate manifest.

Classify the actual current runtime consumer and observable completion condition, never a file
extension, directory name, task title, or guessed stack.

- `frontendTarget` is true only when the current dispatch changes or directly exercises source, styles,
  assets, runtime wiring, configuration, or a rendered product entry point that is an actual browser or
  native UI runtime consumer.
- `renderedContractChange` is true only when an approved result changes pixels, content or copy,
  interaction or navigation, loading/empty/error/success/permission presentation, responsive behavior,
  accessibility semantics, focus or keyboard behavior, user-visible assets, or motion. A semantics,
  focus, or keyboard change is a rendered-contract change even when pixels do not change.
- Shared source is frontend-bearing only when this current dispatch has an actual frontend consumer or
  renderer impact. Its spelling or location does not decide the classification.

Apply the classification in this order:

1. If the dispatch neither changes nor directly exercises a frontend runtime consumer, use `NONE`.
2. If it changes frontend runtime source, configuration, state, integration, or performance while its
   approved rendered and UX result must be exactly preserved and no direct rendered-result exercise is
   due now, use `ENGINEERING_ONLY`.
3. Use `UI_IMPLEMENTATION` when the dispatch implements a `renderedContractChange` or includes a
   provisional exercise of that approved rendered result in the intended renderer.

A required direct rendered-result exercise is `UI_IMPLEMENTATION` even when its expected pixels and UX
are preservation rather than change; `ENGINEERING_ONLY` does not bypass rendered evidence.

`UI_IMPLEMENTATION` with Ticket `UI: no` is `BLOCKED` before Worker dispatch because the due-now
rendered contract conflicts with Ticket UI authority. This is not triggered by merely seeing a frontend
file. `UI_IMPLEMENTATION` with Ticket `UI: yes` requires the current approved UI reference, exact
task-relevant locators, linked criteria, and authority-defined rendered conditions. A missing,
insufficient, changed, or conflicting reference or locator is `BLOCKED` for the Ticket/Spec owner.

Ticket `UI: yes` does not make every dispatch UI work: a backend-only task is `NONE` and is classified
again when a later task becomes current. `ENGINEERING_ONLY` is permitted for Ticket `UI: no`, but it
must preserve the existing rendered and UX result exactly and must not infer a UI authority,
requirement, or reference.

The Lead never invokes `ima2-uiux` as a fallback. If a due-now UI/UX product decision is not supplied
by the Ticket/Spec and approved UI authority, do not implement it; return `BLOCKED` for the Ticket/Spec
owner.

### Active frontend guidance resolution

Before every `ENGINEERING_ONLY` or `UI_IMPLEMENTATION` Worker dispatch, including frontend remediation
dispatches, the Lead
must load the active skill by the stable identifier `ima2-front` and read it. From the active loader's
returned base directory, resolve the canonical physical absolute `SKILL.md` path and base directory,
following symlinks to their real paths, then read that exact `SKILL.md`. Do not search for, select, or
substitute a same-named npm, package, local, or copied skill.

If the active `ima2-front` skill, its loader-returned base directory, or its canonical `SKILL.md` cannot
be resolved or read, return `INCOMPLETE` before product mutation. This is an environment/capability
failure, not a product-authority gap; do not approximate guidance or pass a copied substitute. Record
the resolved absolute `SKILL.md` path and base directory in the current task record's existing
`integrationObligations`, and pass both values afresh on every Worker call. Worker context is never assumed to persist
between calls. A `NONE` dispatch neither resolves nor passes `ima2-front`.

Worker runtime checks are provisional focused feedback. They never become a Representative Runtime
Observation or establish a `RUNTIME` Evidence Requirement, even when they use the intended entry point
and happen to run at the eventual final source identity. When all source gaps are closed, proceed to
`FINAL_REVIEW`; Implementation Lead directly performs the smallest set of representative exercises
needed for the remaining runtime requirements. One exercise may support multiple requirements only
when its expected effect and authoritative readback directly establish each one.

Before any Worker dispatch, resolve each known runtime requirement's entry point from, in order: the
Ticket's observable flow, the approved Spec boundary, repository public/runtime contracts and actual
wiring, then Worker proposals. A helper, test seam, or internal function is not an entry point unless a
higher authority makes it the actual product path. An unresolved product entry point is `BLOCKED`; a
repository-authoritative path that cannot be executed locally is `INCOMPLETE`.

### Representative runtime exercise safety

Use the current checkout only when the repository-authoritative command cannot create or change source,
build output, cache, database, screenshot, or another project-root path. Otherwise create an owner-only,
run-scoped source materialization outside the project root using the same bounded source projection as
the final identity. A separately deployed target can support coverage only when repository or
deployment authority binds its exact revision to the final source; an arbitrary running environment or
version string is not evidence. Record the mode, authority, target identity or revision, and bounded
binding summary in `executionTargetBinding`.

Use `DIRECT_RESULT` when the actual entry point's returned or rendered result completely observes the
claimed effect. Use `INDEPENDENT_READBACK` for persisted, authorization, message, integration,
migration, or other side effects that require a separate system-of-record observation. When absence of
a forbidden effect is claimed, inspect that authoritative state rather than relying only on an error.
Use product-supported cleanup for task-owned reversible state after readback and record cleanup
readback. Remove source materializations after observation. A target that would leave unauthorized or
unreadable persistent state is not safe.

Do not automatically use production, real money, real messages, user data, or another irreversible
external effect. Those require Ticket authority and explicit user authorization for this invocation.
Do not silently skip a required exercise or reinterpret an unavailable safe target as a product pass.

### Frontend rendered evidence

`UI_IMPLEMENTATION` never establishes visual, interaction, responsive, or accessibility correctness
through static source inspection alone. In final review, Implementation Lead uses the actual intended
renderer and directly observes every applicable authority-defined viewport/responsive condition,
required state, interaction/timing behavior, accessibility semantic, and focus/keyboard behavior. The
expected rendered effect and authoritative product readback must be observed at the final identity
before runtime coverage becomes `ESTABLISHED`.

Use only repository-authoritative renderer/tool commands, a safe target, and reliable source binding.
If any is unavailable, return `INCOMPLETE` under the existing environment/capability semantics; do not
relabel that condition as a product defect or authority blocker. If the actual renderer lacks the
expected effect, treat it as task feedback. Use the existing bounded remediation path only after Lead
review establishes a Worker-attributable, Ticket-authorized defect in current source; otherwise use the
existing new-initial-task decision for missing due-now behavior.

Do not create an unnecessary product file, project-root screenshot, or evidence artifact merely to
prove rendered behavior. Use existing repository/tool output or run-scoped non-product observation;
create a product artifact only when the Ticket requires it and the frozen allowed scope permits it.

## Sequential Worker loop

While a current source gap remains, process the one selected `PENDING` task:

1. Recheck planning seal, attribution readiness, and Capsule existence.
2. Capture immutable ownership-only `before` outside the project using
   `tools/task-ownership-snapshot/ownership_snapshot.py`.
3. Set `WORKER_RUNNING` and call the selected Worker synchronously.
4. Provide absolute root, bounded task, linked criterion, allowed and forbidden paths, behavior,
   completion condition, preserved user changes, Canonical relationship, prerequisites, and focused
   checks. Identify any runtime check as provisional feedback and forbid the Worker from presenting it
   as final Acceptance evidence. Tell the Worker neither to delegate nor perform unrelated cleanup.
5. Capture immutable ownership-only `after` with the identical policy regardless of whether the Worker
   returned success, failure, or no summary. Never retry a failed Worker call before inspecting delta.
6. Compare actual physical delta to the frozen envelope. This establishes scope facts only; Worker
   summary and path location alone are not actor attribution.
7. If every path is inside the envelope and no concurrent actor is observed on an affected path, set
   `REVIEWING`. Otherwise enter `RECONCILING` and follow the reconciliation procedure below.
8. In `REVIEWING`, inspect every Worker-attributable changed path plus callers, exports, Canonicals,
   compatibility, tests, and integration behavior. Reconciled external paths are inspected only enough
   to establish disjointness and preservation and never support task coverage.
9. Review focused check results only as task feedback. A passing exit code, actual effect observed by
   the Worker, or Worker claim does not establish a runtime Evidence Requirement.
10. For a task dispatch, set `IMPLEMENTED` only when the predicate below is true. If no attributable
     product delta remains, set `WITHDRAWN`, retain the attempt as history, and forbid its evidence from
     supporting coverage.
11. Re-evaluate affected coverage, premises, impact scopes, and dependency closure before selecting
     another task.

### Frontend Worker dispatch contract

For every `ENGINEERING_ONLY` or `UI_IMPLEMENTATION` dispatch, step 4 also passes the freshly resolved
absolute active `ima2-front/SKILL.md` path and canonical base directory. This contract applies again to
every frontend remediation dispatch:

1. Before any product-file mutation, the Worker reads the passed absolute `ima2-front/SKILL.md` from
   beginning to end. It does not assume that the OpenCode `skill` tool is available.
2. From the passed base directory, the Worker directly reads only the task-relevant references that the
   `SKILL.md` routing directs for this dispatch. It neither searches for another copy nor relies on
   context retained from a prior Worker call.
3. Worker authority for this frontend dispatch is, in descending order:

   ```text
   ready Ticket and approved parent Spec
   > approved UI reference and task locator when UI: yes
   > repository design system, commands, and conventions
   > ima2-front objective implementation guidance
   > ima2-front style samples
   ```

   This applies the existing Authority table; it does not replace it. Workflow guidance and style
   samples never add a due-now requirement or Acceptance Criterion.
4. In both modes, the Worker does not invoke `ima2-uiux`, perform intent discovery or concept
   exploration, choose a new design direction, apply no-brief defaults, or create a new Design Read.
   It does not create or change `DESIGN.md` unless that artifact is explicitly approved product work in
   the current Ticket task. It does not invent IA, copy, state meaning, color, typography, asset
   concept, or motion direction outside approved UI authority.
5. The Worker does not install or set up `ima2`, log in, or change global defaults. It may generate a
   production asset only when the current Ticket/task requires it and its output is inside the frozen
   allowed mutation scope. Concept mockup generation is forbidden.
6. In `ENGINEERING_ONLY`, the Worker preserves the rendered and UX result exactly. It applies only
   task-relevant framework, runtime, state, integration, or performance guidance, and does not apply
   design, concept, or asset-generation procedures or infer UI authority/reference.
7. In `UI_IMPLEMENTATION`, the Lead also passes the approved UI-reference path, exact current
   task locators, linked criteria, and authority-defined rendered conditions. The Worker uses only the
   repository-authoritative browser, renderer, and test commands and the intended product entry point.
8. If the Worker cannot read the passed guidance path or a routed required reference, it makes no
   mutation and returns `GUIDANCE_UNAVAILABLE`; the Lead routes this to `INCOMPLETE`. If UI authority
   or a required locator is insufficient, or guidance conflicts with unresolved higher authority, it
   makes no mutation and returns `AUTHORITY_GAP`; the Lead routes this to `BLOCKED` for the Ticket/Spec
   owner.
9. The Worker return includes the `ima2-front` paths read, actual changed paths, frontend/build/test/
   renderer commands run, observed viewport, state, interaction, keyboard, and focus results as
   applicable, provisional rendered effect/readback, and unresolved items. This report is trace only:
   the Lead still reviews changed source, callers, Canonicals, design-system use, focused checks, and
   runtime/rendered effect before accepting completion.

The source-first sequence remains controlling: complete authorized source changes before the Lead-owned
representative or renderer exercise. Repeated-edit guidance in `ima2-front` never bypasses this safety
rule, the frozen allowed/forbidden paths, preserved changes, ownership snapshots, or the no-delegation
rule.

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
  AND every selected focused Worker check was reviewed as implementation feedback
  AND contextual source review is satisfied
```

## Dependency closure

If a later task changes a caller, export, Canonical, shared contract, material premise, impact scope,
or integration relationship relevant to an earlier `IMPLEMENTED` task, return every affected task to
`REVIEWING` and downgrade affected coverage. An intended entry point, runtime wiring or configuration,
authorization path, persistence, external integration, renderer path, and authoritative readback are
relevant integration relationships. Worker observations remain provisional and are never carried into
final runtime coverage. Lead-owned observations are created only after dependency closure on the final
candidate, so any subsequent source change discards them and requires a new final review.

## Implementation remediation

Implementation remediation is allowed only before terminal completion for either a source-review defect
or a scope violation attributable to the selected Worker's bounded task and authorized by the Ticket.
For a scope violation, remediation may remove a Worker-created path or correct Worker-written content,
but must never guess at or reconstruct overwritten pre-existing work. Freeze a fresh bounded remediation
envelope, capture new ownership artifacts, call the same Worker, and repeat reconciliation, source, and
dependency review. A later user bug report or review finding requires new
planning authority and a new Implementation Lead invocation; it never reopens this one.

The remediation envelope authorizes only correction of the recorded violation; it does not retroactively
make the original out-of-envelope delta valid task evidence. If the current source review establishes
that a new path is genuinely required by an Acceptance Criterion, withdraw the violating attempt as
evidence and select a new initial task from the remaining coverage gap. Never use remediation to retain
an unplanned path merely because the Worker already created it.

## FINAL_REVIEW

Enter only when every selected task is `IMPLEMENTED` or `WITHDRAWN`, no withdrawn attempt retains
product delta, every source requirement is `ESTABLISHED`, every runtime requirement has a resolved
entry point/effect/readback/safe-target plan, planning is current, attribution is clear, and the complete
changed-path inventory is current.

1. Close Worker mutation authority and require no Worker to be running.
2. Recheck planning currentness and attribution.
3. Capture `finalReviewStartIdentity` with the Baseline Capsule `identity` operation.
4. Reinspect every Criterion against actual source, callers, exports, Canonicals, compatibility,
   runtime wiring, and retained premises. Create identity-bound `sourceEvidence` for each `SOURCE`
   requirement. If source behavior is missing, downgrade coverage, select an ordinary source task, and
   return to `IMPLEMENTING`.
5. For every remaining `RUNTIME` requirement, resolve a source-bound execution target and capture an
   immutable ownership `before` snapshot outside the project root.
6. Implementation Lead directly executes the actual product entry point. It observes the expected
   effect and performs the selected direct-result, independent readback, or required absence check.
7. Perform product-supported cleanup of task-owned target state, read back cleanup when required, and
   remove any source-bound materialization.
8. Capture the ownership `after` snapshot with the same frozen policy and capture
   `finalSourceIdentity` with the same source projection.
9. Accept an observation only when source identity before and after equals `finalSourceIdentity`, the
   ownership snapshot identities are equal, changed-path count is zero, cleanup is complete or
   authoritatively not required, and the target/planning bindings are current. Otherwise discard it.
10. If actual effect or readback differs, treat it as task feedback and return to authorized source
    remediation. If target capability, binding, cleanup, or stable observation is unavailable, return
    `INCOMPLETE`; if required product authority is absent, return `BLOCKED`.
11. If final-review identities differ, enter `RECONCILING`. When every intervening change is preserved
    and disjoint, discard all observations and restart the complete final review once at the new
    identity. An overlapping or authority change is `BLOCKED`; a second disjoint identity drift is
    `INCOMPLETE`.
12. Build the durable Completion Record, require every Evidence Requirement to be `ESTABLISHED`, every
    evidence reference to be exact and current, and `unresolvedItems` to be empty.
13. Recheck planning currentness immediately before publication.
14. Publish the immutable ImplementationResult with:

```text
tools/implementation-result/implementation_result.py publish --request <request-json>
```

The request contains exactly `protocolVersion = implementation-result-v3`, `projectRoot`,
`planningSeal`, `capsuleRef`, `finalSourceIdentity`, and `completionRecord`; the caller does not submit
`implementationStatus`. The publisher independently reparses current Ticket criteria, recomputes the
Acceptance Criteria and PlanningInputSeal digests, checks all coverage/evidence cardinality and
identity/target/project-delta/cleanup bindings, rechecks supplemental local authority bytes,
Capsule/project binding, and current source identity, then writes `IMPLEMENTATION_COMPLETE`.
`PLANNING_INPUT_CHANGED` is `BLOCKED`. `SOURCE_IDENTITY_MISMATCH` uses the same one-restart final-review
rule. Capsule, malformed-artifact, store, or capability failures are `INCOMPLETE`.

## Completion predicate

```text
completion_preconditions_satisfied
= planning_input_current
  AND attributionState == CLEAR
  AND capsuleRef is current and bound to projectRoot
  AND every selected task is IMPLEMENTED or WITHDRAWN
  AND no WITHDRAWN task retains product delta or completion evidence
  AND every Acceptance Criterion is represented once by current index and raw-byte SHA-256
  AND every Evidence Requirement is ESTABLISHED at finalSourceIdentity
  AND every SOURCE requirement references current source evidence
  AND every RUNTIME requirement references a Lead-owned Representative Runtime Observation whose
       expected effect and authoritative product readback are current
  AND every ESTABLISHED coverage that depends on implementation or renderer evidence from a
      `UI_IMPLEMENTATION` dispatch has applicable approved UI authority and actual-renderer
      effect/readback evidence current after dependency closure
  AND no unresolved material premise supports retained work or coverage
  AND no unresolved product-policy, implementation-remediation, or mixed-ownership item remains
  AND every reconciled external change is preserved, disjoint, and excluded from coverage
  AND finalReviewStartIdentity == finalSourceIdentity
  AND every accepted observation has current planning/target/project-delta/cleanup bindings
```

The terminal transition is strictly:

```text
completion_preconditions_satisfied
-> publisher validates and writes immutable implementation-result-v3
-> RunState becomes IMPLEMENTATION_COMPLETE
```

Publisher success is the last required external effect, not a circular precondition.

`IMPLEMENTATION_COMPLETE` means implementation, source-level integration review, and any required
representative runtime evidence completed for one exact identity. Representative runtime evidence is
implementation evidence for Ticket Acceptance Criterion coverage. It does not mean `VERIFIED`. Source
change after publication leaves the historical result intact and does not make it current for the new
source identity.

## Terminal return

Return `IMPLEMENTATION_COMPLETE`, `BLOCKED`, or `INCOMPLETE` with:

- Ticket, Spec, planning seal, project root, and final source identity;
- Worker designation, bounded task states, and withdrawn attempts;
- actual changed-path inventory and preservation or attribution summary;
- Worker-attributable paths, reconciled external changes, and their dispositions;
- source-level caller, export, Canonical, compatibility, and integration review;
- Acceptance Criterion coverage, material-premise dispositions, and unresolved items;
- Lead-owned representative runtime observations, their directly covered requirements, execution target
  and project-delta bindings, observed effects, authoritative product readbacks, and cleanup disposition;
- frontend dispatch classifications, resolved active guidance paths, approved UI locators where
  applicable, and retained renderer observations/readbacks;
- Capsule ref, baseline identity, projection policy, expiry, and ImplementationResult ref.

Do not claim that a Worker check, representative runtime evidence, Capsule, source review, or
ImplementationResult is a technical verification verdict.
