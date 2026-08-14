# IIS Planning Skills

IIS is the planning layer that turns user intent into approved product authority and a validated Ready Ticket Set. IIS ends at Ready Tickets. It does not implement Tickets, independently verify them, orchestrate delivery agents, or declare product completion.

## Components

- `scope-shaper/`: initiative-scale scope investigation and bounded Work Package selection.
- `scope-investigation-runner/`: read-only planning investigation used only by Scope Shaper.
- `behavior-design-lead/`: canonical Behavior authority design performed inside planning.
- `matt/`: bounded product/Behavior/UI planning, optional explicit adversarial consensus, approved Spec creation, and reviewed Ready Ticket decomposition.
- `planning-workspace/`: project-local planning workspace support.
- `iis-workflow/`: canonical planning-only entry router. It routes Scope Shaper, Ask Matt, To Spec, and To Tickets, then stops at the validated Ready Ticket Set.
- `repo-snapshot/`: independent Git working-tree snapshot skill.

## Planning boundary

The canonical flow is:

```text
Scope Shaper
  -> Ask Matt
  -> Behavior/UI authority
  -> optional explicit adversarial consensus
  -> approved Spec
  -> To Tickets
  -> validated Ready Ticket Set
  -> IIS ends
```

Ticket Verification flows use current positional `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` so observable delivery obligations remain traceable to their parent outcome and semantic authorities without persistent IDs or a trace database.

Ready Tickets are the interface to delivery. A separate delivery layer may later implement and verify a Ticket, but that layer is outside IIS and is not routed, scheduled, or supervised by this repository.

IIS does not use a controller database, persistent Goal state, implementation roster, verification roster, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL.
