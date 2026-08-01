---
name: grilling
description: Stress-test a plan or design through a dependency-aware, adaptive user interview.
---

# Grilling

## Purpose

Reach a shared understanding of a plan or design before it is captured as a planning artifact.

## Inputs

The user's plan, available codebase facts, and the unresolved decisions.

## Process

Treat the interview as a decision graph, not a checklist or a prewritten queue of questions.

Before every interview turn, internally identify the material unresolved decisions implied by the user's goal, confirmed context, and verified project facts. Exclude facts that can be verified directly, implementation-owned choices that the user has not deliberately made part of the product or operational contract, answered or invalidated decisions, and speculative downstream work.

Create a dependency from decision A to decision B only when different answers to A would materially change whether B needs to be decided, B's core scope, ownership, lifecycle, or authority, B's viable choices, or the evidence needed to resolve B. A change only to wording, emphasis, explanation, examples, or recommendation rationale does not make A a gating decision.

A decision is eligible to be asked only when it has no unresolved predecessor. Among eligible decisions, select the next most gating decision in this order:

1. It creates or removes downstream work or changes the core product or system boundary.
2. It changes responsibility, ownership, lifecycle, operating model, or an external authority boundary.
3. It changes the viable choices for the greatest amount of material downstream decision-making.
4. Delaying it risks the greatest amount of invalidated downstream answers or rework.

Do not rank by a mechanical count alone: one downstream decision that changes core scope may outrank several minor details. Treat a decision as gating only when it controls at least two material downstream decisions, or one downstream decision that changes core scope, ownership, lifecycle, or authority. When eligible decisions are genuinely independent, ask up to five in one batch. They are independent only when no answer can materially change another question's necessity, core scope, ownership, viable choices, or required evidence. When uncertain, ask one.

Before asking a gating decision, tell the user in one concise sentence what the next most gating decision is and name the concrete downstream decisions it controls. Mention only downstream decisions already implied by the user's goal, confirmed context, or verified project facts; never invent downstream work to make a question appear gating. Then ask that decision alone, give a recommended answer, and when possible give a brief reason.

After every response, discard invalidated branches, add any newly valid decisions, rebuild the remaining decision graph, and select the next turn again. Never continue a prewritten question queue merely because it was prepared earlier.

If a fact can be found in the codebase or an authoritative source, look it up rather than asking; product and design decisions remain the user's. Write questions, recommendations, and any notes in the user's conversation language. Do not enact the plan until the user confirms a shared understanding.

## Output

Resolved decisions and explicitly recorded open questions for later planning.

## Next Action

Suggest `to-spec` only after the user confirms the understanding, or `wayfinder`, `research`, or `prototype` only when their specific need remains. Do not begin implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
