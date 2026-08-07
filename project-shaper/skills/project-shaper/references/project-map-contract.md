# PROJECT-MAP.md Contract

## Path

```text
<Project-Root>/docs/planning/initiatives/<initiative-slug>/PROJECT-MAP.md
```

The initiative directory is the canonical project-local directory returned by
the shared `planning-workspace` tool with `--kind initiative`. The directory
name must equal `Initiative-Slug`. Existing external or `.scratch` maps remain
readable context but are not current authority destinations.

## Top metadata

The document begins with a title and exactly one occurrence of each of these metadata keys:

```text
Status: draft | approved
Owner: <user or named planning owner>
Project-Root: <one absolute project root>
Initiative-Slug: <initiative slug>
```

Use only `draft` or `approved` as the map status. Approval means the user approved the initiative decomposition. It does not approve any package Spec.

## Exact top-level headings

```text
## Product Outcome
## Product Boundary
## Reference Interpretation
## MVP Cut
## Work Packages
## Dependency Map
## Deferred Capabilities
## Initiative-Level Open Questions
## Matt Handoff Queue
```

Write the map in the user's conversation language.

## Work Package block

Under `## Work Packages`, write every package in this exact shape:

```markdown
### WP-NNN: <title>

Package-Status: proposed | ready-for-matt | blocked-shaping | deferred
Matt-Brief: ./matt-briefs/WP-NNN.md | None

#### Outcome

<one coherent observable product or operating outcome>

#### Includes

- <product scope included in this package>

#### Excludes

- <sibling or deferred product scope excluded from this package>

#### Depends On

None
```

or:

```markdown
#### Depends On

- WP-NNN
```

Then include:

```markdown
#### Why This Is One Package

<why the included scope shares one acceptance and planning boundary>

#### Why It Is Separate

<why merging it with adjacent packages would force unrelated product decisions or erase an independent outcome>

#### Decisions Reserved For Matt

- <package-internal product decision Matt may clarify later>
```

`Decisions Reserved For Matt` may be `None`. Do not put technical implementation choices there.

## Package statuses

- `proposed`: decomposition is still under review.
- `ready-for-matt`: package identity, sibling boundary, and shaping-level dependencies are stable; Matt may clarify its internal product contract.
- `blocked-shaping`: an initiative-level decision can still change this package's identity, boundary, MVP membership, or dependency relation.
- `deferred`: intentionally outside the current Matt handoff queue.

An approved map may contain only `ready-for-matt` and `deferred` packages. A draft map must not contain a `ready-for-matt` package. Resolve every `proposed` or `blocked-shaping` package before approving the map.

Do not use the Project Map as an implementation tracker. Matt, Spec, Ticket, implementation, and verification lifecycle states do not belong here.

## MVP Cut

List each package ID exactly once and add one concise statement of the end-to-end job the complete cut enables. Every listed ID must exist and must not be `deferred` or `blocked-shaping` in an approved map. The cut is dependency-closed: every direct and transitive product dependency of an MVP package must also appear in the MVP Cut.

## Dependency Map

Each package's `Depends On` section is the single authority for product dependency IDs. It must contain exactly `None` or one or more `- WP-NNN` items with no prose or alternate syntax.

`## Dependency Map` is a derived, non-independent projection in package order. Render every package exactly once:

```markdown
- WP-001: None
- WP-002: WP-001
- WP-003: WP-001, WP-002
```

The validator requires this exact projection. Do not encode internal task order or maintain a second hand-written graph.

## Open questions

For an approved map, `## Initiative-Level Open Questions` must contain the exact one-line value:

```text
None
```

A question belongs here only if its answer can change the package set, package boundary, MVP cut, product dependency, or overall product boundary. Package-internal questions belong in the relevant Matt brief.

## Handoff queue

For an approved map, list each ready brief as a path-only Markdown item in a recommended planning order:

```markdown
- ./matt-briefs/WP-001.md
- ./matt-briefs/WP-002.md
```

Every path must be unique. Only `ready-for-matt` packages may appear. Independent packages may be ordered for convenience, but the map must not misrepresent convenience as a dependency.
