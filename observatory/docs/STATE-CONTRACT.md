# IIS Observatory State Contract

## Authority

IIS Observatory is a read-only projection. The current authority is the repository-local direct Scope:

```text
docs/planning/work/<slug>/SCOPE.md
```

The artifact must declare `Schema: iis-scope/v1`, the canonical `Project-Root`, one or more exact `Product Authority` Thesis sources, `Outcome`, `Acceptance`, and `Status: draft|ready|done|superseded`. An optional `Transition Authority` section binds an applicable project-local approved transition source by path and SHA-256. File presence never activates a mandate or baseline.

Observatory never creates a state database, workflow ledger, delivery roster, attempt history, or completion database. `snapshot --write` may persist only the derived read model under `docs/planning/observatory/**`.

## Current Scope selection

1. Scan only canonical `docs/planning/work/*/SCOPE.md` files as direct Scope candidates.
2. `draft` and `ready` are active. Exactly one active Scope is required.
3. Multiple active Scopes produce `IIS502` / `INCONSISTENT`; Observatory does not choose among them.
4. If no active Scope exists, the newest `done` Scope is current read-only history.
5. If only `superseded` Scopes remain, report `STALE` and `transition required`; do not resume or create a replacement.

A direct Scope is not inferred from a Work Package, Increment, Spec, Ticket, filename heading, or latest mtime. Legacy artifacts are retained separately as history.

## Bound source checks

For the selected direct Scope:

- `Product Authority` paths must be project-local files under `docs/planning/product-thesis/**`; their full UTF-8 SHA-256 must match.
- `Transition Authority`, when present, must be project-local regular files and its digest must match.
- Missing, malformed, duplicated, self-referential, out-of-root, or changed sources are consistency errors.
- `ready` and `done` Scopes cannot retain non-`None` `Open Decisions`.

A changed Thesis is stale bound authority, not a reason to silently read the latest Thesis. A changed transition source is likewise reported as stale; no transition is activated.

## Required outcomes

Observatory displays named requirements from the bound Thesis with `status: unassessed`. Text appearing in Scope Outcome/Acceptance, including an exclusion, is not evidence of fulfillment. The `remaining` projection retains these unassessed items; it does not claim that each is actually unfinished. Whole-request completion requires attributable completion evidence outside this text-only projection.

## Next-work precedence

The first matching rule wins:

1. Structural/authority error → `consistency_check` / `INCONSISTENT`.
2. Active direct Scope `draft` → `scope_shaper`, leaf `Scope Shaper`.
3. Active direct Scope `ready` → no exact delivery stage established: ready persists through planning, implementation and pending verification; inspect current method/target/terminal evidence rather than automatically re-planning.
4. Current direct Scope `done` with unassessed named outcomes → Scope Shaper for current-state reconciliation, not automatic further construction or whole-result completion.
5. Current direct Scope `done` with no remaining observed outcome → `none`.
6. Unfinished legacy planning or only superseded direct history → transition assessment. Completed legacy history alone → no migration or execution pointer.
7. Empty planning root → `scope_shaper` / `NEEDS_SCOPE`.

Every next-work value is a read-only pointer. It never executes Plan, Scope Shaper, implementation, verification, transition, or delivery.

## Legacy history

Existing `scope-shaping/**`, Work Package, Increment, Spec, and Ticket files remain visible under `legacy.history` / `Legacy History`. Unfinished legacy items are listed under `transition_required`; Observatory does not auto-migrate them and does not propose their old `ready-for-matt`, Ask Matt, To Spec, To Tickets, or Ticket implementation routes as current work.

## JSON stability

Live scan JSON uses `schema_version: "2.0"` and direct fields (`authority_mode`, `scope`, `required_outcomes`, `legacy`, `next_work`). Snapshot schema is independent. Consumers should ignore unknown fields and treat enum strings as case-sensitive.
