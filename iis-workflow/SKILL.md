---
name: iis-workflow
description: Canonical planning-only router for IIS next-increment admission, Scope Shaping, Matt planning, Spec creation, and Ready Ticket production.
---

# IIS Planning Router

## Purpose

IIS is a planning system. Route the user's planning request through next-increment admission, Scope Shaper, Ask Matt, To Spec, and To Tickets without extending IIS into implementation, verification, delivery orchestration, or product-completion control.

A generic request to "start the IIS workflow" is not an alias for Ask Matt. Before routing an ordinary IIS request, decide whether the request already names one current, durable, observable product increment or whether Scope Shaper must first choose that increment from the user's larger intent and the actual current product state.

The IIS terminal product for one admitted increment is one approved Spec and its reviewed Ready Ticket Set. Ready Tickets are the delivery interface. IIS does not implement them, verify them, schedule delivery agents, or declare the product complete.

Apply explicit planning-leaf requests before broader IIS inference.

## Planning Intent

Preserve the user's current product intent, Scope decisions, and any explicit instruction to run adversarial consensus for the current planning unit. Preserve an exact `Adversarial Planning Challenger` binding only when the user explicitly designates it. A Challenger designation alone does not activate the gate, and an instruction to run the gate without an exact counterpart does not authorize IIS to choose one.

Pass an explicit user instruction to run adversarial consensus to Ask Matt even when its Challenger binding is still missing, so the required binding boundary is not silently dropped. Pass the exact Challenger binding only when both the activation instruction and exact binding are current. The Challenger is a planning-only advisory counterpart; do not repurpose that binding for delivery work.

IIS carries no implementation-agent roster, verifier roster, scheduling order, concurrency setting, consumption ledger, delivery state, or product-completion state.

## Route By Planning Unit

### Next-Increment Admission

Apply explicit planning-leaf requests first. An explicit Scope Shaper request routes to Scope Shaper. An explicit Ask Matt request enters Ask Matt's own admission preflight rather than silently changing the requested leaf. Explicit To Spec and To Tickets requests keep their leaf-specific gates below.

If the user explicitly asks IIS to inspect the current planning state, asks what remains, asks what the next Ticket/Increment/Work Package is, or otherwise asks only for the next planning pointer, run the Current Planning State Check below and stop. A state-check request is read-only and never authorizes execution of the reported next planning leaf.

For an ordinary IIS workflow request that is not a state check, route directly to Ask Matt only when the request is already `next-increment-ready`: the current product baseline is identifiable; the request describes one durable observable state change with an actor or operator, trigger or inspection target, result, and authoritative readback; it does not bundle foundation, intermediate, and mature forms of the capability; no material product-capability ordering or foundation choice remains; and no independently acceptable sibling outcome still needs split/merge judgment.

Route to Scope Shaper when any of those conditions is not established. New-product construction, whole-system or whole-platform requests, new core domain/lifecycle/ownership foundations, requests spanning multiple product maturity stages, and coherent outcomes that still require choosing what should exist first are Scope-Shaping work even when they can be described as one broad outcome. Technical depth, file count, or implementation layers alone do not decide this gate.

### Current Planning State Check

This is a read-only status inspection over existing IIS artifacts. It does not create a workflow ledger, inspect product runtime, re-run Scope Shaper reasoning, or execute the next planning leaf.

When this check applies:

1. Inspect the relevant project-local `docs/planning/scope-shaping/**` and `docs/planning/work/**` artifacts broadly enough to reconstruct the current planning board: Work Packages, Increments, each Increment's work slug/Spec, and Ticket statuses.
2. Prefer the latest confirmed `SCOPE-SHAPING-RESULT.md` as current Scope navigation. Use `Source-Increment` and `Suggested-Work-Slug` links to associate Specs and Tickets with their Increment. Do not spend time choosing among historical lineages when the current Scope already identifies the current selected Increment.
3. Treat `Status: done` Tickets as completed delivery units and omit them from the remaining-work list. Treat `ready`, `blocked`, or `draft` Tickets in the current Increment as remaining work and report them directly.
4. A prior Increment with `Status: superseded` is historical planning state. A stale non-`done` Ticket under that superseded Increment does not block reporting the current planning position; mention the inconsistency only when it materially affects interpretation.
5. If the current selected Increment has any non-`done` Ticket, report that Ticket or Ticket set as the immediate remaining work. Do not select a worker or execute delivery.
6. If the current selected Increment's Tickets are all `done`, report the next planning pointer from already-authored Scope artifacts only:
   - if the current Scope already selects a later `ready-for-matt` Increment, report that exact Increment and `Ask Matt` as the next leaf;
   - otherwise, if the Scope's Work Package decomposition or provisional horizon names a next Work Package/outcome area, report that Work Package as the next candidate area and `Scope Shaper` as the leaf that would create the next Increment;
   - otherwise report that no next planning unit has yet been authored.
7. Artifact inconsistencies such as a referenced missing file may be reported concisely, but this status check does not repair them, validate the whole product, or start a shaping pass. Do not run repository tests, browser/runtime checks, or canonical planning validators solely for this status check.
8. After reporting the state and next pointer, **STOP**. Do not invoke or execute Scope Shaper, Ask Matt, To Spec, To Tickets, implementation, verification, runtime inspection, candidate comparison, or user-confirmation flows in the same request.

Report compactly:

```text
IIS CURRENT PLANNING STATE
Current Scope: <scope/revision or None>
Completed: <completed WP/INC/Ticket summary>
Remaining: <non-done current Tickets or None>
Next Work Package: <WP-NNN / name / None established>
Next Increment: <INC-NNN / not yet shaped>
Next leaf: <delivery outside IIS | Scope Shaper | Ask Matt | none established>
STOP
```

### Scope Shaping

An explicit Scope Shaper request or any IIS request that is not yet next-increment-ready routes to:

`/home/user01/project/iis-skills/scope-shaper/SKILL.md`

Scope Shaper has entry precedence whenever the next durable construction increment still has to be selected. Respect its confirmed planning landscape and exact selected Increment before entering Matt planning.

### Ask Matt

An explicit Ask Matt request or an ordinary IIS request that already passes next-increment admission routes to:

`/home/user01/project/iis-skills/matt/skills/ask-matt/SKILL.md`

Ask Matt owns product, Behavior, UI, completion-contract, and verification-feasibility planning for one admitted increment. Ask Matt must return to Scope Shaper when its preflight finds that the requested unit still contains unresolved construction-stage, foundation, split/merge, or product-capability-ordering decisions. Planning remains declarative: current repository facts inform the contract but do not become implementation authority by themselves.

When adversarial consensus is explicitly active, Ask Matt uses:

`/home/user01/project/iis-skills/matt/skills/adversarial-consensus/SKILL.md`

Ordinary planning never suggests, infers, defaults to, or auto-enables that gate.

### To Spec

An explicit To Spec request routes to:

`/home/user01/project/iis-skills/matt/skills/to-spec/SKILL.md`

An explicit To Spec request does not withdraw, satisfy, or bypass an active adversarial-consensus instruction. When routing, pass the current adversarial-consensus activation or withdrawal fact to To Spec together with the exact current Challenger binding for To Spec's direct admission gate.

To Spec serializes the approved shared understanding for the current increment into the canonical approved Spec. It does not start delivery or authorize a later increment.

### To Tickets

An explicit To Tickets request routes to:

`/home/user01/project/iis-skills/matt/skills/to-tickets/SKILL.md`

To Tickets projects the approved Spec into the smallest reviewed implementation Tickets, validates them, and stops when the complete Ready Ticket Set for the current increment is available.

## IIS Terminal Boundary

IIS planning for the current increment is complete when all required planning authority is approved and To Tickets returns the validated complete Ready Ticket Set for that increment.

Report:

```text
IIS CURRENT INCREMENT PLANNING COMPLETE
Spec: <exact approved Spec>
Ready Tickets:
- <exact ready Ticket path>
Validation: PASS
```

Do not automatically continue into implementation, verification, or planning of a later increment. Do not reinterpret a request naming one exact Ticket as permission to complete sibling Tickets or the whole Spec. After delivery of a Scope-shaped increment, a later planning cycle must inspect the actual resulting product state rather than treating a provisional future construction horizon as already approved scope.

## Delivery Boundary

Implementation and verification are outside IIS. A Ready Ticket may later be consumed by a separate delivery layer. IIS does not route or supervise that layer and does not retain execution intent on its behalf.

If the current request is explicitly to implement or verify an already-existing exact Ready Ticket rather than to plan it, classify the request as outside IIS Planning instead of silently converting it into a planning or whole-Spec workflow.

If the user requests whole-Spec delivery after planning, the caller may deliver Ready Tickets using a separate delivery mechanism. That caller is not IIS, and IIS does not define its scheduling, retries, completion state, or final orchestration.

## Planning Decision Boundary

Ask the user only for unresolved product, Scope, Behavior, UI, completion-contract, or other planning-authority decisions owned by the current planning leaf. Do not ask the user to choose implementation files, libraries, endpoints, internal sequencing, workers, verifier topology, or delivery mechanics.

## Safety And Non-Goals

IIS Planning does not create a controller runtime, workflow database, delivery scheduler, implementation roster, verification roster, persistent Goal state, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL. It does not mutate product source as part of planning and does not claim implementation or verification completion.
