"""Generation engine: service, runner, process-tree control, PNG validation, and staging."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from PIL import Image

from comic_new.store import (
    RunnerAlreadyActiveError,
    TransactionalStore,
    TransactionalStoreError,
    ValidationError,
)


def get_process_start_token(pid: int) -> str | None:
    """Read starttime field from /proc/<pid>/stat for PID reuse protection."""
    if pid <= 0:
        return None
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            content = f.read()
        rparen = content.rfind(")")
        if rparen == -1:
            return None
        rest = content[rparen + 2:].split()
        return rest[19]
    except (OSError, IndexError):
        return None


def is_process_alive_with_token(pid: int, token: str | None) -> bool:
    """Return True if process exists, is non-zombie, and start token matches."""
    if pid <= 0 or not token:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False

    actual_token = get_process_start_token(pid)
    if actual_token != token:
        return False

    # Check non-zombie
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            content = f.read()
        rparen = content.rfind(")")
        if rparen != -1:
            state = content[rparen + 2:].split()[0]
            if state == "Z":
                return False
    except (OSError, IndexError):
        return False

    return True


def is_process_alive(pid: int) -> bool:
    """Check if process exists and is non-zombie."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            content = f.read()
        rparen = content.rfind(")")
        if rparen != -1:
            state = content[rparen + 2:].split()[0]
            if state == "Z":
                return False
    except (OSError, IndexError):
        return False
    return True


def is_pid_non_zombie_alive(pid: int) -> bool:
    """Alias for is_process_alive."""
    return is_process_alive(pid)


def find_descendant_pids(root_pid: int) -> set[int]:
    """Find all descendant PIDs of root_pid by scanning /proc."""
    if root_pid <= 0:
        return set()
    parent_map: dict[int, int] = {}
    try:
        for entry in os.scandir("/proc"):
            if entry.name.isdigit():
                p = int(entry.name)
                try:
                    with open(f"/proc/{p}/stat", "r", encoding="utf-8") as f:
                        content = f.read()
                    rparen = content.rfind(")")
                    if rparen != -1:
                        ppid = int(content[rparen + 2:].split()[1])
                        parent_map[p] = ppid
                except (OSError, IndexError):
                    continue
    except OSError:
        pass

    descendants: set[int] = set()
    queue = [root_pid]
    while queue:
        curr = queue.pop()
        for p, parent in parent_map.items():
            if parent == curr and p not in descendants:
                descendants.add(p)
                queue.append(p)
    return descendants

def find_session_or_group_pids(pgid: int, root_start_token: str | None = None) -> set[int]:
    """Find all alive non-zombie PIDs belonging to session or process group pgid."""
    if pgid <= 0:
        return set()
    root_start_tick = int(root_start_token) if (root_start_token and root_start_token.isdigit()) else None
    matching: set[int] = set()
    try:
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            p = int(entry.name)
            try:
                with open(f"/proc/{p}/stat", "r", encoding="utf-8") as f:
                    content = f.read()
                rparen = content.rfind(")")
                if rparen == -1:
                    continue
                fields = content[rparen + 2:].split()
                state = fields[0]
                if state == "Z":
                    continue
                pgrp = int(fields[2])
                session = int(fields[3])
                if pgrp == pgid or session == pgid:
                    if root_start_tick is not None:
                        starttime = int(fields[19])
                        if starttime < root_start_tick:
                            continue
                    matching.add(p)
            except (OSError, IndexError, ValueError):
                continue
    except OSError:
        pass
    return matching


def terminate_process_tree(
    pid: int | None,
    pgid: int | None,
    start_token: str | None,
    timeout: float = 3.0,
) -> bool:
    """Bounded process-tree TERM -> bounded wait -> KILL -> reap with PID reuse protection.

    Handles surviving reparented session descendants even after recorded root has exited.
    """
    if pid is None or pid <= 0:
        return True

    # Check root identity if root PID is currently alive
    root_alive = is_process_alive(pid)
    if root_alive:
        if start_token and not is_process_alive_with_token(pid, start_token):
            # PID was reused by an unrelated process! Never signal it.
            return True

    # Collect target PIDs
    session_id = pgid if (pgid is not None and pgid > 0) else pid
    descendants = find_descendant_pids(pid) if root_alive else set()
    session_pids = find_session_or_group_pids(session_id, start_token)
    all_pids = ({pid} if root_alive else set()) | descendants | session_pids

    if not all_pids:
        return True

    # Phase 1: SIGTERM
    if session_id is not None and session_id > 0:
        try:
            os.killpg(session_id, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    for p in all_pids:
        try:
            os.kill(p, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    # Wait bounded grace
    deadline = time.monotonic() + min(timeout, 1.0)
    while time.monotonic() < deadline:
        alive = [p for p in all_pids if is_process_alive(p)]
        if not alive:
            break
        time.sleep(0.05)

    # Phase 2: SIGKILL if still alive
    re_desc = find_descendant_pids(pid) if is_process_alive(pid) else set()
    re_sess = find_session_or_group_pids(session_id, start_token)
    all_pids = ({pid} if is_process_alive(pid) else set()) | re_desc | re_sess
    alive = [p for p in all_pids if is_process_alive(p)]
    if alive:
        if session_id is not None and session_id > 0:
            try:
                os.killpg(session_id, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for p in alive:
            try:
                os.kill(p, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

        kill_deadline = time.monotonic() + (timeout - 1.0 if timeout > 1.0 else 1.0)
        while time.monotonic() < kill_deadline:
            alive = [p for p in all_pids if is_process_alive(p)]
            if not alive:
                break
            time.sleep(0.05)

    # Re-check liveness
    final_desc = find_descendant_pids(pid) if is_process_alive(pid) else set()
    final_pids = ({pid} if is_process_alive(pid) else set()) | final_desc | find_session_or_group_pids(session_id, start_token)
    remaining = [p for p in final_pids if is_process_alive(p)]
    return len(remaining) == 0

def validate_staging_png(staging_path: Path) -> tuple[int, int, str]:
    """Validate that staging candidate is a non-empty, fully decodable PNG."""
    if not staging_path.is_file():
        raise ValidationError(f"Candidate file does not exist: {staging_path}")
    if staging_path.stat().st_size == 0:
        raise ValidationError(f"Candidate file is empty: {staging_path}")

    # Format verification
    try:
        with Image.open(staging_path) as img:
            if img.format != "PNG":
                raise ValidationError(f"Candidate format is not PNG: {img.format}")
            img.verify()
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Candidate verification failed: {e}") from e

    # Full pixel decode & dimension check
    try:
        with Image.open(staging_path) as img:
            img.load()
            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValidationError(f"Invalid image dimensions: {width}x{height}")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Candidate decode failed: {e}") from e

    content_hash = hashlib.sha256(staging_path.read_bytes()).hexdigest()
    return width, height, content_hash


@dataclasses.dataclass(frozen=True)
class EnqueueReceipt:
    authority_revision: int
    jobs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class CancelReceipt:
    job_id: str
    disposition: str
    was_running: bool

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class StopReceipt:
    stop_epoch: int
    cancelled_queued_count: int
    interrupted_running_count: int

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class RunReceipt:
    terminal_counts: dict[str, int]
    terminal_job_ids: dict[str, list[str]]
    realization_complete: bool
    snapshot: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class GenerationService:
    """Unified service for enqueueing, cancelling, and stopping generation jobs."""

    def __init__(self, store: TransactionalStore, project_dir: Path | str | None = None) -> None:
        self.store = store
        self.project_dir = Path(project_dir or store.db_path.parent).resolve()

    def enqueue(
        self,
        cut_id: int | None = None,
        expected_authority_revision: int = 0,
    ) -> EnqueueReceipt:
        """Enqueue generation jobs for all cuts (if cut_id is None) or a single cut."""
        if cut_id is not None and cut_id not in (1, 2, 3, 4, 5):
            raise ValidationError(f"Invalid cut_id {cut_id}; must be between 1 and 5")

        new_rev, jobs = self.store.enqueue_generation_jobs(
            expected_authority_revision=expected_authority_revision,
            cut_id=cut_id,
        )
        return EnqueueReceipt(authority_revision=new_rev, jobs=jobs)

    def cancel(self, job_id: str) -> CancelReceipt:
        """Cancel a single generation job (queued or running)."""
        disposition, att_info = self.store.cancel_job_in_store(job_id)
        if disposition == "cancelled_queued":
            return CancelReceipt(job_id=job_id, disposition="cancelled", was_running=False)
        if disposition == "running" and att_info:
            pid = att_info.get("process_pid")
            pgid = att_info.get("process_group_id")
            token = att_info.get("process_start_token")
            staging_path = att_info.get("staging_path")

            terminated = True
            if pid:
                terminated = terminate_process_tree(pid, pgid, token)

            if not terminated:
                failed_ident = f"job={job_id},attempt={att_info.get('attempt_id')},pid={pid}"
                raise TransactionalStoreError(
                    f"Cancel failed to terminate running process tree for {failed_ident}; job remains running"
                )

            if staging_path:
                stg = Path(staging_path)
                stg.unlink(missing_ok=True)
                if stg.parent.exists() and not any(stg.parent.iterdir()):
                    try:
                        stg.parent.rmdir()
                    except OSError:
                        pass

            self.store.mark_job_and_attempt_cancelled(
                job_id=job_id,
                attempt_id=att_info.get("attempt_id"),
                detail="Cancelled by user",
            )
            return CancelReceipt(job_id=job_id, disposition="cancelled", was_running=True)

        return CancelReceipt(
            job_id=job_id,
            disposition=disposition,
            was_running=False,
        )

    def stop_all(self) -> StopReceipt:
        """Global STOP: advance stop_epoch, cancel queued, terminate running process trees."""
        stop_epoch, running_procs = self.store.stop_all_and_cancel_queued()
        items_to_mark: list[tuple[str, str]] = []
        failed_procs: list[dict[str, Any]] = []

        for proc_info in running_procs:
            pid = proc_info.get("process_pid")
            pgid = proc_info.get("process_group_id")
            token = proc_info.get("process_start_token")
            staging = proc_info.get("staging_path")

            terminated = True
            if pid:
                terminated = terminate_process_tree(pid, pgid, token)

            if not terminated:
                failed_procs.append(proc_info)
                continue

            if staging:
                stg = Path(staging)
                stg.unlink(missing_ok=True)
                if stg.parent.exists() and not any(stg.parent.iterdir()):
                    try:
                        stg.parent.rmdir()
                    except OSError:
                        pass

            if proc_info.get("job_id") and proc_info.get("attempt_id"):
                items_to_mark.append((proc_info["job_id"], proc_info["attempt_id"]))

        if items_to_mark:
            self.store.mark_attempts_and_jobs_interrupted(items_to_mark, reason="global_stop")

        if failed_procs:
            failed_idents = [
                f"job={p.get('job_id')},attempt={p.get('attempt_id')},pid={p.get('process_pid')}"
                for p in failed_procs
            ]
            raise TransactionalStoreError(
                f"Global STOP failed to terminate running process trees: {', '.join(failed_idents)}; affected rows remain running"
            )

        snap = self.store.snapshot()
        cancelled_queued = sum(
            1 for j in snap["jobs"] if j["status"] == "cancelled" and j.get("terminal_detail") == "global_stop"
        )

        return StopReceipt(
            stop_epoch=stop_epoch,
            cancelled_queued_count=cancelled_queued,
            interrupted_running_count=len(running_procs),
        )



class GenerationRunner:
    """Fixed-concurrency-two runner that claims jobs from SQLite queue and drives subprocesses."""

    def __init__(
        self,
        store: TransactionalStore,
        project_dir: Path | str | None = None,
        ima2_binary: str | None = None,
        provider_cmd_factory: Callable[..., list[str]] | None = None,
        provider_timeout: float = 60.0,
        watchdog_timeout: float | None = None,
    ) -> None:
        self.store = store
        self.project_dir = Path(project_dir or store.db_path.parent).resolve()
        self._claimed_job_ids: set[str] = set()
        self._claimed_lock = threading.Lock()
        self._worker_exceptions: list[Exception] = []
        self._active_workers = 0

        self._worker_cond = threading.Condition()
        self.ima2_binary = ima2_binary or os.environ.get(
            "COMIC_NEW_IMA2_BIN", "/home/user01/.nvm/versions/node/v24.18.0/bin/ima2"
        )
        self.provider_cmd_factory = provider_cmd_factory
        self.provider_timeout = provider_timeout
        self.watchdog_timeout = watchdog_timeout if watchdog_timeout is not None else provider_timeout
        self.staging_base_dir = self.project_dir / ".generation-staging"
        self._exec_script = Path(__file__).parent / "_generation_exec.py"

    def default_provider_cmd(self, job_id: str, staging_path: Path, timeout: int) -> list[str]:
        parts = shlex.split(self.ima2_binary)
        return parts + [
            "gen",
            "--stdin",
            "--mode",
            "direct",
            "--no-size-nudge",
            "--model",
            "nano-banana-pro",
            "--size",
            "1024x1536",
            "--quality",
            "high",
            "--timeout",
            str(timeout),
            "-o",
            str(staging_path),
            "--json",
        ]

    def run_until_idle(self) -> RunReceipt:
        """Acquire single runner ownership, reconcile startup orphans, and run 2-worker pool until queue drained."""
        runner_pid = os.getpid()
        runner_start_token = get_process_start_token(runner_pid) or str(runner_pid)
        runner_id = f"runner-{runner_pid}-{uuid4().hex[:8]}"

        # Acquire ownership in generation_control
        stop_epoch = self.store.acquire_runner_ownership(
            runner_id=runner_id,
            runner_pid=runner_pid,
            runner_start_token=runner_start_token,
        )

        try:
            # Startup orphan reconciliation
            orphans = self.store.reconcile_startup_orphans()
            orphan_items_to_mark: list[tuple[str, str]] = []
            failed_orphans: list[dict[str, Any]] = []
            for orphan in orphans:
                pid = orphan.get("process_pid")
                pgid = orphan.get("process_group_id")
                token = orphan.get("process_start_token")
                staging = orphan.get("staging_path")
                terminated = True
                if pid:
                    terminated = terminate_process_tree(pid, pgid, token)
                if not terminated:
                    failed_orphans.append(orphan)
                    continue
                if staging:
                    stg = Path(staging)
                    stg.unlink(missing_ok=True)
                    if stg.parent.exists() and not any(stg.parent.iterdir()):
                        try:
                            stg.parent.rmdir()
                        except OSError:
                            pass
                if orphan.get("job_id") and orphan.get("attempt_id"):
                    orphan_items_to_mark.append((orphan["job_id"], orphan["attempt_id"]))

            if orphan_items_to_mark:
                for jid, _ in orphan_items_to_mark:
                    self._claimed_job_ids.add(jid)
                self.store.mark_startup_orphans_interrupted(orphan_items_to_mark)

            if failed_orphans:
                failed_idents = [
                    f"job={o.get('job_id')},attempt={o.get('attempt_id')},pid={o.get('process_pid')}"
                    for o in failed_orphans
                ]
                raise TransactionalStoreError(
                    f"Startup recovery failed to terminate orphan process trees: {', '.join(failed_idents)}; affected rows remain running"
                )

            # Worker pool execution
            stop_event = threading.Event()
            threads: list[threading.Thread] = []

            for worker_idx in range(2):
                t = threading.Thread(
                    target=self._worker_loop,
                    args=(runner_id, runner_pid, runner_start_token, stop_epoch, stop_event),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            if self._worker_exceptions:
                exc = self._worker_exceptions[0]
                raise exc


        finally:
            self.store.release_runner_ownership(runner_id)

        # Snapshot readback
        snap = self.store.snapshot()
        counts: dict[str, int] = {}
        job_ids_by_status: dict[str, list[str]] = {}
        for j in snap["jobs"]:
            if j["job_id"] in self._claimed_job_ids:
                st = j["status"]
                counts[st] = counts.get(st, 0) + 1
                job_ids_by_status.setdefault(st, []).append(j["job_id"])

        return RunReceipt(
            terminal_counts=counts,
            terminal_job_ids=job_ids_by_status,
            realization_complete=snap["realization_complete"]["complete"],
            snapshot=snap,
        )

    def _worker_loop(
        self,
        runner_id: str,
        runner_pid: int,
        runner_start_token: str,
        stop_epoch: int,
        stop_event: threading.Event,
    ) -> None:
        try:
            self._worker_loop_impl(runner_id, runner_pid, runner_start_token, stop_epoch, stop_event)
        except Exception as e:
            self._worker_exceptions.append(e)
            stop_event.set()

    def _worker_loop_impl(
        self,
        runner_id: str,
        runner_pid: int,
        runner_start_token: str,
        stop_epoch: int,
        stop_event: threading.Event,
    ) -> None:
        while not stop_event.is_set():

            claim = self.store.claim_next_generation_job(
                runner_id=runner_id,
                runner_pid=runner_pid,
                runner_start_token=runner_start_token,
                captured_stop_epoch=stop_epoch,
                staging_base_dir=self.staging_base_dir,
            )
            if claim is None:
                with self.store._connect() as chk_con:
                    ctrl = chk_con.execute(
                        "SELECT stop_epoch FROM generation_control WHERE singleton_id = 1"
                    ).fetchone()
                    cur_epoch = ctrl["stop_epoch"] if ctrl else 0
                if cur_epoch != stop_epoch or stop_event.is_set():
                    break

                with self._worker_cond:
                    if self._active_workers > 0 and not stop_event.is_set():
                        self._worker_cond.wait(timeout=0.05)
                        continue
                    else:
                        self._worker_cond.notify_all()
                        break

            with self._worker_cond:
                self._active_workers += 1
            try:
                with self._claimed_lock:
                    self._claimed_job_ids.add(claim["job_id"])
                job_id = claim["job_id"]
                attempt_id = claim["attempt_id"]
                staging_file = Path(claim["staging_path"])
                staging_file.parent.mkdir(parents=True, exist_ok=True)
                prompt = claim["prompt"]

                # Determine provider command
                if self.provider_cmd_factory:
                    provider_cmd = self.provider_cmd_factory(
                        claim["cut_id"], staging_file, claim["target_desired_revision"]
                    )
                else:
                    provider_cmd = self.default_provider_cmd(
                        job_id, staging_file, int(self.provider_timeout)
                    )

                # Set up synchronization pipe gate
                r_fd, w_fd = os.pipe()
                launcher_cmd = [sys.executable, str(self._exec_script), str(r_fd)] + provider_cmd

                try:
                    proc = subprocess.Popen(
                        launcher_cmd,
                        pass_fds=(r_fd,),
                        start_new_session=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except Exception as e:
                    os.close(r_fd)
                    os.close(w_fd)
                    self.store.fail_job_and_attempt(
                        runner_id=runner_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        detail=f"Failed to spawn subprocess: {e}",
                    )
                    staging_file.unlink(missing_ok=True)
                    continue
                finally:
                    try:
                        os.close(r_fd)
                    except OSError:
                        pass

                proc_pid = proc.pid
                proc_pgid = proc.pid
                proc_token = get_process_start_token(proc_pid) or str(proc_pid)

                # Attach process identity to DB before opening gate
                attached = self.store.attach_attempt_process(
                    job_id=job_id,
                    attempt_id=attempt_id,
                    runner_id=runner_id,
                    pid=proc_pid,
                    pgid=proc_pgid,
                    start_token=proc_token,
                    captured_stop_epoch=stop_epoch,
                )

                if not attached:
                    # Attach failed: close w_fd without start byte, terminate child
                    try:
                        os.close(w_fd)
                    except OSError:
                        pass
                    terminated = terminate_process_tree(proc_pid, proc_pgid, proc_token)
                    try:
                        proc.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        pass
                    if not terminated:
                        raise TransactionalStoreError(
                            f"Attach failed and process termination failed for job {job_id} attempt {attempt_id} (pid {proc_pid})"
                        )
                    continue

                # Open gate: write exactly 1 byte
                try:
                    os.write(w_fd, b"\x01")
                except OSError:
                    pass
                finally:
                    try:
                        os.close(w_fd)
                    except OSError:
                        pass

                # Write prompt bytes to child stdin and wait with timeout
                try:
                    stdout_bytes, stderr_bytes = proc.communicate(
                        input=prompt.encode("utf-8"),
                        timeout=self.watchdog_timeout,
                    )
                except subprocess.TimeoutExpired:
                    terminated = terminate_process_tree(proc_pid, proc_pgid, proc_token)
                    try:
                        stdout_bytes, stderr_bytes = proc.communicate(timeout=2.0)
                    except Exception:
                        stdout_bytes, stderr_bytes = b"", b""
                    if not terminated:
                        raise TransactionalStoreError(
                            f"Process timed out and termination failed for job {job_id} attempt {attempt_id} (pid {proc_pid})"
                        )
                    self.store.fail_job_and_attempt(
                        runner_id=runner_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        detail=f"Process timed out after {self.watchdog_timeout}s",
                    )
                    staging_file.unlink(missing_ok=True)
                    continue

                # Process completed and reaped
                if proc.returncode != 0:
                    # Check if stop_epoch changed or job is already interrupted/cancelled
                    with self.store._connect() as chk_con:
                        ctrl = chk_con.execute(
                            "SELECT stop_epoch FROM generation_control WHERE singleton_id = 1"
                        ).fetchone()
                        cur_epoch = ctrl["stop_epoch"] if ctrl else 0
                        j_row = chk_con.execute(
                            "SELECT status FROM generation_jobs WHERE job_id = ?", (job_id,)
                        ).fetchone()
                        j_status = j_row["status"] if j_row else None

                    if cur_epoch != stop_epoch or j_status in ("interrupted", "cancelled"):
                        staging_file.unlink(missing_ok=True)
                        continue

                    err_msg = stderr_bytes.decode("utf-8", errors="replace").strip()[:200]
                    detail = f"Process exited with code {proc.returncode}: {err_msg}"
                    self.store.fail_job_and_attempt(
                        runner_id=runner_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        detail=detail,
                    )
                    staging_file.unlink(missing_ok=True)
                    continue

                # Extract provider request ID if present
                provider_req_id = None
                try:
                    out_str = stdout_bytes.decode("utf-8", errors="replace").strip()
                    if out_str:
                        out_json = json.loads(out_str)
                        if isinstance(out_json, dict) and "request_id" in out_json:
                            provider_req_id = str(out_json["request_id"])
                except Exception:
                    pass

                # Validate staging PNG
                try:
                    width, height, content_hash = validate_staging_png(staging_file)
                except Exception as e:
                    err_str = str(e)
                    if "Candidate file does not exist" in err_str or "empty" in err_str:
                        detail = f"Validation failed: {err_str}"
                    else:
                        detail = f"PNG decoding failed: {err_str}"

                    self.store.fail_job_and_attempt(
                        runner_id=runner_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        detail=detail,
                        provider_request_id=provider_req_id,
                    )
                    staging_file.unlink(missing_ok=True)
                    continue

                # Atomic commit gate
                try:
                    self.store.commit_candidate(
                        runner_id=runner_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        candidate_png_path=staging_file,
                        content_hash=content_hash,
                        provider_request_id=provider_req_id,
                    )
                finally:
                    staging_file.unlink(missing_ok=True)
                    if staging_file.parent.exists() and not any(staging_file.parent.iterdir()):
                        try:
                            staging_file.parent.rmdir()
                        except OSError:
                            pass
            finally:
                with self._worker_cond:
                    self._active_workers -= 1
                    self._worker_cond.notify_all()
