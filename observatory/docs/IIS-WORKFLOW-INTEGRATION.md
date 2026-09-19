# IIS Workflow Integration

Observatory is a deterministic read-only projection for the Thesis → Scope → Plan path. It reads repository-local `docs/planning/work/<slug>/SCOPE.md` using `Schema: iis-scope/v2` and displays authored fixed-source refs without pretending to perform trusted admission.

```bash
iis-observatory scan /absolute/project/path --format json
iis-observatory doctor /absolute/project/path
```

The integration boundary is deliberately narrow:

- The scanner reads Markdown planning artifacts, v2 source refs, available live projection files and optional Git history; it writes no planning authority.
- `overview`, `scan`, `doctor` and `history` are read-only. `snapshot --write` writes only derived `docs/planning/observatory/**`.
- `scope.status` is `draft`, `ready`, `done` or `superseded`.
- `ready` is not role admission. Product Thesis closure and fixed-source resolution belong to `iis_artifacts.admission` under the trusted host.
- Existing Scope Shaping/Increment/Spec/Ticket artifacts are read-only legacy history; no automatic migration or old Matt/Ticket pointer is emitted.
- `next_work.leaf` is a read-only pointer, never authorization to execute.
- Optional Transition Authority is displayed only when authored; it does not infer activation.
- Structural inconsistency or duplicate active Scope is reported rather than guessed around.

For a portfolio view:

```bash
iis-observatory overview /home/user01/project --format json
iis-observatory overview /home/user01/project --format markdown
```

A future Web UI should consume this JSON instead of implementing independent Scope-selection or admission rules. Durable Observatory snapshots remain derived read models.
