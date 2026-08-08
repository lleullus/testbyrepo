---
name: scope-shaper
description: "Use when the user explicitly requests Scope Shaper for one proposed change, or when an IIS request contains several potentially independent product outcomes. Investigate the connected planning landscape with the exact user-designated Investigation Runner roster, verify material claims directly, and produce either one bounded Ask Matt handoff or a conditional Work Package proposal in the same result. End at observable scope and unavoidable constraints; leave detailed product policy, UI/UX, and implementation design to their IIS owners."
compatibility: "Requires read access to one exact existing project root and a host subagent invocation mechanism. Confirmed artifacts are written only under that project's docs/planning tree."
---

# Scope Shaper

Write findings, recommendations, questions, and artifacts in the user's
conversation language.

## Purpose

Understand the directly connected planning landscape around one proposed change
before detailed product planning begins.

Scope Shaper answers:

> What must be understood together so the next planning unit neither optimizes
> one visible feature in isolation nor expands into unsupported product strategy?

When the result is one coherent observable outcome, prepare one bounded Ask Matt
handoff. When several credible outcome areas may be independently accepted,
deferred, or rejected, add a Work Package proposal at the bottom of the same
result. The same Lead, evidence, conversation, and user approval cover both.

Scope Shaper may inspect implementation surfaces deeply enough to understand the
landscape. Its normative result stops at observable outcome scope and verified
constraints. Detailed product policy, rendered interaction, and internal design
remain with the later IIS owners.

## Position In IIS

```text
explicit Scope Shaper request
or initiative-scale IIS request
-> Scope Shaping Lead and Investigation Runners
-> verified planning landscape
-> bounded Matt handoff
   or conditional Work Package proposal
-> one user confirmation
-> confirmed Scope result and, when needed, thin Work Package files
-> later explicit Ask Matt continuation
```

Ordinary bounded requests continue directly to Ask Matt unless the user names
Scope Shaper. Initiative-scale work enters Scope Shaper because this skill owns
the integrated decomposition decision.

## Required Inputs And Preflight

For a new investigation, require:

- one exact existing project root;
- one proposed change or request; and
- one user-designated Investigation Runner roster with maximum concurrency.

Represent the roster as exact slots:

```text
Investigation Runners:
- Slot: <stable slot id>
  Configured Agent Or Model: <exact user-designated value>
Maximum Concurrency: <positive integer>
```

Before investigation, verify that the project root is readable and is the
intended product root, the request is internally consistent and bounded enough
to form material questions, every Runner slot is unique and available, and the
concurrency limit fits the supplied roster.

A missing, malformed, ambiguous, or inconsistent input returns a short
`SCOPE SHAPING: WAITING FOR INPUT` response with the smallest clarification
needed. An unavailable project root, Runner slot, or invocation surface returns
`SCOPE SHAPING: BLOCKED` with the exact unavailable item. Neither response
creates a planning artifact.

## Roles And Authority

### Scope Shaping Lead

The current main agent is the Lead. The Lead owns:

- the provisional landscape and material-question map;
- Runner assignments and evidence requirements;
- direct first-hand inspection;
- evaluation and challenge of Runner material;
- the planning boundary and unavoidable planning constraints;
- identification of decisions reserved for later IIS owners;
- conditional split/merge, product dependency, and release-cut decisions;
- the user-facing proposal and one confirmation; and
- confirmed Scope and Work Package artifacts.

The Lead reaches its own conclusion from primary evidence. Runner agreement is
neither required nor sufficient.

### Investigation Runner

Each Runner receives one bounded read-only assignment and follows the canonical
`scope-investigation-runner` skill. The Runner supplies evidence and advisory
planning relevance. The Lead owns every boundary, constraint, package,
approval, and continuation decision.

The host owns invocation transport, scheduling, background execution, retry,
resume, timeout, and communication. Scope Shaper owns the exact roster,
concurrency, assignment envelope, assignment ledger, and use of returned
material.

## IIS Decision Boundaries

| Decision | Owner |
| --- | --- |
| Verified material claims and connected planning boundary | Scope Shaper |
| Unavoidable external or preserved-product planning constraints | Scope Shaper |
| Candidate outcome areas | Scope Shaper |
| Conditional split/merge, Work Packages, product dependencies, release cut | Scope Shaper |
| Detailed observable contract and product-policy choices inside one selected unit | Ask Matt |
| Semantic states, transitions, recovery, ordering, concurrency | Behavior Design within Matt |
| Rendered interaction and presentation | Matt's Central UI / UX Routing |
| Internal design, mutation surface, mechanism, and implementation sequence | Implementation Lead and Worker |
| Spec, Tickets, implementation, independent verification | Existing IIS owners |

Delivery Context is evidence for later owners. It is not planning authority by
itself.

## Scope Depth Boundary

Scope Shaper investigates broadly enough to understand the connected landscape,
but the confirmed result has a fixed depth.

A normative Scope statement belongs in the Planning Boundary only when removing
it would change the accepted observable outcome, break the connected user or
operator flow, violate an unavoidable external contract, or fail to preserve an
explicitly adopted existing observable behavior.

Apply these tests before recording a Lead finding:

### Observable Necessity Test

Ask whether the proposed statement changes what a user or operator can complete,
observe, or rely on within the assessed outcome. A useful implementation detail
that leaves the same observable result is not Planning Boundary scope.

### Product-Policy Replaceability Test

Try two reasonable user-visible policies or presentations that both satisfy the
current Planning Boundary. When both remain valid, record the unresolved choice
under `Decisions Reserved For Matt` rather than selecting one here.

### Implementation Replaceability Test

Try two materially different internal implementations that satisfy the same
outcome and Planning Constraints. When both remain valid, the choice is owned by
Implementation. Scope Shaper may preserve the supporting repository fact in
Delivery Context, but does not turn one implementation path into a requirement.

### Constraint Test

A current repository or runtime fact becomes a Planning Constraint only when it
is an unavoidable external, public, persisted, safety, authority, or deliberately
preserved observable boundary. Other current-code facts remain Delivery Context.

These tests govern the result, not the depth of inspection. The Lead may inspect
files, symbols, tests, and runtime behavior in detail while keeping the planning
output at the correct authority level.

## Lead-First Investigation Frame

Before dispatching, inspect enough of the project to identify the smallest set
of unknowns that can change:

- whether the request is one coherent observable outcome;
- whether adjacent outcome areas are independently acceptable;
- what belongs inside or outside the connected planning boundary;
- which verified constraints cannot be chosen away by later planning;
- which product-policy or rendered decisions remain for Matt;
- whether an existing capability already satisfies part of the request; or
- whether an external contract materially constrains the result.

Investigate only the connected landscape: current user or operator flow,
relevant existing behavior, extension and state boundaries, permissions,
external contracts, tests, documentation, reusable capabilities, and concrete
omissions that can make the result incomplete or force redesign of the same
boundary.

Product-wide strategy, market positioning, unrelated roadmap work, and
possibilities without an evidenced connection remain outside this assessment.

## Runner Dispatch

Split assignments by evidence domain rather than desired conclusion.
Independent questions may run in parallel within the supplied concurrency
limit; dependent questions remain sequential.

Every assignment states:

```text
Assignment ID:
Runner Slot:
Configured Agent Or Model:
Question:
Why the answer can change the planning boundary:
Project Root:
Allowed Evidence:
Required Source Anchors:
Explicit Exclusions:
```

The same slot and configured identity appear in the report.

## Assignment Ledger And Fan-In

Maintain one in-session ledger:

```text
Assignment ID:
Runner Slot:
Configured Agent Or Model:
Terminal Status: COMPLETED | BLOCKED | FAILED | TIMEOUT | INVALID_REPORT
Question Resolution: VERIFIED_FROM_REPORT | LEAD_DIRECT | NO_LONGER_MATERIAL | UNRESOLVED
```

`COMPLETED` means only that a report returned. The exact question becomes
`VERIFIED_FROM_REPORT` when the report establishes the answer, material gaps and
counterevidence are resolved, anchors are sufficient, and the Lead directly
reopens or reproduces the primary evidence.

`Answer: Not established`, a material `Unverified` item, conflicting evidence,
or insufficient anchors keeps the question `UNRESOLVED`. A failed Runner also
remains unresolved unless the Lead closes the exact question directly or a
verified boundary change makes it no longer material.

A material unresolved question blocks a normal proposal. Report the unresolved
question and the smallest action that can close it.

## Evidence And Lead Challenge

Normalize findings as:

- **Fact** — directly supported by an inspectable primary source.
- **Inference** — an interpretation connecting verified facts.
- **Proposal** — a suggested boundary or direction.
- **Unknown** — not established by current evidence.

For each material claim used in a boundary or package decision, the Lead:

1. opens or reproduces the primary evidence;
2. checks that it belongs to the current project or current external contract;
3. matches the strength of the claim to the evidence;
4. tests a plausible conflicting explanation or counterexample;
5. applies the Scope Depth Boundary tests; and
6. records only the finding that survives those checks at the correct authority
   level.

A material claim records one planning relevance:

- `BOUNDARY` — necessary observable scope;
- `PLANNING_CONSTRAINT` — an unavoidable or deliberately preserved boundary;
- `RESERVED_FOR_MATT` — a material product, Behavior, or UI decision that the
  current boundary does not settle;
- `OUTCOME_CANDIDATE` — a connected result that may be independently accepted;
- `DELIVERY_CONTEXT` — a verified implementation or environment fact with no
  automatic normative force;
- `DECOMPOSITION` — evidence used only for split/merge, dependency, or release
  cut; or
- `NONE` — no material planning effect.

Runner prose and consensus locate questions and evidence; they do not establish
a final planning fact.

Use simple local numbering inside the Scope result for readability. Those
numbers are not cross-file identifiers.

## Planning Landscape

The proposal separates six meanings.

### Planning Boundary

The smallest coherent observable product or operating outcome that can be
planned and accepted as one unit. `Includes` states observable obligations and
preserved behavior, not detailed acceptance criteria, UI presentation choices,
or internal mechanisms.

### Planning Constraints

Verified external, public, persisted, safety, authority, or deliberately
preserved observable boundaries that later planning must honor. Current
implementation facts enter this section only when the Constraint Test succeeds.

### Candidate Outcome Areas

Connected results that may be independently acceptable. They remain candidates
until the decomposition test below decides whether they belong together.

### Decisions Reserved For Matt

Material product-policy, semantic Behavior, or rendered-interaction decisions
inside the boundary that are not fixed by the user's request, an adopted
authority, or an unavoidable contract. Their presence is not an unresolved
Scope question when Ask Matt is the correct owner.

### Delivery Context

Verified repository, runtime, migration, build, tool, test, or external facts
that later IIS owners need to know. Record what exists, is absent, or was
observed. File and component names may serve as evidence anchors. Delivery
Context does not prescribe a mutation surface, component choice, state
placement, reuse decision, mechanism, or implementation sequence.

### Outside The Assessed Landscape

Nearby possibilities that lack a verified connection to the current request.
This means only that they are outside this investigation.

## Conditional Work Package Proposal

When the landscape contains one coherent outcome, omit this section and prepare
one Ask Matt handoff.

When several candidate outcome areas remain, the same Lead applies
`references/initiative-decomposition-rules.md` and adds:

```text
## Work Package Proposal

### Split / Merge Decisions
- candidate relationship
- MERGE or SPLIT
- independent acceptance test
- strongest reasonable counterexample
- Lead finding
- supporting material claim numbers from this document

### Proposed Work Packages
- outcome
- includes
- excludes
- dependencies
- why this is one package
- why it is separate
- decisions reserved for Matt

### Release Cut
- MVP
- Next
- Deferred

### Next Planning Units
- exact proposed Work Package paths
```

Package count is an output of these decisions. Technical layers, APIs, modules,
UI components, test surfaces, and anticipated implementation order are evidence
about delivery, not independent product acceptance by themselves.

Work Package boundaries inherit applicable Planning Constraints from the source
Scope result. Package definitions do not convert Delivery Context into product
scope.

## User Confirmation And Corrections

Present the complete current proposal once: verified claims, Planning Boundary,
Planning Constraints, candidate areas, Decisions Reserved For Matt, Delivery
Context, and the Work Package proposal when present. Ask the user to confirm or
correct that whole result.

Confirmation approves the Scope-owned boundary, constraints, and decomposition.
It acknowledges that listed Matt decisions remain open; it does not silently
approve one of their possible answers.

A correction reopens only the affected evidence, boundary entries, constraints,
reserved decisions, split/merge decisions, dependency descendants, and release
cut. Recalculate those parts before presenting the complete proposal again. The
earlier proposal is not used for continuation after a material correction. When
confirmed files already exist, keep them unchanged until the corrected result is
confirmed, then rewrite the source and regenerate every affected Work Package
file.

After explicit confirmation, write the confirmed artifacts. There is no second
shaping approval.

## Confirmed Artifacts

### Source Authority

Write exactly one source authority:

```text
<Project-Root>/docs/planning/scope-shaping/<work-slug>/SCOPE-SHAPING-RESULT.md
```

It owns:

- the verified material claims;
- Planning Boundary;
- Planning Constraints;
- Candidate Outcome Areas;
- Decisions Reserved For Matt;
- Delivery Context;
- split/merge decisions when applicable;
- Work Package definitions and release cut when applicable; and
- the confirmation record.

Use `templates/SCOPE-SHAPING-RESULT.template.md`. Write it only after user
confirmation with `Status: confirmed` and `Unresolved Material Questions: None`.

### Bounded Continuation

For one bounded outcome, the confirmed Scope result itself is the Ask Matt
handoff. A later explicit user action names that exact path.

Ask Matt receives the Planning Boundary and Planning Constraints as the current
frame, treats Decisions Reserved For Matt as unresolved product decisions, and
uses Delivery Context only as non-normative evidence.

### Initiative Continuation

For an initiative, create one thin file per non-deferred package:

```text
<Project-Root>/docs/planning/scope-shaping/<work-slug>/work-packages/WP-NNN.md
```

Each file carries only the selected package boundary, dependencies, decisions
reserved for Matt, and the source Scope result path. It does not duplicate the
investigation record, decomposition rationale, Planning Constraints, or
Delivery Context. Ask Matt reads the source result and applies only constraints
whose scope contains the selected package.

Use `templates/WORK-PACKAGE.template.md`, then run:

```text
python3 <scope-shaper-directory>/tools/validate_scope_result.py \
  <absolute-SCOPE-SHAPING-RESULT.md-path>
```

The validator checks structural integrity and boundary drift: confirmed source,
required planning sections, open material questions, unique package IDs, valid
acyclic dependencies, release-cut membership, MVP dependency closure, expected
package files, source links, and package Outcome/Includes/Excludes/Dependencies
matching the source. It does not grade product judgment, depth classification,
or exact explanatory prose.

## Handoff

After confirmation, report:

```text
Confirmed Scope Result:
- <absolute path>

Next Planning Unit:
- Ask Matt from the confirmed Scope result
```

or:

```text
Confirmed Scope Result:
- <absolute path>

Ready Work Packages:
- <absolute WP path>
- ...
```

Stop there. Ask Matt begins only from a later explicit user action naming the
confirmed Scope result or one exact Work Package file.
