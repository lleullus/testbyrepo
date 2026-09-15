---
name: repository-investigation
description: Use when the user asks for a structured repository investigation, repo preflight, codebase grounding, architecture/current-state investigation, or a reusable evidence baseline before IIS/Adaptive planning, review, or another decision. Investigate the exact current repository read-only, trace material execution/state/authority paths, challenge the first model with counterpaths, separate facts from inference, and write one immutable project-local investigation artifact when a durable handoff is requested. This skill supplies evidence only and never selects IIS Scope, an Increment, product policy, Spec/Ticket meaning, implementation, or verification verdicts.
---

# Repository Investigation

## Purpose

Produce a consistent, decision-grade repository evidence baseline before a later planning, review, or implementation decision. The skill investigates what the repository and authorized runtime actually establish; it does not turn those facts into product authority.

The normal output is one terminal investigation result. When the user requests a durable/reusable handoff, or the investigation is explicitly being prepared for a later separate IIS/Adaptive invocation, also write one immutable project-local artifact under `docs/investigation/**` using the canonical helper and validator.

Before investigation work, read [references/investigation.md](references/investigation.md) in full.

## Authority

The current Main is the **Repository Investigation Lead**. It owns:

- exact investigation objective and connected evidence boundary;
- bounded reconnaissance and investigation-frontier construction;
- direct primary-source inspection;
- dynamic read-only lane assignment when explicit `SUBAGENT` execution is selected;
- evidence attribution, contradiction handling, counterpath challenge, and final fan-in;
- `FACT | INFERENCE | UNKNOWN` separation;
- coverage sufficiency and `COMPLETE | PARTIAL | BLOCKED` investigation completion; and
- the optional immutable investigation artifact.

It does **not** own:

- IIS Planning Boundary, Work Package decomposition, or Increment selection;
- Adaptive Mandate, Run Contract, Required/Candidate Named Items, or completion meaning;
- Behavior/UI/product-policy decisions;
- Spec or Ticket authority;
- implementation design or mutation; or
- verification verdicts or Ticket progression.

Any planning relevance in the result is a candidate interpretation of evidence only. A later IIS owner independently decides whether an observed fact becomes Current Product State, a Planning Constraint, a product-capability dependency, Delivery Context, or no planning authority at all.

## Inputs

Required:

- `Project Root`: one exact canonical existing project root.
- `Investigation Objective`: the concrete question the repository investigation must answer.

Derive when inspectable; ask only when materially ambiguous:

- `Repository Root`: the Git root containing the project, which may equal Project Root.
- `Focus Target`: component, feature, wrapper, flow, or outcome area named by the user.
- `Decision Context`: why the answer matters, without importing a desired conclusion.
- `Explicit Exclusions`: known out-of-scope surfaces.
- `Runtime Inspection Authority`: read-only only unless the current user separately authorizes a concrete effect.
- `Durable Artifact`: `yes | no`. Default `yes` when the user asks for a reusable handoff or says this investigation will feed a later separate IIS/Adaptive run; otherwise default `no`.

Do not ask the user to identify files, symbols, entrypoints, tests, state owners, or internal call order when the repository can answer those questions directly.

## Execution mode

Top-level execution defaults to `DIRECT`.

- `DIRECT`: current Main performs the complete investigation itself.
- `SUBAGENT`: use only when the current user explicitly selects subagents, multiple models/agents, or parallel investigation for this exact investigation.
- Never infer SUBAGENT merely from repository size, task difficulty, lane count, model capability, or available worker capacity.
- In SUBAGENT mode, create a dynamic worker set only for material independent lanes. There is no fixed worker count or permanent role roster.
- A delegated investigator receives `Delegated Investigator: yes`, stays read-only, answers exactly one bounded lane, and does not delegate again.
- Worker agreement is never evidence. One attributable counterexample survives fan-in even when every other worker missed it.

If the user explicitly requests SUBAGENT execution but the host cannot provide the required bounded worker invocation/fan-in capability, return `SUBAGENT CAPABILITY UNAVAILABLE` rather than silently changing execution mode.

## Required investigation frontier

After bounded reconnaissance, classify each of these evidence concerns exactly once as `INVESTIGATE | COVERED_BY_OTHER_LANE | NOT_APPLICABLE`:

1. `FLOW_AND_READBACK` — material entry/trigger -> execution path -> observable result -> authoritative readback.
2. `STATE_AND_AUTHORITY` — state, data, configuration, persistence, lifecycle, and ownership/authority boundaries relevant to the objective.
3. `ALTERNATE_PATHS` — plausible bypass, direct entry, fallback, legacy, plugin/dynamic registration, environment-specific, or sibling route that could falsify the first model.
4. `EVIDENCE_ALIGNMENT` — whether current code, tests, documentation, configuration, and authorized runtime/readback materially agree.

`NOT_APPLICABLE` requires a concrete reason. Do not invent lanes merely to use workers or make the investigation appear exhaustive.

## Evidence discipline

For every load-bearing conclusion:

- open or reproduce primary evidence directly;
- distinguish observed fact from inference;
- record a plausible counterexample, conflicting source, or boundary condition;
- state the inspected/search universe behind an absence claim;
- keep documentation, tests, logs, implementation narration, and filenames at their actual evidentiary strength;
- do not treat a test name as proof of product behavior;
- do not treat a failed search as proof of global absence; and
- keep unverified gaps explicit.

When operational or historical context outside code can change the answer, investigate it under the same evidence discipline and current read access; use the selective source guidance in `references/investigation.md` rather than a mandatory source inventory.

Prefer the smallest investigation that decides the objective. Do not inventory the whole repository, create a generic architecture encyclopedia, or continue searching solely for confidence once every material frontier question is closed.

## Durable artifact

When `Durable Artifact: yes`, before writing:

1. capture repository binding before the artifact itself dirties the tree;
2. resolve `tools/prepare_investigation_workspace.py` from this skill's canonical physical directory;
3. run it with exact Project Root and one lowercase kebab-case investigation slug;
4. write exactly the returned `INV-NNN.md` using [templates/REPOSITORY-INVESTIGATION.template.md](templates/REPOSITORY-INVESTIGATION.template.md);
5. never overwrite a prior `INV-NNN.md`;
6. run `tools/validate_investigation.py <absolute-artifact-path>` and require exact `VALID`; and
7. report the exact canonical artifact path.

The artifact is repository evidence, not IIS authority and not an authoritative product readback by itself. It may identify actual readback surfaces and evidence anchors for a later owner to reopen.

## Completion

Use exactly one result:

- `COMPLETE` — every material frontier question reached an attributable bounded conclusion/non-finding, the first repository model received a deliberate counterpath challenge, all load-bearing facts have primary anchors, decision-critical unknowns are `None`, and any requested durable artifact is exact `VALID`.
- `PARTIAL` — useful attributable evidence exists but one or more unresolved unknowns could materially change the investigation answer or later decision.
- `BLOCKED` — target identity, required read access, required read-only runtime/readback, or safe evidence attribution prevents a valid investigation.

`COMPLETE` does not mean the repository has no defects, that every file was examined, or that a later IIS plan should adopt any planning-relevance candidate.

Return exactly one terminal `REPOSITORY INVESTIGATION RESULT` as defined in the reference. Stop after the result. Do not automatically start IIS, Adaptive Planning, implementation, remediation, or verification.
