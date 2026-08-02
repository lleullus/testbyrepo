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

One exact local Markdown path. It may be in any validated external planning
workspace; its path is not inferred from the product root:

```text
<initiative-planning-workspace>/matt-briefs/WP-NNN.md
```

Do not accept only a package name, a directory, a pasted partial block, or the entire `PROJECT-MAP.md` when an exact brief is available.

## Preflight

Before starting Matt, resolve the parent map and run the bundled `project-shaper/tools/validate_project_map.py` checker when available. Any validation error means the handoff is invalid or stale. The adapter must still verify the active brief-specific checks below rather than delegating authority to the tool.

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
11. The brief and parent map share one canonical external initiative workspace
    that is disjoint from the canonical product `Project-Root`.

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
- The latest user-confirmed contract-only shared understanding inside this Matt flow is the sole normative source for the package Spec.
- Repository facts, references, and the parent map must not silently add detailed package requirements.

## Opening Turn

Read the package block and brief. Present a concise package-framing checkpoint:

```text
이번 Matt 기획 단위: <WP-NNN and title>
결과: <Package Outcome>
포함: <Included Product Scope summary>
제외: <Excluded Sibling Scope summary>
```

Use the user's language rather than the Korean labels above when different.

If the same user explicitly confirmed this exact package frame in the current conversation, do not ask them to confirm it again. Immediately start the appropriate normal Matt path.

Otherwise ask one question only:

> Shall Matt plan this package within this frame, or should any included/excluded boundary be corrected first?

Recommend accepting the frame when it faithfully projects the approved map. This is a frame confirmation, not the full Matt requirements interview.

## Continue Into Matt

After the frame is confirmed:

1. Treat only this Work Package as the current planning unit.
2. Enter the central `ask-matt` Main Flow, including its Central UI / UX Routing
   audit. This adapter has no independent specialist decision path. The central
   flow chooses `grill-with-docs` for codebase-backed unresolved decisions or
   `grill-me` otherwise, and skips grilling only when the package contract is
   already clear.
3. Ask only package-internal product or operational decisions. Do not ask the user to choose files, modules, schemas, APIs, libraries, algorithms, or implementation order.
4. When the central flow is about to write its first artifact, including a
   package-scoped UI authority, use the brief's `Suggested-Work-Slug` once to
   prepare an independent default package planning workspace unless the user
   explicitly selects another external durable workspace. If `ask-matt`
   already prepared it for `DESIGN.md`, reuse that exact returned workspace and
   do not prepare another. Resolve
   `../../../planning-workspace/planning_workspace.py` from this skill's
   canonical physical directory and reuse that canonical package workspace for
   its `DESIGN.md`, Spec, Tickets, Wayfinder, Handoff, and planning reports. Keep the
   initiative map and brief at their exact original paths; do not nest the
   package workspace under the initiative workspace.
5. Follow the unmodified `to-spec` and `to-tickets` contracts. Do not add Project Shaper metadata to those artifacts unless the user adopts it as part of the package contract.
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

The first package-framing checkpoint or, when already confirmed in the current conversation, the first normal Matt interview turn. Do not stop at a route recommendation.
