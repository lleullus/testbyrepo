---
name: ready-ticket-heuristic-probe
description: "Heuristically probe one implemented IIS Ready Ticket before final verification. Use the exact validated Ticket and current implementation target to discover plausible black-box false-completion paths, minimize material triggers, and hand fresh evidence to the separate verifier. Execution defaults to DIRECT; SUBAGENT probing is supported only when the current user explicitly selects it. This skill never issues AC/Ticket verdicts or marks the Ticket done."
---

# Ready Ticket Heuristic Probe

## Purpose and authority

Probe one implemented, exact IIS Ready Ticket between implementation completion and final verification. The purpose is to discover material product behavior that could make the Ticket look satisfied while a hidden input, state transition, attribution boundary, UI/backend disagreement, partial response, ordering edge, or adjacent runtime path contradicts the approved observable meaning.

The **Heuristic Probe Lead** owns canonical admission, current target binding, Ticket-derived probe frontier selection, safe execution topology, evidence attribution, trigger minimization, fan-in, cleanup, and one terminal `READY TICKET HEURISTIC PROBE RESULT`.

This is an **exploration authority**, not a verification or remediation authority. It does not issue flow `SATISFIED/CONTRADICTED`, AC `PASS/FAIL`, whole-Ticket `VERIFIED/FAILED`, Adaptive defect classifications, planning corrections, source remediation, or Ticket `done` progression.

Before product/runtime work, read [references/probe.md](references/probe.md) in full. Also load the current installed `production-heuristic-probing` skill for the black-box/minimal-trigger investigation method and read the sibling [purpose-first-review](../purpose-first-review/SKILL.md) contract for materiality and anti-bloat discipline. Those methods guide exploration; the validated Ticket and its current parent authorities remain product authority.

## Inputs

Required contract-authority input:

- Ticket: `<exact absolute canonical TICKET-NNN.md path>`

Optional navigation inputs:

- Candidate Probe Target: `None | <current source/config/build/artifact/runtime hint>`
- Implementation Report / Evidence: `None | <navigation/reference only>`
- Additional User Instructions: `<instructions>`

Derive `Status`, `Parent-Spec`, `Project-Root`, Acceptance Criteria, Scope, Non-Goals, Verification flows, Behavior Authorities, UI authority, Blockers and References from the validated Ticket and current canonical parents. Implementation narration and candidate targets never override fresh current observation.

## Execution topology

Top-level execution defaults to `DIRECT`.

- `DIRECT`: current Main acts as Heuristic Probe Lead and performs the admitted probing itself.
- `SUBAGENT`: only when the current user explicitly selects SUBAGENT for this exact probe stage, Main remains Heuristic Probe Lead and may assign admitted probe lanes to delegated workers.
- Never infer or change topology from model capability, task difficulty, cost, lane count or worker availability. Never auto-switch or fall back between `DIRECT` and `SUBAGENT`.

In `SUBAGENT` mode:

1. Derive the material probe frontier before worker assignment.
2. Use a dynamic worker set only for actual admitted lanes; there is no fixed worker count or fixed role roster.
3. Include exact Ticket, Project Root, target identity, one bounded lane, allowed actions/readbacks, cleanup boundary, current user instructions and `Delegated Probe Worker: yes` in each assignment.
4. A delegated probe worker does not delegate again and does not issue verifier verdicts.
5. Parallelize only lanes whose observations and authorized effects are isolated from one another. Serialize lanes that share mutable product/runtime state or whose cleanup/initial state can affect another lane.
6. Worker agreement, majority, voting and confidence averaging are never evidence. Lead fan-in preserves every current material finding supported by attributable evidence.
7. If required child capability is unavailable, return `SUBAGENT CAPABILITY UNAVAILABLE`. Do not silently run DIRECT instead.

## Canonical Ready Ticket gate

Before probing, resolve the current installed `iis-workflow` skill only as the canonical planning-authority locator, follow its current To Tickets route, require the adjacent `validate_ticket.py`, and require exact `VALID` for the exact Ticket.

Normal delivery probing requires exact `Status: ready`. `draft` or `blocked` does not enter probing. `done` is outside the normal pre-verification delivery gate; an explicit diagnostic probe may inspect it but never reopens or rewrites status.

After structural admission, resolve the current Parent Spec, applicable Behavior/UI authorities and exact current implementation target directly. If canonical admission, authority, target attribution or required action authority cannot be established, stop without inventing findings or verdicts.

## Ticket-derived heuristic frontier

Review every authored Verification flow and its applicable conditional boundaries once. A distinct probe lane is admitted only when all of these are established:

1. exact current Ticket/Spec/Behavior/UI contract anchor;
2. concrete plausible false-completion or attribution path;
3. material observable/canonical consequence if that path holds; and
4. current target/readback capable of investigating the path within existing authority.

Record each flow/boundary as `ADMIT_LANE` or `NO_DISTINCT_HEURISTIC_LANE`. Do not create lanes merely for exhaustiveness, generic fuzzing, implementation curiosity, future hardening, unrelated security exploration, worker utilization, or a remote hypothetical.

A Ticket may legitimately yield no distinct heuristic lane. In that case the gate may still finish `Probe Completion: COMPLETE` after the full frontier review, with `Material Findings: None` and no product/runtime perturbation. That means no separate material lane was established, not that hidden defects are impossible.

## Investigation principle

For each admitted lane, use the current `production-heuristic-probing` method to prefer the smallest condition that changes material behavior before constructing a larger test apparatus. Cross UI, modality, auth, caching, network, provider, persistence and state-machine boundaries only where the Ticket-derived lane makes that boundary material and current authority permits the action.

When a suspicious behavior is found, minimize it toward a reproducible trigger and capture direct attributable observation/readback. Stop confidence-only exploration once the lane's material question is decidable or its exact evidence limit is known.

## Target stability and safety

Bind enough current identity to attribute all lane evidence to one implementation target without creating a persistent probe ID or evidence store. Source/config/build/artifact/runtime drift that affects attribution makes prior supportive evidence stale for the changed target.

Credential-bearing, shared/production, payment, messaging, deployment, destructive, irreversible, one-shot or duplicate-sensitive actions require exact existing Ticket/user authority. Lateral investigation never grants permission to bypass access controls, production safeguards or rate/protection boundaries.

A transport/network failure during a mutation-capable probe action does not prove success or failure. Read current authoritative state before considering another action; do not blindly repeat a possibly applied effect.

## Result boundary

The Probe Lead returns exactly one terminal result with:

```text
READY TICKET HEURISTIC PROBE RESULT

Ticket:
Execution Mode: DIRECT | SUBAGENT
Heuristic Probe Lead:
Ticket status before probe:
Probe Target:
Authority Snapshot: <Ticket + Parent Spec + applicable Behavior/UI current identities>
Target Stability:
Heuristic Method: production-heuristic-probing
Probe Frontier Matrix:
Worker Execution / Concurrency:
Material Findings: None | <findings>
Minimal Triggers: None | <finding -> trigger>
Direct Evidence:
Evidence Limits:
Cleanup / Terminal State:
Ticket status after probe: ready (unchanged) | <unchanged diagnostic status>
Verification status: NOT ADJUDICATED BY THIS SKILL
Probe Completion: COMPLETE | PARTIAL | BLOCKED
```

`Probe Completion: COMPLETE` means every admitted lane reached a bounded investigation conclusion or explicit non-finding with required cleanup and target attribution. It does **not** mean the Ticket passes verification. Findings are counterexample/evidence inputs for the separate verifier, not automatic implementation defects or verification verdicts.

Do not automatically invoke implementation, final verification, Adaptive Planning, a new Ticket, or another Increment from this skill. The caller/Outer Main owns the next handoff.
