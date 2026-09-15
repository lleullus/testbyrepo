# Durable `project-state.json` Schema

`project-state.json` is a repository-relative, derived read model written by `iis-observatory snapshot --write`. It is not canonical Scope, Thesis, transition, Plan, implementation, or verification authority.

Current snapshot schema: `1.0` (independent of live scan JSON `schema_version: "2.0"`).

## Top-level shape

```json
{
  "schemaVersion": "1.0",
  "projection": {},
  "project": {},
  "planning": {},
  "progress": [],
  "adaptiveProvenance": {}
}
```

## `planning`

The planning projection includes:

- `stage`, `health`, and `nextWork` (`kind`, `targetId`, `targetPath`, `leaf`, `reason`);
- `authorityMode`: `direct-scope`, `legacy-history`, or `none`;
- `current.scope` as a stable path/status reference and `current.workSlug`;
- `scope.current` with the current `SCOPE.md` path, status, authored Outcome and Acceptance;
- `scope.boundThesis` and optional `scope.transitionAuthority`, each preserving exact path and digest;
- `scope.requiredOutcomes` and `scope.remainingRequiredOutcomes` preserve named source requirements with status `unassessed`; the latter retains unresolved fulfillment assessment, not a proven unfinished-work denominator;
- `scope.active` / `scope.history` for direct Scopes;
- `legacy.history`, `legacy.transitionRequired`, and `legacy.automaticMigration: false`;
- `tickets` and old `followUp` only as an empty/derived compatibility projection when direct Scope is current. Legacy Tickets are not current delivery authority;
- `issues`.

A stale Thesis or Transition Authority source is an issue and prevents an accepted snapshot write.

## `projection`

Contains projection metadata only:

- `authority`: `derived-read-only`;
- `generatedBy`, `generatedAt`;
- `sourceFingerprint`, `sourceFingerprintAlgorithm`;
- `freshness`: `current-at-generation` in newly written files;
- `consistency`: `consistent` for accepted writes;
- `inputs`: repository-relative source file identities and hashes, including bound Thesis/Transition sources;
- informational generation-time `git` metadata;
- snapshot filenames and the Markdown SHA-256.

No absolute repository root is serialized as canonical snapshot identity.

## `progress`

Progress entries are typed measurements. A Ticket ratio is emitted only when the current projection actually has Tickets; direct Scope status is not converted into a Ticket ratio. Presentation bars never affect health or next-work routing.

## `adaptiveProvenance`

Existing Adaptive Mandate/Trace files may be recorded as provenance. `activationInference` remains `not-performed`: a recorded `Status: active` does not activate an adaptive mode or transition baseline.
