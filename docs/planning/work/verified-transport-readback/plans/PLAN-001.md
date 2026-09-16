# PLAN-001 — Verified Transport and Content-Identity Readback

## Bound Authority

- Project Root: `/home/user01/project/comic_new`
- Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`THESIS-002`, sha256 `1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Scope: `/home/user01/project/comic_new/docs/planning/work/verified-transport-readback/SCOPE.md` (sha256 `5d49db55655e6efcf1462674b69675e181805f8950b192f3ec2766f2b82c3833`, `Status: ready`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (sha256 `629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`, selected `BLOCK-08`)
- Repository investigation: None supplied; direct current source inspection is the evidence baseline.
- Entry: BLOCK-07 exact Scope is `done`; independent Gemini verification v5 `VERIFIED`; Luna Coverage v5 `COMPLETE / Findings: None`.

## Current State

1. `DeliveryService.preflight_release()` validates active authorization, current currency, review artifact hash/PNG and five physical cut assets, but returns `(auth_record, artifact_path, content_hash)`.
2. `export_png()` performs a later `shutil.copyfile(artifact_path, ...)`; `deliver_blogger()` performs a later `artifact_path.read_bytes()`. Both reopen the mutable source after verification, leaving a TOCTOU window.
3. `GoogleBloggerAdapter.publish()` embeds the PNG as a data URL without artifact identity marker. `_readback_destination()` only reads and discards the body; any successful HTTP response satisfies it.
4. `ControlledBloggerAdapter(mode='success')` returns post identity without content readback, so current tests cannot distinguish exact remote content from an unrelated 200 page.
5. `delivery_attempts.evidence_json` can retain provisional post facts without a schema change. Current `record_delivery_observation()` permits repeated rewrites of terminal outcomes and must be tightened for safe reconcile.
6. Server has export/Blogger endpoints but no reconcile endpoint. Frontend truth surfaces already distinguish authorization and delivery outcome; BLOCK-09 owns degraded synchronization, not this Plan.

## Method

### 1. One verified in-memory handoff

Add one frozen `VerifiedArtifactPayload` in `delivery.py` containing only the release facts needed downstream: authorization ID, artifact ID, content hash, immutable `bytes`, and canonical filename. `preflight_release()` returns this payload with the authorization record after all existing currentness, closure, physical cut-asset, image and hash checks.

Read the review artifact once. Prefer `CompositionService.read_artifact(artifact_id)` when the service is available so the canonical reader verifies DB registration, full SHA-256, PNG dimensions/mode, renderer metadata and five-cut closure. Confirm its bytes hash equals the active authorization hash. If no composition service was supplied (CLI construction), perform the same existing direct file/PIL checks and capture those exact bytes once. No downstream API receives the source path.

### 2. Consume bytes, never reopen source

`export_png()` receives the payload from preflight and writes `payload.png_bytes` to the same-directory temp file before `os.replace`. Read back only the destination. Remove `shutil.copyfile` and every post-preflight read of the review-artifact source.

`deliver_blogger()` obtains the same payload before starting its attempt and passes the payload bytes and identity directly to the adapter. Introduce a narrow test seam/callback only if required to inject a source mutation between preflight and consumption; do not add a production abstraction layer. Tests must prove a source replacement/deletion after preflight cannot change exported or transmitted bytes.

### 3. Exact Blogger marker and readback contract

Define one marker formatter and parser:

`<!-- comic-new:artifact-id={artifact_id}:sha256={content_hash} -->`

Artifact ID and hash come exclusively from `VerifiedArtifactPayload`. Validate both against the product's existing identity/hash shapes before HTML construction. `GoogleBloggerAdapter.publish()` builds content from the verified PNG data URL plus exactly one marker.

Extend the adapter contract with a read-only `readback(destination_url, artifact_id, content_hash)` operation used both immediately after insert and by reconcile. `_readback_destination()` reads the HTML body and parses all `comic-new` identity comments. Exactly one well-formed marker must exist and both fields must equal the expected identity. Return structured evidence containing expected/observed marker, body-read completion and verification result.

- exact unique match → success-capable readback;
- missing, malformed, duplicate or mismatched marker → `BloggerContentIdentityError`, a definitive failure carrying expected/observed evidence;
- timeout, disconnect, 5xx, incomplete body/decoding → transport-unknown error;
- authoritative 4xx → authoritative failure.

The insert response's post ID/URL is provisional until this readback passes. If the insert succeeded but readback is unknown, raise a transport-unknown value that retains post ID, URL and raw insert response so the delivery evidence can support reconciliation without claiming success.

Update `ControlledBloggerAdapter` to execute the same formatter/parser contract and support discriminating modes: exact match, missing marker, wrong artifact ID, wrong hash, duplicate/malformed marker, readback timeout after known destination, and timeout before destination identity. Do not let `success` bypass content verification.

### 4. Honest delivery transitions and reconcile

Keep `delivery_attempts` schema v4. Persist provisional post ID/URL/raw insert response inside `evidence_json` for unknown readback; terminal destination columns remain null until content identity is verified.

Tighten `TransactionalStore.record_delivery_observation()` inside its transaction: load current outcome and identity, permit observation transition only while current outcome is `unknown`, and reject changes to a terminal attempt. Preserve the existing requirement that `confirmed_success` includes destination ID, URL and evidence. This is a clean cutover; no terminal rewrite compatibility alias.

Add `DeliveryService.reconcile_blogger(expected_authority_revision, attempt_id, adapter=None)`:

1. read the exact persisted attempt; require `kind='blogger'` and `outcome='unknown'`;
2. recover only its stored provisional post ID/URL and exact attempt artifact identity/hash through the persisted authorization/artifact rows;
3. if destination is absent, return/record no fabricated result and keep `unknown`;
4. perform adapter readback only—never publish again;
5. exact marker → atomically transition the same attempt to `confirmed_success` with destination fields;
6. definitive identity mismatch/4xx → `confirmed_failure` with evidence;
7. ambiguous transport → refresh evidence while remaining `unknown`;
8. terminal attempt or identity ambiguity → reject.

Add the minimal store read method needed to return one attempt joined to its authorization artifact hash. It must not infer current active authorization or replace historical identity.

### 5. Server and caller cutover

Add `POST /api/release/blogger/{attempt_id}/reconcile` with `expected_authority_revision`; execute via `asyncio.to_thread`, return the same delivery result fields and a fresh snapshot. Map definitive content mismatch to the existing honest failure response/result path, not HTTP success-as-publication. Unknown remains a normal outcome with explicit evidence.

Update current CLI/server/tests for the new payload/adapter signatures. Add a CLI `reconcile-blogger <project_dir> <attempt_id>` only if the production Google adapter can perform the same readback without new user decisions; otherwise the HTTP service endpoint is the selected safe reconcile surface. Do not add a frontend retry UI in BLOCK-08; snapshot and existing truth labels remain compatible, and BLOCK-09 owns client state safety.

### 6. Focused evidence

Use the existing real local HTTP Blogger harness pattern, not an external account. Add focused runtime scenarios:

- preflight returns bytes matching authorization and canonical artifact;
- a hook swaps/deletes source after preflight; export destination and adapter-captured payload still match verified bytes/hash;
- preflight-before mutation fails without attempt/output;
- Google request body contains one exact marker and the exact verified data URL;
- destination 200 with absent/wrong/duplicate/malformed marker never confirms success;
- exact marker alone confirms success with identity evidence;
- post insert + readback timeout records unknown with provisional destination; reconcile exact success transitions the same row;
- reconcile mismatch transitions failure; repeated unknown stays unknown; absent destination stays unknown without publish; terminal reconcile is rejected;
- authority mutation during external I/O does not change attempt artifact identity or let a different artifact justify success;
- existing BLOCK-05 export/unknown/failure, BLOCK-06 currency, and BLOCK-07 baseline/dialogue focused suites remain green.

Run focused Python delivery/server/store tests, then the complete backend suite once. Frontend source is not changed unless an existing contract requires a DTO addition; if changed, run Vitest and `vue-tsc --noEmit` once. Main performs independent semantic verification and Luna Coverage after implementation.

## Acceptance Mapping

- A: Sections 1–2; immutable payload, one source read, hash and mutation injection.
- B: Section 2; destination-only readback and preflight-before mutation rejection.
- C: Section 3; marker formatter, payload origin and request capture.
- D: Sections 3–4; 200 body counterexamples and definitive failure evidence.
- E: Sections 3–5; exact marker success and store/snapshot/API identity readback.
- F: Sections 3–5; provisional evidence, read-only reconcile, monotonic attempt state.
- G: Sections 4–6; fixed historical identity under concurrency and prior-block regressions.

## Failure, Race, and Preservation

- No SQLite write transaction spans external network I/O.
- Verified bytes are acquired before attempt creation; preflight failure creates no attempt. After attempt creation, any ambiguous effect remains `unknown`.
- A concurrent authority revision may require observation-write retry, but retry may only update the original attempt from `unknown`; it never rebinds artifact, authorization or destination identity.
- Reconcile is idempotent only while evidence remains unknown. A terminal outcome is immutable and rejected, preventing success/failure oscillation.
- Filesystem mutation after byte capture cannot affect transport; mutation before capture is detected by hash/readback.
- Existing delivery history and schema remain intact. No migration is introduced without evidence it is necessary.

## Non-Goals

No real Blogger side effect, retries/republication, title/time heuristic lookup, new destination, SSE degraded handling, production cutover, audit subsystem, or product-meaning change.

## Return Boundary

Implementation may begin only after an independent Gemini High Plan Review returns `ADMIT` for this exact Scope and Plan. Any finding that requires guessing remote identity, rereading the mutable source after preflight, accepting HTTP 200 without exact marker, or rewriting terminal delivery history returns to Plan/Scope ownership.
