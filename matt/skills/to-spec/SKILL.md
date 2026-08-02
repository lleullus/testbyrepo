---
name: to-spec
description: Synthesize a local Markdown SPEC.md from the current planning conversation; it remains draft until explicitly approved.
disable-model-invocation: true
---

# To Spec

## Purpose

Turn the approved product intent, fixed boundaries, preserved behavior, and
observable completion evidence into one declarative local Markdown Spec
without choosing or beginning the implementation.

## Inputs

- The most recently user-confirmed contract-only shared understanding.
- The exact product project root, work slug, and current external planning workspace when already prepared.
- The planning owner, if one is named.

## Terminal UI / UX Authority Gate

Before drafting the Spec in memory or writing `SPEC.md`, independently
reclassify the confirmed scope under the Central UI / UX Routing semantics in
`ask-matt`. Do not trust an upstream skill to have remembered this obligation.
Classify actual rendered behavior, not filenames, frameworks, or the word
`frontend`: pixels, content/copy, interaction/navigation,
loading/empty/error/success/permission presentation, responsive behavior,
accessibility semantics, focus/keyboard behavior, assets, and motion are all
rendered behavior.

Fail closed only when the confirmed scope introduces a new/material rendered UI
or retains an unresolved material UI design obligation and lacks one applicable,
complete, approved local UI/UX authority explicitly adopted by the latest
shared understanding. Do not write a draft Spec on that failure. Return:

```text
BLOCKED: UI / UX authority required before SPEC.md
Reason: <missing, incomplete, unapproved, inapplicable, or not-explicitly-adopted authority>
Next action: return to Matt's UI authority flow; use active ima2-uiux only for unresolved design judgment, then complete or adopt the authority in shared understanding
```

For a new/material rendered UI, a qualifying authority has a non-empty owner,
an explicit scope, the applicable complete rendered-design decisions, no
unresolved decision in that scope, explicit user or planning-owner approval,
and the exact local path adopted by the latest shared understanding. A
`Status: approved` line or a filename alone is insufficient. A Design Read,
style choice, default, prototype, or generated concept alone is insufficient
for new/material UI. An existing finished applicable approved authority,
including one supplied by the user, may be reused only when the shared
understanding explicitly adopts it.

A bounded rendered contract does not require a separate pre-Spec `DESIGN.md`
when the confirmed shared understanding already fixes every rendered decision
or direct preservation condition in that scope. Preserve them directly in the
`## UI / UX` section; after explicit Spec approval, this exact Spec may serve as
the scoped UI authority. An applicable external approved authority may be used
instead.
Do not block non-UI work or an engineering-only frontend change that exactly
preserves UX and has no due-now direct rendered-result exercise. Any UI
authority supplies rendered-design detail only; it cannot expand, reverse, or
replace the product outcome and scope confirmed for this Spec.

## Normative source lock

The most recently user-confirmed contract-only shared understanding is the sole
normative source for the Spec.

Repository code, prior Specs, Tickets, tests, documentation, prototypes, and
runtime observations may explain the problem, verify current behavior, or
provide later implementation context. They must not add to, strengthen, narrow,
or silently reinterpret the confirmed contract.

Truth is not authority. A verified fact about the repository, runtime, API,
deployment, or previous implementation does not become a requirement merely
because it is true. It is normative only when it is already part of the
confirmed planning baseline or an unavoidable verified external contract.

If writing an accurate Spec appears to require a new product requirement,
boundary, Non-Goal, or externally imposed constraint, stop and obtain explicit
confirmation of that delta. Do not silently include it in the draft.

Do not re-interview the user for decisions already established. If the product
root, work slug, owner, or a material decision is unknown, request only what is
needed to write an accurate Spec. If no planning workspace exists in current
context, prepare the default or user-supplied external workspace with
`../../../planning-workspace/planning_workspace.py` resolved from this skill's
canonical physical directory. If one exists, pass its exact canonical path back
to the same tool as `--workspace` and reuse it. When the intended absolute
product root is fixed but not provisioned yet, use the helper's explicit
`--future-project-root` path; it must not create that root. Spec drafting and
approval may continue with the returned rootless workspace. Do not manually
create, repair, or adopt a workspace after any helper failure.

## Output Contract

Write exactly one file at:

```text
<planning-workspace>/SPEC.md
```

`planning-workspace` must be the tool-validated canonical external directory,
disjoint from the product root. Report the written Spec by canonical absolute
path. Do not create a new `.scratch` planning destination in the product root.
For a future root, disjointness is provisional until the root exists; preserve
the same workspace identity for the later strict revalidation.

The document begins with a title, then these exact metadata keys:

```text
Status: draft
Owner: <user or named planning owner>
```

It contains these exact headings:

```text
## Problem
## Desired Outcome
## Requirements
## Non-Goals
## Implementation Constraints
## Verification Expectations
## UI / UX
## Open Questions
```

Write the Spec in the user's conversation language. For non-UI work, the exact
body of `## UI / UX` is `Not applicable`. For new/material UI, record one exact
local path to the adopted UI/UX authority and its applicable rendered scope;
resolve a relative path from the Spec directory and retain its canonical target
for downstream comparison. Do not restate it as product scope authority. For a
bounded rendered contract without an external authority, record every adopted
rendered decision or preservation condition needed for that scope and state
that this approved Spec is its scoped UI authority. Capture only prototype
decisions the user explicitly adopted; a prototype result alone is not
authority.

## Approval Rules

Start with `Status: draft`. Change the exact status value to `approved` only after the user or explicitly named planning owner confirms it and no product, scope, boundary, or evidence-backed contract-contradiction decision remains unresolved. Never infer approval, and never use `approved` while any unresolved decision remains in `## Open Questions`.

For a Spec that adopts an external UI authority, any later change to that
authority's scoped decisions invalidates the prior adoption. Keep or return the
Spec to `draft` until the changed UI delta is reflected in shared understanding
and explicitly approved; do not silently consume the changed document.

A Spec does not require a complete implementation approach before approval.

When the approved outcome authorizes first product/package/application
artifacts in a scope without current target readiness, approval does require the
three planning authorization facts to be resolved:

1. the scope in which initialization mutation is authorized;
2. every applicable external/public/persisted identity and intentionally fixed
   runtime, toolchain, deployment, or operational constraint, including an
   explicit statement when none applies; and
3. whether every remaining material bootstrap choice is fixed or explicitly
   delegated to Implementation Lead/Worker.

Preserve observable initialization scope and externally consumed identities in
`Requirements`. Preserve intentionally fixed operational/technical constraints
and the fixed/delegated disposition in `Implementation Constraints`. Do not add
new metadata, repeat the absolute product path in the Spec body, or turn current
source absence into a permanent requirement. If any applicable fact remains
unresolved, keep the Spec draft.

Do not require Matt to identify, validate, or prove an implementation path
before approval. Do not block approval because feasibility has not yet been
demonstrated. Block approval only when a specific unresolved contradiction
between the Desired Outcome and the confirmed constraints, Non-Goals, or an
unavoidable external authority boundary is supported by verified evidence or
clear logic.

A feasibility Open Question must name the exact conflicting contract clauses or
external capability fact. It must not ask which endpoint, request shape,
interface, algorithm, or implementation approach should be used.

Do not block approval merely because the exact files, modules, endpoint,
abstraction, task sequence, or focused test seam are not yet known.
Implementation Lead owns those decisions.

Explicit bootstrap delegation permits private implementation choices only. It
does not authorize network access, package publication, global installation,
credential use, external resource creation, or Git metadata changes. An
external identity is required only when a caller, registry, deployment,
persisted contract, or operating environment actually consumes it; do not
invent one for a private package or module.

## Mandatory contract audit

Draft the Spec in memory before writing it. For every statement that can cause
an implementation to pass or fail acceptance, regardless of section, verify
all of the following:

1. Provenance: it traces to the confirmed shared understanding or an
   unavoidable, directly verified external contract.
2. Necessity: violating it would break an approved outcome, preserved observable
   invariant, explicit boundary, Non-Goal, or completion evidence.
3. Replaceability: it does not reject a different internal implementation that
   satisfies the confirmed contract.
4. Specificity: it is no more solution-specific than its normative source.

If a clause fails any check, remove it or rewrite it at the observable-contract
level. If it represents a genuinely new decision, return to the user for an
explicit delta confirmation. Perform this audit internally; do not include the
audit table in the Spec.

## Declarative contract rules

The Spec fixes what must become true, what must remain true, and what evidence
will establish completion. It does not pre-plan the internal reconciliation
path.

Apply these section rules:

- `Desired Outcome` describes the observable end state.
- `Requirements` contain observable behavior, preserved behavior, and approved
   product decisions.
- `Non-Goals` identify only approved work or behavior that the implementation
  must not add.
- `Implementation Constraints` contain only deliberately fixed product or
  operational boundaries, externally owned contracts, security or compatibility
  invariants, and technical mechanisms whose use is itself an approved
  requirement.
- `Verification Expectations` describe observable evidence of the Desired
  Outcome and preserved invariants.
- `Open Questions` contain unresolved product, scope, boundary, or material
  evidence-backed contract-contradiction decisions. Choosing between otherwise
  valid internal implementations is not an Open Question.

Do not launder an implementation choice through `Non-Goals`, `Implementation
Constraints`, `Verification Expectations`, a preservation clause, a
current-environment fact, a Scope statement, or descriptive text. The same
provenance and replaceability rules apply to every statement that can cause an
otherwise valid implementation to fail acceptance, regardless of its section.

Exact paths, ports, URLs, endpoints, request or response fields, protocols,
formats, transports, storage layouts, libraries, interfaces, adapters, probes,
test seams, and task sequences are suspect details. They may remain normative
only when the user explicitly approved that exact mechanism or an unavoidable
external contract requires it.

Do not make any of the following normative unless it is itself an explicit
approved constraint:

- an anticipated root cause;
- an expected file or module;
- a proposed endpoint or request shape;
- an internal interface or abstraction;
- an implementation sequence;
- preparatory or prerequisite work predicted by the planner; or
- an internal test seam, mock, collaborator, or test-file layout.

Use this replaceability test:

> If a different internal implementation could satisfy every Requirement,
> Constraint, Non-Goal, and Verification Expectation, the Spec must not reject
> that implementation.

A factual claim about the current codebase or runtime may be used normatively
only when it is already part of the confirmed planning baseline or an
unavoidable verified external contract. User approval authorizes product
decisions and explicit constraints; it does not make an empirical technical
explanation true.

Prior Specs, Tickets, tests, and current implementations are not imported as
normative authority by reference. When the user asks to preserve existing
behavior, preserve only the confirmed observable behavior and invariants, not a
previous protocol, storage layout, component boundary, data field, test
arrangement, or other internal mechanism. A prior clause becomes normative only
when the user explicitly adopts that clause or its observable meaning in the
current planning baseline.

## Next Action

After the Spec is approved, the user may use `to-tickets` to prepare implementation Tickets. Do not invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
