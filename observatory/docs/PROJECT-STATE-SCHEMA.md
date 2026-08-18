# Durable `project-state.json` Schema

`project-state.json` is a repository-relative, derived read model written by `iis-observatory snapshot --write`. Its snapshot schema version is independent from the live `scan --format json` schema.

Current snapshot schema: `1.0`.

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

## `projection`

Contains projection metadata only:

- `authority`: exact `derived-read-only`
- `generatedBy`: generator name/version
- `generatedAt`: generation timestamp
- `sourceFingerprint`: deterministic content fingerprint
- `sourceFingerprintAlgorithm`
- `freshness`: `current-at-generation` in newly written files
- `consistency`: `consistent` for accepted writes
- `inputs`: repository-relative source file identities and hashes
- `git`: informational generation-time Git metadata; not freshness authority
- `files`: snapshot filenames and the SHA-256 of `PROJECT-OVERVIEW.md`

No absolute repository root is serialized as canonical snapshot identity.

## `planning`

Contains the same current-state projection used by Observatory:

- `stage`, `health`
- current Scope, Work Package, Increment, Spec and work slug
- Ticket counts/items/completed/remaining
- authored follow-up Work Package candidates and Deferred items
- next-work pointer and leaf
- consistency issues

Artifact references contain repository-relative paths. `scoped`, `ready-for-matt`, `approved`, and Ticket statuses remain authored artifact statuses; derived `health` is separate.

## `progress`

Progress entries are typed measurements. Built-in 0.2.1 output currently provides current Ticket delivery when a denominator exists:

```json
{
  "id": "current-ticket-delivery",
  "label": "Current Ticket delivery",
  "measurement": "exact-ratio",
  "numerator": 3,
  "denominator": 5,
  "percent": 60.0,
  "evidence": [
    "docs/planning/work/example/tickets/TICKET-001.md"
  ]
}
```

The visual bar in `PROJECT-OVERVIEW.md` is derived from this measurement and is not a separate state field.

Future project-specific exact coverage, categorical stage, or estimated-range measurements require an explicit provider/rubric contract. Consumers must not reinterpret one measurement type as another.

## `adaptiveProvenance`

May describe existing Adaptive Mandate/Trace files, their recorded metadata, and whether companion provenance is present. `activationInference` is deliberately `not-performed`.

This object never means the current request is running Adaptive Planning, and it does not override canonical current Scope/Increment/Spec/Ticket navigation.
