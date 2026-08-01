---
name: handoff
description: Preserve a planning conversation in a local Markdown handoff for a later session.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

# Handoff

## Purpose

Capture only the context a later planning session needs without duplicating authoritative artifacts.

## Inputs

The current conversation, the target product root, work slug, current external planning workspace, and the focus of the next session when the user provides one.

## Process

Resolve `../../../planning-workspace/planning_workspace.py` from this skill's
canonical physical directory and revalidate the current workspace, then write
`<planning-workspace>/HANDOFF.md` in the user's conversation language. Reuse the
same workspace rather than creating a new task identity. Summarize the current
goal, decisions, unresolved questions, and next planning step. Link to existing
Specs, Wayfinders, research, prototypes, Tickets, and durable product/domain
authority by exact local path instead of copying them. Redact sensitive information.

State explicitly that the handoff is not an authority document: the approved Spec and reviewed Tickets remain authoritative. Do not change artifact status through a handoff.

## Output

One local Markdown context bridge for a new planning session.

## Next Action

Open a new planning session with the handoff and the referenced authority documents. Do not start implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
