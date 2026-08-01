---
name: ask-matt
description: Use when a user presents or pastes a project, feature, product, or architecture brief for planning, clarification, specification, or ticket preparation, including a declarative brief without an explicit command; do not intercept explicit implementation requests.
---

# Ask Matt

Route planning work without starting implementation. Write this guidance, questions, and any planning artifacts in the language the user uses in the conversation.

## Purpose

Choose the smallest planning path that makes the work clear enough for an approved `SPEC.md` and a ready implementation Ticket.

## Main Flow

1. Decide whether grilling is needed. When it is, immediately start the selected `grill-with-docs` or `grill-me` flow and output its first interview turn in the current conversation. Do not stop at a route recommendation or summary. Skip grilling only when the decisions are already clear.
   A target with an existing canonical project root and inspectable repository
   context remains codebase-backed even when the current package/application
   scope has no implementation source yet; route it to `grill-with-docs`.
   Route to `grill-me` when the product root or repository context itself is not
   yet available. Do not classify from words such as greenfield, initialize, or
   bootstrap.
2. Use `to-spec` when the desired outcome, preserved observable behavior and
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
3. Use `to-tickets` only from an approved Spec. It creates the smallest set of
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
