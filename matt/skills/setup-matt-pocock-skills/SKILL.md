---
name: setup-matt-pocock-skills
description: Prepare a project for Matt's local Markdown planning flow without configuring a remote tracker or project policy files.
disable-model-invocation: true
---

# Setup Matt Pocock's Skills

Prepare only the local Markdown planning convention for this project. This is a lightweight orientation step, not a tracker or repository-policy setup.

## Purpose

Explain where planning artifacts will live and confirm the project root and work slug when an artifact is about to be created.

## Inputs

- The target product project root when planning starts.
- A work slug when an artifact is about to be created.

Do not ask for a GitHub, GitLab, Linear, Jira, or other remote tracker. Do not inspect remotes to choose one. Do not create or change `AGENTS.md`, `CLAUDE.md`, `docs/agents/`, labels, or domain-policy files.

## Local Markdown Convention

All durable planning and authority Markdown lives at:

```text
<Project-Root>/docs/planning/
```

Before the first artifact, resolve
`../../../planning-workspace/planning_workspace.py` from this skill's canonical
physical directory and run its `prepare` command with the exact existing
project root and work slug. The tool prepares the canonical planning root and
work artifact directory and rejects external, symlinked, or future-root
destinations.

The flow stores scoped Behavior authorities under `behavior/`, package UI
authority and concept candidates inside the work directory, and `SPEC.md` plus
Tickets inside that same work directory. Concept candidates are not product
assets or authority. Planning roles may mutate only `docs/planning/**`.
Existing external or `.scratch` planning input is context only and is never
selected as a current authority destination.

## Process

1. State that planning is local Markdown only.
2. If no artifact is being written yet, explain the convention and stop. Do not request unused project details.
3. When an artifact is needed, confirm the existing canonical product root and
   work slug, prepare or revalidate `docs/planning`, report its canonical path,
   then direct the user to the appropriate planning skill.

## Output

A short explanation in the user's conversation language. This skill normally writes no files.

## Next Action

Use `grill-with-docs` or `grill-me` when the idea needs clarification, or `to-spec` when the work is ready to be captured. Do not start or orchestrate delivery from this planning setup flow.
