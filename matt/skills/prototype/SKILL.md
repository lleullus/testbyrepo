---
name: prototype
description: Build a throwaway prototype for a user-approved design question without starting product implementation.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Planning Boundary

**Purpose:** make one uncertain logic or UI decision concrete. **Inputs:** a specific question the user wants answered and relevant project context. **Output:** a clearly marked throwaway prototype plus the learned answer, written in the user's conversation language.

Use this only when the question cannot be settled in conversation. A prototype does not start product implementation, does not invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain, and has no authority by itself. Add a prototype result to a Spec only when the user explicitly adopts the decision.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a tiny interactive terminal app that pushes the state machine through cases that are hard to reason about on paper.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious — but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
2. **One command to run.** Whatever the project's existing task runner supports — `pnpm <name>`, `python <path>`, `bun <path>`, etc. The user must be able to start it without thinking.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast and then delete it.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Delete when done.** When the prototype has answered its question, keep only the user's adopted decision in the relevant planning artifact; do not fold prototype code into product code as part of this skill.

## When done

The _answer_ is the only thing worth keeping from a prototype. Keep throwaway
prototype source under its existing product-context and cleanup rules; it is not
planning Markdown. Capture the question and the user's adopted decision in the
current external planning workspace, prepared or revalidated through
`../../../planning-workspace/planning_workspace.py` resolved from this skill's
canonical physical directory, or in an approved Spec when appropriate. If the
user has not adopted a decision, leave it unresolved and delete the prototype
rather than treating it as authority.

## Next Action

Ask the user whether to adopt the learned decision. Only an adopted decision may be reflected by `to-spec`; otherwise record it as unresolved or discard the prototype.
