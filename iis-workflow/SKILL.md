---
name: iis-workflow
description: Canonical planning-only router for IIS scope shaping, Matt planning, Spec creation, and Ready Ticket production.
---

# IIS Planning Router

## Purpose

IIS is a planning system. Route the user's planning request through Scope Shaper, Ask Matt, To Spec, and To Tickets without extending IIS into implementation, verification, delivery orchestration, or product-completion control.

The IIS terminal product is one approved Spec and its reviewed Ready Ticket Set. Ready Tickets are the delivery interface. IIS does not implement them, verify them, schedule delivery agents, or declare the product complete.

Apply explicit planning-leaf requests before broader IIS inference.

## Planning Intent

Preserve the user's current product intent, Scope decisions, and any explicit instruction to run adversarial consensus for the current planning unit. Preserve an exact `Adversarial Planning Challenger` binding only when the user explicitly designates it. A Challenger designation alone does not activate the gate, and an instruction to run the gate without an exact counterpart does not authorize IIS to choose one.

Pass an explicit user instruction to run adversarial consensus to Ask Matt even when its Challenger binding is still missing, so the required binding boundary is not silently dropped. Pass the exact Challenger binding only when both the activation instruction and exact binding are current. The Challenger is a planning-only advisory counterpart; do not repurpose that binding for delivery work.

IIS carries no implementation-agent roster, verifier roster, scheduling order, concurrency setting, consumption ledger, delivery state, or product-completion state.

## Route By Planning Unit

### Scope Shaping

An explicit Scope Shaper request or an initiative-scale IIS request routes to:

`/home/user01/project/iis-skills/scope-shaper/SKILL.md`

Scope Shaper has entry precedence for initiative-scale work. Respect its selected Work Package and planning boundary before entering bounded Matt planning.

### Ask Matt

An explicit Ask Matt request or an ordinary bounded IIS planning request routes to:

`/home/user01/project/iis-skills/matt/skills/ask-matt/SKILL.md`

Ask Matt owns product, Behavior, UI, completion-contract, and verification-feasibility planning. Planning remains declarative: current repository facts inform the contract but do not become implementation authority by themselves.

When adversarial consensus is explicitly active, Ask Matt uses:

`/home/user01/project/iis-skills/matt/skills/adversarial-consensus/SKILL.md`

Ordinary planning never suggests, infers, defaults to, or auto-enables that gate.

### To Spec

An explicit To Spec request routes to:

`/home/user01/project/iis-skills/matt/skills/to-spec/SKILL.md`

An explicit To Spec request does not withdraw, satisfy, or bypass an active adversarial-consensus instruction. When routing, pass the current adversarial-consensus activation or withdrawal fact to To Spec together with the exact current Challenger binding for To Spec's direct admission gate.

To Spec serializes the approved shared understanding into the canonical approved Spec. It does not start delivery.

### To Tickets

An explicit To Tickets request routes to:

`/home/user01/project/iis-skills/matt/skills/to-tickets/SKILL.md`

To Tickets projects the approved Spec into the smallest reviewed implementation Tickets, validates them, and stops when the complete Ready Ticket Set is available.

## IIS Terminal Boundary

IIS planning is complete when all required planning authority is approved and To Tickets returns the validated complete Ready Ticket Set.

Report:

```text
IIS PLANNING COMPLETE
Spec: <exact approved Spec>
Ready Tickets:
- <exact ready Ticket path>
Validation: PASS
```

Do not automatically continue into implementation or verification. Do not reinterpret a request naming one exact Ticket as permission to complete sibling Tickets or the whole Spec.

## Delivery Boundary

Implementation and verification are outside IIS. A Ready Ticket may later be consumed by a separate delivery layer. IIS does not route or supervise that layer and does not retain execution intent on its behalf.

If the current request is explicitly to implement or verify an already-existing exact Ready Ticket rather than to plan it, classify the request as outside IIS Planning instead of silently converting it into a planning or whole-Spec workflow.

If the user requests whole-Spec delivery after planning, the caller may deliver Ready Tickets using a separate delivery mechanism. That caller is not IIS, and IIS does not define its scheduling, retries, completion state, or final orchestration.

## Planning Decision Boundary

Ask the user only for unresolved product, Scope, Behavior, UI, completion-contract, or other planning-authority decisions owned by the current planning leaf. Do not ask the user to choose implementation files, libraries, endpoints, internal sequencing, workers, verifier topology, or delivery mechanics.

## Safety And Non-Goals

IIS Planning does not create a controller runtime, workflow database, delivery scheduler, implementation roster, verification roster, persistent Goal state, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL. It does not mutate product source as part of planning and does not claim implementation or verification completion.
