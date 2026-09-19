#!/usr/bin/env python3
"""Launch the first enforced IIS host: a Linux supervisor with UID-separated workers."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iis_artifacts.linux_worker import LinuxWorkerCommands
from iis_artifacts.store import ArtifactStore
from iis_artifacts.host import HostBoundaryError, HostSupervisor


def _json_list(raw: str, label: str) -> list[str]:
    value = json.loads(raw)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(label + " must be a nonempty JSON string array")
    return value


def _trusted_request(path: Path) -> str:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise HostBoundaryError("CURRENT_REQUEST_FILE_MUST_BE_REGULAR")
    details = path.stat()
    if details.st_uid != os.geteuid() or details.st_mode & 0o022:
        raise HostBoundaryError("CURRENT_REQUEST_FILE_MUST_BE_SUPERVISOR_OWNED_AND_NOT_WRITABLE_BY_WORKER")
    value = path.read_text(encoding="utf-8")
    if not value.strip():
        raise HostBoundaryError("CURRENT_REQUEST_FILE_IS_EMPTY")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--admin-socket", type=Path, required=True)
    parser.add_argument("--worker-uid", type=int, required=True)
    parser.add_argument("--worker-gid", type=int, required=True)
    parser.add_argument("--current-request-file", type=Path, required=True)
    parser.add_argument("--review-budget", type=int, required=True)
    parser.add_argument("--handoff-root", type=Path, required=True)
    parser.add_argument("--review-command-json", required=True)
    parser.add_argument("--role-command-json", required=True)
    parser.add_argument("--worker-env-json", default="{}")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("enforced Linux supervisor must run as root so it can drop worker privileges")
    current_request = _trusted_request(args.current_request_file)
    store = ArtifactStore(args.store, args.project_id)
    adapter = LinuxWorkerCommands(
        store=store,
        project_root=args.project_root,
        worker_uid=args.worker_uid,
        worker_gid=args.worker_gid,
        handoff_root=args.handoff_root,
        review_command=_json_list(args.review_command_json, "review command"),
        role_command=_json_list(args.role_command_json, "role command"),
        worker_env=json.loads(args.worker_env_json),
    )
    supervisor = HostSupervisor(
        store_base=args.store,
        project_id=args.project_id,
        project_root=args.project_root,
        worker_uid=args.worker_uid,
        current_request=current_request,
        review_budget=args.review_budget,
        review_dispatcher=adapter.review,
        role_dispatcher=adapter.role,
        gate_runner=adapter.gate,
        assurance_execution_base=adapter.execution_base,
    )
    admin = threading.Thread(target=supervisor.serve_admin_unix, args=(args.admin_socket,), daemon=True)
    admin.start()
    supervisor.serve_unix(args.socket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
