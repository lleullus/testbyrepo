# PLAN-001 — Structural Baseline and Dialogue Authority

## Bound Authority

- Scope: `/home/user01/project/comic_new/docs/planning/work/baseline-dialogue-authority/SCOPE.md`
- Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Transition: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (`629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`), selected `BLOCK-07`
- Entry: completed BLOCK-06 Scope and current schema v3 implementation.
- Execution: one Gemini High SUBAGENT after independent Gemini High review.

## Observable Result

No intent or generation request can exist without one active Structural Baseline. A cut has one narrative dialogue: the `dialogue` member of its current Cut Intent. Persisted composition bubbles for that cut always carry that same derived text. Intent edits synchronize composition; composition text edits atomically create one new intent revision; geometry/style-only edits do not. Store, HTTP, frontend projection and renderer read the same state.

## Grounding

### EXISTING

- `store.py:622-730` approves a baseline and accepts cut intents. `accept_cut_intent()` reads `current_baseline_id` but permits `None` and inserts it.
- `store.py:775-838` enqueues from any current desired intent without checking a baseline or intent-to-active-baseline binding.
- `schema.sql:16-24` allows `cut_intents.baseline_id NULL`; no baseline guard trigger exists.
- `server.py:877-937` delegates baseline/intent/generation mutations to the store; existing `TransactionalStoreError` handlers can project a dedicated baseline-required error.
- `composition.py:105-220` normalizes `bubbles[].text` as independent persisted data. `store.py:732-773` saves normalized composition without reconciling current intent dialogue.
- `frontend/src/components/inspector/InspectorPanel.vue` edits Cut Intent dialogue and bubble text through separate draft paths. Bubble creation initializes text from current intent dialogue, but later edits can diverge.
- `CompositionService` and `render_canonical()` consume persisted composition text, so divergence reaches the canonical review artifact.
- Existing schema migration chain is v1→v2→v3. Existing production baseline creation provides five structured `{prompt, dialogue}` intents, while historical tests include legacy `text`-only fixtures.
- Python LSP is unavailable; callers were traced by repository search through server, generation, composition service, CLI and tests.

### PROPOSED

1. Add `BaselineRequiredError(TransactionalStoreError)` and a transaction-local `_require_active_baseline(con)` returning the active baseline ID. Use it before `accept_cut_intent()` and `enqueue_generation_jobs()` perform any write. Enqueue additionally requires every target current intent row to be bound to that active baseline.
2. Schema v4 adds a trigger preventing any `cut_intents` insert whose `baseline_id` is NULL or differs from `authority.current_baseline_id`. Reorder baseline approval inside its existing transaction: insert the structural baseline, set it active, then insert its five intents. The foreign key and trigger jointly prevent direct-SQL bypass.
3. Define one store-local structured-intent parser requiring object payloads with string `prompt` and `dialogue` for new production mutations. Update legacy tests/fixtures to this current contract; do not keep a second `text` authority alias. Snapshot continues returning the structured payload.
4. Add store-local composition dialogue synchronization operating on normalized state:
   - current dialogue map comes only from current cut intent rows bound to the active baseline;
   - baseline/intent mutations rewrite every existing bubble text for affected cuts to that dialogue;
   - composition submission groups bubble texts by cut; more than one distinct text for a cut is rejected; one submitted text different from current dialogue creates exactly one new intent revision with the existing prompt and new dialogue, updates desired revision and then canonicalizes every bubble for that cut to the new dialogue;
   - unchanged text performs no intent mutation.
5. `approve_structural_baseline()` performs five intent inserts, desired-revision updates, composition text synchronization and optional single composition-revision increment atomically. `accept_cut_intent()` performs one intent insert, desired update, affected-bubble synchronization and optional single composition-revision increment atomically. `accept_composition()` performs any required per-cut intent revisions plus one composition-revision increment in its existing authority transaction. All three revoke authorization once and advance authority revision once.
6. Schema v3→v4 migration runs as one `BEGIN IMMEDIATE`: reject legacy intent rows that cannot be attributed to an existing active baseline rather than fabricate product meaning; synchronize persisted bubble text from each active current intent dialogue; if bytes change, increment composition revision and authority revision once and revoke active authorization; create the active-baseline trigger and set user_version 4. Preserve realizations, sequences, jobs, artifacts and delivery rows.
7. Add explicit server mapping for `BaselineRequiredError` to HTTP 409 `baseline_required` with current snapshot. The existing intent, generation and composition endpoints remain the only mutation APIs.
8. Keep the frontend interaction model: bubble text submission through composition becomes an atomic intent+composition mutation at the backend; returned snapshot updates both `effective_intent.dialogue` and composition text. Add UI/store behavior checks, not a second client-side authority.

### UNRESOLVED

None. The Scope selects the atomic sync behavior, and all required data already travel through one SQLite mutation boundary.

## Implementation Sequence

1. Schema v4 migration, trigger, schema verification and dedicated error.
2. Structured-intent/current-baseline helpers and baseline/intent/enqueue guards.
3. Dialogue synchronization in baseline, intent and composition transactions.
4. Server error projection and frontend/renderer contract preservation.
5. Focused migration, store, API, composition and frontend regressions.

## Failure, Race, and Preservation

- All guards run after `BEGIN IMMEDIATE`; a concurrent re-baseline or intent/composition mutation is serialized by authority-revision CAS.
- Validation completes before inserts/updates. Multiple different texts for one cut roll back the entire composition mutation.
- New dialogue revisions preserve the existing prompt and active baseline ID, revoke authorization and make the affected realization STALE by desired-revision monotonicity.
- Geometry/style-only composition edits preserve intent revisions and generation request sequences.
- Migration never invents a baseline or dialogue. Unattributable legacy state fails project open with a precise corruption/migration error.
- Existing canonical realizations and historical artifacts are preserved; currentness/authorization reflects the new intent/composition state.

## Self-Check and Verification Handoff

Focused implementer checks:

- fresh INIT store/API rejects intent and single/all generation with no state change; direct SQL trigger rejects NULL/non-active baseline;
- approved baseline admits intent/enqueue and re-baseline binds exactly five current intents;
- intent dialogue edit synchronizes all affected bubbles only;
- composition uniform text edit creates one intent revision atomically; divergent same-cut texts roll back; geometry-only edit preserves desired revision/request sequence;
- v3 migration synchronizes existing bubble text and preserves all other authority rows;
- HTTP snapshot, frontend projection and materialized PNG metadata/pixels reflect the same dialogue.

Main runs aggregate backend/frontend suites. Independent verification uses real SQLite, FastAPI and canonical materialization boundaries for Acceptance A-H, including rollback/readback and migration. External provider/network is unnecessary.

## Revision Boundary

Helper names and equivalent transaction-local SQL are discretion. Any second dialogue authority, asynchronous cross-request sync, fabricated baseline, bubble-specific narrative model, or change to BLOCK-08/09 behavior is material and returns to Plan/Scope ownership.
