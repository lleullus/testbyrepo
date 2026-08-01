---
name: wayfinder
description: Map a large, unclear multi-session planning effort in local Markdown until it is ready for a Spec.
disable-model-invocation: true
---

# Wayfinder

## Purpose

Clarify the route for a large effort whose destination is known but whose decisions cannot fit in one planning session. Wayfinder produces decisions and open questions, not implementation deliverables.

## When To Use

Use only when the work is both large and unclear enough to need multiple sessions. If the route is visible or the work fits in a normal planning session, do not create a Wayfinder; use grilling and then `to-spec` instead.

## Inputs

- A destination for the effort.
- The target project root and work slug.
- The currently known constraints, decisions, and uncertainties.

## Process

1. Use grilling to state the destination and the first decisions needed to make the route visible.
2. Write or update `<project-root>/.scratch/<work-slug>/WAYFINDER.md` as a local Markdown map. Keep it limited to the destination, decisions made, open decision questions, known dependencies, and explicit out-of-scope work.
3. Resolve one decision at a time. Research or prototype only when that decision needs them; record their result as a candidate until the user adopts it.
4. When the route is clear, summarize the adopted decisions and hand the work back to `to-spec`.

Write questions and the map in the user's conversation language. Do not use a remote tracker, create tracker issues, or turn Wayfinder entries into implementation Tickets.

## Output

A local Markdown map that explains the planning route and the remaining decisions. It is a planning aid, not implementation authority.

## Next Action

When the user confirms that the decisions needed for the work are clear, use `to-spec`. Do not start implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
