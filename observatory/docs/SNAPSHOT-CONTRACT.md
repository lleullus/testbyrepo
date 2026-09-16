# Durable Snapshot Contract

## Purpose

`iis-observatory snapshot` persists a human-readable and machine-readable **derived read model** of one repository's current IIS planning state:

```text
docs/planning/observatory/
├── PROJECT-OVERVIEW.md
└── project-state.json
```

These files are not Scope, Work Package, Increment, Spec, Ticket, verification, release, or runtime authority. Observatory never changes canonical IIS state while producing them.

## Commands

```bash
iis-observatory snapshot <repo> --write
iis-observatory snapshot <repo> --check
```

`--check` is the default when neither mode flag is supplied.

Freshness outcomes:

- `CURRENT` — stored source fingerprint equals the current source fingerprint and the Markdown checksum matches the JSON record.
- `STALE` — canonical inputs, displayed Scope/legacy history, or displayed Adaptive provenance changed after generation.
- `MISSING` — neither durable snapshot file exists.
- `INCONSISTENT` — canonical planning is inconsistent, the pair is incomplete/corrupt, or the stored projection contract is invalid.

Exit codes are `0`, `6`, `7`, and `3` respectively.

## Source fingerprint

Freshness is content-based, not Git-HEAD-based. The fingerprint includes the current direct `SCOPE.md`, its bound Thesis sources, optional bound Transition Authority sources, the current work area (including `PLAN.md`), displayed Scope/legacy history files, and displayed Adaptive provenance. Adding, changing or removing a displayed history artifact invalidates the snapshot; historical files remain read-only projection inputs, not current product or runtime authority. `CURRENT` establishes projection freshness, not continued runtime correctness of a done Scope.

It excludes `docs/planning/observatory/**`. Therefore committing a generated snapshot, or committing unrelated repository files, does not by itself make the snapshot stale.

Git revision and dirty state may be recorded as generation metadata, but they do not decide freshness.

## Write semantics

A write is refused when current canonical planning is inconsistent. Otherwise Observatory builds Markdown and JSON from one in-memory state, writes temporary files, fsyncs them, and replaces the pair. The JSON records the SHA-256 of `PROJECT-OVERVIEW.md`; a mismatching pair is `INCONSISTENT`.

When the current source fingerprint already matches the stored snapshot, `--write` returns `UNCHANGED` and does not rewrite either file or change their mtimes.

## Progress visualization

Snapshot progress uses typed measurements. In 0.2.1 the built-in measurement is the current Ticket delivery ratio:

```text
Current Ticket delivery: ██████░░░░ 3 / 5 (60.0%) — exact ratio
```

The bar is presentation only. Exact numerator, denominator, and percentage are always shown beside it. Fractional Unicode blocks are used for small non-zero values so a ratio such as 1.2% is not visually exaggerated into a full 10% cell.

Observatory does not synthesize product-wide completion percentages, capability maturity, source coverage, or estimated ranges without an explicit future measurement provider/rubric.

## Adaptive Planning boundary

`docs/planning/adaptive/**` is provenance, not canonical current-state authority for Observatory. A recorded Adaptive Mandate may say `Status: active`, but the presence or content of that file does not establish current mandate activation or a Transition Baseline.

Snapshot output may report that Adaptive companion provenance exists, its recorded revision/status, and its paths. It must also state that current Adaptive activation inference was not performed.

Adaptive and Observatory directories are excluded from canonical artifact scanning. Legacy Scope/Increment/Spec/Ticket history remains visible but never becomes current direct Scope authority.

## History

`iis-observatory history` reads all `docs/planning` Git history but categorizes entries as:

- canonical planning,
- Adaptive provenance,
- Observatory projection.

This prevents a companion `Status: active` line from being presented as though it were a canonical Increment/Ticket transition.
