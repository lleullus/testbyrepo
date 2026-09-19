# IIS Observatory State Contract

## Authority

IIS Observatory is a read-only projection. The repository-local direct Scope is:

```text
docs/planning/work/<slug>/SCOPE.md
```

The artifact must declare `Schema: iis-scope/v2`, the canonical `Project-Root`, one or more executor-owned `Product Authority` refs, `Outcome`, `Acceptance`, and `Status: draft|ready|done|superseded`. Optional `Transition Authority` uses the same `{snapshot,path}` ref shape. File/ref presence never activates a mandate or proves admission.

Observatory never creates the trusted Product Thesis lifecycle store, role admission credential, delivery roster, attempt history, or completion database. `snapshot --write` persists only the derived read model under `docs/planning/observatory/**`.

## Current Scope selection

1. Scan only canonical `docs/planning/work/*/SCOPE.md` files as direct Scope candidates.
2. `draft` and `ready` are active. Exactly one active Scope is required.
3. Multiple active Scopes produce `IIS502 / INCONSISTENT`; Observatory does not choose among them.
4. If no active Scope exists, the newest `done` Scope is current read-only history.
5. If only `superseded` Scopes remain, report `STALE` and transition required; do not resume or create a replacement.

A direct Scope is not inferred from a Work Package, Increment, Spec, Ticket, filename heading, or latest mtime. Legacy artifacts are retained separately as history.

## Bound source projection

For the selected direct Scope, Observatory validates source-ref structure and shows the referenced snapshot/path. It does not resolve the trusted external store and does not claim that a live file proves the fixed source is current.

- Product refs must name Product Thesis relative paths.
- Optional Transition refs use the same fixed-ref form.
- malformed or duplicated refs are consistency errors.
- `ready` and `done` Scopes cannot retain non-`None` Open Decisions.
- Product Thesis closure and downstream eligibility are checked only by common host admission.

When a live file exists at a referenced relative path, Observatory may read it to display named requirements. That live view is a projection input, not a substitute for the executor-owned fixed original.

## Required outcomes

Observatory displays named requirements with `status: unassessed`. Text appearing in Scope Outcome/Acceptance is not evidence of fulfillment. Whole-request completion requires attributable completion evidence outside this projection.

## Next-work precedence

1. Structural/source-ref error → `consistency_check / INCONSISTENT`.
2. Active Scope `draft` → `scope_shaper`.
3. Active Scope `ready` → no exact delivery stage established. Common admission is still required before a downstream role starts.
4. Current Scope `done` with unassessed named outcomes → Scope Shaper for current-state reconciliation.
5. Current Scope `done` with no remaining observed outcome → `none`.
6. Unfinished legacy planning or superseded-only direct history → transition assessment.
7. Empty planning root → `scope_shaper / NEEDS_SCOPE`.

Every next-work value is read-only.

## Legacy history

Existing scope-shaping, Work Package, Increment, Spec and Ticket files remain visible as history. They are not automatically upgraded to v2 admission.

## JSON stability

Live scan JSON uses `schema_version: "3.0"`. Snapshot schema is independently `2.0`. Consumers should ignore unknown fields and treat enum strings as case-sensitive.
