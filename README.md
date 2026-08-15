# IIS Planning Skills

IIS is the planning layer that turns user intent into approved product authority and a validated Ready Ticket Set for one current construction Increment. IIS ends at Ready Tickets. It does not implement Tickets, independently verify them, orchestrate delivery agents, or declare product completion.

## Components

- `scope-shaper/`: connected outcome-landscape investigation plus selection of exactly one durable next product construction Increment from the actual current product state.
- `scope-investigation-runner/`: optional read-only evidence investigation used only when the user explicitly authorizes Runner use and supplies the exact roster/concurrency binding.
- `behavior-design-lead/`: canonical Behavior authority design performed inside planning.
- `matt/`: one-Increment product/Behavior/UI planning, optional explicit adversarial consensus, approved Spec creation, and reviewed Ready Ticket decomposition.
- `planning-workspace/`: project-local planning workspace support.
- `iis-workflow/`: canonical planning-only entry router. A generic IIS request goes to Ask Matt only when it is already next-increment-ready; otherwise Scope Shaper first selects the Increment.
- `repo-snapshot/`: independent Git working-tree snapshot skill.

## Planning boundary

The canonical Scope-shaped flow is:

```text
Long-term intent + actual current product state
  -> Scope Shaper
  -> horizontal Work Package decomposition when needed
  -> exactly one ready-for-matt INC-NNN
  -> Ask Matt
  -> Behavior/UI authority
  -> optional explicit adversarial consensus
  -> approved Spec for that Increment
  -> To Tickets
  -> validated Ready Ticket Set for that Increment
  -> IIS ends
```

A Work Package is a horizontal outcome boundary with `Status: scoped`; it is not an Ask Matt handoff. Future construction can be described provisionally, but only the current selected `INC-NNN.md` is `ready-for-matt`. Every confirmed shaping pass has an immutable `revisions/SHAPE-NNN.md` snapshot, and its Increment keeps that exact revision as historical planning authority even after the current `SCOPE-SHAPING-RESULT.md` advances. After delivery, a later Scope Shaping cycle inspects the actual resulting product state before selecting another Increment; prior ready Increments become `superseded` so only one Scope-shaped handoff remains admissible.

Construction candidates use a small auditable structure: outcome area, current/target state, actor, trigger or inspection target, observable result, authoritative readback, durable foundation, future policy avoided, disposition, and reason. Exactly one candidate is selected and must close structurally into the Selected Increment. The validator checks that closure only; it does not score product judgment or decide which candidate is substantively best.

A Scope-shaped Spec records `Source-Increment` and To Spec revalidates that Increment immediately before writing. Direct next-increment-ready Ask Matt work records `Source-Increment: None`. The trace does not import deferred or provisional future scope into the Spec.

A direct ordinary request may enter Ask Matt without Scope Shaper only when the current baseline and one durable observable current-to-next state transition are already clear and no construction-stage, foundation, product-capability-ordering, or split/merge decision remains. A genuinely unrooted greenfield request may be shaped from the brief before a repository exists, but durable artifacts and Ask Matt admission wait for one exact project root; IIS does not bootstrap product source as a planning side effect.

Legacy `ready-for-matt` Work Packages are not directly re-admitted. Scope Shaper treats them as preserved historical planning context, re-inspects the actual current product state, and performs semantic migration into the current one-Increment contract. This avoids restoring the old bypass while preserving prior approved evidence.

Ticket Verification flows use current positional `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` so observable delivery obligations remain traceable to their parent outcome and semantic authorities without persistent IDs or a trace database.

Ready Tickets are the interface to delivery. A separate delivery layer may later implement and verify a Ticket, but that layer is outside IIS and is not routed, scheduled, or supervised by this repository.

IIS does not use a controller database, persistent Goal state, implementation roster, verification roster, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL.
