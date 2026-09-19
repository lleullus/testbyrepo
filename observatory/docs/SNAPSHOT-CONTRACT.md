# Observatory Snapshot Contract

The Observatory snapshot is a durable read-only projection under `docs/planning/observatory/`. It does not become IIS authority and it never grants role admission.

Current snapshot schema: `2.0`.

## Files

- `PROJECT-OVERVIEW.md`
- `project-state.json`

They are written as one projection pair. The JSON declares those filenames; the checker renders the Markdown again from stored JSON and compares the actual text directly.

## Freshness

The checker returns:

- `CURRENT` — stored input originals equal the current observed input originals and the Markdown exactly matches the stored JSON projection.
- `STALE` — planning/display inputs changed after generation.
- `MISSING` — neither projection file exists.
- `INCONSISTENT` — the pair is incomplete, malformed, based on an obsolete schema, or current planning structure is inconsistent.

## Direct input comparison

Freshness is not Git-HEAD-based and does not use a checksum or aggregate fingerprint. Inputs include the current direct `SCOPE.md`, its work directory, available live projections of bound source paths, displayed direct/legacy history, and Adaptive provenance that is shown by the snapshot.

For each input, the snapshot stores the repository-relative path, category, size, and actual input content. Freshness compares that stored content directly with the current observed content. Metadata such as mtime is not used as a hidden identity substitute.

A bound Product Thesis snapshot ref is not independently resolved by Observatory. Common host admission owns closure/currentness. The live file at the ref path may be used only as a display input and is labeled as such.

## Write behavior

When the stored pair is already `CURRENT`, `--write` returns `UNCHANGED` and does not rewrite the files. Otherwise it writes temporary files and replaces the Markdown then JSON, after which a full check must return `CURRENT`.

A crash between replacements is detected because re-rendered Markdown no longer equals the stored JSON projection.

## Boundaries

`CURRENT` establishes projection freshness only. It does not establish Product Thesis closure, Scope admission, runtime identity, execution success, completion evidence, or user authorization.
