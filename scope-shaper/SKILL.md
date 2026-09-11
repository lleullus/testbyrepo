---
name: scope-shaper
description: "Use when the user explicitly requests Scope Shaper or when an IIS request is not yet one current durable observable increment. Investigate the connected planning landscape, preserve the long-term intent, establish the actual current product state, decompose independently acceptable outcomes when needed, and select exactly one smallest durable next construction Increment for Ask Matt. Future construction remains provisional until later re-entry against the actual delivered state."
compatibility: "Codebase-backed shaping and all durable artifact writing require one exact existing project root. Genuinely unrooted greenfield work may be shaped from supplied evidence before a root exists, but cannot write artifacts or enter Ask Matt until the root is supplied. Investigation Runners require explicit user authorization, an exact roster, a readable project root, and a host subagent invocation mechanism."
---

# Scope Shaper

Write findings, recommendations, questions, and artifacts in the user's conversation language.

## Purpose

Scope Shaper does two related jobs before detailed product planning begins:

1. understand the connected outcome landscape so one visible feature is not optimized in isolation and unrelated strategy is not pulled in; and
2. choose exactly one durable next product construction Increment from the actual current product state.

The second job is mandatory whenever Scope Shaper runs. A broad outcome may be coherent yet still contain foundation, intermediate, and mature product states that should not all be planned now. Scope Shaper must therefore distinguish the user's long-term intent from the one product state transition that becomes normative for the current IIS cycle.

The selected Increment is not a technical scaffold, temporary mock, or arbitrary small slice. It is the smallest durable, dependency-closed product state change that produces an observable result and can remain as a real foundation for later product capability. Future capability and maturity may be recorded as a provisional horizon, but they are not current delivery authority.

Scope Shaper may inspect implementation surfaces deeply enough to understand the landscape and current state. Its normative result stops at observable outcome scope, unavoidable constraints, and the selected Increment. Detailed product policy, semantic Behavior, rendered interaction, internal design, and implementation sequence remain with their later IIS owners.

## Position In IIS

```text
explicit Scope Shaper request
or IIS request not yet next-increment-ready
-> Scope Shaping Lead
-> direct current-state and landscape investigation
-> optional bounded Investigation Runners when materially useful
-> verified outcome landscape
-> Work Package decomposition when independent outcome areas exist
-> construction-candidate comparison
-> exactly one Selected Next Increment
-> one user confirmation
-> confirmed Scope result and one ready-for-matt Increment
-> later explicit Ask Matt continuation from that exact Increment
```

An ordinary IIS request may bypass Scope Shaper only when the IIS router and Ask Matt admission can already establish one current durable observable increment. Technical depth, file count, or implementation layers alone never decide whether Scope Shaper is required.

### Product Thesis Input

Before shaping a new or materially revised product meaning, the current Lead directly reads and performs `../product-thesis/SKILL.md`. This applies to an explicit Scope Shaper request as well as a router-directed entry. If a current applicable Product Thesis conclusion is already recoverable from current conversation authority or confirmed Scope/Matt authority and fresh evidence does not invalidate it, reuse it without recalibration.

Product Thesis supplies the Reason to Exist, Core Utility, high-level Core Completion Loop, truth/causal invariants, named-item meaning, and success claim boundary. Scope Shaper does not reinvent those conclusions, and Product Thesis does not choose the next Increment. `USER_INPUT_REQUIRED` stops before shaping mutation; `CALIBRATED` continues into normal current-state and landscape investigation.

Preserve applicable Product Thesis meaning through the existing confirmed artifact fields: `Intent Horizon`, `Verified Material Claims`, `Planning Boundary`, and `Planning Constraints`; this remains the semantic-adoption responsibility. In addition, write one compact `Product Meaning Binding` containing only Core Utility, Core Completion Loop, explicit Required Outcomes / Means, Truth / Causal Invariants, and Success Observation in the confirmed `SCOPE-SHAPING-RESULT.md`. The immutable `SHAPE-NNN` revision preserves those fields with the rest of the confirmed Scope and, by the existing byte-for-byte snapshot contract, preserves the exact same binding. Before artifact closure, use `python3 ../product-thesis/tools/product_meaning_binding.py fingerprint <SCOPE-SHAPING-RESULT.md>` to calculate the `iis-product-meaning/v1` fingerprint, write it to the binding, then run the normal Scope validator, which validates the binding internally. Do not create a required separate Product Thesis artifact, copy the complete Product Thesis report into every file, or copy the binding into `INC-NNN.md`, Work Packages, or Tickets.

The selected Increment may establish one durable product state that materially advances the Core Completion Loop; it need not complete the whole loop. Reject a candidate that contributes only technical preparation or does not materially advance the Core Utility, but do not expand the current Increment with future capability merely to complete the long-term thesis. Leave detailed Behavior/UI policy and exact completion semantics to Matt.

Return to the product-meaning owner only when fresh actual evidence invalidates the Reason to Exist, Core Utility, or an essential truth, identity, or ownership premise. Ordinary delivery progress, implementation detail, or a changed construction ordering decision does not trigger Product Thesis recalibration.

## Required Inputs And Preflight

For every new shaping pass require one proposed change, product direction, or request. Use one of two evidence modes:

- **Codebase-backed** — one exact existing project root is available. Verify that it is readable and is the intended product root, then establish Current Product State from direct repository, document, test, and runtime evidence as applicable.
- **Unrooted greenfield** — the product is genuinely new and no intended project root exists yet. Scope Shaper may still investigate the user brief, supplied references, external contracts, and the absence of an existing product baseline, then compare and present construction candidates. Do not invent repository facts or treat a hypothetical future implementation as Current Product State.

A Lead-only shaping pass requires no Investigation Runner roster. Scope Shaper may invoke a Runner only when the user has explicitly authorized Runner use for the current shaping pass and designated the exact roster. Never infer, select, substitute, expand, or reorder Runner identities on the user's behalf.

When Runner use is authorized, require:

```text
Investigation Runners:
- Slot: <stable slot id>
  Configured Agent Or Model: <exact user-designated value>
Maximum Concurrency: <positive integer>
```

Every slot must be unique and available, and the concurrency limit must fit the supplied roster. If the user explicitly requests Runner use but the exact roster or concurrency is missing or ambiguous, return `SCOPE SHAPING: WAITING FOR INPUT` with only that binding defect. If the user did not authorize Runners, continue Lead-only rather than suggesting, auto-selecting, or blocking on a roster. The canonical Runner currently requires a readable Project Root, so unrooted greenfield shaping remains Lead-only until a root exists.

Before investigation, verify that the request is internally consistent enough to form material questions. In codebase-backed mode also verify the root. In unrooted greenfield mode record the exact baseline as `no existing project root or product implementation available for inspection` plus any user-supplied product facts that can be treated as intent or constraints rather than observed repository behavior.

An ambiguous product request returns `SCOPE SHAPING: WAITING FOR INPUT` with the smallest clarification needed. A supplied but unavailable project root returns `SCOPE SHAPING: BLOCKED`; do not silently reinterpret it as greenfield. A genuinely unrooted greenfield request is not blocked merely because the root does not exist yet.

Scope Shaper may take an unrooted greenfield proposal through evidence analysis, construction-candidate comparison, and the normal single user confirmation. After that confirmation, return `SCOPE SHAPING: PROJECT ROOT REQUIRED FOR ARTIFACTS` instead of writing files or entering Ask Matt. When the caller later supplies one exact newly created project root, verify that it is the intended root and recheck whether its actual contents materially change the confirmed Current Product State or construction choice. If nothing material changed, write the already confirmed Scope and Increment artifacts without a second approval ceremony. If material evidence appeared, reopen only the affected shaping decisions and obtain fresh confirmation before writing.

IIS does not create the project root or bootstrap product source as part of planning. Creating an empty project root is host/caller preparation, not a product construction Increment and not permission to invent a technical scaffold as the first product outcome.

Whenever the caller-facing result is `SCOPE SHAPING: WAITING FOR INPUT`, `SCOPE SHAPING: BLOCKED`, `SCOPE SHAPING: PROJECT ROOT REQUIRED FOR ARTIFACTS`, or another non-continuation that returns/redirects instead of completing the requested shaping pass, read and apply the current `iis-workflow` [Non-Continuation Decision Provenance](../iis-workflow/SKILL.md#non-continuation-decision-provenance) section. Preserve the existing Scope Shaper result label and report only the decision-triggering condition, governing rule, effect, and exact next allowed action. Do not add provenance ceremony to the normal proposal, confirmation, or successful Scope result.

## Legacy Scope Artifact Compatibility

Older IIS Scope artifacts may predate `Scope-Revision` and `INC-NNN.md` and may contain `work-packages/WP-NNN.md` with `Status: ready-for-matt` plus `Next Planning Units`. Treat those files as **legacy planning context**, not as current Ask Matt admission and not as automatically valid construction Increments.

Do not restore direct legacy Work Package admission merely for compatibility: doing so would bypass Current Product State reinspection and the durable-Increment selection rules this Scope Shaper now owns. Do not run the current Scope validator and interpret its expected schema failure as evidence that the old product decision was wrong.

When the user names a legacy Scope result or ready Work Package for continuation:

1. verify the exact legacy source and package paths are local, readable, non-symlink files under the stated existing Project Root;
2. before rewriting the active Scope directory, run the canonical `tools/prepare_scope_workspace.py` helper, preserve the legacy source byte-for-byte as `<legacyImport>/SCOPE-SHAPING-RESULT.md`, and preserve every referenced legacy Work Package byte-for-byte under the returned `legacyWorkPackages` directory with its original `WP-NNN.md` basename; if any archive destination already exists with different bytes, block rather than overwrite history;
3. treat the legacy confirmed boundary, constraints, package outcome, includes/excludes, dependencies, and reserved decisions as prior approved planning evidence, while treating old `MVP`, `Next`, `Deferred`, `Next Planning Units`, and `ready-for-matt` status as legacy workflow state rather than current admission authority;
4. directly re-establish the actual Current Product State and any material external constraints now;
5. run the current Work Package/dependency and Construction Increment Shaping rules. A legacy package may be proposed unchanged as the selected candidate only when the Lead verifies that its whole boundary still forms one smallest durable observable Increment under the current evidence. Otherwise narrow, split, defer, or reshape it normally; and
6. present the resulting current Scope proposal and one Selected Next Increment for the normal explicit confirmation. Prior legacy approval is evidence and must not be silently reinterpreted as approval of a materially changed Increment or of the new construction-selection judgment.

This is a semantic migration, not a mechanical file-format conversion. No converter may automatically turn every legacy ready Work Package into an Increment. After current confirmation, write the normal `SCOPE-SHAPING-RESULT.md`, immutable `SHAPE-NNN` revision, `Status: scoped` Work Package records when applicable, and exactly one `Status: ready-for-matt` Increment. The preserved `legacy-import/` files remain historical context only.

## Roles And Authority

### Scope Shaping Lead

The current main agent is the Lead. The Lead owns:

- preservation of the user's long-term intent without turning all of it into current scope;
- direct establishment of the actual current product state;
- the material-question map and optional Runner assignments;
- direct first-hand inspection and evidence challenge;
- the connected outcome landscape and unavoidable Planning Constraints;
- split/merge, Work Package, and product dependency decisions;
- product-capability dependency analysis relevant to construction order;
- comparison and selection of the one next durable Increment;
- explicit identification of future decisions deferred until re-entry;
- the user-facing proposal and one confirmation; and
- confirmed Scope, Work Package, and selected Increment artifacts.

The Lead reaches its own conclusion from primary evidence. Runner agreement is neither required nor sufficient.

### Investigation Runner

Each used Runner receives one bounded read-only assignment and follows the canonical `scope-investigation-runner` skill. A Runner supplies evidence and advisory planning relevance. It does not choose the planning boundary, Work Package, construction order, selected Increment, approval, or continuation.

The user owns the exact Runner roster, configured identities, and maximum concurrency. Scope Shaper may choose bounded evidence-domain questions and map them only onto those supplied slots; it owns the assignment envelope, assignment ledger, and use of returned material. The host owns invocation transport, scheduling within the user-supplied concurrency ceiling, background execution, retry, resume, timeout, and communication.

## IIS Decision Boundaries

| Decision | Owner |
| --- | --- |
| Long-term Intent preservation | Scope Shaper |
| Actual current product state relevant to shaping | Scope Shaper |
| Verified material claims and connected planning boundary | Scope Shaper |
| Unavoidable external or preserved-product Planning Constraints | Scope Shaper |
| Candidate outcome areas and Work Package split/merge | Scope Shaper |
| Product-capability dependencies that determine what can meaningfully exist next | Scope Shaper |
| Selected next durable construction Increment | Scope Shaper |
| Detailed observable contract and product-policy choices inside that Increment | Ask Matt |
| Semantic states, transitions, recovery, ordering, concurrency | Behavior Design within Matt |
| Rendered interaction and presentation | Matt's Central UI / UX Routing |
| Internal design, mutation surface, mechanism, and implementation sequence | Later Ticket delivery |
| Spec and Tickets for the selected Increment | IIS Planning |

Delivery Context is evidence for later owners. It is not planning authority by itself.

## Scope Depth Boundary

Scope Shaper investigates broadly enough to understand the connected landscape and construction choice, but its normative result has a fixed depth.

A statement belongs in the current normative frame only when removing it would change the selected observable outcome, make the selected Increment non-durable or product-dependency-incomplete, violate an unavoidable external contract, or fail to preserve an explicitly adopted existing observable behavior.

Apply these tests before recording a Lead finding.

### Observable Necessity Test

Ask whether the proposed statement changes what a user or operator can complete, observe, or rely on in the assessed outcome or selected Increment. A useful implementation detail that leaves the same observable result is not Scope authority.

### Product-Policy Replaceability Test

Try two reasonable user-visible policies or presentations that both satisfy the current boundary and selected Increment. When both remain valid, record the unresolved choice under `Decisions Reserved For Matt` rather than selecting one here.

### Implementation Replaceability Test

Try two materially different internal implementations that satisfy the same selected outcome and Planning Constraints. When both remain valid, the choice is Implementation-owned. Scope Shaper may preserve the supporting repository fact in Delivery Context, but does not turn one implementation path into a requirement.

### Constraint Test

A current repository or runtime fact becomes a Planning Constraint only when it is an unavoidable external, public, persisted, safety, authority, or deliberately preserved observable boundary. Other current-code facts remain Delivery Context.

These tests govern the result, not the depth of inspection. The Lead may inspect files, symbols, tests, and runtime behavior in detail while keeping the planning output at the correct authority level.

## Lead-First Investigation Frame

Before any Runner dispatch, inspect enough of the available authoritative evidence to establish:

- the user's long-term intended outcome without assuming every mature capability belongs now;
- the actual current baseline: directly observed product behavior for codebase-backed work, or the confirmed absence of an existing product implementation for unrooted greenfield work;
- which requested capabilities already exist, partly exist, or do not exist when direct evidence can establish that fact;
- whether the request contains independently acceptable outcome areas;
- which observable product capabilities genuinely depend on earlier product results;
- what belongs inside or outside the connected landscape;
- which verified constraints cannot be chosen away by later planning;
- which product-policy, Behavior, or rendered decisions remain for Matt; and
- which smaller candidate Increment could become a durable product foundation rather than a temporary preparation step.

Investigate only the connected landscape. For codebase-backed work this may include current user or operator flow, relevant existing behavior, extension and state boundaries, permissions, external contracts, tests, documentation, and reusable capabilities. For unrooted greenfield work use the user brief, supplied references, examples, and external contracts, and explicitly mark implementation facts as unavailable rather than hypothesizing them. In both modes investigate concrete omissions that can make the selected Increment incomplete or force redesign of the same boundary.

Product-wide strategy, market positioning, unrelated roadmap work, and possibilities without an evidenced connection remain outside this assessment.

## Optional Runner Dispatch

Runner dispatch is explicit-user-authority only. When no exact authorized roster is current, do not invoke a Runner. When one is current, split assignments by evidence domain rather than desired conclusion. Independent questions may run in parallel only within the user's supplied concurrency ceiling; dependent questions remain sequential. Use only the exact supplied slot and configured identity values.

Every assignment states the canonical Runner fields exactly:

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

The same slot and configured identity must appear in the returned report. Maintain one in-session ledger:

```text
Assignment ID:
Runner Slot:
Configured Agent Or Model:
Terminal Status: COMPLETED | BLOCKED | FAILED | TIMEOUT | INVALID_REPORT
Question Resolution: VERIFIED_FROM_REPORT | LEAD_DIRECT | NO_LONGER_MATERIAL | UNRESOLVED
```

`COMPLETED` means only that a report returned. The exact question becomes `VERIFIED_FROM_REPORT` only when the report establishes the answer, material gaps and counterevidence are resolved, anchors are sufficient, and the Lead directly reopens or reproduces the primary evidence.

`Answer: Not established`, a material `Unverified` item, conflicting evidence, insufficient anchors, identity mismatch, or a failed/blocked/timed-out Runner keeps the question `UNRESOLVED` unless the Lead closes that exact question directly or verified boundary change makes it `NO_LONGER_MATERIAL`. Runner consensus never upgrades unresolved evidence.

A material `UNRESOLVED` question blocks normal Scope confirmation. Report the unresolved question and the smallest evidence action that can close it; do not replace or add Runner identities to work around the failure without new explicit user authorization.

## Evidence And Lead Challenge

Normalize findings as:

- **Fact** — directly supported by an inspectable primary source.
- **Inference** — an interpretation connecting verified facts.
- **Proposal** — a suggested boundary, package, construction candidate, or direction.
- **Unknown** — not established by current evidence.

For each material claim used in a boundary, package, dependency, or Increment decision, the Lead:

1. uses primary evidence already directly established for this project in the current conversation, or opens/reproduces the missing or changed load-bearing evidence;
2. checks that it belongs to the current project, a user-supplied greenfield brief/reference, or a current external contract as applicable;
3. distinguishes observed current-state facts from user intent, adopted constraints, and proposals so an unrooted brief never masquerades as repository behavior;
4. matches the strength of the claim to the evidence;
5. tests a plausible conflicting explanation or counterexample;
6. applies the Scope Depth Boundary tests; and
7. records only the finding that survives those checks at the correct authority level.

Changing planning leaves does not by itself invalidate directly established facts. Reuse them only within their attributable evidence boundary: recheck a changed file/config anchor, a changed registration or expanded search universe behind an absence claim, and fresh mutable runtime or external-version facts when those are load-bearing. A historical artifact or another agent's prose is navigation, not a substitute for this first-hand check. Investigate a new material question or counterexample, not the same broad landscape again for confidence; Scope still owns every shaping decision.

A material claim records one planning relevance:

- `BOUNDARY` — necessary observable outcome scope;
- `PLANNING_CONSTRAINT` — an unavoidable or deliberately preserved boundary;
- `RESERVED_FOR_MATT` — a material product, Behavior, or UI decision that Scope does not settle;
- `OUTCOME_CANDIDATE` — a connected result that may be independently accepted;
- `CONSTRUCTION` — evidence that can change product-capability ordering or the selected Increment;
- `DELIVERY_CONTEXT` — a verified implementation or environment fact with no automatic normative force;
- `DECOMPOSITION` — evidence used for split/merge, Work Package dependency, or release grouping; or
- `NONE` — no material planning effect.

Runner prose and consensus locate questions and evidence; they do not establish final planning facts.

## Planning Landscape

The confirmed Scope result separates these meanings.

### Intent Horizon

The user's larger product direction that should remain recognizable across later IIS cycles. It constrains interpretation of the initiative but is not current delivery scope merely because it is desired eventually.

### Current Product State

The evidence-grounded baseline from which construction begins. For codebase-backed work, record what users or operators can currently complete and read back, which relevant concepts or capabilities exist, and what material requested capability is absent from direct evidence. For genuinely unrooted greenfield work, record the confirmed absence of an existing product implementation and keep user-desired future behavior under Intent Horizon or later product decisions rather than pretending it already exists. Do not substitute a previously predicted future state for direct inspection on a later re-entry.

### Planning Boundary

The connected observable product or operating landscape relevant to the request. `Includes` and `Excludes` bound what must be understood together; they do not make every included mature capability part of the current Increment.

### Planning Constraints

Verified external, public, persisted, safety, authority, or deliberately preserved observable boundaries that later planning must honor. Current implementation facts enter this section only when the Constraint Test succeeds.

### Candidate Outcome Areas

Connected results that may be independently acceptable. They remain candidates until split/merge analysis decides whether they belong in separate Work Packages.

### Product Capability Dependencies

Product-level prerequisite relationships used only when an earlier observable product result must exist for a later result to be meaningful or coherently accepted under any reasonable internal design. Shared code, likely database order, implementation convenience, and technical scaffolding are not product-capability dependencies.

### Decisions Reserved For Matt

Material product-policy, semantic Behavior, or rendered-interaction decisions inside the selected Increment that are not fixed by user intent, adopted authority, or unavoidable contract. Their presence is not an unresolved Scope question when Ask Matt is the correct owner.

### Delivery Context

Verified repository, runtime, migration, build, tool, test, or external facts later IIS owners may need. Delivery Context does not prescribe mutation surface, component choice, state placement, reuse decision, mechanism, or implementation sequence.

### Outside The Assessed Landscape

Nearby possibilities that lack a verified connection to the current request. This means only that they are outside this investigation.

## Work Package Decomposition

Use `references/initiative-decomposition-rules.md` when several candidate outcome areas may be independently accepted, deferred, or rejected. A Work Package is a horizontal product-outcome boundary, not a construction step and not an Ask Matt handoff.

Create the largest Work Package that remains independently plannable and acceptable. Split and merge on observable product meaning, not technical layers. Product dependencies between Work Packages remain product-level counterfactuals, not anticipated implementation order.

Work Package files are durable decomposition records with `Status: scoped`. They are never `ready-for-matt`. Selecting a Work Package only identifies the outcome area in which the next Increment is shaped. When a candidate Increment belongs to a Work Package that depends on another Work Package, select it only if the dependency's observable product result is directly verified in Current Product State. Otherwise shape the earliest missing dependency outcome first; do not absorb an independently acceptable sibling Work Package into the current Increment merely to satisfy ordering.

A coherent bounded outcome may omit Work Package decomposition entirely and proceed directly to construction Increment shaping.

## Construction Increment Shaping

After the outcome landscape and any Work Packages are understood, compare plausible next construction states. Do not forward the whole bounded outcome or Work Package to Matt merely because it is coherent.

### Candidate Rule

Each candidate must describe a transition from the verified Current Product State to a product state that can actually exist after one IIS delivery cycle. Give every candidate one local `Candidate <label>` heading and record exactly one Outcome Area (`None` for bounded shaping or one `WP-NNN`), Current Product State, Target Product State, Actor Or Operator, Trigger Or Inspection Target, Observable Result, Authoritative Readback, Durable Foundation, Future Policy Avoided, `Lead Disposition: SELECT | REJECT`, and Reason. These fields make alternatives auditable; they do not turn product judgment into a scoring engine.

Do not generate technical preparation candidates such as database setup, an abstraction, an adapter, a service layer, a test seam, or a refactor unless that artifact is itself the externally consumed product outcome. Exactly one candidate is `SELECT`. The Selected Next Increment names that local candidate and copies its Current Product State, Target Product State, and four-part observable contract exactly. The validator checks only this structural closure and single-selection property; it never decides whether the Lead's chosen candidate is substantively the best or smallest durable product state.

### Durable Increment Tests

A selected candidate must pass all applicable tests:

1. **Observable Completeness** — state the actor or operator, trigger or canonical inspection target, observable result, and authoritative readback. The result cannot be only "ready for later work".
2. **Durable Foundation** — the product concepts, identity, ownership, lifecycle, capability, persistence meaning, or readback established by the Increment can remain as a real basis for later capability instead of being an intentionally disposable miniature.
3. **Product-Dependency Closure** — include every earlier observable product capability required for this result to be meaningful. Do not include technical prerequisites merely because one implementation is likely to need them.
4. **Future-Policy Deferral** — exclude product policy, maturity, scale, sharing, automation, or other later capability that is not necessary for this Increment's observable result. Record it as deferred rather than resolving it prematurely.
5. **Smallest Durable Choice** — when several candidates satisfy the first four tests, prefer the one that establishes the least additional product surface and policy while still creating a durable usable foundation and moving toward the Intent Horizon.

### Atomic Exception

Do not force an artificially small Increment. A broader Increment is justified when verified evidence shows that a smaller candidate cannot produce a safe, meaningful, independently readable product state, or when an unavoidable compatibility, migration, external-contract, or atomic lifecycle boundary requires the broader state. Record the smaller candidate tested and the exact reason it fails.

### Provisional Construction Horizon

The Lead may record likely later capability ordering to explain why the selected Increment is foundational. This horizon is explicitly non-normative. Do not create future ready Increment files, pre-approve their product policy, or let Matt import them into the current Spec.

### Selected Next Increment

Select exactly one Increment for the current Scope confirmation. It contains:

- Suggested Work Slug — one project-wide unique lowercase kebab-case slug for the later `docs/planning/work/<slug>/` workspace; it must never be reused by another Scope Increment, including a superseded one;
- Selected Candidate — the exact local `Candidate <label>` whose disposition is `SELECT`;
- Current Product State;
- Target Product State;
- Observable Outcome — exact Actor Or Operator, Trigger Or Inspection Target, Observable Result, and Authoritative Readback copied from the selected candidate;
- Includes;
- Excludes;
- Required Product Dependencies;
- Preserved Foundations;
- Decisions Reserved For Matt;
- Deferred Until Re-entry;
- Verification Boundary;
- Re-entry Contract; and
- Delivery Context.

The `Re-entry Contract` states what actual delivered product state must be inspected before a later Scope Shaping pass chooses another Increment. Re-entry is a new shaping decision against reality, not automatic continuation of the provisional horizon.

Exactly one selected Increment may have `Status: ready-for-matt` in one confirmed Scope result. Future increments do not exist as ready artifacts yet. On a later re-entry in the same Scope directory, assign the next unused `INC-NNN` ordinal and change every earlier `ready-for-matt` Increment to exact `Status: superseded` before the newly confirmed Increment becomes ready. `superseded` is planning-admission state only; it does not claim that delivery completed.

## User Confirmation And Corrections

Present the complete current proposal once: Intent Horizon, Current Product State, verified claims, Planning Boundary, Planning Constraints, candidate outcome areas, Work Package decomposition when present, Product Capability Dependencies, construction candidates and tradeoffs, the one Selected Next Increment, Deferred Until Re-entry, Decisions Reserved For Matt, Delivery Context, and the provisional construction horizon when useful. Ask the user to confirm or correct that whole result.

Confirmation approves the Scope-owned landscape, decomposition, and selected next Increment. It acknowledges that listed Matt decisions remain open and that provisional future construction is not approved current scope.

A correction reopens only affected evidence, boundaries, constraints, package decisions, product dependencies, construction candidates, and the selected Increment. Recalculate affected descendants before presenting the complete proposal again. After explicit confirmation, write the confirmed artifacts. There is no second shaping approval.

## Confirmed Artifacts

Before writing or updating any durable Scope artifact, resolve `tools/prepare_scope_workspace.py` from this skill's canonical physical directory and run it with the exact Project Root and Scope `Work-Slug`. Use only the returned `scopeWorkspace`, `workPackages`, `revisions`, `increments`, `legacyImport`, and `legacyWorkPackages` directories. The helper creates missing directories with safe ownership/permissions and rejects symlinked, noncanonical, foreign-owned, or unsafe existing paths. Do not manually create an alternate Scope directory after helper failure. `--repair-owned-permissions` is an explicit maintenance option limited to IIS-owned `scope-shaping/**` artifact directories; it never repairs shared `docs/` or `planning/` permissions, and ordinary shaping does not silently change existing directory permissions.

A confirmed shaping pass is not durable until its complete artifact chain exists and validates. For a new revision, write the new immutable `revisions/SHAPE-NNN.md`, the new selected `increments/INC-NNN.md`, every required Work Package update, and the required prior-Increment `superseded` metadata before treating the new `SCOPE-SHAPING-RESULT.md` navigation state as complete. Prefer writing the immutable revision and selected Increment before replacing current navigation so an interruption cannot leave a current Scope result pointing only to nonexistent authority. After the current result is replaced, immediately run both canonical Scope and selected-Increment validators. If either validator fails, report Scope artifact closure as incomplete and do not report a confirmed handoff or continue to Ask Matt. A later entry encountering such an incomplete current artifact chain repairs or completes that exact confirmed pass before any new shaping decision.

### Source Authority And Immutable Revision

Maintain one current Scope navigation/authority file and one immutable revision snapshot for each confirmed shaping pass:

```text
<Project-Root>/docs/planning/scope-shaping/<work-slug>/SCOPE-SHAPING-RESULT.md
<Project-Root>/docs/planning/scope-shaping/<work-slug>/revisions/SHAPE-NNN.md
```

`SCOPE-SHAPING-RESULT.md` represents the latest confirmed shaping state. Its exact `Scope-Revision: SHAPE-NNN` snapshot must be written byte-for-byte to the matching revision path at confirmation. That revision owns the historical evidence, Intent Horizon, Current Product State, Planning Boundary, Planning Constraints, candidate outcome areas, Product Capability Dependencies, Decisions Reserved For Matt, Delivery Context, split/merge and Work Package definitions when applicable, construction comparison, provisional construction horizon, selected Increment reference, deferred future scope, and confirmation record that produced that Increment.

Never rewrite an earlier `revisions/SHAPE-NNN.md`. On re-entry, inspect the actual current product state, prepare the next confirmed Scope state under the next revision ordinal, then update `SCOPE-SHAPING-RESULT.md` and create only that new immutable revision after confirmation. Every Increment records its own `Source-Scope-Revision` and continues to point to that revision even after the current Scope result advances.

Use `templates/SCOPE-SHAPING-RESULT.bounded.template.md` for a bounded landscape and `templates/SCOPE-SHAPING-RESULT.initiative.template.md` when Work Package decomposition is present. Write the selected template only after user confirmation with `Status: confirmed`, one exact `Scope-Revision: SHAPE-NNN`, and `Unresolved Material Questions: None`.

### Work Package Records

For an initiative, create one thin file per proposed Work Package:

```text
<Project-Root>/docs/planning/scope-shaping/<work-slug>/work-packages/WP-NNN.md
```

Use `templates/WORK-PACKAGE.template.md`. Every Work Package has `Status: scoped`. It carries only the horizontal package boundary and dependencies from the source result. It is not an Ask Matt admission artifact and must not contain `ready-for-matt` status.

### Selected Increment

For the current shaping pass, create exactly one new selected Increment file. Earlier Increment files from prior passes remain only as `Status: superseded` records:

```text
<Project-Root>/docs/planning/scope-shaping/<work-slug>/increments/INC-NNN.md
```

Use `templates/INCREMENT.template.md`. It has `Status: ready-for-matt`, keeps `Source-Scope-Result` only as current navigation, references the exact immutable `Source-Scope-Revision` that approved it, references one Work Package when the landscape is initiative-shaped or `None` for a bounded landscape, and contains only the selected current construction contract. Do not duplicate the investigation record or provisional future horizon into the Increment.

Run:

```text
python3 <scope-shaper-directory>/tools/validate_scope_result.py \
  <absolute-SCOPE-SHAPING-RESULT.md-path>
python3 <scope-shaper-directory>/tools/validate_increment.py \
  <absolute-INC-NNN.md-path>
```

The validators check structural integrity, canonical path ownership, source confirmation, exactly one selected ready Increment, Work Package/source drift, Increment/source drift, and strict `Product Meaning Binding` schema/fingerprint consistency whenever that section is present. New applicable Scope artifacts emitted by this skill must contain the binding; legacy artifacts are not bulk-migrated merely to satisfy this addition. The validators do not grade Product Thesis correctness, semantic adoption into Scope prose, product judgment, or implementation design.

## Handoff

After confirmation, report:

```text
Confirmed Scope Result:
- <absolute path>

Selected Next Increment:
- <absolute INC-NNN path>

Deferred Until Re-entry:
- <non-normative summary>
```

Stop there. Ask Matt begins only from a later explicit user action naming the exact selected Increment, or from a direct ordinary request that independently passes Ask Matt's next-increment admission without Scope Shaper. Never continue automatically into a future provisional Increment.
