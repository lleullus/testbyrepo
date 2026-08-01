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

- An approved parent Spec at `<project-root>/.scratch/<work-slug>/SPEC.md`.
- The unique project root for the work.
- The user's review of the proposed Ticket breakdown.

Read the parent Spec first. Refuse to create Tickets from a missing or non-`approved` Spec. Preserve its scope and non-goals; a Ticket must not expand, reverse, or replace the parent Spec.

The approved parent Spec is the sole normative source for a Ticket. References,
current code, prior Tickets, tests, and expected implementation work may provide
context or evidence, but do not authorize additional Ticket requirements.

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

References do not import normative authority. If a required Ticket clause
cannot be traced to the parent Spec, remove it or reopen the Spec for an
explicit approved delta. Perform this audit internally; do not add a trace table
to the Ticket unless the approved parent Spec requires one.

## Output Contract

Write one implementation Ticket per file at:

```text
<project-root>/.scratch/<work-slug>/tickets/TICKET-NNN.md
```

Each Ticket begins with its title, then these exact metadata keys:

```text
Status: draft
Parent-Spec: ../SPEC.md
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

Write Tickets in the user's conversation language. A Ticket represents exactly
one independently observable contract increment or one explicit rollout or
migration boundary.

A Ticket may require several internal technical steps. Those steps remain
inside the Ticket and are selected and revised by Implementation Lead.

The `## Blockers` body is either the exact one-line value `None` or a Markdown
list whose complete item values are local Markdown paths. For a UI Ticket, set
`UI: yes` and include at least one approved UI/UX authority in `## References`
as a Markdown list item whose complete value is its local Markdown path.

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

Implementation Lead selects focused implementation evidence, including any
representative runtime exercise. A separate Verification Lead owns an
independent technical verification verdict.

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

For `UI: yes`, at least one `## References` list item must contain only one
local Markdown path. Do not wrap that authority path in backticks or combine it
with a label, colon prefix, parenthetical explanation, or URL. Resolve relative
paths from the Ticket directory. The target must be a readable regular file
with exactly one top-metadata `Status: approved` entry, and its content must
establish it as the approved UI/UX authority. Other References remain context
only and cannot supply product authority. Put any explanation outside the
authority list item.

## Readiness Rules

Draft the breakdown and obtain the user's confirmation before changing any Ticket to `ready`. A Ticket may be `ready` only when all of these are true:

- The parent Spec is `approved`.
- The user confirmed the Ticket.
- `Blockers` uses the exact `None` or path-only form, and every referenced
  blocker is `resolved` or `done`.
- Acceptance Criteria are observable.
- The project root is uniquely determined.
- A UI Ticket has a path-only approved local UI/UX authority reference.
- The Ticket is not merely an anticipated internal preparatory step.
- Its Goal and Acceptance Criteria do not depend on a provisional technical
  explanation being true.
- `Goal` is only a non-normative summary; it has no conflict or implementation
  obligation absent from the execution-authority sections.
- Every normative Ticket clause has identifiable authority in the approved
  parent Spec.
- The Ticket does not increase solution specificity beyond the parent Spec.

Use only `draft`, `ready`, `blocked`, or `done` as the Ticket status value. `Worker:` must remain empty.
Matt must not ask for, select, suggest, or record a Worker.

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
