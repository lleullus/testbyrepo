---
name: grill-with-docs
description: Use when ask-matt routes a codebase-backed brief, or when a user presents a codebase-backed plan with unresolved decisions, to clarify it through a dependency-aware, adaptive interview using domain vocabulary when needed.
---

# Grill With Docs

## Purpose

Sharpen a plan or design against the relevant codebase and its domain vocabulary before creating a Spec.

## Inputs

The user's goal, relevant codebase context, and existing domain documentation when present.

## Process

Run a `grilling` session using its dependency-aware decision-graph and adaptive batching policy. Do not begin from a prepared checklist. Before the first question and after every answer, use `grilling` to select the next most gating unresolved decision; ask it alone and briefly name the concrete downstream decisions it controls. Verify codebase facts directly before ranking decisions, and do not turn an inspectable fact or an implementation-owned choice into a user decision. Use `domain-modeling` when terminology or an architectural decision needs attention. Write questions and any documentation in the user's conversation language.

## Planning boundary

Drive the interview toward:

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

Before recommending `to-spec`, present one contract-only shared understanding
and obtain explicit user confirmation. State it without anticipated root
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

A clarified planning basis with resolved decisions, constraints, and open questions. Do not create implementation work as part of the interview.

## Next Action

Use `to-spec` when the user confirms the understanding. Do not start implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
