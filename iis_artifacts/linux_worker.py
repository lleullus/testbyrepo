"""Concrete Linux subprocess adapter for the trusted IIS supervisor."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from .store import ArtifactStore
from .supervisor import HostBoundaryError, HostIntegrationUnavailable


class LinuxWorkerCommands:
    def __init__(
        self,
        *,
        store: ArtifactStore,
        project_root: Path,
        worker_uid: int,
        worker_gid: int,
        handoff_root: Path,
        review_command: list[str],
        role_command: list[str],
        worker_env: dict[str, str] | None = None,
        timeout: int = 3600,
    ) -> None:
        if os.geteuid() != 0:
            raise HostBoundaryError("LINUX_ENFORCED_SUBPROCESS_HOST_REQUIRES_ROOT")
        if worker_uid == 0 or worker_uid == os.geteuid():
            raise HostBoundaryError("WORKER_UID_MUST_BE_UNPRIVILEGED_AND_DISTINCT")
        self.store = store
        self.project_root = Path(project_root).resolve(strict=True)
        self.worker_uid = int(worker_uid)
        self.worker_gid = int(worker_gid)
        self.handoff_root = Path(handoff_root).resolve()
        self.handoff_root.mkdir(parents=True, exist_ok=True, mode=0o755)
        if self.handoff_root.is_symlink() or self.handoff_root.stat().st_uid != os.geteuid():
            raise HostBoundaryError("HANDOFF_ROOT_MUST_BE_SUPERVISOR_OWNED")
        if self.handoff_root.stat().st_mode & 0o022:
            raise HostBoundaryError("HANDOFF_ROOT_MUST_NOT_BE_GROUP_OR_WORLD_WRITABLE")
        self.execution_base = self.handoff_root / "executions"
        self.execution_base.mkdir(parents=True, exist_ok=True, mode=0o755)
        self.review_command = list(review_command)
        self.role_command = list(role_command)
        if not self.review_command or not self.role_command:
            raise HostBoundaryError("REVIEW_AND_ROLE_COMMANDS_REQUIRED")
        self.worker_env = dict(worker_env or {})
        self.timeout = int(timeout)

    def _drop_privileges(self) -> None:
        os.setgroups([])
        os.setgid(self.worker_gid)
        os.setuid(self.worker_uid)

    def _materialize_refs(self, refs: list[dict], prefix: str) -> tuple[Path, list[dict]]:
        handoff = Path(tempfile.mkdtemp(prefix=prefix + "-", dir=self.handoff_root))
        rendered: list[dict] = []
        try:
            for index, ref in enumerate(refs):
                row = self.store.ref_record(ref)
                target = handoff / f"input-{index}" / str(row["path"])
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                target.write_bytes(self.store.read_bytes(ref))
                target.chmod(0o444)
                rendered.append({"ref": ref, "path": str(target)})
            for directory in sorted(
                [item for item in handoff.rglob("*") if item.is_dir()],
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                directory.chmod(0o555)
            handoff.chmod(0o555)
            return handoff, rendered
        except BaseException:
            shutil.rmtree(handoff, ignore_errors=True)
            raise

    def _run(self, command: list[str], payload: dict) -> dict:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            **self.worker_env,
        }
        completed = subprocess.run(
            command,
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.project_root,
            env=env,
            timeout=self.timeout,
            preexec_fn=self._drop_privileges,
            check=False,
        )
        if completed.returncode != 0:
            raise HostIntegrationUnavailable(
                f"WORKER_COMMAND_FAILED:{completed.returncode}:{completed.stderr[-1000:]}"
            )
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise HostIntegrationUnavailable("WORKER_COMMAND_RETURNED_NON_JSON") from exc
        if not isinstance(value, dict):
            raise HostIntegrationUnavailable("WORKER_COMMAND_RETURNED_NON_OBJECT")
        return value

    def gate(
        self,
        argv: list[str],
        cwd: str,
        env: dict[str, str],
        timeout: float,
    ) -> tuple[int | None, bytes, bytes, str | None]:
        worker_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            **self.worker_env,
            **{key: value for key, value in env.items() if key.startswith("IIS_ASSURANCE_")},
        }
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                env=worker_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                preexec_fn=self._drop_privileges,
                check=False,
            )
            return completed.returncode, completed.stdout, completed.stderr, None
        except subprocess.TimeoutExpired as exc:
            return None, exc.stdout or b"", exc.stderr or b"", "TIMEOUT_EFFECT_SETTLEMENT_REQUIRED"
        except OSError as exc:
            return None, b"", b"", str(exc)

    def review(self, phase: str, run_id: str, inputs: list[dict], candidate: dict | None) -> dict:
        handoff, rendered = self._materialize_refs(inputs, "review")
        try:
            return self._run(
                self.review_command,
                {
                    "kind": "product-thesis-review",
                    "phase": phase,
                    "run_id": run_id,
                    "inputs": rendered,
                    "candidate": candidate,
                    "handoff_root": str(handoff),
                },
            )
        finally:
            handoff.chmod(0o755)
            shutil.rmtree(handoff, ignore_errors=True)

    def role(self, role: str, admission: dict) -> dict:
        refs = [
            admission["scope"],
            admission["request"],
            *admission.get("product_authorities", []),
            *admission.get("transition_authorities", []),
        ]
        handoff, rendered = self._materialize_refs(refs, "role")
        try:
            return self._run(
                self.role_command,
                {
                    "kind": "iis-role",
                    "role": role,
                    "admission": admission,
                    "inputs": rendered,
                    "handoff_root": str(handoff),
                    "project_root": str(self.project_root),
                },
            )
        finally:
            handoff.chmod(0o755)
            shutil.rmtree(handoff, ignore_errors=True)
