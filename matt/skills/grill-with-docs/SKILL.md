---
name: grill-with-docs
description: Use when ask-matt routes a codebase-backed brief, or when a user presents a codebase-backed plan with unresolved decisions, to clarify it through evidence-backed, dependency-aware recommendation review using domain vocabulary when needed.
---

# Grill With Docs

## Purpose

Sharpen a plan or design against the relevant codebase and its domain vocabulary before creating a Spec.

## Inputs

The user's goal, relevant codebase context, and existing domain documentation when present.

## Process

Run `grilling` as the sole owner of the interaction policy. Before its first response, use relevant facts already directly established in the current conversation at their attributable currentness boundary; inspect the minimum sufficient missing or changed code, documentation, approved authorities, external contracts, and runtime evidence. A new leaf is not a new evidence question. Refresh a load-bearing changed anchor, expanded absence-search boundary, mutable state, or external version rather than repeating a broad investigation. Supply facts and constraints to `grilling`; do not duplicate its recommendation, gate, approval, delta, or explicit batch-mode rules. Do not turn an inspectable fact or an implementation-owned choice into a user decision. Clarify terminology or architectural decisions within this review when they need attention. Write in the user's conversation language.

## Planning boundary

Drive planning toward:

- the desired observable outcome;
- existing behavior and invariants that must be preserved;
- explicit product or operational constraints;
- non-goals; and
- observable completion evidence.

Truth is not authority. Repository facts, prior planning artifacts, tests,
documentation, prototypes, and runtime observations may provide context or
evidence, but do not add to, strengthen, narrow, or silently reinterpret the
planning contract. A verified fact becomes normative only when it is already
part of the confirmed planning baseline or an unavoidable verified external
contract.

Treat every proposed technical approach as provisional. A proposed approach
becomes part of the planning contract only when the user deliberately requires
that approach itself, or when a verified external contract requires it.

Use this replaceability test:

> If another internal implementation could produce the same observable outcome
> while preserving every explicit constraint and invariant, the choice between
> those implementations is not part of the planning contract.

Verify a codebase or runtime claim before relying on it when that claim is
necessary to determine the meaning of completion or whether the contract is
internally coherent. Do not ask the user to validate a fact that can be
inspected directly, and do not investigate technical approaches merely to
prove the work implementable.

Uncertainty about the best implementation, or the absence of a currently known
implementation path, does not block `to-spec`. Block `to-spec` only when a
verified external fact or clear logical contradiction shows that the confirmed
outcome, constraints, and Non-Goals cannot all hold. If an external capability
fact is necessary to determine whether the contract is internally coherent,
verify only that fact; do not design the implementation path as part of the
feasibility check.

For a scope that may require first product/package/application artifacts,
inspect current target readiness directly. Target-readiness absence is a
repository fact, not a user question and not a durable acceptance claim. Root
emptiness is not the test: an existing monorepo can have a new scope, while an
empty documentation-only target need not initialize a product. Ask only the
authorization decisions that inspection cannot answer:

- whether initialization mutation is allowed in the current planning scope;
- applicable external/public/persisted identities and intentionally fixed
  runtime, toolchain, deployment, or operational constraints; and
- whether every remaining material bootstrap choice is fixed or explicitly
  delegated to later Ticket delivery.

Do not ask the user to select private package/module identity, dependencies,
source/config/test paths, internal structure, commands, or a mutation envelope
when those choices are not externally consumed constraints.

Before the first user-facing decision response, apply `ask-matt`'s Central UI /
UX Routing, use the inspected evidence to form the provisional frame, and
perform the complete Behavior Design analysis. When material UI lacks an
applicable approved authority, complete Matt's direct UI judgment far enough to
identify its currently determinable user-owned rendered decisions. Merge every
currently identifiable Grill, Behavior, and UI decision into one dependency
graph and present its current frontier through `grilling`; do not create a later
round merely because Behavior or UI was analyzed after an earlier question.
Before recommending `to-spec`, present one integrated contract-only shared understanding containing
the approved Behavior authorities and obtain explicit user confirmation. State it without anticipated root
causes, files, modules, endpoints, internal abstractions, implementation order,
or test seams. If removing one of those mechanisms changes the user's intended
contract, ask whether the mechanism itself is an explicit requirement.

After confirmation, freeze that understanding as the normative planning
baseline. Codebase inspection, prior Specs, Tickets, tests, documentation, and
runtime observations must not add new requirements. If a new product, scope,
boundary, non-goal, or external-contract decision emerges, present only that
delta and obtain confirmation before continuing.

When preserving existing behavior, name the observable behavior or invariant.
Do not preserve an internal mechanism merely because the current system or a
prior planning artifact uses it.

## Output

A clarified planning basis with resolved decisions, constraints, and open questions. Do not create implementation work as part of planning.

## Next Action

Use `to-spec` only after Behavior Design completes and the user confirms the integrated understanding. Do not start or orchestrate delivery from this planning flow.
