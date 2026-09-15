---
name: scope-implement
description: "Implement one existing ready IIS Scope from a current independent method review and perform implementer self-check. The Scope stays ready; this role never performs semantic verification or finalization."
---

# Scope Implement

## Caller contract

The caller binds one exact construction unit before dispatch:

- **Project Root:** exact canonical absolute path.
- **Thesis:** every Scope-bound project-local Thesis source, exact path, revision and full UTF-8 SHA-256; preserve the complete source set.
- **Scope:** exact canonical `docs/planning/work/<slug>/SCOPE.md` path.
- **Transition Authority:** when the Scope has `## Transition Authority`, preserve each exact project-local baseline path and full SHA-256 and apply only its selected approved Block/conditions. If the section is absent, no baseline is required. A digest proves bytes, not approval or continuation authority.
- **Plan Review:** exact outside-Project-Root `plan_review_path` containing schema `iis-scope-plan-review/v2`, one current `ADMIT` for this Scope and the independent reviewer provenance.
- **Plan:** exact reviewed method paths and conditional first work.
- **User instructions:** current permitted actions, selected execution mode and model/effort.
- **Existing evidence:** implementation baseline, findings and readback locations, or `None supplied`.

Tell the implementing actor: **read all bound Thesis sources, the exact Scope and the exact current Plan Review directly before implementation, including product purpose, complete loop, false-success distinctions, failure/recovery meaning, Acceptance and authoritative readback.** A summary or file-name lookup is not a substitute. These sources bound the work; they do not authorize Scope expansion.

### Evidence boundary — copy into every assignment

> **Evidence boundary — apply before role-specific work**
> - Do not use mocks, stubs, canned responses, seeded success states or surrogate readbacks as completion or verification evidence for the real acceptance boundary they replace.
> - When the approved result requires real execution, state transitions or external effects, self-check evidence must exercise the real path and authoritative readback. Internal success or HTTP acceptance alone cannot prove the external result.
> - A double for an ancillary dependency does not invalidate an unrelated real boundary. Distinguish observed boundaries from boundaries replaced by doubles.
> - If required evidence is unavailable, preserve the gap in the implementation result. Do not infer success or obtain evidence through unauthorized actions.

Forward the source assignment unchanged and append exact role documents, target, plan/review, allowed effects and result path. The caller does not create a lease, execution database, hidden retry phase or replacement worker.

## Purpose and authority

This role implements one existing ready Scope and performs implementer self-check. It does not redesign Thesis/Scope, select another outcome, write a new Plan, issue the independent semantic verdict, dispatch Coverage or change Scope status. The separate verifier owns its verdict; Main owns eligible status recording after independent Coverage.

## Inputs and admission

The normal input is exact `Status: ready`. A `draft`, `blocked` or `superseded` Scope is not admitted. A `done` Scope is not reimplemented; report its existing completion/diagnostic state.
Before admission, compare any validator `transition_authorities` records with the Scope's exact section and preserve their currentness. Do not add a transition mode or mandatory stage merely because a baseline exists.

Immediately before the first source mutation, the actual implementing actor uses the supplied canonical Scope validator and ordinary read/hash tools to confirm the exact Project Root, ready Scope, bound Thesis and applicable Transition bytes, reviewed Plans and outside-root Plan Review. Compare actual bytes against the v2 review's source/Plan records and the caller-supplied review digest. Confirm the completed independent review's attribution, exact `ADMIT`, permitted start scope, conditions and lack of unresolved material findings. A valid-looking field set is not independent review evidence. Missing, stale or non-admitted review stops affected implementation with the exact reason and next owner; do not invent admission.

Repeat this currentness and admission check immediately before `Completion: COMPLETE`. If Scope, Thesis, applicable Transition, Plan, review, validator, target identity or required readback is stale/unavailable, do not claim COMPLETE. Return `PARTIAL` or `BLOCKED` with the exact boundary and next owner.

After admission, use ordinary read/search/edit/write/test/build/lint/CLI/service tools. A settled nonzero command is an ordinary command result: inspect it, correct within the reviewed method, and rerun when safe. Do not rebuild shell grammar, a scheduler, an execution lock or a generic uncertainty state.

For a non-idempotent or external effect with timeout, abort or lost response, do not blind replay. Use the Scope/Plan-authorized authoritative readback and cleanup. Continue only when applied/not-applied is established. If settlement or attribution remains unknown, stop dependent work and return the exact evidence gap.

## Execution topology

Top-level execution defaults to one `SUBAGENT`. Use `DIRECT` only when the current user explicitly selects DIRECT for this exact implementation stage. Do not change mode because of cost, model capability or worker availability; there is no automatic fallback. A delegated worker performs the implementation core directly and never delegates again.

Preserve the current selected model/effort. A capability failure returns `SUBAGENT CAPABILITY UNAVAILABLE` with the observed limit; it does not silently become DIRECT. Keep one implementation owner on one mutable worktree/effect surface. Do not start a replacement until the prior worker/process has actually settled; cancellation receipt alone is not settlement.

The caller reads this entry contract. The actual worker reads [references/implement.md](references/implement.md) in full. A permitted DIRECT actor reads that reference itself. The caller must not copy the worker procedure into a substitute result.

## Contract preflight

Before the first source-file change, the actor:

1. reads every bound Thesis source, exact Scope, Plan, Plan Review and applicable references;
2. identifies the observable result and the applicable preservation/non-goal boundaries;
3. chooses the cheapest real self-checks that discriminate the changed behavior, reusing Scope scenarios without rewriting their full matrix;
4. traces the real product entry to the deciding state/effect and readback, separating this Scope's owner from existing or external owners;
5. records pre-existing working-tree changes separately from this Scope delta;
6. confirms the first change advances the observable result or an approved invariant.

If a material meaning/authority conflict or missing canonical source prevents faithful implementation, stop `BLOCKED`; do not choose a convenient interpretation.

## Implementation and method changes

Implement the smallest reviewed change that satisfies the Scope's `Outcome`, all applicable `Acceptance` obligations and preservation/failure conditions. Preserve existing behavior already satisfying the Scope. Do not add speculative telemetry, fallback, persistence, recovery guarantees, interfaces or tests without a direct contract anchor or a concrete necessary failure path.

Apply the reuse, deletion and consolidation choices in `references/implement.md` before adding structure; smallest means coherent and easier to understand, not merely fewer lines. These choices remain within the reviewed method and existing revision boundary.

For each finding supplied by the caller or discovered in scope, identify it before claiming completion and give it one disposition: directly fixed, fixed with the same evidenced cause group, separately fixed, or returned at a Scope/Thesis/material-method boundary with exact next owner. Do not pass known related findings to the verifier as if they were closed. Connect each change to its Acceptance scenario, impact span, cheapest discriminating check, real acceptance readback and external-condition limit.

A material change to cause, owner, shared interface, persistence meaning, acceptance/readback, target identity or external-effect strategy changes the reviewed method. Stop mutation that depends on the new direction and return:

```text
SCOPE IMPLEMENT RESULT
Scope: <exact Scope>
Completion: PARTIAL | BLOCKED
Material method change: yes
Reviewed direction: <current Plan/reviewed method>
New direct evidence: <exact observation>
Affected plan scope: <exact section>
Current working-tree state: <exact state>
Next allowed action: revise affected Plan -> independent review -> fresh implementation actor
```

Do not keep the old actor alive through a continuation flag or edit the bound Plan to force admission.

## Completion self-check

Before COMPLETE, confirm current admission, faithful Scope outcome and preserved exclusions, disposition of known in-scope findings, and actual self-check evidence for the changed behavior. Keep pre-existing changes separate. State unobserved external conditions and limits honestly. Do not repeat already-current observations, require a second full verifier cycle, or mechanically exercise every listed failure mechanism when it is irrelevant to the change.

Tests or source inspection are supporting evidence when they do not exercise the required product boundary. Do not claim semantic verification from implementer evidence.

## Status and result

This role never changes `Status:`. A normal ready Scope remains `ready` after implementation. Only Main may record `done` after the independent verifier result, Coverage and currentness checks under `scope-verify`. Do not amend Thesis, Scope, Acceptance or Plan Review during implementation.

```text
SCOPE IMPLEMENT RESULT
Scope: <exact Scope path>
Execution Mode: SUBAGENT | DIRECT
Implemented result: <observable change and known finding dispositions>
Self-check: <actual command/readback/evidence and limits>
Plan admission at completion: CURRENT | <actual failure>
Verification handoff: <exact stable target/navigation; independent verdict not issued>
Remaining limits: <only material gaps, method changes or next-owner action>
Completion: COMPLETE | BLOCKED | PARTIAL
```

For a non-complete result, explain the governing constraint, observed blocker, preserved working state and exact next action. Do not add a second mandatory provenance form or infer a product defect from a transport/tool failure.
