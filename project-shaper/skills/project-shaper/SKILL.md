---
name: project-shaper
description: Use when a user has a product-, project-, or initiative-scale goal that is too broad for one Matt planning flow and needs to be split into large, independently plannable product work packages first; especially when the user references an entire existing product or repository. Do not use for an already bounded feature, a technical design, or implementation-task decomposition.
---

# Project Shaper

Write questions, recommendations, maps, and handoff briefs in the language the user uses in the conversation.

## Purpose

Turn one broad initiative into the smallest useful set of the largest still-independent `Matt-sized Work Packages`.

Project Shaper answers:

> Which large product outcomes should be planned separately, in what product-level dependency shape, and which of them form the first usable release?

It does not answer how those outcomes will be implemented, and it does not replace Matt's contract clarification, Spec, Ticket, or approval flow.

## Position In The Flow

```text
initiative or reference product
-> project-shaper
-> approved PROJECT-MAP.md
-> one ready Matt brief at `matt-briefs/WP-NNN.md` per Work Package
-> from-project-shaper / ask-matt
-> approved SPEC.md
-> ready Tickets
-> Implementation Lead
```

Never send an initiative containing several independently acceptable outcomes directly into one Matt Spec merely because the user supplied one paragraph.

## Admission

Use Project Shaper when at least one of these is true:

- the user wants to build, recreate, replace, or take inspiration from an entire product or repository;
- the desired end state contains multiple outcomes that could be accepted, used, released, deferred, or rejected independently;
- one planning conversation would have to settle unrelated product decisions for different actors, operating modes, lifecycles, or expansion branches; or
- the user explicitly asks for large pieces, phases, a product breakdown, an MVP cut, or a queue of separate Matt planning units.

Do not use Project Shaper when the input already describes one coherent observable change, even if implementing it will touch many technical layers. Technical complexity alone does not make an initiative.

When the work is already one Matt-sized unit, route directly to `ask-matt`. When one already-bounded unit needs several planning sessions, use `wayfinder`; do not use `wayfinder` as a substitute for initiative decomposition.

## Authority Boundary

- The user's stated goal and explicitly adopted product decisions are the source of authority.
- A reference product, repository, document, or competitor is discovery evidence, not an automatic parity contract. Do not import every observed capability as a requirement.
- An approved `PROJECT-MAP.md` authorizes only initiative coordination: the product boundary, Work Package boundaries, sibling ownership, MVP cut, and product-level dependency relation the user approved.
- A package Matt brief at `matt-briefs/WP-NNN.md` is a projection of that map. It is not an approved package Spec and cannot silently create detailed package requirements.
- Matt must still obtain a user-confirmed contract-only shared understanding before `to-spec`. Matt's approved Spec remains the package-level product authority.
- Project Shaper never selects files, modules, schemas, APIs, libraries, algorithms, test seams, or implementation order.

## Inputs

- The broad product or project outcome.
- Any explicitly known top-level boundaries, non-goals, target users, and release intent.
- Optional reference products, repositories, documents, or examples.
- The target project root and an initiative slug only when artifacts are about to be written.
- The planning owner, if one is named.

Do not request a project root or slug before an artifact is needed. Do not ask technical questions that Matt or Implementation Lead can own later.

## Core Terms

### Work Package

A large product-level outcome that:

- can be clarified and approved through one independent Matt Spec flow;
- has one coherent acceptance moment;
- has an explicit product boundary against sibling packages;
- may contain many internal implementation tasks; and
- is not merely preparation for another package.

### Matt-sized

A package is Matt-sized when Matt can resolve its package-level outcome, preserved behavior, boundaries, non-goals, and observable completion evidence without also deciding the product contract of a sibling package.

### Product dependency

`WP-B` depends on `WP-A` only when `WP-B`'s observable product outcome cannot be meaningfully delivered or accepted without the observable outcome of `WP-A`. Shared infrastructure, likely code reuse, or anticipated implementation sequence is not a product dependency.

## Process

### 1. Establish the initiative frame

State the broad product outcome, intended user or operator, explicit top-level boundary, and the role of any reference material. When parity versus inspiration would materially change the package set or MVP cut, make that the first shaping decision and recommend the smallest useful interpretation.

Do not begin with a feature inventory copied from the reference.

### 2. Inspect references only for product evidence

When a repository, product, or document is provided, inspect authoritative material before relying on it. Extract only user-visible capabilities, operator-visible lifecycle outcomes, externally meaningful modes, and explicit product boundaries relevant to the user's stated goal.

Do not infer required internal architecture from the reference implementation. Distinguish observed current capability from user-adopted scope.

### 3. Discover candidate outcomes

Express each candidate as an observable result, normally in the form:

```text
<actor> can <complete a meaningful job or operate a meaningful lifecycle>
```

Do not use technical layers such as frontend, backend, database, API client, adapter, framework, refactor, or test infrastructure as candidate packages unless that mechanism is itself the approved product outcome.

### 4. Split and merge by product decision boundary

Use the rules in `references/decomposition-rules.md`.

Prefer the largest package that remains independently plannable. Split only when the resulting outcomes can genuinely be planned or accepted independently, or when they represent a real product, rollout, authority, or lifecycle boundary. Merge candidates that are only technical prerequisites, fragments of one acceptance moment, or meaningless without each other.

Do not target a package count. The map may contain a few packages or many; every split must change what Matt can plan independently.

### 5. Build the product dependency graph

Add only necessary product dependencies. Record each edge only in the package's canonical `Depends On` list. The top-level Dependency Map is an exact derived projection of those lists, never a second authority. For every edge, state the counterfactual:

> Without the predecessor's observable result, the dependent package cannot deliver or define this specific observable result.

If the explanation is only “we probably need the same abstraction/data model/service first,” remove the edge and leave implementation order to Implementation Lead.

Acyclic dependencies are required. Independent expansion branches may share the same predecessor and remain unordered relative to each other.

### 6. Choose the MVP cut

Select the smallest dependency-closed connected set of Work Packages that delivers the initiative's core end-to-end job for a real user or operator. Every transitive product dependency of an MVP package must also be in the MVP. A package belongs in the MVP only when removing it makes that core job unavailable, not merely less polished, less broad, or less scalable.

Separate:

- `MVP`: required for the first usable product outcome;
- `Next`: independently valuable near-term expansion; and
- `Deferred`: intentionally outside the current shaping commitment.

Do not turn every observed reference feature into MVP scope.

### 7. Resolve only shaping-level decisions

Ask only decisions whose answers materially change at least one of:

- the number or identity of Work Packages;
- a package's product boundary or sibling ownership;
- the MVP cut;
- a product dependency; or
- whether a capability is in the initiative at all.

Use a dependency-aware interview: ask the most gating shaping decision first, recommend an answer, and defer questions that belong wholly inside one package to Matt. Do not conduct each package's full requirements interview during shaping.

### 8. Review the proposed map

Before approval, present:

- the product outcome and boundary;
- the proposed Work Packages in dependency order;
- the MVP cut;
- deferred capabilities; and
- any initiative-level open question that still changes the decomposition.

Obtain explicit user confirmation of the decomposition. Never infer approval.

### 9. Write the artifacts

Use the exact contracts in:

- `references/project-map-contract.md`
- `references/matt-handoff-contract.md`

Write:

```text
<project-root>/.scratch/<initiative-slug>/PROJECT-MAP.md
<project-root>/.scratch/<initiative-slug>/matt-briefs/WP-NNN.md
```

A map starts as `draft`. Mark it `approved` only after the user confirms the initiative boundary, package split, MVP cut, and dependency graph and no shaping-level open question remains.

Create a `ready-for-matt` brief only for a package whose identity and sibling boundary cannot still be changed by an unresolved initiative-level decision. Details intentionally reserved for Matt do not block readiness.

### 9.5 Validate the handoff set

Before reporting any package as ready, validate the approved map and every referenced brief with the bundled dependency-free checker when it is available:

```text
python3 <project-shaper-skill-directory>/tools/validate_project_map.py <absolute-PROJECT-MAP.md-path>
```

A non-zero result blocks handoff. Repair only artifact-contract or projection defects reported by the checker; do not use validation as authority to change an approved product decision. If the checker is unavailable, manually perform the same path, metadata, dependency, cycle, queue, and exact-projection checks defined in the artifact contracts.

### 10. Hand one package to Matt

Do not fan out several live Matt planning conversations automatically.

Report the exact paths of all `ready-for-matt` briefs in the approved handoff queue. The user may start exactly one with:

```text
from-project-shaper <exact-matt-brief-path>
```

When the integrated `ask-matt` overlay is installed, this is also valid:

```text
ask-matt <exact-matt-brief-path>
```

Project Shaper may start `from-project-shaper` immediately only when the user explicitly asks to continue into a selected package in the current conversation.

## Boundary Change Return

If Matt discovers that a package cannot be coherently planned without moving outcome scope across siblings, merging packages, splitting the package, or changing the MVP/dependency graph, Matt must not absorb that change silently.

Return a concise shaping delta containing:

```text
Affected package:
Observed boundary conflict:
Proposed map change:
Packages affected:
Why package-local clarification is insufficient:
```

Resume Project Shaper, obtain user approval for the map delta, regenerate affected briefs, and then restart the package handoff. A technical implementation difficulty alone is not a shaping delta.

## Prohibitions

- Do not create one giant Spec for the whole initiative.
- Do not write package Specs, Acceptance Criteria, or implementation Tickets.
- Do not decompose by code layer, repository directory, team, language, or anticipated task sequence.
- Do not create “foundation,” “platform,” “refactor,” “schema,” “API,” or “test” packages unless they have an independently approved observable product or rollout outcome.
- Do not use the reference product as automatic authority.
- Do not settle package-internal product decisions merely to make the map look complete.
- Do not invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.

## Final Output

When shaping is complete, report:

```text
Approved Project Map:
- <absolute-project-map-path>

Ready for Matt:
- <absolute-WP-brief-path>
- ...

MVP Cut:
- WP-...
```

Then state only that one ready brief can be used to start Matt. Do not select a Worker or begin implementation.
