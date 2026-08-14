---
name: ask-matt
description: Use for an ordinary bounded planning request, or for a later explicit continuation from one exact confirmed bounded Scope result or one exact ready-for-matt Work Package. Do not intercept an initiative-scale request that has not completed Scope Shaper or an explicit implementation request.
---

# Ask Matt

Route planning work without starting implementation. Write this guidance, questions, and any planning artifacts in the language the user uses in the conversation.

## Purpose

Choose the smallest planning path that makes the work clear enough for an approved `SPEC.md` and a ready implementation Ticket.

## Central UI / UX Routing

Before choosing grilling or finalizing contract-only shared understanding, Matt
internally classifies the confirmed or proposed scope by its actual rendered
result. This is a dependency-aware audit, not a checklist to present to the
user. Do not classify from filenames, framework names, directory names, or the
word `frontend`.

Rendered behavior includes pixels, content or copy, interaction or navigation,
loading/empty/error/success/permission presentation, responsive behavior,
accessibility semantics, focus or keyboard behavior, user-visible assets, and
motion. Classify the scope as one of the following:

- `NON_UI`: it does not change or directly exercise a rendered product result.
- `ENGINEERING_ONLY`: it changes frontend-facing implementation while the
  rendered and UX result is exactly preserved and no direct rendered-result
  exercise is due now.
- `BOUNDED_RENDERED_CONTRACT`: it has an exact, limited rendered change, or a
  due-now direct exercise of an exactly preserved rendered result, whose
  applicable behavior and design decisions are already fixed. It may use a
  proportionate scoped UI authority; do not require a separate full `DESIGN.md`.
- `MATERIAL_RENDERED_UI`: it introduces a new rendered UI, materially redesigns
  one, or leaves a material user-visible rendered behavior/design decision
  unresolved.

For `MATERIAL_RENDERED_UI`, first determine whether an existing finished,
applicable, complete, approved local UI/UX authority is explicitly adopted by
the current or resulting shared understanding. A user-supplied authority may
satisfy this condition. References, defaults, prototypes, visual concepts, or a
status line do not become authority without that explicit adoption. When no such
authority exists, Matt directly performs enough rendered-design judgment from
the confirmed Scope, adopted Behavior authorities, current product/repository
evidence, and user intent to identify every currently determinable material
user-owned rendered decision before contract-only shared understanding can be
finalized. This analysis does not require an external UI specialist, image
generator, prototype, or generated concept. Matt planning never invokes frontend
implementation or mutates product files outside `docs/planning/**`.

Complete this UI judgment before the first user-facing decision response. Merge
its currently determinable decisions into the same initial dependency graph as
Grill and Behavior. Do not postpone UI analysis until after the first frontier or
use late UI analysis to justify an extra round. Final authority writing and
approval still follow their gates below. After an answer, revisit UI judgment
only where that answer materially changes it, and apply the same newly-identifiable
dependency rule as Behavior Design.

Before Matt writes a planning authority, prepare or revalidate the one
project-local planning root and work artifact directory that later Design,
Spec, and Tickets use. Resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory with the existing canonical project root and work slug.
Durable planning is blocked until that project root exists. Do not accept or
prepare an external workspace.

Matt creates and governs `<artifact-workspace>/DESIGN.md` for new/material UI:

- Use a non-empty H1 followed before the first H2 by exact plain Markdown
  metadata lines `Status: draft`, non-empty `Owner:`, and explicit `Scope:`.
- Cover every applicable new/material rendered decision: inherited visual
  system/tokens or deliberate deltas; information architecture and view hierarchy;
  responsive behavior for supported viewports; loading, empty, error, success,
  permission, navigation, and other scoped states; product-locale copy;
  accessibility semantics, focus, and keyboard behavior; assets and motion
  when present; and rendered verification conditions.
- Conditional dimensions may be `Not applicable` only with a reason. Do not
  invent list/detail views, Korean copy, live updates, mobile support, assets,
  or motion when the confirmed product scope does not include them.
- A utility CRUD/dashboard classification never waives the Matt-owned decision
  set above.
- A visual reference, style choice, default, prototype, generated concept,
  filename, or status line alone does not complete the authority. Only decisions
  explicitly adopted into `DESIGN.md` can become UI authority.
- Actual browser or renderer evidence remains implementation-time work. This
  artifact defines which supported viewports, states, and interactions must be
  exercised later.

Change `DESIGN.md` to exact `Status: approved` only after all applicable
decisions are complete, `Open Questions` is `None`, and the user or named owner
explicitly approves it. Any later scoped decision change returns it to `draft`
and reopens an already approved Spec for an explicit delta. Integrate the
package authority into the same shared understanding; keep questions limited
to decisions that block it. One explicit user response may approve both the
completed authority and integrated shared understanding when both are
presented clearly.

Legacy image-review process metadata may remain in older planning artifacts as
non-normative historical evidence. New planning neither requires nor writes it,
and its presence or absence does not decide UI authority validity.

`NON_UI` and exact-preservation `ENGINEERING_ONLY` work do not enter full UI
planning. A bounded rendered contract needs only its fixed rendered decisions
or preservation conditions in the confirmed shared understanding. It may reuse
a proportionate approved UI authority, or let the later approved Spec become
the scoped authority through its `## UI / UX` section; it does not require a
separate full `DESIGN.md`. Reclassify when later clarification changes the
rendered obligation.

## Central Behavior Design

Every Matt planning unit must complete the canonical Behavior Design phase
before Matt presents a final shared understanding:

```text
/home/user01/project/iis-skills/behavior-design-lead/SKILL.md
```

Matt forms a provisional frame: desired outcome, included and excluded scope,
Non-Goals, preserved behavior, external constraints, UI authority when
applicable, exact project root, planning owner, and known unresolved decisions.
This frame is not approved or normative.

Matt directly reads and performs the complete canonical leaf in the current
conversation context; the phase has no separate execution role or context.
Before the first user-facing decision question, Matt must inspect the project's
`docs/planning/behavior/INDEX.md` and applicable scoped authorities, conduct the
required first-hand investigation, behavior model, and counterexample stress
test, and either adopt unchanged approved authorities, revise their canonical
documents, or create authorities for genuinely new persistent behavior
boundaries. Combine every currently identifiable user-owned decision from that
analysis with Grill's scope, authority, constraint, and UI decisions in one
dependency graph. Matt must not waive the phase because the work appears clear,
reduce its completion test, treat a per-work Behavior document as a substitute,
or start questioning before this synthesis is complete.

`BEHAVIOR DECISIONS REQUIRED` is an internal contribution to that initial
decision graph, not a separate user-facing stage after Grill has already asked
questions. Present the graph through the active Grill interaction policy. After
an answer, update the affected Behavior model and dependency descendants. A
later round is allowed only when the answer creates or resolves a material
dependency that makes a downstream decision newly identifiable; late research,
late Behavior analysis, question count, or response-length preference does not
qualify. Package-boundary changes return to Scope Shaper; rendered
presentation decisions return to the UI authority flow.

## Optional Adversarial Planning Consensus

Adversarial consensus is an explicit-only Ask Matt gate. Load and run
`../adversarial-consensus/SKILL.md` only when the user has both explicitly
instructed adversarial consensus for this exact planning unit and explicitly
designated one exact `Adversarial Planning Challenger`. A designation alone does
not activate the gate. If the user explicitly instructed adversarial consensus
but did not designate one exact Challenger, do not choose a counterpart, do not
silently fall back to ordinary finalization, and do not approve or enter `to-spec`;
at the finalization boundary return `ADVERSARIAL CONSENSUS: CHALLENGER BINDING
REQUIRED`. Do not proactively suggest or default to the gate for ordinary Ask
Matt work.

When active, complete Matt's ordinary first-hand investigation, Behavior/UI
analysis, current user-decision frontier, and verification-feasibility closure
before invoking the Challenger. Hold new or changed Behavior/UI authority at
draft/approval-ready state until the gate has a current result. Before the first
Challenger invocation, present and obtain user confirmation of the Intent Anchor
and bounded disclosure required by the gate. The Challenger remains read-only and
advisory; Matt retains first-hand fact confirmation, Behavior/UI conclusion, and
planning synthesis authority.

`ADVERSARIAL CONSENSUS REACHED` never substitutes for final user approval. When
the gate is active, a current consensus plus the user's final approval of the
resulting integrated shared understanding are both required before `to-spec`.
Material intent/Scope/Behavior/UI/verification changes after consensus invalidate
the affected consensus and require renewed review while the user's activation
remains current. If the user explicitly withdraws adversarial consensus, return
to the ordinary Ask Matt completion boundary; prior Challenger findings remain
advisory context only.

When the phase reaches `BEHAVIOR AUTHORITY APPROVAL REQUIRED` and no
adversarial-consensus gate is active, Matt may present the completed draft authorities and one
clearly labeled proposed integrated contract-only shared understanding for joint
approval. When that gate is active, defer this joint approval until its latest
candidate reaches current consensus as required above. After the applicable final
approval, continue the phase, mark the authorities approved, and establish
`BEHAVIOR DESIGN: COMPLETE`. Only then does Matt record the jointly approved
understanding as final or, when no joint approval occurred, present the final
understanding for confirmation. The final understanding must identify every
approved Behavior authority and exact applicable scope. Unchanged approved
authorities are adopted without reapproval. The pre-completion approval state
never permits `to-spec`.

Behavior owns semantic product behavior; `DESIGN.md` owns rendered expression
and interaction. Neither silently overrides the other. A conflict blocks final
confirmation. A material Behavior delta returns the authority, every adopting
Spec, and affected unfinished Tickets to `draft`.

## Entry Routing And Scope Handoff Preflight

Before Grill, Behavior Design, UI routing, workspace creation, or Spec writing,
classify and validate the entry:

1. An ordinary bounded request enters the normal flow only when it does not name
   a Scope result or Work Package, does not explicitly request Scope Shaper, and
   does not contain several potentially independent product outcomes. Technical
   depth, file count, or implementation layers alone do not make an initiative.
2. A direct brief returns to Scope Shaper when outcomes may be independently
   accepted, deferred, or rejected; when an MVP/Next/Deferred cut among outcomes
   is material; when product dependencies among outcomes remain undecided; or
   when split versus merge is itself unresolved.
3. A bounded Scope continuation must name one exact absolute local Markdown path
   at
   `<Project-Root>/docs/planning/scope-shaping/<Work-Slug>/SCOPE-SHAPING-RESULT.md`.
   Run the canonical `scope-shaper/tools/validate_scope_result.py` validator and
   require `Status: confirmed`, `Planning-Shape: bounded`, exact
   `Project-Root`, matching lowercase kebab-case `Work-Slug`, and exact
   `Unresolved Material Questions: None`. Inherit its Planning Boundary and
   Planning Constraints, carry Decisions Reserved For Matt into the first
   integrated frontier, and use Delivery Context only as non-normative evidence.
4. An initiative continuation must name one exact raw, non-symlink local path at
   `<Project-Root>/docs/planning/scope-shaping/<scope-slug>/work-packages/WP-NNN.md`.
   Apply the validator's selected-Work-Package raw-path gate before validating
   its source. Require `Status: ready-for-matt`, matching `Project-Root`, a
   matching `Work-Package` filename, lowercase kebab-case
   `Suggested-Work-Slug`, the same canonical confirmed initiative source, and
   exact source/package Outcome, Includes, Excludes, Dependencies, and Decisions
   Reserved For Matt. The package must be one of the source's non-deferred Next
   Planning Units. Plan only that package and apply source Planning Constraints
   whose scope contains it.
5. A named initiative Scope result without one exact selected ready Work Package
   never enters Ask Matt. Draft, invalid, unresolved, wrong-project,
   noncanonical, symlinked, deferred, or drifted sources or packages also stop
   here.

On failure, do not begin the normal flow. Report:

```text
ASK MATT: BLOCKED
Input: <exact source or Work Package path>
Reason: <invalid status, wrong project, unresolved questions, path or slug drift,
         invalid or deferred package, boundary drift, or exact defect>
Next action: <return to Scope Shaper or select one exact ready Work Package>
```

## Main Flow

1. Run the Central UI / UX Routing audit and select `grill-with-docs` or
   `grill-me` for the current evidence context, but do not present a user-facing
   decision yet. A target with an existing canonical project root and
   inspectable repository context remains codebase-backed even when the current
   package/application scope has no implementation source yet; route it to
   `grill-with-docs`. Route to `grill-me` when the product root or repository
   context itself is not yet available. Do not classify from words such as
   greenfield, initialize, or bootstrap.
2. Before the first decision response, perform the selected Grill analysis and
   complete Existing Authority First, Lead-First Investigation, Behavioral
   Design, and Counterexample Stress Test. When material UI lacks an applicable
   approved authority, also complete Matt's direct UI judgment far enough to
   identify its currently determinable user-owned rendered decisions.
   Merge all Grill, Behavior, UI, and applicable Scope Shaper package-frame decisions
   into one dependency graph. Resolve inspectable facts directly and exclude
   implementation-owned choices.
3. Present the complete current unblocked frontier through `grilling`. Batch
   mode numbers every decision; normal mode may compress related decisions into
   coherent recommendation blocks, but neither mode may hide an already
   identifiable unblocked material decision for a later turn. If the frontier
   is empty, proceed without a question. Skipping a question never skips
   Behavior Design.
4. After each answer, update only materially affected recommendations, Behavior
   and UI analysis, and dependency descendants. Ask another round only for
   decisions that the answer made newly identifiable under the dependency rule
   above. Continue until the frontier is empty. When material UI applies,
   complete the Matt-owned authority content and decision closure before finalizing
   shared understanding, but when adversarial consensus is active hold final
   authority approval until that gate has reviewed the complete provisional
   contract; do not rediscover user-owned design decisions that the initial UI
   analysis could have identified.
5. When new or changed Behavior authorities are approval-ready, keep their
   canonical drafts complete against the resolved frame. Without an active
   adversarial-consensus gate, use the ordinary joint approval flow above. With
   an active gate, do not ask for final authority approval yet; the completed
   drafts remain reviewable candidate authority until the gate finishes.
6. Before final integrated approval or `to-spec`, close the
   verification-feasibility decisions for
   every independently acceptable observable outcome. This is part of the same
   user-owned product decision frontier, not implementation-path research. For
   each outcome confirm:

   - the observable claim;
   - its acceptance boundary, such as UI, CLI, API, generated artifact,
     canonical source, persisted state, or document;
   - the product trigger/input or canonical inspection target;
   - the expected observable result and authoritative readback;
   - whether its disposition is `Independent`, `Operator-assisted`, or `Not
     independently verifiable`;
   - whether independent verification is required by the product contract;
   - whether direct inspection establishes that the required acceptance surface
     exists, this delivery Scope must create it, a confirmed delivery contract
     guarantees a disposable target and its availability condition, an operator
     owns it, or no independent surface exists for a confirmed reason; and
   - any external condition that limits execution or observation.

   Confirm only the applicable claim-specific boundary: an absence terminal
   condition; ordering event source and range; persistence storage identity and
   lifecycle boundary; interruption checkpoint; external-effect sandbox,
   authority, cleanup, and readback; or UI rendered-state and interaction
   readback. Do not ask for irrelevant dimensions.

   `Independent` means the current outcome and delivery Scope let a fresh
   verifier execute or inspect the authored product flow and use its
   authoritative readback. If independent verification is required, an
   acceptance boundary and readback must already exist, be created as ordinary
   Ticket-Scope-owned product behavior, or rely on required disposable-target
   availability that the delivery contract guarantees. Otherwise the shared
   understanding is not complete. Use a delivery guarantee only when the
   confirmed delivery contract actually guarantees the disposable target and
   its availability condition; do not infer a sandbox or turn user approval
   into evidence that a current surface exists. `Operator-assisted` means a declared
   credential, shared/production target, or separately authorized external
   effect requires the stated operator path. `Not independently verifiable`
   means the confirmed contract has no independent execution or observation
   boundary and this delivery Scope will not create one. Do not present either
   non-independent disposition as independent success.

   A runtime outcome cannot be complete without its product acceptance boundary
   and authoritative readback. A source, artifact, document, or structure claim
   may instead use current canonical-target inspection and must not be forced
   through a runtime command. Internal tests, mocks, private helpers, proposed
   test seams, and implementation narration are never the normative product
   boundary or authoritative readback.
7. When adversarial consensus is active, execute
   `../adversarial-consensus/SKILL.md` now against the complete provisional
   candidate. Require the user-confirmed Intent Anchor before Challenger
   invocation. Do not proceed past an unresolved `CHALLENGER BINDING REQUIRED`,
   `BLOCKED`, or `USER DECISION REQUIRED` result. A material change produced by
   the debate is rechecked directly by Matt and, while activation remains current,
   returned to the designated Challenger until the latest complete candidate
   reaches current `ADVERSARIAL CONSENSUS REACHED`.
8. Present one final integrated contract-only shared understanding. When new or
   changed Behavior/UI authority exists, present its completed current content in
   the same final approval request. Require explicit user approval. Only after
   that approval mark the applicable authority approved and finish Behavior
   Design. If the user materially changes the contract while approving and the
   adversarial gate remains active, return the changed candidate to the
   Challenger before treating approval as final.
9. Use `to-spec` when the desired outcome, preserved observable behavior and
   invariants, explicit boundaries, non-goals, and the confirmed outcome-local
   verification contracts above are clear, Behavior Design is complete, every applicable
   Behavior authority is approved, and the user has confirmed one integrated
   contract-only shared understanding. When adversarial consensus is active, also
   require current `ADVERSARIAL CONSENSUS REACHED` for that exact latest
   understanding. That understanding is normative for outcome and scope; the
   approved Behavior authorities it adopts are normative for their exact behavior
   scopes. Repository facts, prior planning artifacts, prototypes, and anticipated
   implementation approaches remain context only.

   A complete or known implementation mechanism is not required. Matt does not
   search for or prove one. Keep planning open only when verified evidence or
   clear logic shows a specific contradiction between the desired outcome and
   the confirmed boundaries, non-goals, or an unavoidable external authority
   boundary. The absence of a known path or uncertainty about the best path is
   not a blocker.

   When the confirmed outcome requires the first product/package/application
   artifacts in a scope that currently lacks target readiness, planning must
   resolve only: whether initialization mutation in that scope is authorized;
   applicable external/public/persisted identities and deliberately fixed
   runtime, toolchain, deployment, or operational constraints; and whether all
   remaining material bootstrap choices are fixed or explicitly delegated to
   Implementation Lead/Worker. Do not ask the user to invent a private package
   identity, future file list, dependency, or mutation envelope.
10. Use `to-tickets` only from an approved Spec. It creates the smallest set of
   independently observable desired-state Tickets, not an anticipated internal
   implementation sequence.

Planning artifacts may become more observable and testable as they progress
from shared understanding to Spec to Ticket, but they must not become more
solution-specific. A downstream artifact may restate, split, or clarify an
approved contract; it must not introduce a more specific protocol, interface,
format, transport, storage model, component, algorithm, or implementation
sequence than its normative source.

Planning stops at a ready Ticket. Do not invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.

Do not direct users to `triage`, `improve-codebase-architecture`, remote trackers, or execution skills as active paths in this local planning flow.

## Inputs

The user's current goal, the amount of uncertainty, and whether a project/codebase is involved.

## Output

The result of starting the selected planning flow, not merely a recommended planning path. When grilling is selected, present a recommendation, a necessary explicit gate, or the complete contract-only shared understanding; do not output only a path explanation or summary.

## Planning Completion

Matt owns contract coherence, not implementation feasibility proof. Matt ends
with declarative Tickets and does not choose or recommend the final internal
implementation path. Implementation Lead inspects the current repository and
selects, validates, and revises that path later.

After ready Tickets exist, stop the Matt flow and report every ready Ticket by
its canonical absolute path. Ask Matt itself never invokes Implementation Lead,
the Ralph loop, a Worker, `/implement`, `/tdd`, `/code-review`, or another
execution chain.

For an explicit or planning-only Matt request, state only that these Tickets can
be used to start implementation later; starting implementation is a separate
user action. When Ask Matt was invoked by the canonical IIS entry router under an
already explicit end-to-end product-completion request, return the ready Ticket
result to that router. The router may reuse that still-current user completion
intent to enter the Ralph Goal Fulfillment Loop after Matt has stopped. This does
not let Ask Matt continue into implementation, ask for or suggest a Worker, or
create a second planning mode.
