# PLAN-002 — Generation Currency Closure at Production Readers

## Bound Authority

- Scope: `/home/user01/project/comic_new/docs/planning/work/generation-currency-interruption/SCOPE.md` (`5256771c1c080c4c7663e5415c3d5ebc3f13b23052a858e4ac01ace8e74b63b6`)
- Product Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Transition: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (`629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`), selected `BLOCK-06`
- Prior method: `PLAN-001.md` produced the schema, enqueue/claim/commit/FSM implementation. Independent verification v3 resolved its A-H race and preservation evidence, but Luna Max Coverage v3 (`/home/user01/tmp/comic-new-block06-coverage-v3.txt`, sha256 `bb9503fa22f8f2a6c28047f6724de6ebd8a2118f5d7d506f27fb7720907ea083`) found two production-reader gaps. This revision owns only those gaps and the necessary current-target re-verification.
- Execution: one Gemini High SUBAGENT after independent Gemini High review.

## Observable Result and Boundary

A newly accepted same-revision generation request makes the cut and whole work non-current everywhere, not only inside `TransactionalStore.snapshot()`. The production HTTP/SSE snapshot exposes the cut's latest request sequence and each job's request sequence. Existing release authorization is revoked in the same enqueue transaction, and review registration, release authorization and delivery preflight reject the work until the latest sequence succeeds. Existing canonical bytes remain preserved and visible as STALE.

This remains BLOCK-06 sequence currency. It does not implement BLOCK-08 byte transport or destination readback, nor add frontend controls from BLOCK-09.

## Grounding

### EXISTING

- `store.py:750-806` increments `latest_generation_request_seq`, inserts the bound job and advances `authority_revision` in one `BEGIN IMMEDIATE`, but does not call `_revoke_active_authorization`.
- `store.py:344-440` correctly computes `currency` and whole-work completion from revision equality plus a succeeded latest-sequence job.
- `server.py:500-582` projects store snapshots for GET, mutations and SSE but omits `cuts[].latest_generation_request_seq` and `jobs[].request_seq`; `server.py:871-935` proves production snapshot/enqueue responses use this projection.
- `frontend/src/api/contracts.ts` defines the web DTO types and currently has no request-sequence fields.
- `store.py:1344-1416` (`register_review_artifact`) and `store.py:1418-1488` (`authorize_release`) test only desired/realized revision and closure identity. A pending same-revision request therefore passes those currentness checks.
- `delivery.py:439-531` reads the authoritative snapshot but tests only revision equality, so a stale latest sequence can pass preflight if an active authorization survives or is recreated.
- `start_delivery_attempt` is already authority-revision guarded; enqueue advances the revision, so a race after successful preflight conflicts rather than silently delivering. The missing cases are enqueue-time revocation and before-preflight/before-authorization sequence currency.
- `server.py` release routes map `RealizationIncompleteError` to an honest 409 and can reuse the existing error boundary.
- Python LSP remains unavailable; direct callers were traced through `server.py`, `composition_service.py`, `delivery.py`, frontend contracts, and release/server tests.

### PROPOSED

1. In `enqueue_generation_jobs()`, revoke every active release authorization with the same `new_rev` and timestamp before committing the new request sequence. This makes acceptance of pixel-changing regeneration close authorization atomically with sequence acceptance.
2. Use one private store currentness check, or an equivalently direct shared SQL shape, that requires exactly five cuts and for each cut: non-null desired revision, realized revision equality, and—when `latest_generation_request_seq > 0`—a `succeeded` job at that exact sequence. Reuse it inside `register_review_artifact()` and `authorize_release()` while their existing write transaction is held. Do not derive currency from files or process memory.
3. In `DeliveryService.preflight_release()`, require `snapshot.realization_complete.complete` and each cut's existing `currency == "CURRENT"`; revision equality alone is not accepted. Preserve all current authorization, artifact closure and physical asset checks.
4. Project `latest_generation_request_seq` and `request_seq` unchanged through `_snapshot_dto()`. Add the same required numeric fields to the web API contracts. No new UI display or control is introduced.
5. Add load-bearing regressions: active authorization is revoked by same-revision enqueue; old artifact cannot be authorized or delivered while latest sequence is pending/cancelled/interrupted; materialization is rejected while sequence-stale; after latest sequence commits and a new artifact/authorization is created, existing release flow remains available; GET snapshot, generation response and an emitted SSE snapshot expose sequence fields equal to SQLite/store values.

### UNRESOLVED

None. The authoritative store already computes the required state, existing release paths already use `RealizationIncompleteError`, and production snapshot projection is a direct field-preservation change.

## Implementation Sequence

1. Add the transaction-local sequence-current check and call it from review registration and release authorization. Add enqueue-time authorization revocation.
2. Strengthen delivery preflight to consume snapshot currency/completion.
3. Preserve request-sequence fields in the server DTO and frontend DTO contracts.
4. Update focused transactional, release and server tests. Keep prior A-H race tests unchanged except for directly affected expected authorization/currentness behavior.

## Failure, Race, and Preservation

- Enqueue revocation, sequence increment, job insert and authority revision commit together. A failed transaction changes none of them.
- Authorization/materialization currentness is checked under the same `BEGIN IMMEDIATE` transaction as the write, preventing a sequence enqueue from interleaving after the check and before commit.
- Delivery preflight reads one deferred SQLite snapshot. If enqueue happens afterward, `start_delivery_attempt(expected_authority_revision)` conflicts because enqueue advanced authority revision and revoked authorization.
- Cancellation/interruption leaves the latest job terminal but not succeeded; the cut remains STALE and cannot be materialized, authorized or delivered until a later latest sequence succeeds.
- Existing canonical realization identity/hash/bytes are preserved; only authorization is revoked.

## Self-Check and Verification Handoff

Implementer runs focused tests only:

- transactional currentness/revocation cases in `tests/test_transactional_core.py` and generation tests;
- release authorization/preflight regressions in `tests/test_release.py`;
- HTTP snapshot, enqueue response and SSE projection in `tests/test_server.py`;
- frontend typecheck/test only if contract changes require it, not a project-wide suite.

Main runs the aggregate suites after implementation. Fresh independent verification must cover every Scope Acceptance A-H plus the two Coverage v3 findings: an authorized current project becomes revoked and release-blocked immediately after same-revision enqueue; production HTTP/SSE readback exposes sequences; currentness is restored only after the latest sequence commits and a new review/authorization closure is established. Stable targets include the prior six files plus `delivery.py`, `server.py`, `frontend/src/api/contracts.ts` and affected focused tests.

## Revision Boundary

Private helper naming and equivalent SQL are implementation discretion. Changing release semantics beyond sequence-current blocking, adding BLOCK-08 transport behavior, changing frontend action policy, or introducing a second currency authority is material and returns to Plan/Scope ownership.
