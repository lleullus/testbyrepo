# Durable `project-state.json` Schema

`project-state.json` is a repository-relative, derived read model written by `iis-observatory snapshot --write`. It is not canonical Scope, Thesis, Transition, Plan, implementation, admission, or verification authority.

Current snapshot schema: `2.0` (independent of live scan JSON `schema_version: "3.0"`).

## Top-level shape

```json
{
  "schemaVersion": "2.0",
  "projection": {},
  "project": {},
  "planning": {},
  "progress": [],
  "adaptiveProvenance": {}
}
```

## `planning`

The planning projection includes:

- `stage`, `health`, and `nextWork`;
- `authorityMode`: `direct-scope`, `legacy-history`, or `none`;
- current Scope path/status and authored Outcome/Acceptance;
- `scope.boundThesis` and optional `scope.transitionAuthority` as executor-owned `{snapshot,path}` refs;
- required-outcome text derived from an available live projection only; it is not a closure or runtime verdict;
- direct Scope history plus read-only legacy history;
- issues.

Observatory validates the v2 reference shape but does not claim fixed-source currentness or Product Thesis closure. Those belong to common host admission.

## `projection`

Contains projection metadata only:

- `authority: derived-read-only`;
- `generatedBy`, `generatedAt`;
- `freshness: current-at-generation`;
- `consistency: consistent` for accepted writes;
- `inputs`: repository-relative source paths and the actual stored input content used for direct freshness comparison;
- informational generation-time Git metadata;
- snapshot filenames.

There is no IIS content digest, checksum, or aggregate fingerprint. `CURRENT` means the stored projection inputs directly equal the currently observed input originals and the rendered Markdown equals the JSON projection.

## `progress`

Progress entries are typed measurements. A Ticket ratio is emitted only when the current projection actually has Tickets. Presentation bars never affect health, admission or next-work routing.

## `adaptiveProvenance`

Existing Adaptive Mandate/Trace files may be recorded as provenance. `activationInference` remains `not-performed`: a recorded status does not activate an adaptive mode or Transition.
