# Planning Ticket Runtime Input

## Purpose

This reference defines the Markdown planning input contract that a staged Implementation Lead will load. It is the runtime expression of the workplan's section 5 document contract and Task 2-2; it does not create a second planning authority.

Implementation starts only on this exact invocation:

```text
implementation-lead <exact-ticket-path> <worker-designation> [project-root]
```

The Ticket path and Worker designation are separate positional inputs. The optional `project-root` is only a constrained fallback described below. Resolve the designation only against the subagent types and descriptions currently exposed by the active runtime. The designation need not equal a runtime type string, but it must identify exactly one type from that current catalog. There is no tracker input, remote lookup, Worker value from the Ticket, hard-coded alias table, or fallback.

## Input Authority

The Ticket is the sole invocation artifact and task-decomposition input. The Lead consumes only these Ticket values:

- supplied Ticket path
- `Status`
- `Parent-Spec`
- `Project-Root`
- `Goal` for preflight coherence validation only
- `Acceptance Criteria`
- `Scope`
- `Non-Goals`
- `Blockers`
- `Verification`
- `UI`
- `References`

In this reference, the execution-authority sections are `Acceptance Criteria`,
`Scope`, `Non-Goals`, `Blockers`, and `Verification`. The approved UI reference
required by `UI: yes` applies only under the UI-reference rules below.

The Ticket title is validated as document structure only. `Goal` is a
non-normative summary and never supplies task-decomposition or completion
authority. Contextual preflight reads it only to ensure that it neither
conflicts with the execution-authority sections nor contains an outcome,
constraint, invariant, exclusion, or verification obligation absent from them.
Any such Goal-only obligation or conflict is a planning contract defect and
blocks for the Ticket/Spec owner. `Worker:` is a required planning-format
placeholder that new Matt Tickets leave empty. It must
not be selected, compared, or otherwise consumed at runtime. A non-empty value from an older Ticket is
ignored and does not satisfy the invocation Worker input. The Worker designation supplied in the
separate Implementation Lead invocation is the sole Worker authority, and the execution core resolves
it to exactly one of the active runtime's currently available subagent types. The runtime-selected Worker exists
only in invocation scratch and must never be written back to the Ticket, Spec, blocker, UI reference,
or other planning artifact.

The parent Spec is runtime input only for approval and scope-authority validation. The Lead reads its title, `Status`, `Owner`, and the raw bodies of the eight required sections, including `Open Questions` for unresolved product decisions. It must not create tasks or add requirements outside the Ticket to decomposition; it is not a second task-decomposition input.

Metadata, headings, and body text outside the listed Ticket values and required parent Spec validation fields do not extend input authority and must not be used by a runtime consumer.

## Markdown Form

Ticket, parent Spec, blocker, and UI/UX reference documents are local UTF-8 Markdown regular files. Their raw bytes are read as Markdown; no JSON or YAML schema is used.

For a Ticket or parent Spec:

- The title is the first H1 and must be a non-empty literal `# <title>` heading.
- Metadata is the region after that title and before the first H2.
- A metadata entry is one line in the exact form `Key: Value`. Required key names are case-sensitive.
- Each required metadata key appears exactly once. A missing, duplicate, malformed, or empty required value blocks preflight.
- `Worker:` is the planning-format exception: its key must appear exactly once. New Matt Tickets write
  an empty value. A non-empty legacy value is ignored and never supplies runtime Worker authority.
- `Project-Root:` is the root-resolution exception: its key must appear exactly once and may be blank only when the optional invocation root supplies the unique root. A blank value without that valid fallback blocks.
- Required sections are literal H2 headings, each appearing exactly once. Their body is the raw Markdown between that H2 and the next H2 or EOF.
- A duplicate, missing, or altered required heading blocks preflight. Unknown headings are not consumed.
- No slug, case folding, Unicode normalization, whitespace repair, inferred key, or inferred heading is allowed.

The required Ticket metadata is:

```text
Status
Parent-Spec
Project-Root
Worker
UI
```

The required Ticket sections are:

```text
Goal
Acceptance Criteria
Scope
Non-Goals
Blockers
Verification
References
```

Only `Acceptance Criteria` supplies positive completion conditions, and its body
must be non-empty and observable. `Goal` remains a required structural field
with only the narrow coherence check defined above. The other required Ticket
sections are preserved as raw Markdown except for their explicit preflight
rules in this reference; this reference adds no generic content schema for
them. `Verification` may describe an observable product flow, expected effect,
and product readback for an Acceptance Criterion, but does not itself add a
positive completion condition or require an internal command or test seam.

The required parent Spec metadata is:

```text
Status
Owner
```

The required parent Spec sections are:

```text
Problem
Desired Outcome
Requirements
Non-Goals
Implementation Constraints
Verification Expectations
UI / UX
Open Questions
```

## Paths And Root

All supplied or referenced paths are local filesystem paths. A URL, `file:` URI, shell expansion, environment substitution, slug substitution, case change, or Unicode transformation is not a path resolution mechanism.

- The supplied Ticket path is the exact local path from the invocation and must resolve to a readable regular file.
- `Parent-Spec` is an absolute local path or a local path relative to the Ticket directory. It must resolve to one readable regular file. A relative path is never resolved from the current directory or another fallback base.
- After the project root is established, the canonical parent Spec path must remain inside that root. A path that escapes the root, has no single canonical local target, or is otherwise ambiguous blocks preflight. Explicit `..` segments are permitted only when they resolve unambiguously inside the root, such as `../SPEC.md` from a Ticket directory.
- Ticket `Project-Root` takes priority only when its value is an exact absolute local directory path that resolves to one canonical, accessible directory. A relative, multi-value, placeholder, or non-directory value is malformed and blocks rather than becoming a fallback.
- The optional invocation `project-root` may supply the root only when the Ticket `Project-Root` value is blank. A nonblank invalid value blocks and must not permit fallback. When the Ticket value is valid and an optional root is also supplied, their canonical real paths must be identical. A mismatch blocks.
- A blank `Project-Root:` without an optional absolute local directory path is blocked. This is the supported Markdown case where the Ticket does not uniquely determine a root.
- Symlinks are checked through canonical real paths. The supplied path bytes and authored path value are retained separately from the resolved canonical path; resolution never rewrites the user's path spelling.

## Readiness Preflight

Preflight blocks unless all of the following are true:

- Ticket `Status` is exactly `ready`.
- The parent Spec `Status` is exactly `approved` and its `Owner` is non-empty.
- The Ticket has non-empty observable Acceptance Criteria.
- The project root is uniquely resolved under the root rules above.
- A Worker designation was supplied, resolves unambiguously to an available type, and that type can modify the required project paths.
- `Goal` is only a non-normative summary and has no conflict or obligation absent from the execution-authority sections.
- Blockers are clear under the blocker rules below.
- `UI` is exactly `yes` or `no`, with the required UI reference when it is `yes`.
- Contextual preflight establishes that the Ticket preserves, rather than expands or reverses, the parent Spec's scope and non-goals.

A Ticket may intentionally implement a strict subset of the parent Spec. Requirements assigned to
sibling Tickets may be excluded by this Ticket's Scope or Non-Goals; that decomposition is not a scope
conflict and does not make the current Ticket responsible for the full Spec. Scope preservation blocks
only when the current Ticket expands or contradicts the parent boundary, or its own Acceptance Criteria
cannot be completed within that boundary.

The parent Spec's `Open Questions` must not retain an unresolved product decision. A literal `None` indicates no open question; any question or undecided product choice that remains unresolved blocks even when the Spec claims `approved`.

Heading and metadata checks are mechanical only. Goal coherence and scope
preservation are contextual preflight judgments, not lexical parser decisions.
If either relationship is conflicting or cannot be established, preflight is
blocked for the Ticket/Spec owner rather than allowing a mechanical parser to
decide product policy.

## Blockers

The exact one-line `Blockers` body `None` means there is no blocker. Any other body is a local-Markdown blocker list and is fail-closed:

- The body contains only Markdown list items. Every item's entire value is one exact local Markdown path. Backticks, a label, a colon prefix, a status, a parenthetical explanation, prose before or after the list, a URL, or an unreadable or ambiguous target blocks.
- Relative blocker paths resolve from the Ticket directory. Each target must be a readable regular file.
- Each blocker file must have exactly one top-metadata `Status:` entry. Only the exact lower-case values `resolved` or `done` resolve a blocker.
- A missing, duplicate, malformed, or other blocker status blocks.

This is the minimum initial local-Markdown blocker rule. It intentionally does not generalize to remote trackers, free-form claims, or another resolution authority.

## UI References

`UI` is exact lower-case `yes` or `no`.

- When `UI: yes`, `References` must include at least one Markdown list item whose entire value is one exact local Markdown path. This is the meaning of a standalone path. Backticks, a label, a colon prefix, a status, or a parenthetical explanation makes that item ineligible as UI authority. The path must resolve to a readable regular file with exactly one top-metadata `Status: approved` entry. Contextual preflight must be able to establish that the approved document is a UI/UX authority; its name alone is not proof.
- When `UI: no`, the Lead must not infer UI authority, requirements, or work from `References` or any other Ticket text.
- A remote URL or unreadable local path never supplies UI authority. Other Reference entries may remain raw documented context, but they do not qualify for this check or add planning authority.

## Blocked Results

Preflight returns terminal RunState `BLOCKED` for this invocation with a concrete cause. It does not
alter the Ticket or Spec, and a later invocation may start after the named owner resolves the cause.

| Blocked cause | Next owner |
| --- | --- |
| Ticket format, status, Goal coherence, Acceptance Criteria, scope, non-goals, blocker, or UI reference problem | Ticket/Spec owner |
| Parent Spec format, approval, Owner, or unresolved product decision problem | Ticket/Spec owner |
| Missing, ambiguous, or unavailable Worker designation, or insufficient capability | User |
| Unreadable, escaping, mismatched, ambiguous, or non-directory project root | User or repository owner |
| Unreadable Ticket, parent Spec, blocker, or required local reference | Ticket/Spec owner; repository owner when the environment is the cause |

## Task Boundary

This is a reference contract, not resolver code. It defines Ticket and parent-Spec preflight mechanics,
but does not define `PlanningInputSeal`, hashing, input-currentness checks, recheck points, fixtures,
validators, or a new authority source.
