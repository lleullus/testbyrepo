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
- The user's review of the proposed Ticket breakdown.

Read the parent Spec first. Refuse to create Tickets from a missing or non-`approved` Spec. Preserve its scope and non-goals; a Ticket must not expand, reverse, or replace the parent Spec.

The approved parent Spec is the product outcome, delivery scope, and Non-Goal
authority for a Ticket. The approved Behavior authorities adopted by that Spec
supply behavioral meaning only within their exact adopted scopes. For a UI
Ticket, the exact UI authority adopted by the parent Spec may supply
rendered-design detail only within that approved scope. Other
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
must not change what later Ticket delivery must implement, preserve, exclude, or
verify.

References do not import normative authority except for approved Behavior and
UI authorities explicitly adopted by the parent Spec. Every product outcome,
scope, boundary, and Non-Goal still traces to the parent Spec; behavioral and
rendered meaning comes only from the applicable adopted authority scope.
If a required Ticket clause cannot be traced under those rules, remove it or
reopen the Spec for an explicit approved delta. Perform this audit internally;
do not add a trace table to the Ticket unless the approved parent Spec requires
one.

## Output Contract

Resolve `../../../planning-workspace/planning_workspace.py` from this skill's
canonical physical directory and revalidate the project-local work artifact
directory before writing. The approved Spec must be the exact `SPEC.md` in that
directory. Legacy external Specs are context only and do not authorize writing
current Tickets. Do not manually create, repair, or adopt another destination
after helper failure.

Write one implementation Ticket per file at:

```text
<Project-Root>/docs/planning/work/<work-slug>/tickets/TICKET-NNN.md
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
## Behavior Authorities
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
inside the Ticket and are selected and revised by later Ticket delivery.

The `## Behavior Authorities` body contains every parent-Spec-adopted Behavior
authority applicable to this increment, using the exact path-and-scope item
format from the Spec. It must not add an authority or scope absent from the
parent Spec, and it must not restate or summarize Behavior rules. The
`## Blockers` body is either the exact one-line value `None` or a Markdown
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

Keep the number of Tickets minimal. When Independent and Operator-assisted
outcomes are independently acceptable and their mutation/acceptance ownership can
be separated without changing product meaning, prefer separate Tickets so an
Independent delivery unit can use the thin verification checkpoint without
pulling an operator-owned effect into it. Do not split an atomic product outcome
or invent a boundary merely to optimize verification choreography.
later Ticket delivery performs the internal task decomposition one current task at
a time.

## Acceptance Criteria rules

Acceptance Criteria derive only from the parent Spec's observable outcomes,
explicit constraints, and approved decisions together with the applicable
semantic meaning supplied by its adopted Behavior authorities.

Serialize each Criterion as one exact top-level `- ` list item in authored
order. Use two-space-indented continuation lines only when one Criterion needs
multiple lines. Do not use ordered, task-list, nested-only, prose-only, empty,
or mixed-marker bodies. Each exact authored Markdown item remains the
acceptance source consumed by later Ticket delivery; do not generate a digest,
schema identity, or separate user-facing AC ID.

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

Serialize each materially distinct Verification product flow as one exact
top-level `- ` list item in authored order. Use two-space-indented continuation
lines only when one flow needs multiple lines. Do not use ordered, task-list,
nested-only, prose-only, empty, or mixed-marker bodies. Preserve the authored
product-flow grouping and meaning; do not merge materially distinct flows or
split one flow into implementation seams.

Each exact authored Verification item uses these exact two-space-indented core
labels once, in this order:

```text
- Parent outcome ordinal: <one positive ordinal into the parent Spec Verification Expectations>
  AC ordinals: <comma-separated positive ordinals in authored AC order>
  Behavior authority ordinals: None | <comma-separated positive ordinals into this Ticket's Behavior Authorities>
  Initial state: <initial product state>
  Trigger or inspection target: <product trigger/input or canonical target>
  Acceptance boundary: <observable product or canonical boundary>
  Expected observable result: <effect or result>
  Authoritative readback: <product or canonical readback>
  Decision boundary: <observation that satisfies or contradicts this flow>
  Disposition: Independent | Operator-assisted | Not independently verifiable
  Independent verification required: yes | no
  Acceptance surface: Existing | <directly established surface>; Ticket Scope creates | <surface>; Delivery contract guarantees | <disposable target and availability condition>; Operator-owned | <surface>; None | <confirmed reason>
  External condition: None | <declared condition>
```

Add only a claim-specific line that the projected parent-Spec outcome contains,
using the exact applicable label from `to-spec`: `Absence terminal condition`,
`Ordering event source and range`, `Persistence storage identity and lifecycle
boundary`, `Interruption checkpoint`, `External effect sandbox, authority,
cleanup, and readback`, or `UI rendered state and interaction readback`.

`Parent outcome ordinal` is a one-based locator into the current exact top-level
parent Spec `## Verification Expectations` items. `AC ordinals` are one-based
locators into the current exact top-level Ticket `## Acceptance Criteria` items.
`Behavior authority ordinals` are one-based locators into the current exact
Ticket `## Behavior Authorities` items; use exact `None` only when no adopted
Behavior authority supplies semantic meaning to that flow. These are current
positional locators, not outcome names, AC names, rule IDs, persistent IDs,
digests, schema identities, or cross-document identities.

Every Verification flow maps to exactly one parent outcome and at least one AC.
Every AC ordinal must occur in at least one Verification flow, and every Ticket
Behavior Authority item must occur in at least one flow's `Behavior authority
ordinals`. A flow may map several ACs and several Behavior authorities when the
same product observation jointly decides them. Do not repeat an ordinal within
one item. If the parent outcome order, Ticket AC order, or Ticket Behavior
Authority order changes, or a mapped item is semantically edited, return the
Ticket to `draft`, remap every affected ordinal against the current authored
order, and obtain Ticket review again. Never preserve an ordinal as historical
identity.

Project the exact mapped parent-Spec outcome contract for this increment without
making it stronger, more solution-specific, or more executable-specific. The
flow's disposition, independent-verification requirement, acceptance surface,
external condition, and applicable conditional boundaries must remain the exact
combination of its `Parent outcome ordinal`; do not borrow a compatible-looking
combination from a different parent outcome. `Initial state` and `Decision
boundary` clarify how the authored outcome is decided but must not introduce a
new product precondition, internal mechanism, or stricter result. The acceptance
boundary, trigger/inspection target, expected observable result, authoritative
readback, and mapped Behavior authorities preserve the parent meaning. If that
needs a material meaning change, return to planning approval rather than
normalizing the Ticket silently.

An internal test command, test file, mock, fake, stub, private helper, debug
hook, or implementation-only state is not a product flow or authoritative
readback. A source, artifact, document, or structure outcome uses current
canonical-target inspection and does not acquire a runtime command merely to fit
the form.

Every exact authored Verification item remains product-flow authority for
implementation-stage planning and check selection. Preserve its count, order,
product trigger, expected effect, readback, grouping, and meaning; do not merge
materially distinct flows, split one flow into implementation seams, weaken it
into optional guidance, or discard it because there is no later verification
role. later Ticket delivery selects focused source and product-boundary checks
needed for implementation and integration closure and reports what it actually
observed without assigning independent evidence, an AC verdict, or final
`VERIFIED` status. Do not prescribe an internal test seam that could substitute
for the approved observable product behavior.

## Blocker rules

Record a blocker only for:

- an unresolved product, scope, boundary, or approved-contract decision;
- a specific evidence-backed contract contradiction; or
- a concrete external dependency, authority, access, availability, or approval
  condition that currently prevents the declared verification or acceptance
  path.

A blocker must identify the evidence and the condition for resolution.
Implementation difficulty, a presumed cause, uncertainty about the preferred
approach, or lack of a known implementation path is not a blocker.

Apply disposition-specific blocker semantics:

- For `Independent`, the acceptance surface and environment conditions needed
  for independent execution/inspection and authoritative readback are ready
  gates. `Existing` is valid only when directly established from current facts.
  `Ticket Scope creates` is valid only when Scope owns creation of that ordinary
  product surface/readback. `Delivery contract guarantees` is valid only when
  the approved parent contract names the disposable target and guarantees its
  availability condition. An inaccessible assumed-existing surface outside
  Scope blocks independent readiness.
- For `Operator-assisted`, the declared operator path is the acceptance path.
  The normal fact that a verifier alone lacks its credential, production access,
  or separate authorization is not a blocker. A concrete condition that prevents
  the declared operator path itself is a blocker.
- `Not independently verifiable` is not itself a blocker. It records that the
  approved contract has no independent boundary and Scope will not create one.
- If the parent Spec requires independent verification, only `Independent` is
  allowed. An `Operator-assisted` or `Not independently verifiable` projection
  cannot become `ready`; return the conflict to planning.

All prior unresolved product, scope, boundary, authority, dependency, access,
availability, and approval blocker meanings remain in force.

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
regular file with exactly one top-metadata `Status: approved` entry, exactly one
non-empty `Owner:`, and exactly one explicit `Scope:` containing this Ticket's
rendered obligation. Its content must establish complete approved UI/UX
authority for that scope with no unresolved rendered-design or interaction
decision; an incomplete, status-only, visual-reference-only, or style-only
document is insufficient for new/material UI. A Matt-created `DESIGN.md` must
retain exact `Open Questions: None`.
For a bounded parent-Spec authority, the approved Spec must still contain every
applicable rendered decision or direct preservation condition and declare its
scoped authority role. Other References remain context only and cannot supply
product or UI authority. Put any explanation outside the authority list item.

If the adopted authority's metadata, completeness, unresolved-decision state, or
scoped decisions changed after Spec approval, or the relationship to the approved
Spec cannot be established, do not create or ready
the Ticket. Return the changed UI delta to the Spec/UI authority owner for
explicit approval instead of adopting the current file silently.

## Behavior authority rules

Resolve each project-relative `## Behavior Authorities` path from the exact
`Project-Root`. Every target must be the same approved Markdown authority
adopted by the parent Spec, and its canonical parent must be exactly one of the
project's `docs/planning/behavior/contexts/`, `lifecycles/`, or `invariants/`
directories. `behavior/INDEX.md` and files elsewhere in the tree are not
authorities. The Ticket scope must be contained by the Spec's adopted scope.

Before readying any Ticket, review that Ticket against the parent Spec's adopted
Behavior scopes. Include every parent-adopted Behavior authority whose scope is
directly owned or can be materially affected by this Ticket's Acceptance
Criteria and mutation Scope. Every Ticket `## Behavior Authorities` item is
project-relative, resolves from the exact `Project-Root` to the same canonical
authority target and exact Scope already adopted by the parent Spec, and is
linked by current `Behavior authority ordinals` from at least one of that
Ticket's Verification flows.

Do not add an unrelated global or preserved Behavior authority merely to make
the Ticket set appear to cover every Behavior item. Parent-Spec Behavior
obligations that are not acceptance-owned by one Ticket remain whole-Goal
obligations and are checked by fresh completion verification. Fix the decomposition or
reopen the Spec when a Ticket omits an applicable Behavior guardrail or conflicts
with another Ticket. Do not add rule IDs, persistent projection indexes, trace
artifacts, or copied Behavior prose; the ordinals are only current positional
locators inside the authored Ticket.

## Readiness Rules

Draft the breakdown and obtain the user's confirmation before changing any Ticket to `ready`. A Ticket may be `ready` only when all of these are true:

- The parent Spec is `approved`.
- The user confirmed the Ticket.
- `Blockers` uses the exact `None` or path-only form, and every referenced
  blocker is `resolved` or `done`.
- Acceptance Criteria are observable.
- Every current authored Acceptance Criterion is linked by ordinal to at least
  one exact authored Verification flow, and every flow links at least one
  current AC without a persistent AC ID or digest.
- Every Verification flow maps to exactly one current parent-Spec Verification
  Expectation by `Parent outcome ordinal`, and its disposition/surface/external
  and conditional-boundary combination matches that exact parent outcome.
- Every applicable Ticket Behavior authority is approved, project-local,
  adopted by the parent Spec, represented by an exact contained path-and-scope
  item, and linked by `Behavior authority ordinals` from at least one current
  Verification flow.
- Every Verification flow has all core product-contract fields exactly once and
  has a disposition consistent with its independent-verification requirement,
  acceptance surface, external condition, Scope ownership, and mapped parent
  outcome.
- The project root is uniquely determined.
- A UI Ticket has a path-only reference resolving to the parent-Spec-adopted,
  applicable, complete approved local UI/UX authority target.
- The Ticket is not merely an anticipated internal preparatory step.
- Its Goal and Acceptance Criteria do not depend on a provisional technical
  explanation being true.
- `Goal` is only a non-normative summary; it has no conflict or implementation
  obligation absent from the execution-authority sections.
- Every normative Ticket clause has identifiable authority in the approved
  parent Spec or one of its applicable adopted Behavior/UI authorities.
- The Ticket does not increase solution specificity beyond the parent Spec.
- When the Ticket scope may require first product/package/application artifacts,
  its Scope, Acceptance Criteria, Non-Goals, and Verification trace the parent
  Spec's initialization scope authority, applicable external decisions, and
  remaining bootstrap choice fixed/delegated disposition without adding a
  technical value or delegation of their own.
- The exact `Project-Root` is an existing canonical accessible directory and
  this Ticket is under its exact `docs/planning` root.
- No applicable external/public/persisted identity or operational constraint is
  unresolved, and any remaining material private bootstrap choice is either
  fixed by the Spec or explicitly delegated there.

Before changing a Ticket to `ready`, run the adjacent structural validator:

```text
python3 matt/skills/to-tickets/validate_ticket.py <absolute-ticket-path>
```

The validator checks only the local path/status chain, exact list/label shape,
label cardinality, current parent-outcome/AC/Behavior ordinal ranges and closure,
blocker status, exact Ticket Behavior-item adoption, and structural
Disposition/requirement/surface/conditional-boundary combinations against the
mapped approved parent outcome. It does not judge product semantics, AC-to-flow
or Behavior-to-flow semantic correctness, material flow merge/split, solution
specificity, blocker truth, runtime availability, evidence, or verdicts. To
Tickets retains those authored review responsibilities.

After every reviewed Ticket has reached `ready`, run the adjacent set validator
against the exact approved parent Spec:

```text
python3 matt/skills/to-tickets/validate_ticket_set.py <absolute-approved-Spec-path>
```

The set validator requires the canonical sibling Ticket set to be structurally
ready and collectively cover every current parent-Spec Verification Expectation.
Per-Ticket validation still requires every Behavior authority declared by a
Ticket to match a parent-adopted authority and close to at least one authored
Verification flow. The set validator does not require unrelated global or
preserved Behavior authorities to be copied into a Ticket. It is a
planning-closure check, not a runtime state file, execution plan, evidence store,
or semantic verifier.
Do not report planning complete until it passes.

A legacy Ticket that lacks this outcome-local Verification form is not silently
treated as `Independent`. Before using the independent route, normalize it
against the still-approved parent meaning and review it as a current Ticket. If
normalization changes meaning, return to planning approval.

Use only `draft`, `ready`, `blocked`, or `done` as the Ticket status value. To Tickets writes only planning-owned `draft` and `ready` states; `done` is reserved for a later delivery lifecycle that has actually satisfied the Ticket's authored completion obligations, and `blocked` may be used only under its approved blocker semantics. IIS Planning never infers or writes `done` merely because implementation appears to exist. `Worker:` must remain empty.
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

Then report that this validated Ready Ticket Set is the terminal IIS planning
output. To Tickets never asks for or suggests a delivery agent and never loads,
invokes, or supervises an implementation or verification chain.

Any later implementation or verification is outside IIS Planning and consumes
the Ready Ticket Markdown contract directly.
