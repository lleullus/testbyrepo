---
name: research
description: Investigate a planning question against high-trust primary sources and capture cited findings as local Markdown.
---

# Research

## Purpose

Resolve a specific planning question with evidence from primary sources, such as official documentation, source code, specifications, or first-party APIs.

## Inputs

The research question, target project, and any relevant local artifacts or source constraints.

## Process

Investigate directly against the sources that own each claim. Separate sourced facts from assumptions and unresolved questions. Do not use research to choose product policy on the user's behalf.

When a planning report is useful, resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory, prepare or revalidate the current external workspace, and
save one cited Markdown file there. Reuse that workspace for the flow. A
document explicitly approved as durable product/domain documentation follows
its product documentation authority instead; do not move it into planning
storage. Write the report and user-facing findings in the user's conversation language.

## Output

A concise cited Markdown finding that can inform grilling, a Wayfinder decision, or a Spec. It is planning input, not implementation authority.

## Next Action

Return the findings to the user for a decision, then continue the relevant planning skill if needed. Do not start implementation or invoke Implementation Lead, a Worker, `/implement`, `/tdd`, `/code-review`, or another execution chain.
