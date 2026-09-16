# PLAN-001 — Generation Currency and Atomic Interruption Closure

## Bound Authority

- Scope: `/home/user01/project/comic_new/docs/planning/work/generation-currency-interruption/SCOPE.md`
- Product Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Transition: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (`629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`), selected `BLOCK-06`
- Execution: one Gemini High SUBAGENT implementation owner after independent Gemini High review admission.

## Observable Result and Boundaries

The result is one SQLite-owned monotonic request order per cut. A generation candidate can become canonical only when both its desired revision and request sequence equal the cut's latest accepted tuple. Cancel and STOP revoke commit eligibility transactionally before process termination. Existing pixels and accepted intent remain; currency is `CURRENT` only after the latest sequence commits. No baseline/dialogue, delivery, or frontend-resync work belongs here.

Authoritative readback: fresh SQLite connections over `cuts.latest_generation_request_seq`, `generation_jobs.request_seq`, job/attempt FSM states, canonical asset identity/hash/path, authority revision and stop epoch; canonical PNG bytes and OS process liveness where applicable.

## Grounding

### EXISTING

- `src/comic_new/schema.sql:26-38,55-87` defines v2 cuts/jobs without request sequence.
- `src/comic_new/store.py:67-287` owns schema version, migrations and structural verification; only v1→v2 exists.
- `store.py:311-546` projects currency from revision equality alone and omits request sequence.
- `store.py:701-755` enqueues under `BEGIN IMMEDIATE`, so it is the single place to increment and bind per-cut sequence atomically.
- `store.py:861-955` claims queued work using desired revision only.
- `store.py:996-1089` commits under `BEGIN IMMEDIATE`; filesystem promotion and DB state change occur while the same write transaction excludes cancel/STOP. It checks revision but not request sequence.
- `store.py:1126-1249` leaves running rows eligible during cancel/STOP process termination and contains unguarded terminal rewrites in `mark_job_and_attempt_cancelled`.
- `generation.py:340-436` calls the store before process termination but currently relies on a second post-kill status mutation.
- `generation.py:599-827` treats already-cancelled/interrupted process exits as non-failures and routes all successful candidates through `commit_candidate`.
- `tests/test_generation.py` already provides real subprocess, race, STOP, restart and migration fixtures; it lacks same-revision supersession and commit-before-kill gates.
- Cross-file LSP references were unavailable because no Python language server is installed; direct callers are grounded by repository search in `generation.py`, `server.py`, `cli.py`, `tests/test_generation.py`, and `tests/test_transactional_core.py`.

### PROPOSED

1. Schema v3 adds `cuts.latest_generation_request_seq INTEGER NOT NULL DEFAULT 0` and `generation_jobs.request_seq INTEGER NOT NULL`; new-schema constraints require nonnegative cut sequence and positive job sequence. Add `migrations/v2_to_v3.sql`; deterministic per-cut existing-job order is `(created_at, job_id)`, backfilled to `1..N`, with each cut set to its max or zero. Extend migration dispatch and schema verification to require both columns and reject nonpositive persisted job sequences.
2. `enqueue_generation_jobs()` increments each target cut's latest sequence and inserts the same value in its job in the existing write transaction. Receipts/snapshot expose it.
3. Snapshot currency requires revision equality and that the latest-sequence job is `succeeded`; a cut with no generation request remains governed by existing revision equality only for legacy baseline initialization, while any accepted sequence requires its exact successful job.
4. Claim reads job request sequence and cut latest sequence; mismatch on either revision or sequence terminally supersedes the job before provider launch.
5. Commit reads the full tuple and discards/supersedes any non-current candidate without touching canonical pixels. Successful commit keeps its job sequence as the currency proof.
6. `cancel_job_in_store()` changes a queued job directly to `cancelled`; for a running job it captures process metadata and changes the running attempt and job to `cancelled` in the same transaction before return. `GenerationService.cancel()` then only terminates/cleans the captured process; no second state write is needed.
7. `stop_all_and_cancel_queued()` increments epoch, cancels queued rows, captures running process metadata, and changes running attempts/jobs to `interrupted` in one transaction. `GenerationService.stop_all()` then terminates/cleans only. Existing marking helpers are either removed when obsolete or retained solely with `WHERE status = 'running'` guards for startup recovery; no terminal-to-terminal rewrite remains.
8. Physical termination failure raises truthfully while the already accepted logical cancellation/interruption remains terminal and commit-ineligible. No rollback to running occurs.

### UNRESOLVED

None. SQLite is the existing single writer/reader authority, and the current transaction layout can decide commit-vs-cancel ordering without a new lock or interface.

## Implementation Sequence

1. Update `schema.sql`, add v2→v3 migration, raise `SCHEMA_VERSION`, extend migration routing and `verify_schema()`. Preserve v1→v2→v3 chaining in one open.
2. Add sequence fields to snapshot and enqueue receipts. Compute currency from the current tuple and latest job status without introducing process-local state.
3. Extend claim and commit tuple checks; preserve canonical bytes on every rejected path.
4. Move running cancel/STOP FSM transitions into their pre-termination transactions. Simplify service post-termination behavior and constrain/remove obsolete marking calls.
5. Update existing fixtures and behavior assertions for schema v3. Add only load-bearing regression cases: same-revision A/B late completion, queued A skipped before provider launch, cancel-before-commit, STOP-before-commit across two jobs, late cancel preserving success, v2 migration/backfill/new increment, and sequence-bound STALE→CURRENT.

## Failure, Interruption, and Preservation

- Transaction order decides the race: if commit wins first, later cancel sees `succeeded` and cannot rewrite it; if cancel/STOP wins first, commit sees a non-running row and discards.
- Process termination follows logical revocation. Failure to settle is surfaced but does not restore commit eligibility.
- Migration is one `BEGIN IMMEDIATE` transaction. Any SQL or post-migration schema failure rolls back; product open fails rather than exposing partial authority.
- Superseded, cancelled and interrupted candidates are unlinked; current canonical assets and accepted intents are never deleted.
- No retries, alternate queue, file lock, memory sequence, or sidecar authority.

## Self-Check and Verification Handoff

Implementer self-check:

- `python3 -m pytest tests/test_generation.py tests/test_transactional_core.py -q` after targeted scenario development.
- Fresh disposable v2 fixture opened through `TransactionalStore.open_project()`, then direct SQLite/snapshot readback of preserved rows, positive per-cut job sequence order and next enqueue.
- Real local subprocess gates in `tests/mock_provider.py` for race/STOP process settlement; canonical bytes read from the actual promoted file.
- `python3 -m pytest -q` once after the scoped tests pass, because schema version and shared store behavior affect all product paths.

Verifier handoff: unchanged ready Scope; exact source/config hashes; disposable scenario directories as mutable effects; all processes reaped and staging cleaned; fresh DB and file readbacks for every Acceptance A–H. External provider/network is not required because BLOCK-06 promises local subprocess/SQLite/canonical boundaries, not provider semantics.

## Revision Boundary

Private helper names and equivalent SQL formulations are implementer discretion. Any change to SQLite ownership, tuple identity, transaction ordering, filesystem promotion strategy, currency meaning, or service API is material and returns this Plan to independent review.
