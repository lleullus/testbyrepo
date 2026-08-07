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

Before each response, identify the material unresolved decisions implied by the user's goal, confirmed context, and verified facts. Resolve inspectable facts directly. Exclude implementation-owned choices unless the user deliberately makes the choice itself part of the product or operational contract, plus answered, invalidated, and speculative downstream work.

When the current Matt planning unit carries the explicit `batch-grill-me`
interaction mode, retain the same decision graph and authority rules but change
only round presentation. Present every currently unblocked material user-owned
decision in the dependency frontier in one numbered recommendation-first round.
Defer decisions whose prerequisites remain open, omit inspectable facts and
implementation-owned choices, and recompute the frontier after each response.
Carry this mode through product-decision bundles identified during Behavior
Design. Never infer, default to, or fall back to this mode from decision count,
scope size, or a request for many questions.

Create a dependency from decision A to decision B only when different answers to A would materially change whether B needs to be decided, B's core scope, ownership, lifecycle, or authority, B's viable choices, or the evidence needed to resolve B. A change only to wording, emphasis, explanation, examples, or recommendation rationale does not create such a dependency.

Lead with the decision that most affects scope, ownership, lifecycle, authority, or downstream rework; judge material effect, not node count. Default to the smallest coherent recommendation the user can comfortably review: one concise recommendation for simple work, and only a few key decisions for ordinary work. Split when approval scope becomes unclear or a separate operating model begins. Recommend mutually dependent decisions together only when separating them would be arbitrary or misleading. State assumptions, dependencies, or tradeoffs only when they could change the user's choice, and use short labels only when a later delta would otherwise be ambiguous.

Ask an explicit gate only when progress requires a value or permission that only the user or named owner can provide, would cross a confirmed scope or authority boundary, needs separate safety or irreversibility consent, or leaves no responsible default after inspectable facts are resolved. Downstream impact, technical difficulty, and implementation uncertainty alone are not gates. Independent gates for the same owner and scope may share one clearly separated block, but each requires an explicit answer and a general approval never closes them.

End each recommendation with clear approve-or-delta semantics. When the user clearly responds in that mode, treat the other presented recommendations as provisionally accepted unless the delta materially affects them; a question or ambiguous comment is not approval. Acceptance remains provisional until Behavior Design completes, applicable Behavior authorities are approved, and the user explicitly confirms one integrated contract-only shared understanding. Before then, the output is only a provisional frame or product-decision resolution.

After every response, reconsider the changed item and any recommendation whose meaning or support materially changed because of another decision, a verified fact, adopted authority, material assumption, or required artifact state. Preserve everything else and never continue a prepared queue.

If a fact can be found in the codebase or an authoritative source, look it up rather than asking. Repository truth and references provide evidence but do not become planning authority unless already adopted or externally unavoidable. Write recommendations, gates, and any notes in the user's conversation language. Do not enact the plan until the user confirms a shared understanding.

## Output

Evidence-backed recommendations, explicit gates when needed, a provisional
frame for Behavior Design, and the confirmed integrated shared understanding
after the phase completes.

## Next Action

Suggest `to-spec` only after Behavior Design completes and the user confirms the integrated understanding. Do not begin implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
