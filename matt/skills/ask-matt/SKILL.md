---
name: ask-matt
description: Use for one next-increment-ready ordinary planning request, or for a later explicit continuation from one exact Scope-selected ready-for-matt Increment. Before Grill or Behavior/UI planning, return requests that still require construction-stage, foundation, product-capability-ordering, or split/merge decisions to Scope Shaper.
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
explicitly approves it. When adversarial consensus is active, keep a new or
changed `DESIGN.md` at `Status: draft` until the latest complete candidate reaches
current adversarial consensus. The consensus-post final integrated approval may
approve both the completed UI authority and shared understanding in one user
response; do not add a third approval ceremony. Any later scoped decision change
returns it to `draft` and reopens an already approved Spec for an explicit delta.
Integrate the package authority into the same shared understanding; keep questions
limited to decisions that block it. Without an active adversarial gate, one
explicit user response may approve both the completed authority and integrated
shared understanding when both are presented clearly.

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

Matt forms a provisional frame: applicable Product Thesis meaning, desired outcome, included and excluded scope, Non-Goals, preserved behavior, external constraints, UI authority when applicable, exact project root, planning owner, and known unresolved decisions. The Product Thesis contribution is high-level product meaning, not approved detailed Behavior/UI policy or authority to widen the admitted Increment. This frame is not approved or normative.

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
classify and validate the entry. An explicit request to use Ask Matt chooses this
leaf, but it does not waive this admission contract.

Apply Product Thesis admission before evaluating the direct request's next-increment readiness. When the direct request newly establishes or materially revises product meaning, Matt directly reads and performs `../../../product-thesis/SKILL.md` before Grill, Behavior Design, or UI work. A `USER_INPUT_REQUIRED` result stops at that smallest product-meaning decision. A `CALIBRATED` result continues through this unchanged admission contract; it does not make a broad request next-increment-ready.

For a Scope-shaped continuation, reuse the applicable product meaning and exact `Product Meaning Binding` preserved in the exact immutable Scope revision; the selected Increment remains the admission/reference hop and does not copy the binding. Do not rerun or redefine Product Thesis merely because Ask Matt starts in a new session. For a direct request whose existing approved product meaning remains current and sufficient, reuse that meaning. Recalibrate only when fresh actual evidence or newer explicit user authority invalidates the Reason to Exist, Core Utility, or an essential truth, identity, or ownership premise.

Carry applicable Product Thesis meaning into the final confirmed shared understanding through its desired outcome, included/excluded scope, Non-Goals, preserved invariants, and outcome-local verification contracts. Also preserve the five binding values needed for To Spec to serialize exactly one `iis-product-meaning/v1` `Product Meaning Binding`: Core Utility, Core Completion Loop, explicit Required Outcomes / Means, Truth / Causal Invariants, and Success Observation. For Scope-shaped work those values must remain equal to the immutable Scope revision binding; for direct Ask Matt work `SPEC.md` is the first durable binding. Detailed states, transitions, recovery, ordering, concurrency, and UI behavior remain owned by Behavior/UI planning.

The binding is product-level meaning and never widens the admitted Increment. A selected Increment may deliver only part of the Core Completion Loop while preserving the full product-level binding. Mechanical binding equality does not prove that the binding faithfully captured Product Thesis or that the actual Requirements/Verification Expectations faithfully adopt it; those remain planning-owner and Mandatory contract audit responsibilities.

1. A direct ordinary request with no Scope artifact enters the normal flow only
   when it is already `next-increment-ready`: the current product baseline is
   identifiable; one actor or operator can perform one trigger or canonical
   inspection and obtain one durable observable state change with authoritative
   readback; the request does not bundle foundation, intermediate, and mature
   forms of the capability; no material product-capability ordering or foundation
   choice remains; and no independently acceptable sibling outcome still needs
   split/merge judgment. Technical depth, file count, framework count, or
   implementation layers alone do not fail this gate.
2. A direct brief returns to Scope Shaper before any Grill, Behavior, or UI work
   when it describes a new product or whole system, spans multiple product
   maturity stages, leaves the next durable foundation undecided, requires a
   product-capability ordering decision, contains independently acceptable
   outcome areas, or otherwise does not establish one current-to-next product
   state transition. Do not solve this defect by silently shrinking or widening
   the user's request inside Matt.
3. A Scope-shaped continuation must name one exact raw, non-symlink local path at
   `<Project-Root>/docs/planning/scope-shaping/<scope-slug>/increments/INC-NNN.md`.
   Run the canonical `scope-shaper/tools/validate_increment.py` validator. Require
   `Status: ready-for-matt`, matching `Project-Root`, matching `Increment`
   filename, lowercase kebab-case `Suggested-Work-Slug`, one exact immutable
   `Source-Scope-Revision` under the same Scope directory, and exact
   revision/Increment contract content. `Source-Scope-Result` is current
   navigation only; it must still select this Increment at admission but it is
   not allowed to replace the Increment's immutable revision as historical
   planning authority.
4. Plan only the selected Increment's Current Product State, Target Product
   State, Observable Outcome, Includes, Excludes, Required Product Dependencies,
   Preserved Foundations, Decisions Reserved For Matt, Verification Boundary,
   and Planning Constraints applicable from its immutable Scope revision.
   `Deferred Until Re-entry`, the revision's Intent Horizon, Work Package
   siblings, and Provisional Construction Horizon are not current Spec authority.
   Use applicable revision Delivery Context and Increment Delivery Context only
   as non-normative evidence.
5. A named Scope result or `work-packages/WP-NNN.md` file is not an Ask Matt
   handoff. Current Work Packages are horizontal Scope records with
   `Status: scoped`; only the source-selected `increments/INC-NNN.md` may admit
   Scope-shaped work. An older Work Package with `Status: ready-for-matt` is a
   legacy IIS artifact, not an exception: return it to Scope Shaper's `Legacy
   Scope Artifact Compatibility` flow for current-state reinspection and semantic
   migration instead of admitting it directly. Draft, invalid, unresolved,
   wrong-project, noncanonical, symlinked, stale, non-selected, or drifted
   Increment sources also stop here.

For a direct request that fails next-increment admission, report:

```text
ASK MATT: SCOPE SHAPING REQUIRED
Decision: ASK MATT: SCOPE SHAPING REQUIRED
Governing authority: ask-matt / Entry Routing And Scope Handoff Preflight
Observed condition: <missing current baseline, multiple maturity stages, foundation/order choice,
                    independent sibling outcomes, or other exact construction-boundary defect>
Effect: the current unit is not admissible to Ask Matt as one next-increment-ready planning unit
Next allowed action: run Scope Shaper to select one durable next Increment
```

For an invalid Scope-shaped handoff, report:

```text
ASK MATT: BLOCKED
Input: <exact Increment or rejected Scope/Work Package path>
Decision: ASK MATT: BLOCKED
Governing authority: ask-matt / Entry Routing And Scope Handoff Preflight
Observed condition: <invalid status, wrong project, path or slug drift, non-selected Increment,
                    source/Increment drift, or exact defect>
Effect: Ask Matt cannot admit or plan from this handoff
Next allowed action: return to Scope Shaper or select the exact current ready Increment
```

For these caller-facing admission returns and other exceptional non-continuations, read and apply the current `iis-workflow` [Non-Continuation Decision Provenance](../../../iis-workflow/SKILL.md#non-continuation-decision-provenance) section. Keep the existing Ask Matt result header as the owning result; the provenance fields explain that result and do not create another status or approval gate. Normal decision questions and successful continuation need no extra block.

## Main Flow

1. Run the Central UI / UX Routing audit and select `grill-with-docs` or
   `grill-me` for the current evidence context, but do not present a user-facing
   decision yet. A target with an existing canonical project root and
   inspectable repository context remains codebase-backed even when the current
   Increment/application scope has no implementation source yet; route it to
   `grill-with-docs`. Route to `grill-me` when the product root or repository
   context itself is not yet available. Do not classify from words such as
   greenfield, initialize, or bootstrap.
2. Before the first decision response, perform the selected Grill analysis on
   the current directly established factual base, filling only missing or changed
   load-bearing evidence rather than restarting broad Scope investigation.
   Complete Existing Authority First, Lead-First Investigation, Behavioral
   Design, and Counterexample Stress Test. When material UI lacks an applicable
   approved authority, also complete Matt's direct UI judgment far enough to
   identify its currently determinable user-owned rendered decisions.
   Merge all Grill, Behavior, UI, and applicable Scope Shaper Increment-frame decisions
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
   later Ticket delivery. Do not ask the user to invent a private package
   identity, future file list, dependency, or mutation envelope.
10. Use `to-tickets` only from an approved Spec. It creates the smallest set of
   independently observable desired-state Tickets, not an anticipated internal
   implementation sequence.

Product-authority artifacts may become more observable/testable from shared understanding to Spec to Ticket, but not more solution-specific. They may faithfully restate/split/clarify approved meaning, not introduce a more specific protocol, interface, format, transport, storage, component, algorithm or sequence than the normative source.

This restriction governs product norms, not a separate derived execution-method plan. After Ready Tickets, ready-ticket-plan may choose methods and future paths without adding product obligations; Matt does not write or approve that method in place of its preparation owner. Preserve exact current repository/Scope/Matt evidence as non-normative navigation for that owner, including direct Matt work with no Source-Increment. Revalidate load-bearing anchors/search/runtime premises rather than rerunning unchanged broad investigation; evidence never supplies missing product authority.

Planning stops at a ready Ticket. Do not invoke or orchestrate delivery from Ask Matt.

Do not direct users to `triage`, `improve-codebase-architecture`, remote trackers, or execution skills as active paths in this local planning flow.

## Inputs

The user's current goal, the amount of uncertainty, and whether a project/codebase is involved.

## Output

The result of starting the selected planning flow, not merely a recommended planning path. When grilling is selected, present a recommendation, a necessary explicit gate, or the complete contract-only shared understanding; do not output only a path explanation or summary.

## Planning Completion

Matt owns contract coherence, not implementation feasibility proof. Matt ends
with declarative Tickets and does not choose or recommend the final internal
implementation path. Later Ticket delivery owns those implementation decisions.

After ready Tickets exist, stop the Matt flow and report every ready Ticket by
its canonical absolute path. Ask Matt never invokes or supervises delivery.

State that the validated Ready Ticket Set is the terminal IIS planning output.
Any later implementation or verification is outside IIS Planning and starts as a
separate delivery action.
