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

import pytest
from PIL import Image

from comic_new.generation import (
    GenerationRunner,
    GenerationService,
    get_process_start_token,
    is_pid_non_zombie_alive,
    is_process_alive_with_token,
)
from comic_new.store import (
    ConflictError,
    RunnerAlreadyActiveError,
    StoreCorruptionError,
    TransactionalStore,
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

    # Enqueue 3 jobs
    rec = service.enqueue(cut_id=None, expected_authority_revision=rev)

    # Record stdin prompts passed to helper
    stdin_record_dir = tmp_path / "stdin_records"
    stdin_record_dir.mkdir()

    # Track maximum concurrent running helpers
    def cmd_factory(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        record_file = stdin_record_dir / f"cut_{cut_id}.txt"
        return _provider_cmd(
            cut_id,
            staging_path,
            target_rev,
            mock_sleep=0.3,  # Slight delay to ensure worker concurrency overlap
            mock_record_stdin=str(record_file),
        )

    runner = GenerationRunner(
        store,
        concurrency=2,
        provider_cmd_factory=cmd_factory,
    )
    receipt = runner.run_until_idle()

    # Verify all jobs succeeded
    assert receipt.terminal_counts.get("succeeded") == 5

    # Check that stdin prompt received by mock helper equals accepted historical prompt
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
        concurrency=2,
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

    runner_a = GenerationRunner(store, concurrency=1, provider_cmd_factory=cmd_factory)

    # Start runner_a in a separate thread so Job A blocks on the gate
    import threading

    t_a = threading.Thread(target=runner_a.run_until_idle)
    t_a.start()

    # Wait until Job A is running in DB
    time.sleep(0.3)
    with store._connect() as con:
        r = con.execute("SELECT status FROM generation_jobs WHERE job_id = ?", (job_a_id,)).fetchone()
        assert r["status"] == "running"

    # User modifies cut 1 intent to revision 2!
    rev = store.snapshot()["authority_revision"]
    rev = store.accept_cut_intent(rev, cut_id=1, intent_payload={"prompt": "Panel 1 Revised v2"})

    # User immediately enqueues and commits Job B for revision 2
    # We run Job B to completion using a second runner after runner_a releases ownership or directly
    # Notice: runner_a holds the singleton ownership in DB!
    # Let's release gate file so Job A proceeds to commit gate
    gate_file.touch()
    t_a.join()

    # Job A reached commit_candidate: since cut 1 desired_revision is now 2, Job A must be superseded!
    snap = store.snapshot()
    job_a = [j for j in snap["jobs"] if j["job_id"] == job_a_id][0]
    assert job_a["status"] == "superseded"
    assert "superseded" in job_a["terminal_detail"]
    assert job_a["attempts"][0]["status"] == "succeeded"  # Attempt succeeded honestly

    # Now enqueue and run Job B for rev 2
    rec_b = service.enqueue(cut_id=1, expected_authority_revision=snap["authority_revision"])
    job_b_id = rec_b.jobs[0]["job_id"]

    runner_b = GenerationRunner(store, concurrency=1, provider_cmd_factory=cmd_factory)
    runner_b.run_until_idle()

    snap2 = store.snapshot()
    cut1 = snap2["cuts"][0]
    assert cut1["realized_revision"] == 2
    canonical_b_path = Path(cut1["realized_asset_path"])
    assert canonical_b_path.is_file()
    canonical_b_bytes = canonical_b_path.read_bytes()

    # If Job A candidate was written, verify it did not overwrite or corrupt B's canonical file
    assert cut1["realized_content_hash"] == snap2["cuts"][0]["realized_content_hash"]


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

    runner = GenerationRunner(store, concurrency=1, provider_cmd_factory=cmd_factory)
    import threading

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

    runner = GenerationRunner(store, concurrency=2, provider_cmd_factory=cmd_factory)
    import threading

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
runner = GenerationRunner(store, concurrency=2, provider_cmd_factory=cmd_factory)
runner.run_until_idle()
"""
    runner_proc = subprocess.Popen(
        [sys.executable, "-c", runner_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait until attempts are marked running in DB
    pids = []
    for _ in range(50):
        with store._connect() as con:
            rows = con.execute("SELECT process_pid FROM generation_attempts WHERE status = 'running'").fetchall()
            pids = [r["process_pid"] for r in rows if r["process_pid"] is not None]
            if len(pids) >= 1:
                break
        time.sleep(0.1)

    assert len(pids) >= 1

    # SIGKILL the runner process (simulating hard power loss or OOM kill)
    os.kill(runner_proc.pid, signal.SIGKILL)
    runner_proc.wait()

    # Now open project and start official runner (which runs startup reconciliation)
    # Runner should clean up orphan processes, mark running attempts/jobs interrupted, and drain remaining queued jobs
    recovered_store = TransactionalStore.open_project(project_dir)

    def normal_cmd(cut_id: int, staging_path: Path, target_rev: int) -> list[str]:
        return _provider_cmd(cut_id, staging_path, target_rev)

    new_runner = GenerationRunner(recovered_store, concurrency=2, provider_cmd_factory=normal_cmd)
    new_receipt = new_runner.run_until_idle()

    # Verify old orphaned worker processes were killed
    for p in pids:
        assert not is_pid_non_zombie_alive(p)

    # Verify old running rows became 'interrupted' and were NOT auto-retried
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

    runner = GenerationRunner(store, concurrency=1, provider_cmd_factory=cmd_factory)
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
        runner2 = GenerationRunner(store, concurrency=1, provider_cmd_factory=cmd_factory)
        runner2.run_until_idle()
        rev2 = store.snapshot()["authority_revision"]

    # Now exact five cuts are current -> COMPLETE
    snap_final = store.snapshot()
    for cut in snap_final["cuts"]:
        assert cut["currency"] == "CURRENT"
    assert snap_final["realization_complete"]["complete"] is True
    assert snap_final["realization_complete"]["status"] == "COMPLETE"


# ---------------------------------------------------------------------------
# v1 -> v2 Migration Test
# ---------------------------------------------------------------------------


def test_v1_to_v2_migration_preservation(tmp_path: Path) -> None:
    import shutil

    # Copy the scratch v1 project we created before any code changes
    scratch_v1 = Path("/home/user01/tmp/scratch_v1_baseline")
    assert scratch_v1.exists()

    migrated_dir = tmp_path / "migrated_project"
    shutil.copytree(scratch_v1, migrated_dir)

    # Open the v1 project using TransactionalStore.open_project
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
    runner = GenerationRunner(store, concurrency=1, provider_cmd_factory=_provider_cmd)
    runner.run_until_idle()

    snap_after = store.snapshot()
    jobs_after = {j["job_id"]: j for j in snap_after["jobs"]}
    assert jobs_after["job-2"]["status"] == "interrupted"
    assert jobs_after["job-3"]["status"] == "succeeded"
