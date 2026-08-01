# Matt Handoff Contract

## Path

```text
<project-root>/.scratch/<initiative-slug>/matt-briefs/WP-NNN.md
```

## Purpose

A Matt brief carries one approved Work Package boundary into one normal Matt planning flow. It prevents the initiative from expanding back into one giant Spec while preserving Matt's authority model.

The brief is not an approved Spec and is not a substitute for user confirmation.

## Top metadata

The document begins with a title and exactly one occurrence of each of these metadata keys:

```text
Status: ready-for-matt
Parent-Project-Map: ../PROJECT-MAP.md
Work-Package: WP-NNN
Project-Root: <the same absolute project root as the parent map>
Suggested-Work-Slug: <unique package work slug>
```

Only create the brief when the parent map is `approved` and the package is `ready-for-matt`.

## Exact headings

```text
## Authority Notice
## Product Context
## Package Outcome
## Included Product Scope
## Excluded Sibling Scope
## Dependencies
## Adopted Initiative Decisions
## Decisions Reserved For Matt
## Reference Material
## Matt Start
```

Write the brief in the user's conversation language.

## Authority Notice

It must state all of these meanings:

- the brief is a projection of an approved initiative decomposition;
- it fixes the active package frame for the opening Matt turn;
- it is not an approved package Spec;
- it does not silently create detailed package requirements; and
- Matt must obtain a user-confirmed contract-only shared understanding before `to-spec`.

## Content rules

- `Product Context` is concise and non-normative. It explains why this package exists in the initiative.
- `Package Outcome` repeats the package's observable Outcome without strengthening it.
- `Included Product Scope` and `Excluded Sibling Scope` project the approved package boundary exactly.
- `Dependencies` names only parent-map product dependencies and their user-visible reason. Use exact `- WP-NNN — <user-visible reason>` items in the same order as the parent package, or exact `None`. It must not prescribe implementation order.
- `Adopted Initiative Decisions` contains only decisions the user explicitly adopted while shaping and that materially constrain this package boundary.
- `Decisions Reserved For Matt` contains unresolved package-internal product, scope, boundary, non-goal, or completion-evidence decisions. It must not contain implementation-owned choices.
- `Reference Material` supplies context only. A reference does not import normative authority.
- `Matt Start` instructs Matt to plan only this package, confirm or correct the package frame, then run the normal `ask-matt` flow.

## Opening handshake

`from-project-shaper` must begin with a package-framing checkpoint containing:

```text
Work Package
Outcome
Includes
Excludes
```

If the same user explicitly confirmed the exact frame in the current conversation, the adapter may immediately begin the normal Matt interview. Otherwise it asks for one confirmation or correction of the frame before grilling package details.

This checkpoint confirms the active planning frame, not a complete package contract.

## Scope escape

During Matt planning, a question or newly discovered fact may remain inside the package when it only clarifies the package's own outcome, preserved behavior, boundary, non-goals, or evidence.

Return to Project Shaper when resolving it would instead:

- move an outcome between sibling packages;
- merge or split packages;
- change the MVP cut;
- add or remove a product dependency; or
- change the initiative's product boundary.

Do not return merely because implementation looks difficult or a technical approach is unknown.
