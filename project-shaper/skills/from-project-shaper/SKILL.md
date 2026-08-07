---
name: from-project-shaper
description: Start one normal Matt planning flow from an exact ready-for-matt Work Package brief produced by project-shaper, preserving the approved package boundary without treating the brief as an approved Spec.
argument-hint: "<exact-matt-brief-path>"
---

# From Project Shaper

Write the checkpoint, questions, and all later Matt artifacts in the language used by the user and the brief.

## Purpose

Bridge exactly one approved Project Shaper Work Package into Matt without reopening the whole initiative, skipping Matt's confirmation rules, or turning the Project Map into a package Spec.

## Input

One exact project-local Markdown path:

```text
<Project-Root>/docs/planning/initiatives/<initiative-slug>/matt-briefs/WP-NNN.md
```

Do not accept only a package name, a directory, a pasted partial block, or the entire `PROJECT-MAP.md` when an exact brief is available.

## Preflight

Before starting Matt, resolve the parent map and run the bundled
`../project-shaper/tools/validate_project_map.py` checker when available. Any
validation error means the handoff is invalid or stale. The adapter must still
verify the active brief-specific checks below rather than delegating authority
to the tool.

Verify all of the following:

1. The brief is a readable regular file.
2. It has exactly one top metadata `Status: ready-for-matt`.
3. `Parent-Project-Map` resolves to a readable local `PROJECT-MAP.md`.
4. The parent map has exactly one top metadata `Status: approved`.
5. `Work-Package` is one `WP-NNN` identifier that exists in the parent map.
6. The matching package has `Package-Status: ready-for-matt`.
7. The matching package's `Matt-Brief` resolves back to the exact input file.
8. `Project-Root` is one absolute path and matches the parent map.
9. `Suggested-Work-Slug` is present and unique to the package.
10. Every package dependency named by the brief exists in the parent map.
11. The brief and parent map are under the exact canonical
    `<Project-Root>/docs/planning/initiatives/<Initiative-Slug>/` directory.

If any check fails, stop with:

```text
BLOCKED: invalid or stale Project Shaper handoff
Reason: <specific failed condition>
Next owner: Project Shaper
```

Do not repair the map or brief silently.

## Authority Model

- The approved Project Map is authority only for the active package identity, sibling boundary, MVP/dependency coordination, and adopted initiative decisions.
- The brief is a faithful context projection, not independent authority.
- The latest user-confirmed contract-only shared understanding owns package
  outcome and delivery scope; the approved Behavior and UI authorities it
  adopts own only their exact semantic and rendered scopes.
- Repository facts, references, and the parent map must not silently add detailed package requirements.

## Package Frame Input

Read the package block and brief. Form this provisional package-frame node:

```text
이번 Matt 기획 단위: <WP-NNN and title>
결과: <Package Outcome>
포함: <Included Product Scope summary>
제외: <Excluded Sibling Scope summary>
```

Use the user's language rather than the Korean labels above when different.

If the same user explicitly confirmed this exact package frame in the current
conversation, treat the node as settled. Otherwise do not ask a standalone frame
question. Use the approved map projection as the recommended provisional input,
enter the complete `ask-matt` initial Grill/Behavior/UI synthesis, and include
frame acceptance or correction as one user-owned decision in that first
integrated frontier. It follows the active normal or Batch presentation mode.
If the user changes the frame, ask a later round only when that answer newly
unlocks a material dependency under `ask-matt`'s rule. A package frame never
creates its own preliminary waiting turn.

## Continue Into Matt

Using that settled or provisional frame:

1. Treat only this Work Package as the current planning unit.
2. Enter the central `ask-matt` Main Flow, including its UI audit and mandatory
   Matt-performed Behavior Design phase. The central flow chooses
   `grill-with-docs` for codebase-backed unresolved decisions or `grill-me`
   otherwise. A Grill skip never skips Behavior Design.
3. Ask only package-internal product or operational decisions. Do not ask the user to choose files, modules, schemas, APIs, libraries, algorithms, or implementation order.
4. Use the brief's `Suggested-Work-Slug` to prepare the one project-local work
   directory under `docs/planning/work/`. Reuse it for `DESIGN.md`, Spec, and
   Tickets. Behavior Design uses the persistent `docs/planning/behavior/`
   authorities. Keep the initiative map and brief at their original local paths.
5. Follow the normal `to-spec` and `to-tickets` authority contracts. Do not add
   Project Shaper metadata unless the user adopts it as package scope.
6. End at ready Tickets exactly as normal Matt does. Do not invoke Implementation Lead or a Worker.

Use the normal Matt target-readiness and initialization-authorization gate; do
not duplicate a Project Shaper-specific greenfield checklist. A Project Map's
existing `Project-Root` does not itself authorize initialization mutation, fix
an external identity, or delegate remaining bootstrap choices.

## Boundary Escape Test

Remain in Matt when a decision only clarifies this package's own observable outcome, preserved behavior, package boundary, non-goals, or completion evidence.

Stop and return to Project Shaper when a required decision would:

- move an observable outcome into or out of a sibling package;
- merge or split Work Packages;
- change the initiative MVP cut;
- add or remove a product dependency; or
- change the initiative's approved product boundary.

Output:

```text
SHAPING DELTA REQUIRED
Affected package: <WP-NNN>
Observed boundary conflict: <specific conflict>
Proposed map change: <move, split, merge, dependency, MVP, or boundary change>
Packages affected: <IDs>
Why package-local clarification is insufficient: <reason>
```

A missing implementation path, technical uncertainty, or codebase difficulty is not a boundary escape.

## Output

The first integrated frontier, with package-frame confirmation or correction
included when not already settled in the current conversation, or the complete
contract-only shared understanding when no user-owned decision remains. Do not
stop at a route recommendation or standalone package-framing checkpoint.
