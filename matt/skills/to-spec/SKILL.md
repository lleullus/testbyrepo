---
name: to-spec
description: Synthesize and defect-review a local Markdown SPEC.md from current planning authority; adopt a faithful complete candidate unless the user explicitly requires a separate approval gate.
disable-model-invocation: true
---

# To Spec

## Purpose

Turn the approved product intent, fixed boundaries, preserved behavior, and
observable completion evidence into one declarative local Markdown Spec
without choosing or beginning the implementation.

## Inputs

- The most recently user-confirmed contract-only shared understanding.
- The exact existing product project root and work slug.
- `Source Increment`: the exact Scope-selected Increment path when Ask Matt entered from Scope Shaper, otherwise exact `None` for a direct next-increment-ready Ask Matt unit.
- The planning owner, if one is named.
- The completed Behavior Design result and every approved scoped Behavior authority adopted by the confirmed shared understanding.
- The current adversarial-consensus activation or explicit withdrawal fact for this planning unit when one exists in the current conversation or caller handoff.

## Non-Continuation Reporting

Whenever an admission, authority, source, or projection gate stops To Spec before the requested Spec can be faithfully drafted/written, or returns the work to another planning owner, read and apply the current `iis-workflow` [Non-Continuation Decision Provenance](../../../iis-workflow/SKILL.md#non-continuation-decision-provenance) section. Preserve the existing To Spec result/header and do not create a new lifecycle state. Normal successful Spec projection does not carry this block.

## Adversarial Consensus Admission

A direct or explicit To Spec request is not withdrawal of an active adversarial-consensus instruction and does not itself satisfy that gate. When the current planning unit has an active adversarial-consensus instruction that the user has not explicitly withdrawn, do not draft or write `SPEC.md` until the current planning context establishes all of the following:

- one exact `Adversarial Planning Challenger` binding explicitly designated by the user;
- a user-confirmed Intent Anchor for the current candidate;
- `ADVERSARIAL CONSENSUS REACHED` for the latest complete candidate, with no material candidate delta after that review; and
- post-consensus final integrated user approval of that exact latest shared understanding.

An approval given before the current consensus is not the post-consensus final integrated user approval and must not be reused as though it were. When any required condition is missing, return without drafting or writing the Spec:

```text
TO SPEC: BLOCKED
Decision: TO SPEC: BLOCKED
Governing authority: to-spec / Adversarial Consensus Admission
Observed condition: <missing Challenger binding | Intent Anchor confirmation | current latest-candidate consensus | post-consensus final integrated user approval>
Effect: SPEC.md drafting and writing cannot start while the active adversarial-consensus admission gate is incomplete
Next allowed action: complete the exact missing Ask Matt/adversarial-consensus gate or explicitly withdraw adversarial consensus
```

If the user explicitly withdraws adversarial consensus for this planning unit, this additional admission gate no longer applies and ordinary To Spec admission continues. Do not create a receipt, flag file, sidecar, or persistent gate state; use only the current conversation/caller context.

## Source Increment Admission

Before drafting or writing the Spec, resolve `Source Increment` from the current Ask Matt/caller context.

- For a direct next-increment-ready Ask Matt unit that never entered Scope Shaper, require exact `None`.
- For Scope-shaped work, require one exact raw, non-symlink local `increments/INC-NNN.md` path under the exact Project Root. Run `../../../scope-shaper/tools/validate_increment.py` against it immediately before Spec drafting. Require it to remain the current `Status: ready-for-matt` Increment selected by its current Scope result, to remain bound to its immutable `Source-Scope-Revision`, and to have `Suggested-Work-Slug` exactly equal to this Spec's work slug.
- Never convert a known Scope-shaped source to `None`, and never reuse a superseded, stale, drifted, wrong-project, or different-work-slug Increment merely because Matt previously completed planning against it.

For Product Meaning Binding source resolution, do not add a new Spec metadata reference. After the existing Increment admission succeeds, follow that exact admitted Increment's existing `Source-Scope-Revision` to the exact immutable `revisions/SHAPE-NNN.md`. That immutable revision is the binding source for Scope-shaped work. The mutable `SCOPE-SHAPING-RESULT.md` remains navigation only, and `INC-NNN.md` remains a reference hop rather than another binding copy.

When this gate fails, do not draft or write the Spec. Return:

```text
TO SPEC: BLOCKED
Decision: TO SPEC: BLOCKED
Governing authority: to-spec / Source Increment Admission
Observed condition: <missing Source Increment | stale or superseded Increment | project/work-slug mismatch | revision/Increment drift>
Effect: the current Spec cannot be bound to one valid admitted Increment
Next allowed action: return to the current Scope Shaper / Ask Matt boundary and establish one current admitted Increment
```

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
Decision: BLOCKED: UI / UX authority required before SPEC.md
Governing authority: to-spec / Terminal UI / UX Authority Gate
Observed condition: <missing, incomplete, unapproved, inapplicable, or not-explicitly-adopted authority>
Effect: To Spec cannot serialize a material rendered contract without current adopted UI/UX authority
Next allowed action: return to Matt's UI authority flow and complete or adopt the missing rendered-design authority in shared understanding
```

For a new/material rendered UI, a qualifying authority has a non-empty owner,
an explicit scope, the applicable complete rendered-design decisions, no
unresolved decision in that scope, explicit user or planning-owner approval,
and the exact local path adopted by the latest shared understanding. A
`Status: approved` line or a filename alone is insufficient. A visual reference,
style choice, default, prototype, or generated concept alone is insufficient for
new/material UI. An existing finished applicable approved authority,
including one supplied by the user, may be reused only when the shared
understanding explicitly adopts it.

Legacy image-review process metadata may remain in an otherwise complete approved
UI authority as non-normative historical evidence. It is not required for Spec
admission and must not be copied into Spec or Ticket acceptance criteria.

A bounded rendered contract does not require a separate pre-Spec `DESIGN.md`
when the confirmed shared understanding already fixes every rendered decision
or direct preservation condition in that scope. Preserve them directly in the
`## UI / UX` section. After this skill's adoption guard passes and the Spec
reaches exact `Status: approved`, this exact Spec may serve as the scoped UI
authority. An applicable external approved authority may be used instead.
Do not block non-UI work or an engineering-only frontend change that exactly
preserves UX and has no due-now direct rendered-result exercise. Any UI
authority supplies rendered-design detail only; it cannot expand, reverse, or
replace the product outcome and scope confirmed for this Spec.

## Behavior Authority Gate

Before drafting or writing `SPEC.md`, independently verify that Matt completed
the full mandatory Behavior Design phase for this planning unit. Require the
latest confirmed shared understanding to identify every applicable approved
Behavior authority and exact scope.

Resolve each project-relative authority path from the exact Project Root. Every
target must be a readable regular Markdown file whose canonical parent is
exactly one of `<Project-Root>/docs/planning/behavior/contexts/`,
`lifecycles/`, or `invariants/`; `behavior/INDEX.md` and files elsewhere in the
tree are not authorities. It must contain exactly one non-empty `Owner:` and
`Scope:`, and have exact `Status: approved`. Its scope must cover the behavior
needed by this Spec without expanding the confirmed delivery scope. Unchanged
approved authorities may be adopted without reapproval.

Fail closed and do not draft or write `SPEC.md` when Behavior Design did not
complete, an applicable authority is missing/draft/outside the project planning
root, an authority scope is inapplicable or incomplete, a behavior decision is
unresolved, or Behavior and UI authorities conflict. Return the exact defect to
Matt's Behavior Design phase; do not invent, copy, summarize, or override the
missing behavior inside the Spec.

## Normative source lock

The most recently user-confirmed contract-only shared understanding is the
normative source for product outcome, delivery scope, Non-Goals, and deliberate
constraints. When Ask Matt entered from a Scope-selected Increment, that shared
understanding must remain within the exact current Increment and the immutable
`Source-Scope-Revision` that approved it. The mutable current
`SCOPE-SHAPING-RESULT.md` is navigation only for historical interpretation. The
Increment revision's `Intent Horizon`, Work Package siblings, `Provisional
Construction Horizon`, and the Increment's `Deferred Until Re-entry` content are
context for future shaping, not authority for this Spec. If accurate Spec writing
appears to need any of that deferred future capability, stop and return to Scope
Shaper rather than importing it.

The approved Behavior authorities that understanding explicitly adopts are
normative only for their exact behavioral scopes. Applicable UI authorities
remain normative only for rendered design and interaction.

Repository code, prior Specs, Tickets, tests, documentation, prototypes, and
runtime observations may explain the problem, verify current behavior, or
provide later implementation context. They must not add to, strengthen, narrow,
or silently reinterpret the confirmed contract.

Truth is not authority. A verified fact about the repository, runtime, API,
deployment, or previous implementation does not become a requirement merely
because it is true. It is normative only when it is already part of the
confirmed planning baseline or an unavoidable verified external contract.
User approval authorizes product decisions and explicit constraints; it does
not make an empirical technical explanation true.

If writing an accurate Spec appears to require a new product requirement,
boundary, Non-Goal, or externally imposed constraint, stop and obtain explicit
confirmation of that delta. Do not silently include it in the draft.

Do not re-interview the user for decisions already established. If the product
root, work slug, owner, or a material decision is unknown, request only what is
needed to write an accurate Spec. Resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory and prepare or revalidate the work artifact directory under
the existing canonical project root. If the project root does not exist or the
helper fails, do not draft or write the Spec and do not create or adopt an
external fallback.

## Output Contract

Write exactly one file at:

```text
<Project-Root>/docs/planning/work/<work-slug>/SPEC.md
```

The work directory must be the exact `artifactWorkspace` returned by the helper.
Report the written Spec by canonical absolute path. Do not write to `.scratch`,
an external planning directory, or another work slug.

The document begins with a title, then these exact metadata keys:

```text
Status: draft
Owner: <user or named planning owner>
Source-Increment: None | <project-relative docs/planning/scope-shaping/<scope-slug>/increments/INC-NNN.md path>
```

For Scope-shaped work, resolve the admitted raw Increment from the exact Project Root and serialize its project-relative canonical path. For direct Ask Matt work, serialize exact `None`. This metadata is traceability only; it does not import the source revision's deferred or provisional future scope into the Spec.

It contains these exact headings:

```text
## Product Meaning Binding
## Problem
## Desired Outcome
## Requirements
## Non-Goals
## Implementation Constraints
## Verification Expectations
## Behavior Authorities
## UI / UX
## Open Questions
```

`## Product Meaning Binding` follows `../../../product-thesis/SKILL.md`: new direct work uses `iis-product-meaning/v2`, with exact absolute Source and SHA-256 of full source bytes. Scope-shaped work preserves its immutable Scope revision binding unchanged, including supported legacy v1. Read the actual source before projecting Requirements and Verification Expectations; a reference/hash alone does not establish semantic fidelity. Run `python3 ../../../product-thesis/tools/product_meaning_binding.py fingerprint <absolute-SPEC.md-path>` to calculate the source hash, then `validate-spec` to verify the binding and existing Increment → immutable revision lineage. Do not copy the source or its binding into Tickets.

Write the Spec in the user's conversation language. `## Behavior Authorities`
contains one path-and-scope item for every adopted authority:

```text
- <project-relative local path> | Scope: <exact applicable scope>
```

Do not restate Behavior rules in the Spec. For non-UI work, the exact
body of `## UI / UX` is `Not applicable`. For new/material UI, record one exact
local path to the adopted UI/UX authority and its applicable rendered scope;
resolve a relative path from the Spec directory and retain its canonical target
for downstream comparison. Do not restate it as product scope authority. For a
bounded rendered contract without an external authority, record every adopted
rendered decision or preservation condition needed for that scope and state
that this approved Spec is its scoped UI authority. Capture only prototype
decisions the user explicitly adopted; a prototype result alone is not
authority.

Serialize each confirmed outcome-local verification contract as one exact
top-level `- ` item in `## Verification Expectations`, in the outcome order of
the confirmed shared understanding. Use the following exact two-space-indented
labels once per item:

```text
- Outcome: <observable claim>
  Acceptance boundary: <product or canonical inspection boundary>
  Trigger or inspection target: <product input/trigger or canonical target>
  Expected observable result: <expected result>
  Authoritative readback: <product or canonical readback>
  Disposition: Independent | Operator-assisted | Not independently verifiable
  Independent verification required: yes | no
  Acceptance surface: Existing | <surface>; Ticket Scope creates | <surface>; Delivery contract guarantees | <disposable target and availability condition>; Operator-owned | <surface>; None | <confirmed reason>
  External condition: None | <declared operator, authority, environment, or target condition>
```

Add only an applicable outcome-local line, using its exact label:

```text
  Absence terminal condition: <condition>
  Ordering event source and range: <source and range>
  Persistence storage identity and lifecycle boundary: <identity and boundary>
  Interruption checkpoint: <checkpoint>
  External effect sandbox, authority, cleanup, and readback: <contract>
  UI rendered state and interaction readback: <contract>
```

These labels serialize confirmed product meaning; they do not create a new
schema identity, metadata block, persistent outcome ID, executable recipe, or
implementation plan. Do not add a conditional line merely to fill a template.
Do not invent a value omitted by the confirmed shared understanding. An
undecided boundary, readback, disposition, requirement, surface responsibility,
or external condition keeps the Spec draft.

`Not available` is not a placeholder for an unresolved value. Use it only in a
non-independent outcome whose confirmed contract explicitly says that the
particular boundary or readback does not exist and gives the reason, and only
when the disposition and acceptance-surface lines consistently preserve that
decision. `Independent` always requires a concrete acceptance boundary,
trigger/inspection target, authoritative readback, and an existing,
Ticket-Scope-created, or contract-guaranteed disposable acceptance surface.
Use `Delivery contract guarantees` only when the confirmed shared understanding
actually guarantees the named disposable target and its availability condition.
It is not permission to infer a sandbox or convert an unverified current-surface
claim into authority.
`Independent verification required: yes` cannot be combined with
`Operator-assisted` or `Not independently verifiable`.

For an `Operator-assisted` outcome, record the actual operator-owned path and
external condition without representing it as independently executable. For a
`Not independently verifiable` outcome, record the confirmed absence and reason
without creating a verifier path. Source, artifact, document, and structure
claims use direct current canonical-target inspection where that is their
authoritative boundary; do not add a runtime command. Runtime outcomes require
the confirmed product boundary and authoritative readback. Internal tests,
mocks, private helpers, proposed test seams, implementation narration, and
anticipated implementation commands cannot become the normative boundary or
readback.

## Adoption and Optional Approval Rules

Start with `Status: draft`. Self-review is a leaf-local transition guard, not a
new artifact lifecycle. Do not create review-progress statuses, sidecars,
receipts, counters, or workflow records.

By default, change the exact status value to `approved` only after all existing
admission gates and the Mandatory contract audit pass, the exact current
candidate is a complete faithful projection of current authority, and no
material finding or unresolved product/Scope/Behavior/UI/completion decision
remains. Immediately before that status transition, Scope-shaped work must first
rerun the canonical `../../../scope-shaper/tools/validate_increment.py` against
the exact `Source-Increment`, then run
`python3 ../../../product-thesis/tools/product_meaning_binding.py validate-spec <absolute-SPEC.md-path>`
from the canonical skill path. This preserves the existing Increment admission
rules rather than reimplementing them in the binding validator. For Scope-shaped
work `validate-spec` then resolves the exact
`SPEC.Source-Increment -> INC.Source-Scope-Revision -> revisions/SHAPE-NNN.md`
chain, validates both bindings and fingerprints, and requires canonical source/
target equality. For direct Ask Matt work it validates the Spec binding's shape
and internal fingerprint consistency only. A binding mismatch keeps the Spec at
`draft` and reports the differing binding field(s) without rerunning Product
Thesis automatically, creating another approval stage, or invoking a semantic
reviewer. Do not describe this default adoption as an explicit user approval and
do not add provenance metadata to the canonical Spec.

A successful binding validator means only that the recorded binding structure,
fingerprint, exact source resolution, and source/target equality are valid. It
does not prove Product Thesis correctness, Product Thesis -> first-binding
semantic fidelity, binding -> Requirements/Verification Expectations semantic
fidelity, current Increment appropriateness, implementation safety, or product
success. Those remain with the existing planning owner, faithful projection,
and Mandatory contract audit.

If the current user explicitly requires separate user or planning-owner
approval of the completed Spec, run the same full self-review first and then
wait for approval of that exact candidate. A material candidate delta requires
fresh self-review and, when this optional gate is active, fresh approval.
Explicit approval never overrides a failed guard or unresolved decision.

Correct a local serialization, omission, or wording defect inside this same To
Spec lifecycle and rerun the complete guard. If correction requires new or
changed product meaning, return to Ask Matt or Scope Shaper instead of looping
on the draft. Never use `approved` while any unresolved decision remains in
`## Open Questions`.

Adoption also requires one complete outcome-local `## Verification
Expectations` item for every independently acceptable observable outcome. Keep
the Spec draft when a runtime outcome lacks its acceptance boundary or
authoritative readback; an `Independent` outcome lacks a directly established
existing, Ticket-Scope-created, or confirmed delivery-contract-guaranteed
disposable acceptance surface; an
operator-owned or separately authorized path is labeled `Independent`; or the
parent contract requires independent verification but the disposition is
non-independent. Verification-contract completeness is a product-contract
decision, not proof of the eventual internal implementation path.

For a Spec that adopts an external UI authority, any later change to that
authority's scoped decisions invalidates the prior adoption. Keep or return the
Spec to `draft` until the changed UI delta is resolved by its owning authority,
reflected in shared understanding, and the refreshed Spec passes the full
adoption guard; do not silently consume the changed document.

Any semantic change to an adopted Behavior authority returns that authority,
this Spec, and affected unfinished Tickets to `draft`. A conflict among the
shared understanding, Behavior authority, Spec, or UI authority blocks adoption
without an inferred priority.

A Spec does not require a complete implementation approach before adoption.

When the approved outcome authorizes first product/package/application
artifacts in a scope without current target readiness, adoption does require the
three planning authorization facts to be resolved:

1. the scope in which initialization mutation is authorized;
2. every applicable external/public/persisted identity and intentionally fixed
   runtime, toolchain, deployment, or operational constraint, including an
   explicit statement when none applies; and
3. whether every remaining material bootstrap choice is fixed or explicitly
   delegated to later Ticket delivery.

Preserve observable initialization scope and externally consumed identities in
`Requirements`. Preserve intentionally fixed operational/technical constraints
and the fixed/delegated disposition in `Implementation Constraints`. Do not add
new metadata, repeat the absolute product path in the Spec body, or turn current
source absence into a permanent requirement. If any applicable fact remains
unresolved, keep the Spec draft.

Do not require Matt to identify, validate, or prove an implementation path
before adoption. Do not block adoption because implementation feasibility has
not yet been demonstrated. Block adoption only when a specific unresolved contradiction
between the Desired Outcome and the confirmed constraints, Non-Goals, or an
unavoidable external authority boundary is supported by verified evidence or
clear logic.

A feasibility Open Question must name the exact conflicting contract clauses or
external capability fact. It must not ask which endpoint, request shape,
interface, algorithm, or implementation approach should be used.

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

Every normative Goal-level clause must also be decidable during fresh completion
verification from a current authoritative product, canonical artifact, source,
approved operator-owned readback, or other approved current boundary. A clause
that can be established only from historical implementation steps,
implementation reports, diffs, or prior execution records must not be approved
as a Goal-level Requirement, Non-Goal, or Implementation Constraint. Move a
bounded mutation restriction to the applicable Ticket Scope or Non-Goals, or
restate it as a current observable product invariant when that is the actual
approved requirement. Do not weaken fresh completion verification or introduce a
durable history mechanism to admit a historical-only clause.

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
- `Requirements` contain delivery requirements and approved product decisions
  not already owned by adopted Behavior or UI authorities.
- `Non-Goals` identify only approved work or behavior that the implementation
  must not add.
- `Implementation Constraints` contain only deliberately fixed product or
  operational boundaries, externally owned contracts, security or compatibility
  invariants, and technical mechanisms whose use is itself an approved
  requirement.
- `Verification Expectations` describe observable evidence of the Desired
  Outcome and applicable authority scopes through the outcome-local contract
  above, without restating their semantic or rendered rules.
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

Prior Specs, Tickets, tests, and current implementations are not imported as
normative authority by reference. When the user asks to preserve existing
behavior, preserve only the confirmed observable behavior and invariants, not a
previous protocol, storage layout, component boundary, data field, test
arrangement, or other internal mechanism. A prior clause becomes normative only
when the user explicitly adopts that clause or its observable meaning in the
current planning baseline.

## Next Action

After the Spec is approved, use `to-tickets` to prepare implementation Tickets. To Spec does not invoke or orchestrate delivery.
