"""Load-bearing integration and lifecycle tests for BLOCK-02: Unified Generation Engine.

Verifies:
- PLAN-001 §11.1 Scenarios A-G
- BLOCK-02 Exit Predicates 1-16
- Process tree termination, PID start token protection, staging lifecycle, and Pillow decode.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import threading

import pytest
from PIL import Image

from comic_new.generation import (
    GenerationRunner,
    GenerationService,
    find_descendant_pids,
    find_session_or_group_pids,
    get_process_start_token,
    is_pid_non_zombie_alive,
    is_process_alive_with_token,
)
from comic_new.store import (
    ConflictError,
    RunnerAlreadyActiveError,
    StoreCorruptionError,
    TransactionalStore,
    TransactionalStoreError,
    ValidationError,
)

MOCK_PROVIDER = str(Path(__file__).parent / "mock_provider.py")


def _provider_cmd(
    cut_id: int,
    staging_path: Path,
    target_rev: int,
    *,
    mock_sleep: float = 0.0,
    mock_exit_code: int = 0,
    mock_spawn_descendant: bool = False,
    mock_corrupt_png: bool = False,
    mock_no_output: bool = False,
    mock_gate_file: str | None = None,
    mock_record_stdin: str | None = None,
) -> list[str]:
    cmd = [
        sys.executable,
        MOCK_PROVIDER,
        "gen",
        "--stdin",
        "--mode",
        "direct",
        "--no-size-nudge",
        "--model",
        "mock-model",
        "--size",
        "1024x1536",
        "--quality",
        "high",
        "--timeout",
        "60",
        "-o",
        str(staging_path),
        "--json",
    ]
    if mock_sleep > 0:
        cmd += ["--mock-sleep", str(mock_sleep)]
    if mock_exit_code != 0:
        cmd += ["--mock-exit-code", str(mock_exit_code)]
    if mock_spawn_descendant:
        cmd += ["--mock-spawn-descendant"]
    if mock_corrupt_png:
        cmd += ["--mock-corrupt-png"]
    if mock_no_output:
        cmd += ["--mock-no-output"]
    if mock_gate_file:
        cmd += ["--mock-gate-file", str(mock_gate_file)]
    if mock_record_stdin:
        cmd += ["--mock-record-stdin", str(mock_record_stdin)]
    return cmd


def _init_five_cut_project(project_dir: Path) -> tuple[TransactionalStore, int]:
    store = TransactionalStore.create_project(project_dir)
    intents = {i: {"prompt": f"Dramatic panel {i} description"} for i in range(1, 6)}
    rev = store.approve_structural_baseline(0, "BASE-001", {"genre": "comic"}, intents)
    return store, rev


# ---------------------------------------------------------------------------
# Scenario A / Exit 1, 3: Unified all/single queue and no sidecar files
# ---------------------------------------------------------------------------


def test_scenario_a_unified_enqueue_all_and_single(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_a"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # 1. Enqueue all 1..5
    receipt_all = service.enqueue(cut_id=None, expected_authority_revision=rev)
    assert len(receipt_all.jobs) == 5
    assert [j["cut_id"] for j in receipt_all.jobs] == [1, 2, 3, 4, 5]
    for j in receipt_all.jobs:
        assert j["target_desired_revision"] == 1

    # Verify no sidecar queue files or lock files exist
    files = list(project_dir.iterdir())
    for f in files:
        assert not f.name.endswith(".lock"), f"Forbidden lock file: {f}"
        assert not f.name.endswith(".json"), f"Forbidden JSON queue file: {f}"

    # Read raw SQLite table in a separate connection
    with store._connect() as con:
        rows = con.execute("SELECT job_id, cut_id, status FROM generation_jobs ORDER BY cut_id").fetchall()
        assert len(rows) == 5
        for r in rows:
            assert r["status"] == "queued"

    # 2. Single cut enqueue uses the exact same queue table and status
    new_rev = receipt_all.authority_revision
    receipt_single = service.enqueue(cut_id=2, expected_authority_revision=new_rev)
    assert len(receipt_single.jobs) == 1
    assert receipt_single.jobs[0]["cut_id"] == 2

    with store._connect() as con:
        rows = con.execute("SELECT job_id, cut_id, status FROM generation_jobs WHERE cut_id = 2").fetchall()
        assert len(rows) == 2  # One from all, one from single


# ---------------------------------------------------------------------------
# Scenario B / Exit 2: Concurrency two, stdin prompt, valid PNG, candidate commit
# ---------------------------------------------------------------------------


def test_scenario_b_success_and_concurrency_two(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_b"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    service.enqueue(cut_id=None, expected_authority_revision=rev)

    stdin_record_dir = tmp_path / "stdin_records"
    stdin_record_dir.mkdir()

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        record_file = stdin_record_dir / f"cut_{cut_id}.txt"
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=0.25,
            mock_record_stdin=str(record_file),
        )

    # Polling monitor during run_until_idle to measure live generation helper PIDs in /proc
    sampled_counts: list[int] = []
    stop_monitor = threading.Event()

    def monitor_live_roots() -> None:
        while not stop_monitor.is_set():
            with store._connect() as con:
                rows = con.execute("SELECT process_pid FROM generation_attempts WHERE status = 'running'").fetchall()
                running_pids = [r["process_pid"] for r in rows if r["process_pid"] is not None]
            live = [p for p in running_pids if is_pid_non_zombie_alive(p)]
            sampled_counts.append(len(live))
            time.sleep(0.02)

    mon_t = threading.Thread(target=monitor_live_roots, daemon=True)
    mon_t.start()

    runner = GenerationRunner(
        store,
        provider_cmd_factory=cmd_factory,
    )
    receipt = runner.run_until_idle()
    stop_monitor.set()
    mon_t.join()

    assert max(sampled_counts, default=0) <= 2
    assert 2 in sampled_counts

    with pytest.raises(TypeError):
        GenerationRunner(store, concurrency=3)

    # Verify all jobs succeeded
    assert receipt.terminal_counts.get("succeeded") == 5
    snap = store.snapshot()
    for cut in snap["cuts"]:
        cid = cut["cut_id"]
        record_file = stdin_record_dir / f"cut_{cid}.txt"
        assert record_file.is_file(), f"Missing stdin record for cut {cid}"
        assert record_file.read_text(encoding="utf-8") == f"Dramatic panel {cid} description"

        # Check canonical asset promotion
        canonical_path = Path(cut["realized_asset_path"])
        assert canonical_path.is_file()
        assert canonical_path.name.startswith(f"rev-1-")
        with Image.open(canonical_path) as im:
            assert im.format == "PNG"
            im.verify()

    # Verify staging directory is cleaned up
    staging_dir = project_dir / ".generation-staging"
    if staging_dir.exists():
        for job_staging in staging_dir.iterdir():
            assert not (job_staging / "candidate.png").exists()

    # Realization complete is true
    assert snap["realization_complete"]["complete"] is True
    assert snap["realization_complete"]["status"] == "COMPLETE"


# ---------------------------------------------------------------------------
# Scenario B-failure / Exit 7, 8, 9: Nonzero exit, timeout, missing, corrupt PNG
# ---------------------------------------------------------------------------


def test_scenario_b_failures(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_b_fail"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # Cut 1: Nonzero exit
    # Cut 2: Timeout with descendant process
    # Cut 3: Missing output
    # Cut 4: Corrupt/truncated PNG
    service.enqueue(cut_id=None, expected_authority_revision=rev)

    def fail_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        if cut_id == 1:
            return _provider_cmd(cut_id, staging_path, target_rev, mock_exit_code=42)
        elif cut_id == 2:
            return _provider_cmd(
                cut_id,
                staging_path,
                target_rev,
                mock_sleep=2.0,
                mock_spawn_descendant=True,
            )
        elif cut_id == 3:
            return _provider_cmd(cut_id, staging_path, target_rev, mock_no_output=True)
        elif cut_id == 4:
            return _provider_cmd(cut_id, staging_path, target_rev, mock_corrupt_png=True)
        else:
            return _provider_cmd(cut_id, staging_path, target_rev)

    runner = GenerationRunner(
        store,
        provider_cmd_factory=fail_factory,
        provider_timeout=0.4,  # Fast timeout for test
    )
    receipt = runner.run_until_idle()

    assert receipt.terminal_counts.get("failed", 0) >= 4

    snap = store.snapshot()
    # Check cut failure details
    jobs_by_cut = {j["cut_id"]: j for j in snap["jobs"]}

    assert "exited with code 42" in jobs_by_cut[1]["terminal_detail"]
    assert "timed out" in jobs_by_cut[2]["terminal_detail"]
    assert "Validation failed" in jobs_by_cut[3]["terminal_detail"]
    assert "PNG decoding failed" in jobs_by_cut[4]["terminal_detail"]

    # Cuts 1..4 have NOT been realized: currency is STALE
    for cid in range(1, 5):
        assert snap["cuts"][cid - 1]["realized_revision"] is None
        assert snap["cuts"][cid - 1]["currency"] == "STALE"
    assert snap["realization_complete"]["complete"] is False


# ---------------------------------------------------------------------------
# Scenario C / Exit 4, 5, 6, 7: Late stale race preserving newer realization bytes
# ---------------------------------------------------------------------------


def test_scenario_c_stale_revision_race(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_c"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # Job A for Cut 1 at desired revision 1
    rec_a = service.enqueue(cut_id=1, expected_authority_revision=rev)
    job_a_id = rec_a.jobs[0]["job_id"]

    # Gate file to hold Job A in running state
    gate_file = tmp_path / "job_a_gate.txt"

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        if target_rev == 1:
            return _provider_cmd(cut_id, staging_path, target_rev, mock_gate_file=str(gate_file))
        return _provider_cmd(cut_id, staging_path, target_rev)

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)

    t_runner = threading.Thread(target=runner.run_until_idle, daemon=True)
    t_runner.start()

    # Wait until Job A is running in DB and held at mock_gate_file
    for _ in range(50):
        with store._connect() as con:
            r = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_a_id,)).fetchone()
            if r and r["status"] == "running":
                break
        time.sleep(0.05)
    with store._connect() as con:
        r = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_a_id,)).fetchone()
        assert r["status"] == "running"

    # User modifies cut 1 intent to revision 2!
    rev = store.snapshot()["authority_revision"]
    rev = store.accept_cut_intent(rev, cut_id=1, intent_payload={"prompt": "Panel 1 Revised v2"})

    # Enqueue Job B for revision 2 while Job A is still running and blocked on gate
    rec_b = service.enqueue(cut_id=1, expected_authority_revision=rev)
    job_b_id = rec_b.jobs[0]["job_id"]

    # Sibling worker claims and finishes Job B while Job A is STILL BLOCKED on gate_file
    for _ in range(50):
        with store._connect() as con:
            rb = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_b_id,)).fetchone()
            if rb and rb["status"] == "succeeded":
                break
        time.sleep(0.05)

    # Verify Job B committed and canonical bytes/hash are present while Job A is STILL running
    with store._connect() as con:
        ra = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_a_id,)).fetchone()
        rb = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_b_id,)).fetchone()
        assert ra["status"] == "running", "Job A must still be running while B is completed"
        assert rb["status"] == "succeeded", "Job B must have completed first"

    snap_mid = store.snapshot()
    cut1_mid = snap_mid["cuts"][0]
    assert cut1_mid["realized_revision"] == 2
    canonical_b_path = Path(cut1_mid["realized_asset_path"])
    assert canonical_b_path.is_file()
    canonical_b_bytes = canonical_b_path.read_bytes()
    canonical_b_hash = cut1_mid["realized_content_hash"]

    # Now release gate file so late Job A proceeds to its commit gate
    gate_file.touch()
    t_runner.join(timeout=10.0)
    assert not t_runner.is_alive()

    # Job A reached commit_candidate: cut 1 desired_revision is 2, so Job A (target rev 1) is superseded!
    snap_final = store.snapshot()
    job_a = [j for j in snap_final["jobs"] if j["job_id"] == job_a_id][0]
    assert job_a["status"] == "superseded"
    assert "superseded" in job_a["terminal_detail"]
    assert job_a["attempts"][0]["status"] == "succeeded"  # Attempt executed honestly

    # Late Job A must NOT overwrite or alter Job B's canonical file, bytes, or content hash!
    cut1_final = snap_final["cuts"][0]
    assert cut1_final["realized_revision"] == 2
    assert cut1_final["realized_content_hash"] == canonical_b_hash
    assert Path(cut1_final["realized_asset_path"]).read_bytes() == canonical_b_bytes
# ---------------------------------------------------------------------------
# Scenario D / Exit 7: Pending and running cancellation
# ---------------------------------------------------------------------------


def test_scenario_d_cancel_pending_and_running(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_d"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # 1. Cancel pending queued job
    rec = service.enqueue(cut_id=1, expected_authority_revision=rev)
    job_id = rec.jobs[0]["job_id"]

    cancel_rec = service.cancel(job_id)
    assert cancel_rec.disposition == "cancelled"
    assert cancel_rec.was_running is False

    snap = store.snapshot()
    j = [job for job in snap["jobs"] if job["job_id"] == job_id][0]
    assert j["status"] == "cancelled"
    assert len(j["attempts"]) == 0  # Process was never spawned!

    # 2. Cancel running job with descendant process
    gate_file = tmp_path / "gate_d.txt"

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=2.0,
            mock_spawn_descendant=True,
            mock_gate_file=str(gate_file),
        )

    rec2 = service.enqueue(cut_id=2, expected_authority_revision=snap["authority_revision"])
    job2_id = rec2.jobs[0]["job_id"]

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)

    t = threading.Thread(target=runner.run_until_idle)
    t.start()

    time.sleep(0.3)
    # Check running
    with store._connect() as con:
        att = con.execute("SELECT process_pid FROM generation_attempts WHERE job_id = ? AND status = 'running'", (job2_id,)).fetchone()
        assert att is not None
        pid = att["process_pid"]

    # Cancel running job
    cancel_rec2 = service.cancel(job2_id)
    assert cancel_rec2.disposition == "cancelled"
    assert cancel_rec2.was_running is True

    # Unblock gate to let worker loop terminate
    gate_file.touch()
    t.join()

    # Verify process is not alive
    assert not is_pid_non_zombie_alive(pid)

    snap2 = store.snapshot()
    j2 = [job for job in snap2["jobs"] if job["job_id"] == job2_id][0]
    assert j2["status"] == "cancelled"
    assert j2["attempts"][0]["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Scenario E / Exit 10, 11, 12: Global STOP physical and durable effects
# ---------------------------------------------------------------------------


def test_scenario_e_global_stop(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_e"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # Enqueue all 5
    service.enqueue(cut_id=None, expected_authority_revision=rev)

    gate_file = tmp_path / "gate_e.txt"

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=5.0,
            mock_spawn_descendant=True,
            mock_gate_file=str(gate_file),
        )

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)

    t = threading.Thread(target=runner.run_until_idle)
    t.start()

    # Wait until two workers are actively running in DB
    pids = []
    for _ in range(50):
        with store._connect() as con:
            rows = con.execute("SELECT process_pid FROM generation_attempts WHERE status = 'running'").fetchall()
            pids = [r["process_pid"] for r in rows if r["process_pid"] is not None]
            if len(pids) == 2:
                break
        time.sleep(0.05)

    assert len(pids) == 2

    # Invoke global STOP
    stop_rec = service.stop_all()
    assert stop_rec.stop_epoch >= 1
    assert stop_rec.interrupted_running_count == 2

    gate_file.touch()
    t.join()

    # Verify both process trees are dead
    for p in pids:
        assert not is_pid_non_zombie_alive(p)

    snap = store.snapshot()
    # Running jobs were marked interrupted
    # Queued jobs were cancelled
    st_counts = {}
    for j in snap["jobs"]:
        st_counts[j["status"]] = st_counts.get(j["status"], 0) + 1

    assert st_counts.get("interrupted") == 2
    assert st_counts.get("cancelled") == 3

    # All desired revisions and intents are preserved!
    for cut in snap["cuts"]:
        assert cut["desired_revision"] == 1
        assert cut["currency"] == "STALE"


# ---------------------------------------------------------------------------
# Scenario F / Exit 13, 14: Runner crash (SIGKILL) and startup recovery
# ---------------------------------------------------------------------------


def test_scenario_f_restart_recovery(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_f"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    service.enqueue(cut_id=None, expected_authority_revision=rev)

    # Spawn a child runner in a separate process that starts workers
    runner_code = f"""
import sys, time
from pathlib import Path
from comic_new.store import TransactionalStore
from comic_new.generation import GenerationRunner

def cmd_factory(cut_id, staging_path, target_rev):
    return [
        sys.executable,
        {repr(MOCK_PROVIDER)},
        "gen",
        "--stdin",
        "-o", str(staging_path),
        "--mock-sleep", "10",
        "--mock-spawn-descendant",
        "--json"
    ]

store = TransactionalStore.open_project({repr(str(project_dir))})
runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)
runner.run_until_idle()
"""
    runner_proc = subprocess.Popen(
        [sys.executable, "-c", runner_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait until attempts are marked running in DB
    pids = []
    tree_pids = set()
    for _ in range(50):
        with store._connect() as con:
            rows = con.execute("SELECT process_pid, process_group_id FROM generation_attempts WHERE status = 'running'").fetchall()
            pids = [r["process_pid"] for r in rows if r["process_pid"] is not None]
            if len(pids) >= 1:
                break
        time.sleep(0.1)

    assert len(pids) >= 1
    for p in pids:
        tree_pids.add(p)
        tree_pids.update(find_descendant_pids(p))
        tree_pids.update(find_session_or_group_pids(p))
    # SIGKILL the runner process (simulating hard power loss or OOM kill)
    os.kill(runner_proc.pid, signal.SIGKILL)
    runner_proc.wait()

    # Now open project and start official runner (which runs startup reconciliation)
    recovered_store = TransactionalStore.open_project(project_dir)

    def normal_cmd(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(cut_id, staging_path, target_rev)

    new_runner = GenerationRunner(recovered_store, provider_cmd_factory=normal_cmd)
    new_receipt = new_runner.run_until_idle()
    # Verify all orphaned processes (recorded root AND reparented descendants) are dead
    for p in tree_pids:
        assert not is_pid_non_zombie_alive(p), f"Process {p} is still alive after startup recovery!"

    snap = recovered_store.snapshot()
    interrupted_jobs = [j for j in snap["jobs"] if j["status"] == "interrupted"]
    assert len(interrupted_jobs) >= 1
    for j in interrupted_jobs:
        assert "startup_recovery" in j["terminal_detail"]

    # Queued jobs that were not claimed before the crash were processed by new_runner
    succeeded_jobs = [j for j in snap["jobs"] if j["status"] == "succeeded"]
    assert len(succeeded_jobs) + len(interrupted_jobs) == 5


# ---------------------------------------------------------------------------
# Scenario G / Exit 15, 16: Queue drained vs Realization Complete separation
# ---------------------------------------------------------------------------


def test_scenario_g_queue_vs_completion_truth(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj_g"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)

    # 1. Enqueue single cut 1
    service.enqueue(cut_id=1, expected_authority_revision=rev)

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(cut_id, staging_path, target_rev)

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)
    receipt = runner.run_until_idle()

    assert receipt.terminal_counts.get("succeeded") == 1

    # Queue is empty (0 queued, 0 running)
    snap = store.snapshot()
    queued_cnt = len([j for j in snap["jobs"] if j["status"] in ("queued", "running")])
    assert queued_cnt == 0

    # BUT realization is UNRESOLVED because cuts 2..5 are still stale!
    assert snap["realization_complete"]["complete"] is False
    assert snap["realization_complete"]["status"] == "UNRESOLVED"
    assert snap["cuts"][0]["currency"] == "CURRENT"
    assert snap["cuts"][1]["currency"] == "STALE"

    # 2. Complete remaining cuts 2..5
    rev2 = snap["authority_revision"]
    for cid in range(2, 6):
        service.enqueue(cut_id=cid, expected_authority_revision=rev2)
        runner2 = GenerationRunner(store, provider_cmd_factory=cmd_factory)
        runner2.run_until_idle()
        rev2 = store.snapshot()["authority_revision"]
    snap_final = store.snapshot()
    for cut in snap_final["cuts"]:
        assert cut["currency"] == "CURRENT"
    assert snap_final["realization_complete"]["complete"] is True
    assert snap_final["realization_complete"]["status"] == "COMPLETE"


# ---------------------------------------------------------------------------
# v1 -> v2 Migration Test
# ---------------------------------------------------------------------------


def _create_v1_fixture_project(project_dir: Path) -> Path:
    """Create an exact reproducible v1 project fixture directly inside project_dir."""
    import sqlite3
    from PIL import Image
    import hashlib

    project_dir.mkdir(parents=True, exist_ok=True)
    db_path = project_dir / "comic-new.sqlite3"
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA application_id = 0x434f4d43;")
    con.execute("PRAGMA user_version = 1;")

    v1_sql = """
    CREATE TABLE authority (
        singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
        authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
        current_baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id)
    );

    CREATE TABLE structural_baselines (
        baseline_id TEXT PRIMARY KEY,
        structure_json TEXT NOT NULL CHECK (json_valid(structure_json)),
        authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
        created_at TEXT NOT NULL
    );

    CREATE TABLE cut_intents (
        cut_id INTEGER NOT NULL CHECK (cut_id BETWEEN 1 AND 5),
        revision INTEGER NOT NULL CHECK (revision > 0),
        baseline_id TEXT NULL REFERENCES structural_baselines(baseline_id),
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        authority_revision INTEGER NOT NULL CHECK (authority_revision >= 0),
        created_at TEXT NOT NULL,
        PRIMARY KEY (cut_id, revision)
    );

    CREATE TABLE cuts (
        cut_id INTEGER PRIMARY KEY CHECK (cut_id BETWEEN 1 AND 5),
        desired_revision INTEGER NULL CHECK (desired_revision IS NULL OR desired_revision > 0),
        realized_revision INTEGER NULL CHECK (realized_revision IS NULL OR realized_revision > 0),
        realized_asset_id TEXT NULL,
        realized_asset_path TEXT NULL,
        realized_content_hash TEXT NULL,
        CHECK (
            (realized_revision IS NULL AND realized_asset_id IS NULL AND realized_asset_path IS NULL AND realized_content_hash IS NULL) OR
            (realized_revision IS NOT NULL AND realized_asset_id IS NOT NULL AND realized_asset_path IS NOT NULL AND realized_content_hash IS NOT NULL)
        ),
        FOREIGN KEY (cut_id, desired_revision) REFERENCES cut_intents(cut_id, revision)
    );

    CREATE TABLE baseline_intents (
        baseline_id TEXT NOT NULL REFERENCES structural_baselines(baseline_id) ON DELETE CASCADE,
        cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
        intent_revision INTEGER NOT NULL CHECK (intent_revision > 0),
        PRIMARY KEY (baseline_id, cut_id),
        FOREIGN KEY (cut_id, intent_revision) REFERENCES cut_intents(cut_id, revision)
    );

    CREATE TABLE composition (
        singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
        revision INTEGER NOT NULL CHECK (revision >= 0),
        state_json TEXT NOT NULL CHECK (json_valid(state_json)),
        updated_at TEXT NOT NULL
    );

    CREATE TABLE generation_jobs (
        job_id TEXT PRIMARY KEY,
        cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
        target_desired_revision INTEGER NOT NULL CHECK (target_desired_revision > 0),
        status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted', 'superseded')),
        terminal_detail TEXT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE generation_attempts (
        attempt_id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES generation_jobs(job_id) ON DELETE CASCADE,
        ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
        status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'interrupted', 'cancelled')),
        started_at TEXT NOT NULL,
        finished_at TEXT NULL,
        detail TEXT NULL,
        UNIQUE (job_id, ordinal)
    );

    CREATE TABLE review_artifacts (
        artifact_id TEXT PRIMARY KEY,
        content_hash TEXT NOT NULL UNIQUE,
        composition_revision INTEGER NOT NULL CHECK (composition_revision >= 0),
        created_at TEXT NOT NULL
    );

    CREATE TABLE artifact_cuts (
        artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id) ON DELETE CASCADE,
        cut_id INTEGER NOT NULL REFERENCES cuts(cut_id) CHECK (cut_id BETWEEN 1 AND 5),
        realized_revision INTEGER NOT NULL CHECK (realized_revision > 0),
        asset_id TEXT NOT NULL,
        PRIMARY KEY (artifact_id, cut_id)
    );

    CREATE TABLE release_authorizations (
        authorization_id TEXT PRIMARY KEY,
        artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id),
        artifact_content_hash TEXT NOT NULL,
        authorized_authority_revision INTEGER NOT NULL CHECK (authorized_authority_revision >= 0),
        revoked_authority_revision INTEGER NULL CHECK (revoked_authority_revision IS NULL OR revoked_authority_revision >= 0),
        created_at TEXT NOT NULL,
        revoked_at TEXT NULL
    );

    CREATE UNIQUE INDEX idx_active_release_authorization
    ON release_authorizations ((1))
    WHERE revoked_authority_revision IS NULL;

    CREATE TABLE delivery_attempts (
        attempt_id TEXT PRIMARY KEY,
        kind TEXT NOT NULL CHECK (kind IN ('png', 'blogger')),
        authorization_id TEXT NOT NULL REFERENCES release_authorizations(authorization_id),
        artifact_id TEXT NOT NULL REFERENCES review_artifacts(artifact_id),
        request_id TEXT NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN ('unknown', 'confirmed_success', 'confirmed_failure')),
        destination_id TEXT NULL,
        destination_url TEXT NULL,
        evidence_json TEXT NULL CHECK (evidence_json IS NULL OR json_valid(evidence_json)),
        observed_authority_revision INTEGER NULL CHECK (observed_authority_revision IS NULL OR observed_authority_revision >= 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (
            outcome != 'confirmed_success' OR (
                destination_id IS NOT NULL AND
                destination_url IS NOT NULL AND
                evidence_json IS NOT NULL
            )
        )
    );

    INSERT INTO authority (singleton_id, authority_revision, current_baseline_id) VALUES (1, 0, NULL);
    INSERT INTO composition (singleton_id, revision, state_json, updated_at) VALUES (1, 0, '{}', '2026-09-15T00:00:00Z');
    INSERT INTO cuts (cut_id) VALUES (1), (2), (3), (4), (5);

    CREATE TRIGGER trg_cuts_no_insert BEFORE INSERT ON cuts
    BEGIN
        SELECT RAISE(ABORT, 'exactly five cuts are immutable');
    END;

    CREATE TRIGGER trg_cuts_no_delete BEFORE DELETE ON cuts
    BEGIN
        SELECT RAISE(ABORT, 'exactly five cuts are immutable');
    END;

    CREATE TRIGGER trg_cuts_no_update_cut_id BEFORE UPDATE OF cut_id ON cuts
    BEGIN
        SELECT RAISE(ABORT, 'exactly five cuts are immutable');
    END;
    """
    con.executescript(v1_sql)

    con.execute(
        "INSERT INTO structural_baselines (baseline_id, structure_json, authority_revision, created_at) VALUES ('BASE-V1', '{}', 1, '2026-09-15T00:00:00Z');"
    )
    con.execute(
        "UPDATE authority SET authority_revision = 3, current_baseline_id = 'BASE-V1' WHERE singleton_id = 1;"
    )
    for c in range(1, 6):
        con.execute(
            "INSERT INTO cut_intents (cut_id, revision, baseline_id, payload_json, authority_revision, created_at) VALUES (?, 1, 'BASE-V1', ?, 1, '2026-09-15T00:00:00Z');",
            (c, json.dumps({"prompt": f"Dramatic panel {c} description"}))
        )
        con.execute(
            "INSERT INTO baseline_intents (baseline_id, cut_id, intent_revision) VALUES ('BASE-V1', ?, 1);",
            (c,)
        )
        con.execute(
            "UPDATE cuts SET desired_revision = 1 WHERE cut_id = ?;",
            (c,)
        )

    asset_dir = project_dir / "assets" / "realizations" / "cut-1"
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "rev-1-job-1.png"
    im = Image.new("RGB", (100, 100), color=(10, 20, 30))
    im.save(str(asset_file), format="PNG")
    h = hashlib.sha256(asset_file.read_bytes()).hexdigest()

    con.execute(
        "UPDATE cuts SET realized_revision = 1, realized_asset_id = 'asset-1', realized_asset_path = ?, realized_content_hash = ? WHERE cut_id = 1;",
        (str(asset_file), h)
    )

    con.execute(
        "INSERT INTO generation_jobs (job_id, cut_id, target_desired_revision, status, terminal_detail, created_at, updated_at) VALUES ('job-1', 1, 1, 'succeeded', 'done', '2026-09-15T00:00:00Z', '2026-09-15T00:00:00Z');"
    )
    con.execute(
        "INSERT INTO generation_attempts (attempt_id, job_id, ordinal, status, started_at, finished_at, detail) VALUES ('att-1', 'job-1', 1, 'succeeded', '2026-09-15T00:00:00Z', '2026-09-15T00:00:00Z', 'done');"
    )

    con.execute(
        "INSERT INTO generation_jobs (job_id, cut_id, target_desired_revision, status, terminal_detail, created_at, updated_at) VALUES ('job-2', 2, 1, 'running', NULL, '2026-09-15T00:00:00Z', '2026-09-15T00:00:00Z');"
    )
    con.execute(
        "INSERT INTO generation_attempts (attempt_id, job_id, ordinal, status, started_at, finished_at, detail) VALUES ('att-2', 'job-2', 1, 'running', '2026-09-15T00:00:00Z', NULL, NULL);"
    )

    con.execute(
        "INSERT INTO generation_jobs (job_id, cut_id, target_desired_revision, status, terminal_detail, created_at, updated_at) VALUES ('job-3', 3, 1, 'queued', NULL, '2026-09-15T00:00:00Z', '2026-09-15T00:00:00Z');"
    )

    con.commit()
    con.close()
    return project_dir


def test_v1_to_v2_migration_preservation(tmp_path: Path) -> None:
    migrated_dir = tmp_path / "migrated_project"
    _create_v1_fixture_project(migrated_dir)
    # It must detect user_version == 1, apply v1_to_v2.sql in BEGIN IMMEDIATE, and verify schema
    store = TransactionalStore.open_project(migrated_dir)

    snap = store.snapshot()
    assert snap["schema_version"] == 2
    assert "generation_control" in snap
    assert snap["generation_control"]["stop_epoch"] == 0
    assert snap["generation_control"]["runner_id"] is None

    # Preexisting truths from scratch v1 baseline:
    # 5 cuts, cut 1 realized, cut 2 running (un-reconciled until runner startup), cut 3 queued
    assert len(snap["cuts"]) == 5
    assert snap["cuts"][0]["currency"] == "CURRENT"
    assert snap["cuts"][0]["realized_revision"] == 1

    jobs_by_id = {j["job_id"]: j for j in snap["jobs"]}
    assert "job-1" in jobs_by_id
    assert jobs_by_id["job-1"]["status"] == "succeeded"
    assert "job-2" in jobs_by_id
    assert jobs_by_id["job-2"]["status"] == "running"
    assert "job-3" in jobs_by_id
    assert jobs_by_id["job-3"]["status"] == "queued"

    # Now, runner startup reconciles orphan running job-2 into interrupted without auto-retry!
    runner = GenerationRunner(store, provider_cmd_factory=_provider_cmd)
    runner.run_until_idle()

    snap_after = store.snapshot()
    jobs_after = {j["job_id"]: j for j in snap_after["jobs"]}
    assert jobs_after["job-2"]["status"] == "interrupted"
    assert jobs_after["job-3"]["status"] == "succeeded"

def test_regression_public_concurrency_assignment_invariant(tmp_path: Path) -> None:
    """Verify that public runner.concurrency = 3 does NOT produce 3 live roots."""
    project_dir = tmp_path / "proj_concurrency_invariant"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)
    service.enqueue(cut_id=None, expected_authority_revision=rev)

    gate_file = tmp_path / "gate_concurrency.txt"

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=2.0,
            mock_gate_file=str(gate_file),
        )

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)
    runner.concurrency = 3  # Arbitrary public assignment probe

    sampled_roots: list[int] = []
    stop_monitor = threading.Event()

    def monitor() -> None:
        while not stop_monitor.is_set():
            with store._connect() as con:
                rows = con.execute("SELECT process_pid FROM generation_attempts WHERE status = 'running'").fetchall()
                live_pids = [r["process_pid"] for r in rows if r["process_pid"] is not None]
                sampled_roots.append(len(live_pids))
            time.sleep(0.02)

    mon_t = threading.Thread(target=monitor, daemon=True)
    mon_t.start()

    runner_thread = threading.Thread(target=runner.run_until_idle)
    runner_thread.start()

    # Wait until 2 workers are active
    for _ in range(50):
        if 2 in sampled_roots:
            break
        time.sleep(0.05)

    gate_file.touch()
    runner_thread.join()
    stop_monitor.set()
    mon_t.join()

    assert max(sampled_roots, default=0) <= 2, f"Observed more than 2 roots: {max(sampled_roots)}"
    assert 2 in sampled_roots


def test_regression_stop_settlement_failure_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed process settlement must leave execution truth running."""
    project_dir = tmp_path / "proj_stop_settlement_failure"
    store, rev = _init_five_cut_project(project_dir)
    service = GenerationService(store)
    service.enqueue(cut_id=1, expected_authority_revision=rev)

    gate_file = tmp_path / "gate_stop_fail.txt"

    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=10.0,
            mock_gate_file=str(gate_file),
        )

    runner = GenerationRunner(store, provider_cmd_factory=cmd_factory)
    runner_thread = threading.Thread(target=runner.run_until_idle)
    runner_thread.start()

    # Wait until cut 1 worker is running in DB
    pid = None
    for _ in range(50):
        with store._connect() as con:
            row = con.execute("SELECT process_pid FROM generation_attempts WHERE status = 'running'").fetchone()
            if row and row["process_pid"] is not None:
                pid = row["process_pid"]
                break
        time.sleep(0.05)

    assert pid is not None
    assert is_pid_non_zombie_alive(pid)

    # Inject false termination into terminate_process_tree
    import comic_new.generation as gen_mod
    orig_terminate = gen_mod.terminate_process_tree
    monkeypatch.setattr(gen_mod, "terminate_process_tree", lambda *args, **kwargs: False)

    try:
        with pytest.raises(TransactionalStoreError) as exc_info:
            service.stop_all()
        assert "Global STOP failed to terminate" in str(exc_info.value)

        # DB attempt and job must remain running!
        snap = store.snapshot()
        job_1 = next(j for j in snap["jobs"] if j["cut_id"] == 1)
        assert job_1["status"] == "running"
        assert job_1["attempts"][0]["status"] == "running"

        # Controlled process is still alive under fault
        assert is_pid_non_zombie_alive(pid)
    finally:
        # Test cleanup must kill controlled process
        monkeypatch.undo()
        gate_file.touch()
        orig_terminate(pid, pid, None)
        runner_thread.join(timeout=3.0)
        assert not is_pid_non_zombie_alive(pid)
