# IIS Workflow Integration

Observatory should become the shared deterministic read model beneath human and agent views. Until the router is changed to invoke it directly, use the JSON output as the machine-readable equivalent of a Current Planning State Check:

```bash
iis-observatory scan /absolute/project/path --format json
```

The integration boundary is deliberately narrow:

- The scanner may read planning artifacts and Git history.
- `overview`, `scan`, and `doctor` do not write project planning files. `snapshot --write` is the sole durable projection writer and may write only `docs/planning/observatory/**`; those files are explicitly non-canonical.
- `next_work.leaf` is a pointer, not authorization to execute that leaf.
- When the current delivery unit is complete, `follow_up.next_candidate_work_packages` and `follow_up.deferred_work_packages` preserve the current Scope's authored horizon without choosing among candidates.
- `delivery outside IIS` never selects an implementation agent or verifier.
- An `INCONSISTENT` result should be shown to the user rather than guessed around.

For a portfolio view:

```bash
iis-observatory overview /home/user01/project --format json
```

A future Web UI should consume this JSON instead of implementing independent state-selection rules.

For a durable repository-local projection, use `snapshot --write`. The resulting `PROJECT-OVERVIEW.md` and `project-state.json` are derived read models, not IIS authority. Exact-ratio progress bars are presentation-only; the machine-readable measurement remains the numerator/denominator/percent record. Adaptive Mandate/Trace files may be surfaced as provenance but never activate Adaptive Planning or replace canonical Scope/Increment navigation.
