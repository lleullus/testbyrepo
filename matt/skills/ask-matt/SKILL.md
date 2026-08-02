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
load `ima2-front`, write product code, mutate product files, or create a
product-root design artifact in this Matt flow.

Before Matt writes a package authority, prepare or revalidate the same
external planning workspace that later Spec, Tickets, Wayfinder, and Handoff
artifacts will use. Resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory. Request the product root or work slug only when this first
artifact requires it, and do not prepare a second workspace later.

Matt, not the specialist, creates and governs
`<planning-workspace>/DESIGN.md` for new/material UI:

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
  judgment waives only visual concept/image-generation. For that exemption, do
  not run image-tool bootstrap or generation. It never waives the Matt-owned
  decision set above.
- When visual concept exploration genuinely applies, keep its non-authority
  candidates under `<planning-workspace>/design-concepts/`, never a product
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

`NON_UI` and exact-preservation `ENGINEERING_ONLY` work do not enter full UI
planning. A bounded rendered contract needs only its fixed rendered decisions
or preservation conditions in the confirmed shared understanding. It may reuse
a proportionate approved UI authority, or let the later approved Spec become
the scoped authority through its `## UI / UX` section; it does not require a
separate C2 `DESIGN.md`. Reclassify when later clarification changes the
rendered obligation.

## Main Flow

1. Run the Central UI / UX Routing audit before deciding whether grilling is needed. When its material-UI route applies, complete the Matt-owned authority flow, using active `ima2-uiux` only for design judgment, before finalizing shared understanding.
2. Decide whether grilling is needed. When it is, immediately start the selected `grill-with-docs` or `grill-me` flow and output its first interview turn in the current conversation. Do not stop at a route recommendation or summary. Skip grilling only when the decisions are already clear.
   A target with an existing canonical project root and inspectable repository
   context remains codebase-backed even when the current package/application
   scope has no implementation source yet; route it to `grill-with-docs`.
   Route to `grill-me` when the product root or repository context itself is not
   yet available. Do not classify from words such as greenfield, initialize, or
   bootstrap.
3. Use `to-spec` when the desired outcome, preserved observable behavior and
   invariants, explicit boundaries, non-goals, and observable completion
   evidence are clear, and the user has confirmed one contract-only shared
   understanding. That confirmed shared understanding is the sole normative
   planning baseline. Repository facts, prior planning artifacts, prototypes,
   and anticipated implementation approaches may provide context, but must not
   add to, strengthen, narrow, or silently reinterpret the contract without an
   explicit user-confirmed delta.

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
4. Use `to-tickets` only from an approved Spec. It creates the smallest set of
   independently observable desired-state Tickets, not an anticipated internal
   implementation sequence.

Planning artifacts may become more observable and testable as they progress
from shared understanding to Spec to Ticket, but they must not become more
solution-specific. A downstream artifact may restate, split, or clarify an
approved contract; it must not introduce a more specific protocol, interface,
format, transport, storage model, component, algorithm, or implementation
sequence than its normative source.

Planning stops at a ready Ticket. Do not invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.

## Optional Paths

- `wayfinder`: only for a large, unclear effort that needs multiple sessions to make the route visible. Do not require it for ordinary work.
- `research`: only when reliable information is needed to resolve a planning question.
- `prototype`: only when a specific logic or UI question cannot be settled in conversation. Its result is not authority until the user adopts a decision.
- `handoff`: only when a session must continue elsewhere. It preserves context but is not an authority document.
- `domain-modeling` and `codebase-design`: use when their vocabulary or decisions are needed for the current planning question.

Do not direct users to `triage`, `improve-codebase-architecture`, remote trackers, or execution skills as active paths in this local planning flow.

## Inputs

The user's current goal, the amount of uncertainty, and whether a project/codebase is involved.

## Output

The result of starting the selected planning flow, not merely a recommended planning path. When grilling is selected, output the first interview turn; do not output only a path explanation or summary instead of starting the interview.

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
