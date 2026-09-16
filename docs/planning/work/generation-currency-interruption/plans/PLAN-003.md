# PLAN-003 — Sequence-Current Review Materialization Readback

## Bound Authority

- Scope: `/home/user01/project/comic_new/docs/planning/work/generation-currency-interruption/SCOPE.md` (`5256771c1c080c4c7663e5415c3d5ebc3f13b23052a858e4ac01ace8e74b63b6`)
- Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Transition: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (`629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`), BLOCK-06
- Prior method: PLAN-002 corrected store/release/HTTP/SSE readers. Verification v4 proved those paths. Luna Max Coverage v4 (`/home/user01/tmp/comic-new-block06-coverage-v4.txt`, sha256 `de95a31b54f649ce3f16a9f2322f9f83d9f1c02ef741dd09b6f0b3d5fd717b23`) found one remaining composition-service race.

## Observable Result

`CompositionService.materialize()` may return a current review-materialization receipt only while the fresh authoritative snapshot remains sequence-current: exactly five cuts are `CURRENT` and `realization_complete.complete` is true. A same-revision enqueue interleaved after the initial snapshot invalidates the in-flight current receipt even when a deterministic artifact with identical old canonical bytes already exists. Historical `read_artifact()` remains able to read a registered artifact; it is not a claim that the artifact is current.

## Grounding

### EXISTING

- `composition_service.py:80-262` captures an initial snapshot, renders outside SQLite and calls the now sequence-aware `register_review_artifact()` with the captured authority revision.
- `composition_service.py:263-326` catches any registration error and converges on an existing deterministic artifact using artifact hash, composition revision, closure, file metadata/bytes and desired/realized/asset identities. It does not inspect fresh `realization_complete`, cut `currency`, latest request sequence or job status.
- `composition_service.py:327-332` returns `_verify_and_build_artifact(... expected_comp_rev, expected_closure)` after both successful registration and duplicate convergence.
- `_verify_and_build_artifact():382-408` checks composition and cut identity only when currentness expectations are supplied. A same-revision enqueue preserves those identities while making currency STALE.
- `read_artifact()` calls `_verify_and_build_artifact()` without expectations and is an historical registered-artifact reader.
- `store.register_review_artifact()` now rejects sequence-stale state inside its write transaction, but duplicate convergence can catch its authority/currentness error and return the old artifact.

### PROPOSED

1. Add one private `CompositionService` snapshot-current assertion requiring `realization_complete.complete is True`, exactly five cuts, and every cut `currency == "CURRENT"`; raise `ArtifactNoLongerCurrentError` (or the existing currentness exception mapped by the server) with the artifact identity when false.
2. In duplicate convergence, apply that assertion to `fresh_snap` before accepting the pre-existing artifact. Do not replace the original registration error with duplicate success when the work is sequence-stale.
3. In `_verify_and_build_artifact()`, whenever `expected_comp_rev` or `expected_closure` is supplied—meaning the caller requests a current materialization receipt—apply the same assertion to the final fresh snapshot before identity/file readback. This closes enqueue after successful registration and before return.
4. Keep `read_artifact()` without expected currentness unchanged so registered historical artifacts remain readable. Do not delete or rewrite canonical realization/review bytes.
5. Add one deterministic race regression: establish a registered deterministic artifact; hold a second materialize invocation after its initial current snapshot and before registration; enqueue same-revision regeneration; release registration; assert an honest currentness/conflict failure, STALE/UNRESOLVED readback, unchanged old artifact row/identity/hash/bytes and no false HTTP materialization success. Add a post-registration-before-final-readback interleave case if the same hook can expose it without production scaffolding.

### UNRESOLVED

None. The final authoritative snapshot already contains sequence-aware currency and the server already maps `ArtifactNoLongerCurrentError`/currentness failures to a non-success response.

## Implementation and Checks

Modify `src/comic_new/composition_service.py` and focused `tests/test_composition.py`/`tests/test_server.py` only. Reuse the existing race hooks/patterns in composition tests. Run focused composition and server tests; Main runs aggregate suites. Verifier re-executes all Scope A-H plus the release/HTTP/SSE corrections and the compositor race at the production service/route boundary. Stable target attribution adds `composition_service.py` and affected tests.

## Failure and Preservation

The currentness assertion is read-only. It never deletes a registered historical artifact or canonical realization. An enqueue race advances authority and sequence and revokes authorization in SQLite; materialization reports non-current. If no enqueue occurs, deterministic duplicate convergence remains valid. Any proposal to make historical `read_artifact()` reject stale artifacts, alter artifact IDs, delete race artifacts or change BLOCK-08 delivery behavior is outside this Plan.

## Revision Boundary

Equivalent private helper naming is discretion. Changing artifact identity, persistence, historical read semantics, render/layout behavior or release transport is material and returns to Plan/Scope ownership.
