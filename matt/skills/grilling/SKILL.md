---
name: grilling
description: Stress-test a plan or design through evidence-backed recommendations, explicit gates, and dependency-aware delta review.
---

# Grilling

## Purpose

Reach a shared understanding of a plan or design before it is captured as a planning artifact.

## Inputs

The user's plan, available codebase facts, and the unresolved decisions.

## Process

Treat planning as a decision graph, not a checklist or a prewritten question queue. Use it to form recommendations and to reconsider only what a correction materially changes.

Before the first response, require the complete current Behavior analysis and
merge its decisions with those implied by the user's goal, confirmed context,
verified facts, scope, authority, constraints, and UI obligations. Resolve
inspectable facts directly. Exclude implementation-owned choices unless the user
deliberately makes the choice itself part of the product or operational
contract, plus answered, invalidated, and speculative downstream work. Do not
present a decision response until this integrated graph is ready.

Also apply `ask-matt`'s complete Central UI / UX Routing before the first
response, including direct review or stress-test routes. When material UI lacks
an applicable approved authority, complete Matt's direct UI judgment far enough
to identify every currently determinable user-owned rendered decision and merge
those decisions into this same graph. Do not defer this audit or UI judgment to
`to-spec`, and do not use late UI analysis to create another round.

The current unblocked material user-owned decision frontier is the same in every
interaction mode. Present all of it in the same response. In explicit
`batch-grill-me` mode, number each decision and give its recommendation. In
normal mode, compress related decisions into concise coherent recommendation
blocks, but do not defer an identifiable unblocked decision merely to shorten
the response. Defer only decisions whose prerequisites remain open, omit
inspectable facts and implementation-owned choices, and recompute the frontier
after each answer. Never infer, default to, or fall back to Batch mode from
decision count, scope size, or a request for many questions.

Create a dependency from decision A to decision B only when different answers to A would materially change whether B needs to be decided, B's core scope, ownership, lifecycle, or authority, B's viable choices, or the evidence needed to resolve B. A change only to wording, emphasis, explanation, examples, or recommendation rationale does not create such a dependency.

Lead with the decision that most affects scope, ownership, lifecycle, authority,
or downstream rework; judge material effect, not node count. In normal mode,
use the smallest coherent set of recommendation blocks that still contains the
whole current frontier in this response. Split blocks when approval scope
becomes unclear or a separate operating model begins. Recommend mutually
dependent decisions together only when separating them would be arbitrary or
misleading. State assumptions, dependencies, or tradeoffs only when they could
change the user's choice, and use short labels only when a later delta would
otherwise be ambiguous.

Ask an explicit gate only when progress requires a value or permission that only the user or named owner can provide, would cross a confirmed scope or authority boundary, needs separate safety or irreversibility consent, or leaves no responsible default after inspectable facts are resolved. Downstream impact, technical difficulty, and implementation uncertainty alone are not gates. Independent gates for the same owner and scope may share one clearly separated block, but each requires an explicit answer and a general approval never closes them.

End each recommendation with clear approve-or-delta semantics. When the user clearly responds in that mode, treat the other presented recommendations as provisionally accepted unless the delta materially affects them; a question or ambiguous comment is not approval. Acceptance remains provisional until Behavior Design completes, applicable Behavior authorities are approved, and the user explicitly confirms one integrated contract-only shared understanding. Before then, the output is only a provisional frame or product-decision resolution.

After every answer, reconsider the changed item and any recommendation or
Behavior conclusion whose meaning or support materially changed. A later round
is allowed only when that answer creates or resolves a dependency such that a
downstream decision's existence, core scope or owner, viable choices, applicable
authority or lifecycle, or required evidence is newly identifiable and could
not have been determined accurately before the answer. Late fact-finding, late
Behavior analysis, question count, response length, or a prepared queue is not
justification. Preserve everything else.

If a fact can be found in the codebase or an authoritative source, look it up rather than asking. Repository truth and references provide evidence but do not become planning authority unless already adopted or externally unavoidable. Write recommendations, gates, and any notes in the user's conversation language. Do not enact the plan until the user confirms a shared understanding.

## Output

Evidence-backed recommendations, explicit gates when needed, a provisional
frame for Behavior Design, and the confirmed integrated shared understanding
after the phase completes.

## Next Action

Suggest `to-spec` only after Behavior Design completes and the user confirms the integrated understanding. Do not begin implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
