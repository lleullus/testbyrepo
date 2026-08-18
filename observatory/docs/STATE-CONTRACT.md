# IIS Observatory State Contract

## Authority

IIS Observatory is a read-only projection. It does not own or mutate planning state. The source of truth remains the project-local Markdown artifacts under:

```text
docs/planning/scope-shaping/**
docs/planning/work/**
```

Every state calculation rescans those files. No controller database, workflow ledger, delivery roster, attempt history, or completion database is created. `snapshot --write` may persist only the derived read model under `docs/planning/observatory/**`; that directory and `docs/planning/adaptive/**` are excluded from canonical artifact selection.

## Selection precedence

1. Prefer the newest canonical `SCOPE-SHAPING-RESULT.md`, favoring `confirmed`/`approved` status.
2. Prefer an explicit `Selected-Increment` or `Current-Increment` field.
3. Otherwise use a unique Scope reference to an Increment, favoring `ready-for-matt`.
4. Otherwise use the unique `ready-for-matt` Increment inside the selected Scope lineage.
5. Otherwise use a unique Spec `Source-Increment`.
6. Direct work with `Source-Increment: None` is associated by `Suggested-Work-Slug` or the unique current `docs/planning/work/<slug>` area.

Increment and Work Package identifiers are interpreted within the selected Scope lineage. Sibling or historical Scope lineages may legitimately reuse identifiers such as `INC-001` and retain their own historical `ready-for-matt` artifacts without making the current lineage inconsistent. Multiple `ready-for-matt` Increments inside the selected current lineage are reported as inconsistent because IIS admits only one current Scope-shaped handoff there.

## Next-work precedence

The first matching rule wins:

1. Artifact error → `consistency_check` / `INCONSISTENT`.
2. Blocked current Ticket → `ticket_unblock` / `BLOCKED`.
3. Ready current Ticket → `ticket_implement` / `READY`.
4. Draft or non-terminal current Ticket → `ticket_review` / `PLANNING`.
5. All current Tickets `done` and the current Scope has authored `Outcome Horizon > Expansion` Work Packages → current unit stays `COMPLETE`, preserve every authored Expansion candidate in Scope order, set `Next Increment` to not yet shaped, and report `Scope Shaper` as the next leaf.
6. All current Tickets `done` with no authored Expansion candidate → current unit `COMPLETE` and no next unit established. `Deferred` Work Packages remain visible but are not promoted to next-work candidates.
7. Approved Spec without Tickets → `To Tickets` / `PLANNING`.
8. Non-approved Spec → `To Spec` / `PLANNING`.
9. Current Increment without Spec → `Ask Matt` / `PLANNING`.
10. Scope or Work Package without an admitted Increment → `Scope Shaper` / `NEEDS_SCOPE`.

Outcome-horizon classification is read from the authored `Outcome Horizon` section. Observatory never uses WP numbering to infer ordering or promotion. A reported delivery or planning action is a pointer only; Observatory does not perform it.

Authored statuses such as `scoped`, `ready-for-matt`, and `approved` remain properties of their planning artifacts. The detailed text renderer may additionally show `Derived Delivery State: READY|BLOCKED|COMPLETE` when current Tickets establish a delivery state; this derived label does not rewrite or supersede artifact status.

## Recognized statuses

Tickets use the canonical statuses:

```text
draft
ready
blocked
done
```

Common terminal aliases such as `complete`, `completed`, `closed`, and `verified` normalize to `done`. Unknown current Ticket statuses are errors so the dashboard does not silently invent lifecycle semantics.

## Health values

| Health | Meaning |
|---|---|
| `READY` | A current Ready Ticket can be consumed by delivery outside IIS. |
| `BLOCKED` | A current Ticket is blocked. |
| `PLANNING` | Ask Matt, To Spec, To Tickets, or Ticket readiness work remains. |
| `NEEDS_SCOPE` | Scope Shaper must establish the next Increment. |
| `INCONSISTENT` | Required artifacts disagree or required state is missing. |
| `COMPLETE` | The current selected delivery unit's associated Tickets are all `done`. Authored follow-up Scope candidates may still exist and can point to `Scope Shaper`. |
| `STALE` | Only a superseded lineage can be identified. |
| `NO_IIS` | The repository has no `docs/planning` directory. |

## Durable snapshot boundary

`docs/planning/observatory/PROJECT-OVERVIEW.md` and `project-state.json` are generated projections only. Snapshot freshness uses a content fingerprint of current canonical state inputs plus displayed Adaptive provenance, never Git HEAD alone. The snapshot output directory is excluded from its own fingerprint. A stored Adaptive Mandate status is provenance and must not be interpreted as current Adaptive-mode activation.

Built-in progress visualization is derived only from typed exact-ratio measurements. The visual bar never changes `Health`, current-unit selection, or `next_work` precedence, and the exact numerator/denominator/percent remains the authoritative measurement representation inside the projection.

## JSON stability

JSON output contains `schema_version: "1.0"`. Consumers should ignore unknown fields and treat enum strings as case-sensitive. A future incompatible change will increment the major schema version.
