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

- The target project root when planning starts.
- A work slug when an artifact is about to be created.

Do not ask for a GitHub, GitLab, Linear, Jira, or other remote tracker. Do not inspect remotes to choose one. Do not create or change `AGENTS.md`, `CLAUDE.md`, `docs/agents/`, labels, or domain-policy files.

## Local Markdown Convention

Planning artifacts stay in the target project:

```text
<project-root>/.scratch/<work-slug>/
```

The planning flow may create `SPEC.md`, `WAYFINDER.md` for a large unclear effort, `tickets/TICKET-NNN.md`, and `HANDOFF.md` only when needed. Keep the directory focused on the current work; do not create a separate planning application or tracker configuration.

## Process

1. State that planning is local Markdown only.
2. If no artifact is being written yet, explain the convention and stop. Do not request unused project details.
3. When an artifact is needed, confirm the project root and work slug, then direct the user to the appropriate planning skill.

## Output

A short explanation in the user's conversation language. This skill normally writes no files.

## Next Action

Use `grill-with-docs` or `grill-me` when the idea needs clarification, `wayfinder` only for a large unclear multi-session effort, or `to-spec` when the work is ready to be captured. Do not start implementation or invoke an Implementation Lead or Worker.
