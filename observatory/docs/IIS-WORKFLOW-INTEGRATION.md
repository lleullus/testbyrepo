# IIS Workflow Integration

Observatory is the shared deterministic read model for the unified Thesis → Scope → Plan path. It reads the exact repository-local `docs/planning/work/<slug>/SCOPE.md` (`Schema: iis-scope/v1`) and bound source bytes:

```bash
iis-observatory scan /absolute/project/path --format json
iis-observatory doctor /absolute/project/path
```

The integration boundary is deliberately narrow:

- The scanner reads Markdown planning artifacts, bound Thesis/Transition sources and optional Git history; it writes no planning authority.
- `overview`, `scan`, `doctor` and `history` are read-only. `snapshot --write` may write only derived `docs/planning/observatory/**` files.
- `scope.status` is `draft`, `ready`, `done` or `superseded`; the current Scope is never inferred from legacy Increment/Spec/Ticket metadata.
- `draft` points to Scope Shaper. `ready` does not establish the next delivery stage without current method/target/terminal evidence. A done Scope with unassessed named requirements points to current-state reconciliation, not automatic further construction or whole-result completion.
- Existing Scope Shaping/Increment/Spec/Ticket artifacts are preserved under `legacy.history`. Unfinished ones are `legacy.transition_required`; no automatic migration or old Matt/Ticket pointer is emitted.
- `next_work.leaf` is always a read-only pointer, not authorization to execute Plan, Scope Shaper, implementation, verification, transition, or delivery.
- Optional `Transition Authority` is validated and displayed only when authored in the current Scope. It does not infer mandate activation or create a transition mode.
- `INCONSISTENT` (including stale bound source or duplicate active Scope) is reported rather than guessed around.

For a portfolio view:

```bash
iis-observatory overview /home/user01/project --format json
iis-observatory overview /home/user01/project --format markdown
```

A future Web UI should consume this JSON instead of implementing independent Scope-selection rules. Durable snapshots remain derived read models and never select among future Scopes or execute the reported pointer.
