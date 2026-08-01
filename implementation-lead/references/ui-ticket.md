# UI Ticket Integration Mechanics

This reference is conditional Implementation Lead mechanics. It does not authorize product behavior
or mutation, add states or results, weaken a core guard, or replace approved UI, Ticket, parent Spec,
or repository authority.

## Scope

Use this reference only when the current dispatch is classified by core as `UI_IMPLEMENTATION` and
Ticket `UI: yes`. It covers current approved UI-reference locator inspection, the frontend Worker
handoff, and rendered evidence mechanics. Ticket `UI: yes` does not make every task UI-bearing: a
backend-only dispatch can be `NONE`.

A Ticket with `UI: no` never loads this reference and never supplies inferred UI authority. Core may
still classify a frontend runtime-preservation task as `ENGINEERING_ONLY`, load active `ima2-front`, and
require exact rendered/UX preservation without inferring a UI requirement or reference.

## Mandatory Load Trigger

Load this file before resolving authority for a currently selected `UI_IMPLEMENTATION` dispatch. Do not
load it merely because a file looks frontend-related, a task title sounds visual, or a guessed stack is
present. The core owns the per-dispatch `NONE`, `ENGINEERING_ONLY`, and `UI_IMPLEMENTATION`
classification from the actual runtime consumer and observable rendered contract.

## Preconditions Owned By SKILL.md

The core owns Ticket/Spec authority precedence, block and incomplete semantics, Worker exclusivity,
task source review, final identity binding, and terminal results. `ima2-front` is workflow and
implementation guidance only; it cannot override the approved UI reference, Ticket, parent Spec, or
repository conventions.

If a dispatch requires a rendered-contract change or direct renderer exercise and Ticket `UI: no`, core
returns `BLOCKED` before Worker dispatch. This is an authority conflict, not a classification based on
the presence of frontend files.

## Approved UI Authority

1. Resolve the exact approved local UI/UX reference path named by the Ticket `References` section under
   the Ticket contract.
2. Read its current bytes and preserve the exact task-relevant locator set, linked criteria, and
   authority-defined rendered conditions needed by the current bounded dispatch.
3. Do not broaden UI scope from visual similarity, guessed implementation structure, or a future task.

Resolve and pass only the approved locators needed by the current `UI_IMPLEMENTATION` dispatch. When a
later UI dispatch becomes current, resolve its locators against the same approved UI authority and the
then-current repository state.

A missing, unapproved, unreadable, insufficient, changed, or conflicting approved UI reference or
required locator is an `AUTHORITY_GAP`: no mutation occurs and core returns `BLOCKED` for the
Ticket/Spec owner. It does not authorize a best-effort implementation.

## Active Guidance Boundary

Core resolves and reads active `ima2-front` for every `ENGINEERING_ONLY` and `UI_IMPLEMENTATION`
dispatch, not just the first UI task. It passes the canonical physical absolute `SKILL.md` path and its
canonical base directory to the Worker. The Worker directly reads that path before product mutation,
then directly reads only task-relevant routed references relative to that passed base directory; it does
not assume the OpenCode `skill` tool exists or search for another copy.

If the Lead cannot resolve/read the active guidance loader, base directory, or canonical guidance path,
it returns `INCOMPLETE` before mutation. If the Worker cannot read the passed guidance path or a routed
required reference, it returns `GUIDANCE_UNAVAILABLE` without mutation and the Lead returns
`INCOMPLETE`. Neither is an authority failure or `BLOCKED`. Do not approximate guidance, replace it
with a local copy, or apply the generic no-delta Worker-call retry to that deterministic failure.

## Frontend Worker Handoff

For `UI_IMPLEMENTATION`, pass the approved UI-reference path, exact current locators, linked criteria,
authority-defined rendered conditions, resolved active guidance path/base directory, frozen mutation
envelope, and repository-authoritative browser/renderer/test commands plus the intended product entry
point. Do not invent a command, consumer, UI requirement, or reference.

The core Worker contract forbids `ima2-uiux`, intent discovery, concept exploration, no-brief defaults,
new design-direction selection, unapproved `DESIGN.md` work, global `ima2` setup, and concept mockups.
Objective `ima2-front` guidance and style samples never add a due-now requirement or Acceptance
Criterion. The Worker must return its read guidance paths, actual changed paths, commands, applicable
viewport/state/interaction/keyboard/focus observations, provisional rendered effect/readback, and
unresolved items; the report is trace rather than completion proof.

## Rendered Evidence

Static source inspection cannot establish `UI_IMPLEMENTATION` visual, interaction, responsive, or
accessibility correctness. In the actual intended renderer, observe each applicable authority-defined
viewport/responsive condition, state, interaction/timing behavior, semantic, and focus/keyboard
behavior. A runtime-dependent UI criterion becomes `ESTABLISHED` only when Implementation Lead directly
performs the core final representative runtime exercise with an expected rendered effect and
authoritative product readback at the final source identity.

An unavailable renderer, safe target, capability, or reliable source binding is `INCOMPLETE`; it is not
a product defect or authority blocker. An absent expected rendered effect is task feedback and uses the
existing source-review/remediation or new-initial-task decision. Use repository/tool output or
run-scoped non-product observation; do not create screenshots or other project-root evidence artifacts
unless the Ticket requires the artifact inside the frozen allowed scope.

## Currentness And Dependency Closure

If an approved UI reference or relevant locator changes during the invocation, planning or authority
currentness fails. Stop before further mutation or completion; do not adopt changed UI authority,
relabel a prior task, or continue from stale rendered behavior.

Later changes to shared CSS/design tokens, common layout/chrome, frontend Canonicals/component
primitives, route/state contracts, UI assets, rendered callers/data shapes, renderer entry points, or
relevant design-system use downgrade affected rendered coverage and return its owning earlier task to
`REVIEWING`. Final rendered observations are created only after source dependency closure; any later
source change discards them and restarts final review.

## Return To Core Flow

Return the approved UI-reference path, task locators, authority-defined rendered conditions, active
guidance path/base directory, rendered behavior references, evidence/readback, and unresolved effects.
The core decides task implementation review, coverage, remediation, final identity, and terminal result.

## Non-Authority Statement

This file is not a UX contract, product policy, Adapter schema, Worker instruction replacement,
lifecycle state machine, retry authority, or completion verdict.
