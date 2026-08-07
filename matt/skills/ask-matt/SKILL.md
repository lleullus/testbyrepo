---
name: ask-matt
description: Use when a user presents or pastes a project, feature, product, or architecture brief for planning, clarification, specification, or ticket preparation, including a declarative brief without an explicit command; do not intercept explicit implementation requests.
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
  proportionate scoped UI authority; do not require a full C2 design exercise.
- `MATERIAL_RENDERED_UI`: it introduces a new rendered UI, materially redesigns
  one, or leaves a material user-visible rendered behavior/design decision
  unresolved.

For `MATERIAL_RENDERED_UI`, first determine whether an existing finished,
applicable, complete, approved local UI/UX authority is explicitly adopted by
the current or resulting shared understanding. A user-supplied authority may
satisfy this condition. References, defaults, prototypes, generated concepts,
a Design Read, or a status line do not become authority without that explicit
adoption. When no such authority exists, invoke active `ima2-uiux` only as a
design-judgment specialist inside the Matt flow before contract-only shared
understanding can be finalized. Matt owns the planning boundary and output
contract; `ima2-uiux` itself remains unchanged. Pass the bounded planning
context before the specialist acts. Do not follow its implementation handoff,
load `ima2-front`, write product code, mutate product files outside
`docs/planning/**`, or create a product source artifact in this Matt flow.

When this specialist judgment is required, complete enough of it before the
first user-facing decision response to identify every currently determinable
material user-owned rendered decision. Merge those decisions into the same
initial dependency graph as Grill and Behavior. Do not postpone specialist
judgment until after the first frontier or use late UI analysis to justify an
extra round. Final authority writing, render disposition, and approval still
follow their gates below. After an answer, revisit UI judgment only where that
answer materially changes it, and apply the same newly-identifiable dependency
rule as Behavior Design.

Before Matt writes a planning authority, prepare or revalidate the one
project-local planning root and work artifact directory that later Design,
Spec, and Tickets use. Resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory with the existing canonical project root and work slug.
Durable planning is blocked until that project root exists. Do not accept or
prepare an external workspace.

Matt, not the specialist, creates and governs
`<artifact-workspace>/DESIGN.md` for new/material UI:

- Use a non-empty H1 followed before the first H2 by exact plain Markdown
  metadata lines `Status: draft`, non-empty `Owner:`, and explicit `Scope:`.
  This is not the specialist's optional project-root YAML mini DESIGN format.
- Cover every applicable new/material C2 dashboard decision: Design Read and
  inherited tokens or deltas; information architecture and view hierarchy;
  responsive behavior for supported viewports; loading, empty, error, success,
  permission, navigation, and other scoped states; product-locale copy;
  accessibility semantics, focus, and keyboard behavior; assets and motion
  when present; and rendered verification conditions.
- Conditional dimensions may be `Not applicable` only with a reason. Do not
  invent list/detail views, Korean copy, live updates, mobile support, assets,
  or motion when the confirmed product scope does not include them.
- A utility CRUD/dashboard exemption identified during `ima2-uiux` design
  judgment waives only automatic visual concept/image generation during design
  exploration. A dashboard label alone must not start automatic image
  exploration, image-tool bootstrap, or generation. This exemption never
  waives the Matt-owned decision set above, and it does not prevent a later
  final-approval render when the user explicitly requests one under the Final
  Approval Render Disposition Gate.
- When visual concept exploration genuinely applies, keep its non-authority
  candidates under `<artifact-workspace>/design-concepts/`, never a product
  devlog or product asset directory. Only adopted decisions in `DESIGN.md` can
  become authority.
- The compact intent-discovery fork chooses direction only. A Design Read,
  style choice, default, prototype, generated concept, filename, or status line
  alone does not complete the authority.
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

## Final Approval Render Disposition Gate

Apply this gate when Matt creates a new `MATERIAL_RENDERED_UI` authority or
materially changes one. Do not apply it to `NON_UI`, exact-preservation
`ENGINEERING_ONLY`, or a `BOUNDED_RENDERED_CONTRACT` that does not require a
separate C2 `DESIGN.md`. When the latest shared understanding adopts an
existing complete approved UI/UX authority without changing it, the render
choice is not applicable; record the unchanged adoption as described below
instead of asking for a new render.

For every applicable design, ask the final render disposition question only
after all applicable decisions are written in `DESIGN.md` and `Open Questions`
is `None`, but before changing `Status: draft` to `Status: approved`, obtaining
final approval of the integrated shared understanding, or invoking `to-spec`.
Offer exactly these two choices:

- review a final-approval mockup or concept render; or
- approve from the completed `DESIGN.md` without an image.

Do not ask again when the user already requested or declined a final render for
the same current scope, or already reviewed a render that reflects the final
design. An image produced for early exploration, an image-first fork, or an
automatic HOTL selection does not count as final-render review.

Record exactly one of these plain Markdown lines as approval-procedure
evidence, not as a design requirement:

```text
Final approval render: requested
Final approval render: reviewed
Final approval render: declined
Final approval render: not applicable — unchanged approved authority adopted
```

For a new or materially changed authority, keep the applicable line in
`DESIGN.md`. For unchanged adoption, keep the `not applicable` line in the
latest shared understanding and do not modify the adopted authority merely to
add process evidence. A `reviewed` record may also carry the reviewed images'
local absolute paths in a separate `Final approval render paths:` line. Those
paths are process evidence only and must not be propagated into a Spec or
Ticket acceptance criterion.

When the user requests a render, record `requested` and keep `DESIGN.md` at
`Status: draft`. Use only the decisions in the completed draft as generation
input. The design direction is already decided: do not restart broad
image-first or human-in-the-loop exploration. Generate only the minimum
representative render needed for final review. Use one image when one screen is
sufficient; use more only when materially different key states or viewports
carry important decisions that one image cannot show. Store the results under
`<artifact-workspace>/design-concepts/` and show the actual images to the user
with Markdown image tags whose targets are absolute local paths. State that
each render is non-authoritative review material, not the implementation
contract and not implementation-time visual verification.

After the current render has actually been shown to and reviewed by the user,
and every resulting feedback item is resolved in `DESIGN.md`, replace
`requested` with `reviewed`; only then may the authority proceed to approval.

Convert every adopted visual-feedback item into an explicit `DESIGN.md`
decision, such as color, hierarchy, density, layout, state presentation, or
responsive treatment. An element that exists only in an image is not a
requirement. If feedback materially changes a visual decision, update
`DESIGN.md` and regenerate the minimum render from that current draft before
review can become `reviewed`. Do not regenerate for a typo or nonvisual
explanation change that cannot alter the render. Resolve all feedback and
reflect every adopted item in `DESIGN.md` before invoking `to-spec`.

If the user requested a render but no image-generation tool is available, fail
closed: leave the state `requested`, keep `DESIGN.md` at `Status: draft`, and do
not invoke `to-spec`. Continue only after generation becomes available and the
user reviews the result, or after the user explicitly withdraws the request
and chooses document-only approval, changing the state to `declined`.

When the user declines a render, the completed `DESIGN.md` remains the sole
design authority. Keep `Open Questions` at `None`; require the latest shared
understanding to adopt that exact authority path and scope and require explicit
approval from the user or named owner. The absence of an image does not lower
the authority's completeness standard. One explicit response may decline the
render, approve the completed `DESIGN.md`, and approve the integrated shared
understanding together when all three dispositions are presented clearly.

Images, prototypes, a Design Read, and automatic HOTL choices never become
authority on their own. Every adopted image-derived decision must be explicit
in `DESIGN.md`; browser or renderer evidence remains implementation-time work.
After approval, any material design delta returns `DESIGN.md` to `draft` and
requires the render disposition and any render staleness to be evaluated again.

`NON_UI` and exact-preservation `ENGINEERING_ONLY` work do not enter full UI
planning. A bounded rendered contract needs only its fixed rendered decisions
or preservation conditions in the confirmed shared understanding. It may reuse
a proportionate approved UI authority, or let the later approved Spec become
the scoped authority through its `## UI / UX` section; it does not require a
separate C2 `DESIGN.md`. Reclassify when later clarification changes the
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
qualify. Package-boundary changes return to Project Shaper; rendered
presentation decisions return to the UI authority flow.

When the phase reaches `BEHAVIOR AUTHORITY APPROVAL REQUIRED`, Matt may present
the completed draft authorities and one clearly labeled proposed integrated
contract-only shared understanding for joint approval. After approval, continue
the phase, mark the authorities approved, and establish `BEHAVIOR DESIGN:
COMPLETE`. Only then does Matt record the jointly approved
understanding as final or, when no joint approval occurred, present the final
understanding for confirmation. The final understanding must identify every
approved Behavior authority and exact applicable scope. Unchanged approved
authorities are adopted without reapproval. The pre-completion approval state
never permits `to-spec`.

Behavior owns semantic product behavior; `DESIGN.md` owns rendered expression
and interaction. Neither silently overrides the other. A conflict blocks final
confirmation. A material Behavior delta returns the authority, every adopting
Spec, and affected unfinished Tickets to `draft`.

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
   approved authority, also complete the required `ima2-uiux` design judgment
   far enough to identify its currently determinable user-owned decisions.
   Merge all Grill, Behavior, UI, and applicable Project Shaper frame decisions
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
   complete the Matt-owned authority, render-disposition, and approval flow
   before finalizing shared understanding; do not rediscover user-owned design
   decisions that the initial specialist judgment could have identified.
5. When new or changed Behavior authorities are approval-ready, use the joint
   approval flow above and require the phase to complete against the resolved
   frame.
6. Use `to-spec` when the desired outcome, preserved observable behavior and
   invariants, explicit boundaries, non-goals, and observable completion
   evidence are clear, Behavior Design is complete, every applicable
   Behavior authority is approved, and the user has confirmed one integrated
   contract-only shared understanding. That understanding is normative for
   outcome and scope; the approved Behavior authorities it adopts are normative
   for their exact behavior scopes. Repository facts, prior planning artifacts,
   prototypes, and anticipated implementation approaches remain context only.

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
7. Use `to-tickets` only from an approved Spec. It creates the smallest set of
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

After ready Tickets exist, stop the Matt flow. Report every ready Ticket by its canonical absolute
path. Then state, in the user's conversation language, only that these Tickets can be used to start
Implementation Lead later.

Do not ask for or suggest a Worker, show an Implementation Lead invocation command, load or invoke
Implementation Lead, or continue into implementation. Starting Implementation Lead is a separate user
action after Matt has ended.
