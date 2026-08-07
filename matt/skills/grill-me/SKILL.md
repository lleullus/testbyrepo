---
name: grill-me
description: Use when ask-matt routes a non-codebase brief, or when a user presents a non-codebase plan with unresolved decisions, to clarify it through dependency-aware recommendation review.
---

# Grill Me

## Purpose

Sharpen an idea that does not require codebase context before it becomes a Spec or another planning artifact.

## Inputs

The user's plan or design and the decisions that remain unclear.

## Process

Run `grilling` as the sole owner of the interaction policy. Supply the user's brief, confirmed conversation context, adopted authorities, and directly resolvable facts; do not duplicate its recommendation, gate, approval, delta, or explicit batch-mode rules. Do not begin from a prepared checklist or turn an implementation-owned choice into a user decision. Inspect supplied documents and authoritative public sources directly rather than asking the user for discoverable facts. Write in the user's conversation language.

## Contract boundary

Before Behavior Design, produce only a provisional product frame. Matt then
directly performs the mandatory phase required by `ask-matt`; when it identifies
product decisions, resolve them through `grilling` and continue the phase. Before recommending
`to-spec`, present one integrated contract-only shared understanding containing
the approved Behavior authorities and obtain explicit user confirmation.
Exclude proposed mechanisms,
implementation structure, sequencing, and test arrangements unless the user
deliberately requires them as part of the outcome contract.

After confirmation, freeze that understanding as the normative planning
baseline. Later discussion, prototypes, references, and anticipated approaches
must not add to, strengthen, or narrow the contract without an explicit
user-confirmed delta.

When a new product/package/application will require its first product artifacts
but no inspectable root or repository context exists yet, confirm only:

- the scope in which initialization mutation is authorized;
- applicable external/public/persisted identities and intentionally fixed
  runtime, toolchain, deployment, or operational constraints; and
- whether every remaining material bootstrap choice is fixed or explicitly
  delegated to Implementation Lead/Worker.

Do not ask for private package/module identity, dependencies, future file
layout, commands, or a mutation envelope. The exact product `Project-Root` must
exist as a canonical accessible directory before a Ticket can become `ready`;
planning does not create it.

## Output

A contract-only shared understanding of the problem, decisions, constraints,
and open questions after the user confirms it. This skill does not create
implementation work.

## Next Action

Use `to-spec` only after Behavior Design completes and the user confirms
the integrated contract-only shared understanding. Do not start implementation or invoke Implementation Lead, a
Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
