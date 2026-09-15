"""Permanent tests for BLOCK-01: Single Transactional Authority."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from comic_new.store import (
    AuthorizationRevokedError,
    ConflictError,
    InvalidArtifactClosureError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RealizationIncompleteError,
    StaleRealizationError,
    StoreCorruptionError,
    TransactionalStore,
    ValidationError,
)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "comic_new", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_test_realization(
    store: TransactionalStore,
    expected_auth_rev: int,
    cut_id: int,
    asset_id: str,
    asset_path: str,
    content_hash: str,
    job_id: str | None = None,
) -> int:
    """Test fixture helper for seeding realizations in transactional core tests."""
    jid = job_id or f"test-job-{cut_id}-{uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    with store._connect() as con:
        con.execute("BEGIN IMMEDIATE;")
        cur_rev = con.execute("SELECT authority_revision FROM authority WHERE singleton_id = 1").fetchone()[0]
        if cur_rev != expected_auth_rev:
            raise ConflictError(expected=expected_auth_rev, actual=cur_rev)
        new_rev = cur_rev + 1
        d_rev = con.execute("SELECT desired_revision FROM cuts WHERE cut_id = ?", (cut_id,)).fetchone()[0]
        con.execute(
            "INSERT OR REPLACE INTO generation_jobs (job_id, cut_id, target_desired_revision, status, created_at, updated_at) VALUES (?, ?, ?, 'succeeded', ?, ?)",
            (jid, cut_id, d_rev or 1, now_iso, now_iso),
        )
        con.execute(
            "INSERT OR REPLACE INTO generation_attempts (attempt_id, job_id, ordinal, status, started_at, finished_at, detail) VALUES (?, ?, 1, 'succeeded', ?, ?, 'Test seed')",
            (f"att-{jid}", jid, now_iso, now_iso),
        )
        con.execute(
            "UPDATE cuts SET realized_revision = ?, realized_asset_id = ?, realized_asset_path = ?, realized_content_hash = ? WHERE cut_id = ?",
            (d_rev or 1, asset_id, asset_path, content_hash, cut_id),
        )
        store._revoke_active_authorization(con, new_rev, now_iso)
        con.execute("UPDATE authority SET authority_revision = ? WHERE singleton_id = 1", (new_rev,))
        con.execute("COMMIT;")
        return new_rev

# ---------------------------------------------------------------------------
# Acceptance A: Exactly five cuts, immutable cuts table, no sidecar authority
# ---------------------------------------------------------------------------


def test_acceptance_a_init_and_exactly_five_cuts(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_a"

    # Run official CLI init
    res_init = run_cli("init", str(project_dir))
    assert res_init.returncode == 0, res_init.stderr
    assert "Initialized comic-new project" in res_init.stdout

    # Verify no sidecar files or app lock files exist in project directory
    files = list(project_dir.iterdir())
    file_names = {f.name for f in files}
    assert "comic-new.sqlite3" in file_names
    for name in file_names:
        assert not name.endswith(".lock"), f"Forbidden lock file found: {name}"
        assert not name.endswith(".json"), f"Forbidden JSON authority file found: {name}"

    # Read authoritative snapshot in a separate new process via CLI
    res_snap = run_cli("snapshot", str(project_dir))
    assert res_snap.returncode == 0, res_snap.stderr
    snap = json.loads(res_snap.stdout)

    assert snap["schema_version"] == 2
    assert snap["authority_revision"] == 0
    cuts = snap["cuts"]
    assert len(cuts) == 5
    assert [c["cut_id"] for c in cuts] == [1, 2, 3, 4, 5]

    # Verify no add/delete/reindex CLI command exists
    res_bad = run_cli("add-cut", str(project_dir))
    assert res_bad.returncode != 0
    res_bad2 = run_cli("delete-cut", str(project_dir))
    assert res_bad2.returncode != 0
    res_bad3 = run_cli("reindex-cuts", str(project_dir))
    assert res_bad3.returncode != 0

    # Test direct raw SQL violations on cuts: INSERT, DELETE, UPDATE of cut_id
    db_path = project_dir / "comic-new.sqlite3"
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys = ON;")

        # 1. Attempt INSERT
        with pytest.raises(sqlite3.IntegrityError, match="exactly five cuts are immutable"):
            con.execute("INSERT INTO cuts (cut_id) VALUES (6);")

        # 2. Attempt DELETE
        with pytest.raises(sqlite3.IntegrityError, match="exactly five cuts are immutable"):
            con.execute("DELETE FROM cuts WHERE cut_id = 1;")

        # 3. Attempt UPDATE OF cut_id (reindex)
        with pytest.raises(sqlite3.IntegrityError, match="exactly five cuts are immutable"):
            con.execute("UPDATE cuts SET cut_id = 10 WHERE cut_id = 1;")
    finally:
        con.close()

    # Verify project reinit fails honestly
    res_reinit = run_cli("init", str(project_dir))
    assert res_reinit.returncode != 0
    assert "already initialized" in res_reinit.stderr


def test_acceptance_a_incomplete_schema_and_failed_init_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1. Deliberately partial database (user_version=1, authority singleton, 5 cuts, but missing tables and triggers)
    # reproduces the exact Coverage finding / verifier probe condition.
    proj_partial = tmp_path / "proj_partial"
    proj_partial.mkdir()
    db_partial = proj_partial / "comic-new.sqlite3"
    con = sqlite3.connect(str(db_partial))
    con.execute(f"PRAGMA application_id = {TransactionalStore.APPLICATION_ID};")
    con.execute("PRAGMA user_version = 1;")
    con.execute(
        "CREATE TABLE authority (singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1), authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0), current_baseline_id TEXT NULL);"
    )
    con.execute("INSERT INTO authority (singleton_id, authority_revision) VALUES (1, 0);")
    con.execute("CREATE TABLE cuts (cut_id INTEGER PRIMARY KEY CHECK (cut_id BETWEEN 1 AND 5));")
    con.executemany("INSERT INTO cuts (cut_id) VALUES (?);", [(i,) for i in range(1, 6)])
    con.commit()
    con.close()

    # Authoritative readback: open_project rejects incomplete schema as StoreCorruptionError
    with pytest.raises(StoreCorruptionError, match="Missing required tables"):
        TransactionalStore.open_project(proj_partial)

    # CLI snapshot rejects incomplete schema with non-zero exit and StoreCorruptionError message
    res_snap = run_cli("snapshot", str(proj_partial))
    assert res_snap.returncode != 0
    assert "Missing required tables" in res_snap.stderr

    # Re-initialization on this corrupted/partial database fails with StoreCorruptionError, not ProjectAlreadyExistsError
    with pytest.raises(StoreCorruptionError, match="Unrecognized or partially initialized database"):
        TransactionalStore.create_project(proj_partial)

    # 2. Database missing required exact-five triggers is rejected before cuts can be illegally mutated
    proj_notriggers = tmp_path / "proj_notriggers"
    proj_notriggers.mkdir()
    db_notriggers = proj_notriggers / "comic-new.sqlite3"
    schema_sql_path = Path(__file__).parent.parent / "src" / "comic_new" / "schema.sql"
    sql_text = schema_sql_path.read_text(encoding="utf-8")
    sql_without_triggers = sql_text.split("-- Exactly five cuts triggers")[0]
    con2 = sqlite3.connect(str(db_notriggers))
    con2.execute(f"PRAGMA application_id = {TransactionalStore.APPLICATION_ID};")
    con2.execute("PRAGMA user_version = 1;")
    con2.executescript(sql_without_triggers)
    con2.commit()
    con2.close()

    with pytest.raises(StoreCorruptionError, match="Missing required triggers"):
        TransactionalStore.open_project(proj_notriggers)

    # 3. Fault-injected interrupted initialization is atomic: rollback leaves no valid or partial DB
    proj_fault = tmp_path / "proj_fault"
    orig_read_text = Path.read_text

    def broken_read_text(self: Path, *args: object, **kwargs: object) -> str:
        content = orig_read_text(self, *args, **kwargs)
        if self.name == "schema.sql":
            return content + "\nSYNTAX ERROR INTERRUPTING INITIALIZATION;\n"
        return content

    monkeypatch.setattr(Path, "read_text", broken_read_text)

    with pytest.raises(StoreCorruptionError, match="Database initialization failed"):
        TransactionalStore.create_project(proj_fault)

    # The project database was not published in an incomplete state
    assert not (proj_fault / "comic-new.sqlite3").exists()
    with pytest.raises(ProjectNotFoundError):
        TransactionalStore.open_project(proj_fault)

    # 4. Empty crashed placeholder recovery is preserved
    monkeypatch.undo()
    proj_placeholder = tmp_path / "proj_placeholder"
    proj_placeholder.mkdir()
    placeholder_db = proj_placeholder / "comic-new.sqlite3"
    placeholder_db.touch()
    assert placeholder_db.stat().st_size == 0

    store_recovered = TransactionalStore.create_project(proj_placeholder)
    snap = store_recovered.snapshot()
    assert [c["cut_id"] for c in snap["cuts"]] == [1, 2, 3, 4, 5]

# ---------------------------------------------------------------------------
# Acceptance B: Approved Baseline, monotonic intent, rollback-as-new
# ---------------------------------------------------------------------------


def test_acceptance_b_baseline_and_monotonic_intent(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_b"
    store = TransactionalStore.create_project(project_dir)

    # Approve Structural Baseline with distinct intents for cuts 1..5
    intents = {
        1: {"dialogue": "Scene 1 start", "prompt": "wide shot"},
        2: {"dialogue": "Scene 2 action", "prompt": "medium shot"},
        3: {"dialogue": "Scene 3 reaction", "prompt": "close up"},
        4: {"dialogue": "Scene 4 twist", "prompt": "dramatic angle"},
        5: {"dialogue": "Scene 5 ending", "prompt": "sunset panel"},
    }
    structure = {"act": 1, "theme": "hero journey", "pacing": "standard"}

    rev1 = store.approve_structural_baseline(
        expected_authority_revision=0,
        baseline_id="BASE-001",
        structure=structure,
        intents_by_cut=intents,
    )
    assert rev1 == 1

    # Read back from new connection
    store2 = TransactionalStore.open_project(project_dir)
    snap1 = store2.snapshot()
    assert snap1["authority_revision"] == 1
    assert snap1["baseline"] is not None
    assert snap1["baseline"]["baseline_id"] == "BASE-001"
    assert len(snap1["baseline"]["intents"]) == 5

    # Each cut should now have desired_revision == 1
    for cut in snap1["cuts"]:
        assert cut["desired_revision"] == 1
        assert cut["effective_intent"] == intents[cut["cut_id"]]

    # Consecutive intent updates on cut 2
    rev2 = store2.accept_cut_intent(
        expected_authority_revision=1,
        cut_id=2,
        intent_payload={"dialogue": "Scene 2 modified", "prompt": "dynamic shot"},
    )
    assert rev2 == 2

    rev3 = store2.accept_cut_intent(
        expected_authority_revision=2,
        cut_id=2,
        intent_payload={"dialogue": "Scene 2 final", "prompt": "intense dynamic shot"},
    )
    assert rev3 == 3

    snap2 = store2.snapshot()
    cut2 = [c for c in snap2["cuts"] if c["cut_id"] == 2][0]
    assert cut2["desired_revision"] == 3
    assert cut2["effective_intent"]["dialogue"] == "Scene 2 final"

    # Rollback-as-new: restoring original rev1 payload creates a new higher revision (4)
    rev4 = store2.accept_cut_intent(
        expected_authority_revision=3,
        cut_id=2,
        intent_payload=intents[2],
    )
    assert rev4 == 4

    snap3 = store2.snapshot()
    cut2_restored = [c for c in snap3["cuts"] if c["cut_id"] == 2][0]
    assert cut2_restored["desired_revision"] == 4  # Monotonically increased, not decremented
    assert cut2_restored["effective_intent"] == intents[2]


# ---------------------------------------------------------------------------
# Acceptance C: Composition CAS, atomic authorization revocation, concurrent writers
# ---------------------------------------------------------------------------


def test_acceptance_c_composition_and_auth_revocation_atomicity(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_c"
    store = TransactionalStore.create_project(project_dir)

    # 1. Setup baseline & complete realizations so we can create an active release authorization
    intents = {i: {"dialogue": f"line {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-01", {"title": "Ep 1"}, intents)

    closure = []
    for cid in range(1, 6):
        rev = _seed_test_realization(
            store, rev, cid, asset_id=f"asset-{cid}", asset_path=f"/img/{cid}.png", content_hash=f"hash-{cid}"
        )
        closure.append({"cut_id": cid, "realized_revision": 1, "asset_id": f"asset-{cid}"})

    # Register review artifact and authorize release
    rev = store.register_review_artifact(
        rev, artifact_id="ART-01", content_hash="arthash-01", composition_revision=0, cut_closure=closure
    )
    rev = store.authorize_release(rev, authorization_id="AUTH-01", artifact_id="ART-01", content_hash="arthash-01")

    # Verify active authorization is present
    snap = store.snapshot()
    assert snap["release_authorization"]["active"] is not None
    assert snap["release_authorization"]["active"]["authorization_id"] == "AUTH-01"

    # Now, accept receiver-visible composition change:
    # This must increment composition revision AND revoke active authorization in the EXACT same transaction!
    current_auth_rev = snap["authority_revision"]
    new_auth_rev, new_comp_rev = store.accept_composition(
        expected_authority_revision=current_auth_rev,
        expected_composition_revision=0,
        state={"bubbles": [{"cut_id": 1, "text": "new bubble", "x": 10, "y": 10}]},
    )
    assert new_comp_rev == 1
    assert new_auth_rev == current_auth_rev + 1

    # Read back snapshot from new connection:
    # Must observe new composition AND revoked authorization together.
    # No intermediate state where new composition coexists with active AUTH-01!
    store_read = TransactionalStore.open_project(project_dir)
    snap_after = store_read.snapshot()
    assert snap_after["composition"]["revision"] == 1
    assert snap_after["release_authorization"]["active"] is None
    assert len(snap_after["release_authorization"]["history"]) == 1
    history_auth = snap_after["release_authorization"]["history"][0]
    assert history_auth["authorization_id"] == "AUTH-01"
    assert history_auth["revoked_authority_revision"] == new_auth_rev

    # Stale CAS writer test on composition
    with pytest.raises(ConflictError) as exc_info:
        store.accept_composition(
            expected_authority_revision=current_auth_rev,  # STALE authority revision
            expected_composition_revision=1,
            state={"bubbles": []},
        )
    assert exc_info.value.expected == current_auth_rev
    assert exc_info.value.actual == new_auth_rev


def test_acceptance_c_concurrent_writers_conflict(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_c_concurrent"
    store = TransactionalStore.create_project(project_dir)
    intents = {i: {"text": f"cut {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-01", {}, intents)

    # Two writers attempt to write with the exact same expected_authority_revision (rev)
    results = []
    errors = []

    def writer_task(writer_id: int) -> None:
        local_store = TransactionalStore.open_project(project_dir)
        try:
            r = local_store.accept_cut_intent(
                expected_authority_revision=rev,
                cut_id=1,
                intent_payload={"text": f"intent from writer {writer_id}"},
            )
            results.append((writer_id, r))
        except ConflictError as ce:
            errors.append((writer_id, ce))

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(writer_task, 1)
        f2 = executor.submit(writer_task, 2)
        f1.result()
        f2.result()

    # Exactly one writer must succeed, and exactly one must fail with ConflictError
    assert len(results) == 1
    assert len(errors) == 1
    winner_id, winner_rev = results[0]
    loser_id, loser_err = errors[0]
    assert winner_rev == rev + 1
    assert loser_err.expected == rev
    assert loser_err.actual == rev + 1

    # Final DB check: no split-brain
    snap = store.snapshot()
    assert snap["authority_revision"] == rev + 1
    cut1_intent = [c for c in snap["cuts"] if c["cut_id"] == 1][0]["effective_intent"]
    assert cut1_intent["text"] == f"intent from writer {winner_id}"


# ---------------------------------------------------------------------------
# Acceptance D: Truthful Currency and Complete calculation
# ---------------------------------------------------------------------------


def test_acceptance_d_currency_and_complete_truth(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_d"
    store = TransactionalStore.create_project(project_dir)

    # Brand new project with no intents:
    # All cuts have desired_revision=None, realized_revision=None -> STALE, UNRESOLVED
    snap0 = store.snapshot()
    assert snap0["realization_complete"]["complete"] is False
    assert snap0["realization_complete"]["status"] == "UNRESOLVED"
    for c in snap0["cuts"]:
        assert c["currency"] == "STALE"

    # Approve baseline rev 1
    intents = {i: {"text": f"cut {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-01", {}, intents)

    # Create dummy image files on disk for all 5 cuts
    assets_dir = project_dir / "assets"
    assets_dir.mkdir()
    asset_files = []
    for cid in range(1, 6):
        f = assets_dir / f"cut_{cid}.png"
        f.write_bytes(b"PNG_DATA_PLACEHOLDER")
        asset_files.append(f)

    # Realize cuts 1 through 4 (desired_revision=1, realized_revision=1)
    for cid in range(1, 5):
        rev = _seed_test_realization(
            store, rev, cid, f"asset-{cid}", str(asset_files[cid - 1]), f"hash-{cid}"
        )

    # Cut 5 is NOT realized (desired_revision=1, realized_revision=None)
    snap_partial = store.snapshot()
    assert snap_partial["cuts"][4]["currency"] == "STALE"
    assert snap_partial["realization_complete"]["complete"] is False
    assert snap_partial["realization_complete"]["status"] == "UNRESOLVED"

    # Now realize cut 5 as well
    rev = _seed_test_realization(
        store, rev, 5, "asset-5", str(asset_files[4]), "hash-5"
    )

    # Now all 5 cuts have desired_revision == realized_revision == 1
    snap_full = store.snapshot()
    for c in snap_full["cuts"]:
        assert c["currency"] == "CURRENT"
    assert snap_full["realization_complete"]["complete"] is True
    assert snap_full["realization_complete"]["status"] == "COMPLETE"

    # Modify cut 3 intent to rev 2:
    # Even though valid asset-3 exists on disk, cut 3 has desired_revision=2 != realized_revision=1!
    rev = store.accept_cut_intent(rev, 3, {"text": "cut 3 revised"})
    snap_stale = store.snapshot()
    cut3 = [c for c in snap_stale["cuts"] if c["cut_id"] == 3][0]
    assert cut3["desired_revision"] == 2
    assert cut3["realized_revision"] == 1
    assert cut3["currency"] == "STALE"  # Asset file presence does NOT grant currency!
    assert snap_stale["realization_complete"]["complete"] is False
    assert snap_stale["realization_complete"]["status"] == "UNRESOLVED"

    # Finally, realize cut 3 rev 2:
    rev = _seed_test_realization(
        store, rev, 3, "asset-3-v2", str(asset_files[2]), "hash-3-v2"
    )

    snap_complete_again = store.snapshot()
    for c in snap_complete_again["cuts"]:
        assert c["currency"] == "CURRENT"
    assert snap_complete_again["realization_complete"]["complete"] is True
    assert snap_complete_again["realization_complete"]["status"] == "COMPLETE"


# ---------------------------------------------------------------------------
# Acceptance E: Restart and multi-process persistence
# ---------------------------------------------------------------------------


def test_acceptance_e_restart_authoritative_persistence(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_e"
    store = TransactionalStore.create_project(project_dir)

    # Write all truth dimensions:
    # 1. Baseline & intents
    intents = {i: {"text": f"c{i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-E", {"meta": "data"}, intents)

    # 2. Composition
    rev, _ = store.accept_composition(rev, 0, {"layers": [1, 2, 3]})

    # 3. Realizations
    closure = []
    for cid in range(1, 6):
        rev = _seed_test_realization(
            store, rev, cid, f"asset-e-{cid}", f"/path/e/{cid}.png", f"hash-e-{cid}"
        )
        closure.append({"cut_id": cid, "realized_revision": 1, "asset_id": f"asset-e-{cid}"})

    # 4. Review Artifact & Authorization
    rev = store.register_review_artifact(rev, "ART-E", "arthash-e", 1, closure)
    rev = store.authorize_release(rev, "AUTH-E", "ART-E", "arthash-e")

    # 5. Delivery Attempt
    rev = store.start_delivery_attempt(rev, "DEL-E", "blogger", "AUTH-E", "req-e-01")
    rev = store.record_delivery_observation(
        rev,
        "DEL-E",
        "confirmed_success",
        evidence={"blogger_post_id": "b-999"},
        destination_id="post-999",
        destination_url="https://blog.example.com/post-999",
    )

    # Close store reference
    del store

    # Spawn a fresh Python subprocess to read snapshot
    code = f"""
import json
from comic_new.store import TransactionalStore
store = TransactionalStore.open_project({repr(str(project_dir))})
snap = store.snapshot()
print(json.dumps(snap))
"""
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    snap = json.loads(proc.stdout)

    assert snap["authority_revision"] == rev
    assert snap["baseline"]["baseline_id"] == "BASE-E"
    assert snap["composition"]["revision"] == 1
    assert snap["realization_complete"]["complete"] is True
    assert len(snap["review_artifacts"]) == 1
    assert snap["review_artifacts"][0]["artifact_id"] == "ART-E"
    assert snap["release_authorization"]["active"]["authorization_id"] == "AUTH-E"
    assert len(snap["delivery_attempts"]) == 1
    assert snap["delivery_attempts"][0]["outcome"] == "confirmed_success"
    assert snap["delivery_attempts"][0]["destination_id"] == "post-999"


# ---------------------------------------------------------------------------
# Acceptance F: Boundary separation, interrupted jobs, stale commit rejection
# ---------------------------------------------------------------------------


def test_acceptance_f_interrupted_job_does_not_revoke_desired_intent(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_f1"
    store = TransactionalStore.create_project(project_dir)

    intents = {i: {"text": f"panel {i}", "prompt": f"prompt for panel {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-F", {}, intents)

    from comic_new.generation import GenerationService
    svc = GenerationService(store)
    enq = svc.enqueue(cut_id=1, expected_authority_revision=rev)
    jid = enq.jobs[0]["job_id"]
    att_id = f"att-{jid}-1"

    # Start attempt
    with store._connect() as con:
        con.execute("BEGIN IMMEDIATE;")
        con.execute("UPDATE generation_jobs SET status = 'running' WHERE job_id = ?", (jid,))
        con.execute(
            "INSERT INTO generation_attempts (attempt_id, job_id, ordinal, status, started_at, runner_id) VALUES (?, ?, 1, 'running', '2026-09-15T00:00:00Z', 'runner-test')",
            (att_id, jid),
        )
        con.execute("COMMIT;")

    # Simulate interruption (STOP / system crash)
    store.mark_attempts_and_jobs_interrupted([(jid, att_id)], reason="Subprocess interrupted")

    # Authoritative readback:
    snap = store.snapshot()
    # Job status is interrupted:
    job = [j for j in snap["jobs"] if j["job_id"] == jid][0]
    assert job["status"] == "interrupted"

    # Accepted desired intent is preserved and NOT retracted:
    cut1 = [c for c in snap["cuts"] if c["cut_id"] == 1][0]
    assert cut1["desired_revision"] == 1
    assert cut1["effective_intent"] == {"text": "panel 1", "prompt": "prompt for panel 1"}
    assert cut1["currency"] == "STALE"


def test_acceptance_f_stale_realization_commit_rejection(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_f2"
    store = TransactionalStore.create_project(project_dir)

    intents = {i: {"text": f"panel {i}", "prompt": f"prompt for panel {i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-F2", {}, intents)

    from comic_new.generation import GenerationService
    svc = GenerationService(store)
    enq = svc.enqueue(cut_id=2, expected_authority_revision=rev)
    jid = enq.jobs[0]["job_id"]
    staging_dir = project_dir / ".generation-staging"
    store.acquire_runner_ownership("runner-test", 9999, "9999:0")
    claimed = store.claim_next_generation_job("runner-test", 9999, "9999:0", 0, staging_dir)
    assert claimed is not None

    # User modifies cut 2 intent to revision 2 before the job completes!
    rev = store.accept_cut_intent(
        store.snapshot()["authority_revision"],
        cut_id=2,
        intent_payload={"text": "panel 2 revised", "prompt": "revised prompt"},
    )

    cand_path = Path(claimed["staging_path"])
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    cand_path.write_bytes(b"cand")

    # Stale candidate rejected by commit gate:
    res = store.commit_candidate(
        runner_id="runner-test",
        job_id=jid,
        attempt_id=claimed["attempt_id"],
        candidate_png_path=cand_path,
        content_hash="hash-stale",
    )
    assert res["status"] == "superseded"
    # Verify that job is recorded as superseded, authority revision incremented, and cuts.realized_* untouched
    snap = store.snapshot()
    job = [j for j in snap["jobs"] if j["job_id"] == jid][0]
    assert job["status"] == "superseded"
    assert "superseded" in job["terminal_detail"]

    cut2 = [c for c in snap["cuts"] if c["cut_id"] == 2][0]
    assert cut2["desired_revision"] == 2
    assert cut2["realized_revision"] is None  # Untouched! Stale overwrite prevented!
    assert cut2["realized_asset_id"] is None
    assert cut2["currency"] == "STALE"


def test_acceptance_f_delivery_truth_separation(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_f3"
    store = TransactionalStore.create_project(project_dir)

    intents = {i: {"text": f"c{i}"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-F3", {}, intents)

    closure = []
    for cid in range(1, 6):
        rev = _seed_test_realization(store, rev, cid, f"a-{cid}", f"/p/{cid}", f"h-{cid}")
        closure.append({"cut_id": cid, "realized_revision": 1, "asset_id": f"a-{cid}"})

    rev = store.register_review_artifact(rev, "ART-F3", "hash-f3", 0, closure)
    rev = store.authorize_release(rev, "AUTH-F3", "ART-F3", "hash-f3")

    # Starting delivery attempt sets outcome to unknown
    rev = store.start_delivery_attempt(rev, "DEL-01", "png", "AUTH-F3", "req-01")
    snap = store.snapshot()
    deliv = snap["delivery_attempts"][0]
    assert deliv["outcome"] == "unknown"  # Having authorization does NOT imply delivery success!

    # Recording confirmed_success requires destination_id, destination_url, and evidence
    with pytest.raises(ValidationError):
        store.record_delivery_observation(
            expected_authority_revision=rev,
            attempt_id="DEL-01",
            outcome="confirmed_success",
            evidence=None,  # Missing evidence!
        )

    # Valid confirmed_success recording
    rev = store.record_delivery_observation(
        expected_authority_revision=rev,
        attempt_id="DEL-01",
        outcome="confirmed_success",
        evidence={"bytes_written": 1024},
        destination_id="file-exported",
        destination_url="file:///tmp/comic.png",
    )
    snap2 = store.snapshot()
    assert snap2["delivery_attempts"][0]["outcome"] == "confirmed_success"
