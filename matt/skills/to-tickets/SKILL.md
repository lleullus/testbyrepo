---
name: to-tickets
description: Create reviewed local Markdown implementation Tickets from an approved SPEC.md.
disable-model-invocation: true
---

# To Tickets

## Purpose

Break one approved Spec into the smallest set of independently observable
desired-state Tickets without selecting a Worker, pre-planning internal
implementation steps, or starting implementation.

## Inputs

- An exact approved parent Spec path.
- The unique project root for the work.
- The current exact external planning workspace, or the work slug needed to prepare one.
- The user's review of the proposed Ticket breakdown.

Read the parent Spec first. Refuse to create Tickets from a missing or non-`approved` Spec. Preserve its scope and non-goals; a Ticket must not expand, reverse, or replace the parent Spec.

The approved parent Spec is the sole product outcome and scope authority for a
Ticket. For a UI Ticket, the exact UI authority adopted by the parent Spec may
supply rendered-design detail only within that approved scope. Other
references, current code, prior Tickets, tests, and expected implementation
work may provide context or evidence, but do not authorize additional Ticket
requirements.

## Parent-Spec traceability audit

Before writing or marking a Ticket `ready`, verify that every normative
statement in `Acceptance Criteria`, `Scope`, `Non-Goals`, `Blockers`, and
`Verification` traces to one or more identifiable clauses in the approved
parent Spec. A Ticket may split, restate, or make a parent outcome independently
observable. It must not strengthen the parent constraint, introduce a new
technical choice, or make the contract more solution-specific.

`Goal` is a non-normative summary of the desired outcome already expressed by
those execution-authority sections. It must not introduce, conflict with, or be
the sole location of an implementation obligation. Removing the `Goal` body
must not change what Implementation Lead must implement, preserve, exclude, or
verify.

References do not import normative authority except for the one UI authority
explicitly adopted by the parent Spec for a UI Ticket. Every product outcome,
scope, boundary, and Non-Goal still traces to the parent Spec; rendered detail
may additionally trace to an applicable locator in that adopted UI authority.
If a required Ticket clause cannot be traced under those rules, remove it or
reopen the Spec for an explicit approved delta. Perform this audit internally;
do not add a trace table to the Ticket unless the approved parent Spec requires
one.

## Output Contract

Resolve `../../../planning-workspace/planning_workspace.py` from this skill's
canonical physical directory and revalidate the current external workspace
before writing. When the approved Spec is in that workspace, reuse its parent
directory. A persisted legacy Spec inside the product root remains readable but
does not authorize writing Tickets there; prepare an external workspace and use
the Spec's canonical absolute path as `Parent-Spec` in that case. Ticket
drafting may reuse a workspace validated with `--future-project-root`, but before
any Ticket becomes `ready`, reuse that workspace with strict `--project-root`;
the future-root result is not sufficient for `ready`. Do not manually create,
repair, or adopt a workspace after any helper failure.

Write one implementation Ticket per file at:

```text
<planning-workspace>/tickets/TICKET-NNN.md
```

Each Ticket begins with its title, then these exact metadata keys:

```text
Status: draft
Parent-Spec: ../SPEC.md | <canonical-absolute-parent-Spec-path>
Project-Root: <the one absolute project root>
Worker:
UI: yes | no
```

Each Ticket contains these exact headings:

```text
## Goal
## Acceptance Criteria
## Scope
## Non-Goals
## Blockers
## Verification
## References
```

Any outcome, constraint, invariant, exclusion, or verification expectation
mentioned in `Goal` must also be unambiguously represented in `Acceptance
Criteria`, `Scope`, `Non-Goals`, `Blockers`, or `Verification`.

Use `../SPEC.md` only when it resolves from `tickets/` to the exact approved
Spec. Otherwise use the exact canonical absolute Spec path. Never copy or move a
durable authority document merely to make the path relative. `Project-Root`
continues to mean only the product repository.

Write Tickets in the user's conversation language. A Ticket represents exactly
one independently observable contract increment or one explicit rollout or
migration boundary.

A Ticket may require several internal technical steps. Those steps remain
inside the Ticket and are selected and revised by Implementation Lead.

The `## Blockers` body is either the exact one-line value `None` or a Markdown
list whose complete item values are local Markdown paths. For a UI Ticket, set
`UI: yes`. Carry a path that resolves to the same canonical UI authority target
adopted by the parent Spec into `## References` as a path-only Markdown item.
For a bounded rendered contract whose approved parent Spec declares itself the
scoped UI authority, reference that exact parent Spec target.

## Ticket decomposition rules

Split Tickets by independently acceptable outcomes, not by anticipated
implementation layers or sequence.

Do not create separate preparatory Tickets solely for:

- an abstraction;
- an adapter;
- infrastructure expected to be needed later;
- a test seam;
- a refactor that only makes later work easier;
- an expected migration step;
- separate source and test changes; or
- an anticipated prerequisite that has no independently required outcome.

Create a separate Ticket only when at least one of these is true:

- its outcome can be accepted and used independently;
- it represents an explicit rollout, compatibility, or migration boundary;
- it changes availability or product behavior independently; or
- the approved parent Spec intentionally requires that result as a separate
  contract increment.

Keep the number of Tickets minimal. Implementation Lead performs the internal
task decomposition one current task at a time.

## Acceptance Criteria rules

Acceptance Criteria derive only from the parent Spec's observable outcomes,
preserved invariants, explicit constraints, and approved decisions.

Serialize each Criterion as one exact top-level `- ` list item in authored
order. Use two-space-indented continuation lines only when one Criterion needs
multiple lines. Do not use ordered, task-list, nested-only, prose-only, empty,
or mixed-marker bodies. The current raw UTF-8 item bytes, including authored
line endings and continuation range, become the ImplementationResult v3
`criterionIndex` and `criterionRawSha256` identity; do not normalize or add a
separate user-facing AC ID.

Apply this solution-independence check to every normative Ticket statement, not
only to Acceptance Criteria:

> If a Ticket statement would fail solely because a different internal
> design was chosen, even though the parent Spec's outcome and boundaries are
> satisfied, the statement is too prescriptive unless that design is itself an
> explicit parent-Spec constraint.

For bug work, describe the original observable symptom and corrected behavior,
not a presumed cause.

For feature work, describe the smallest observable end-to-end result.

For refactor or migration work, describe the approved structural end state and
the behavior or invariant that must be preserved.

For performance work, describe the authorized measurement and required
threshold, not a presumed bottleneck.

## Scope rules

`Scope` identifies the product, subsystem, integration, document, or operational
boundary in which mutation is authorized.

Do not require an exact future file list merely because the planner expects
those files to change. Exact paths are normative only when the path or artifact
is itself part of the approved contract, or when the path boundary is necessary
to prevent unrelated mutation.

## Verification rules

`Verification` states how the Ticket's Acceptance Criteria can be observed.
When an approved parent-Spec expectation concerns a runtime result, preserve its
observable product flow, expected effect, and readback at the product-contract
level. Do not preselect an internal focused test seam, command, or test file
unless that surface is itself an approved external contract.

Implementation Lead selects focused implementation evidence. The Worker may run
provisional runtime checks as implementation feedback, but Implementation Lead
directly performs any final representative runtime exercise at the final source
identity. That evidence establishes Ticket completion only and is not an
independent general technical certification.

## Blocker rules

Record a blocker only for:

- an unresolved product, scope, boundary, or approved-contract decision;
- a specific evidence-backed contract contradiction; or
- a concrete external dependency, authority, access, availability, or approval
  condition that currently prevents independent execution or acceptance.

A blocker must identify the evidence and the condition for resolution.
Implementation difficulty, a presumed cause, uncertainty about the preferred
approach, or lack of a known implementation path is not a blocker.

Serialize `## Blockers` in exactly one of these forms:

```text
None
```

```text
- ../blockers/BLOCKER-001.md
- ../blockers/BLOCKER-002.md
```

Each list item must contain only one local Markdown path. Do not add backticks,
a label, a status, a URL, prose, or a parenthetical explanation to the item.
Resolve relative paths from the Ticket directory. Put blocker evidence,
resolution conditions, and explanatory prose inside the referenced blocker
document. Each target must be a readable regular file with exactly one
top-metadata `Status:` entry. A `ready` Ticket accepts only the exact lower-case
status `resolved` or `done` for every referenced blocker.

## UI reference rules

For `UI: yes`, the parent Spec's `## UI / UX` must identify the applicable UI
authority. When it names an external authority, resolve that exact local path
from the Spec directory when relative. For a bounded rendered contract, the
authority may instead be the approved parent Spec itself when that section
contains all scoped rendered decisions or direct preservation conditions and
declares that role. At least one `## References` item must be a path whose
resolved canonical target is that same authority file; its authored spelling
may differ because relative paths resolve from the Ticket directory.

Do not wrap that authority path in backticks or combine it with a label, colon
prefix, parenthetical explanation, or URL. The target must be a readable
regular file with exactly one top-metadata `Status: approved` entry, and its
content must establish complete approved UI/UX authority for this Ticket's
rendered scope; a status-only or Design Read/style-only document is
insufficient for new/material UI. Other References remain context only and
cannot supply product or UI authority. Put any explanation outside the
authority list item.

If the adopted authority's scoped decisions changed after Spec approval, or
the relationship to the approved Spec cannot be established, do not create or
ready the Ticket. Return the changed UI delta to the Spec owner for explicit
approval instead of adopting the current file silently.

## Readiness Rules

Draft the breakdown and obtain the user's confirmation before changing any Ticket to `ready`. A Ticket may be `ready` only when all of these are true:

- The parent Spec is `approved`.
- The user confirmed the Ticket.
- `Blockers` uses the exact `None` or path-only form, and every referenced
  blocker is `resolved` or `done`.
- Acceptance Criteria are observable.
- The project root is uniquely determined.
- A UI Ticket has a path-only reference resolving to the parent-Spec-adopted,
  applicable, complete approved local UI/UX authority target.
- The Ticket is not merely an anticipated internal preparatory step.
- Its Goal and Acceptance Criteria do not depend on a provisional technical
  explanation being true.
- `Goal` is only a non-normative summary; it has no conflict or implementation
  obligation absent from the execution-authority sections.
- Every normative Ticket clause has identifiable authority in the approved
  parent Spec.
- The Ticket does not increase solution specificity beyond the parent Spec.
- When the Ticket scope may require first product/package/application artifacts,
  its Scope, Acceptance Criteria, Non-Goals, and Verification trace the parent
  Spec's initialization scope authority, applicable external decisions, and
  remaining bootstrap choice fixed/delegated disposition without adding a
  technical value or delegation of their own.
- The exact `Project-Root` is an existing canonical accessible directory before
  the Ticket becomes `ready`; Matt does not create it. Revalidate the same
  external workspace with strict `--project-root` after any rootless Spec flow.
- No applicable external/public/persisted identity or operational constraint is
  unresolved, and any remaining material private bootstrap choice is either
  fixed by the Spec or explicitly delegated there.

Use only `draft`, `ready`, `blocked`, or `done` as the Ticket status value. `Worker:` must remain empty.
Matt must not ask for, select, suggest, or record a Worker.

Do not add `Initialization:`, `Planning-Root:`, a bootstrap manifest, exact
future source/config/test paths, private package/module identity, dependencies,
task sequence, or mutation envelope. The Ticket may project externally consumed
identity or fixed constraints only when the approved parent Spec requires them.

## Final Output

Planning ends when the reviewed Tickets are `ready`. Report each ready Ticket by its canonical absolute
path:

```text
Ready Tickets:
- <absolute-ticket-path>
```

Then state, in the user's conversation language, only that these Tickets can be used to start
Implementation Lead later.

Do not ask for or suggest a Worker, show an Implementation Lead invocation command, load or invoke
Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
Starting Implementation Lead is a separate user action after Matt has ended.
