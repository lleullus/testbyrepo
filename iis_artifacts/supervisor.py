"""Linux trusted-supervisor boundary for enforced IIS execution."""
from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
import socket
import struct
from typing import Any, Callable

from .admission import admit_fixed_scope
from .store import ArtifactStore

ROOT = Path(__file__).resolve().parents[1]

LIFECYCLE_SPEC = importlib.util.spec_from_file_location(
    "iis_thesis_lifecycle_supervisor", ROOT / "product-thesis/tools/lifecycle.py"
)
assert LIFECYCLE_SPEC is not None and LIFECYCLE_SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(LIFECYCLE_SPEC)
LIFECYCLE_SPEC.loader.exec_module(LIFECYCLE)

ASSURANCE_SPEC = importlib.util.spec_from_file_location(
    "iis_assurance_supervisor", ROOT / "iis-workflow/tools/assurance.py"
)
assert ASSURANCE_SPEC is not None and ASSURANCE_SPEC.loader is not None
ASSURANCE = importlib.util.module_from_spec(ASSURANCE_SPEC)
ASSURANCE_SPEC.loader.exec_module(ASSURANCE)


class HostIntegrationUnavailable(RuntimeError):
    pass


class HostBoundaryError(RuntimeError):
    pass


class HostSupervisor:
    """Trusted process owner. Workers must not run this object or access its store."""

    def __init__(
        self,
        *,
        store_base: Path,
        project_id: str,
        project_root: Path,
        worker_uid: int,
        current_request: str,
        review_budget: int,
        review_dispatcher: Callable[[str, str, list[dict], dict | None], dict] | None = None,
        role_dispatcher: Callable[[str, dict], dict] | None = None,
        gate_runner: Callable[[list[str], str, dict[str, str], float], tuple[int | None, bytes, bytes, str | None]] | None = None,
        assurance_execution_base: Path | None = None,
    ) -> None:
        if not hasattr(socket, "SO_PEERCRED"):
            raise HostBoundaryError("ENFORCED_HOST_REQUIRES_LINUX_PEER_CREDENTIALS")
        self.supervisor_uid = os.geteuid()
        self.worker_uid = int(worker_uid)
        if self.worker_uid == self.supervisor_uid:
            raise HostBoundaryError("SUPERVISOR_WORKER_UID_MUST_DIFFER")
        if not isinstance(current_request, str) or not current_request.strip():
            raise HostBoundaryError("TRUSTED_CURRENT_REQUEST_REQUIRED")
        if type(review_budget) is not int or review_budget <= 0:
            raise HostBoundaryError("POSITIVE_REVIEW_BUDGET_REQUIRED")

        self.current_request = current_request
        self.review_budget = review_budget
        self.store = ArtifactStore(store_base, project_id)
        self.project_root = Path(project_root).resolve(strict=True)
        project_details = self.project_root.stat()
        if project_details.st_mode & 0o022:
            raise HostBoundaryError("PROJECT_ROOT_MUST_NOT_BE_GROUP_OR_WORLD_WRITABLE")
        self.project_owner_uid = project_details.st_uid

        store_details = self.store.root.stat()
        if store_details.st_uid != self.supervisor_uid or (store_details.st_mode & 0o077):
            raise HostBoundaryError("SUPERVISOR_STORE_MUST_BE_PRIVATE")

        self.review_dispatcher = review_dispatcher
        self.role_dispatcher = role_dispatcher
        self.gate_runner = gate_runner
        self.assurance_execution_base = None if assurance_execution_base is None else Path(assurance_execution_base)
        self._schema()

    def _schema(self) -> None:
        with self.store.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS host_role_invocations(
                  invocation_id TEXT PRIMARY KEY,
                  role TEXT NOT NULL,
                  admission_id TEXT NOT NULL,
                  status TEXT NOT NULL,
                  result_json TEXT,
                  sequence INTEGER NOT NULL
                );
                """
            )

    # Trusted host API -----------------------------------------------------

    def start_thesis(self, **kwargs: Any) -> dict:
        if "budget" in kwargs:
            raise HostBoundaryError("WORKER_MAY_NOT_OVERRIDE_REVIEW_BUDGET")
        run_id = LIFECYCLE.start(
            self.store,
            self.current_request,
            budget=self.review_budget,
            **kwargs,
        )
        return LIFECYCLE.inspect(self.store, run_id)

    def submit_candidate(self, run_id: str, data: bytes, logical_path: str, expected_generation: int) -> dict:
        return LIFECYCLE.submit_candidate_bytes(
            self.store,
            run_id,
            data,
            logical_path,
            expected_generation=expected_generation,
        )

    def inspect_thesis(self, run_id: str) -> dict:
        return LIFECYCLE.inspect(self.store, run_id)

    def apply_thesis_proposal(self, run_id: str, proposal: dict) -> dict:
        if not isinstance(proposal, dict):
            raise ValueError("proposal must be an object")
        kind = proposal.get("kind")
        if kind == "frontier":
            LIFECYCLE.add_frontier(
                self.store,
                run_id,
                item_id=proposal["item_id"],
                origin=proposal["origin"],
                question=proposal["question"],
                material_change=proposal["material_change"],
                decision_bearing=bool(proposal.get("decision_bearing")),
            )
        elif kind == "frontier_disposition":
            LIFECYCLE.disposition_frontier(
                self.store,
                run_id,
                proposal["item_id"],
                proposal["disposition"],
                proposal["basis"],
            )
        elif kind == "premise":
            LIFECYCLE.add_premise(
                self.store,
                run_id,
                premise_id=proposal["premise_id"],
                statement=proposal["statement"],
                kind=proposal["premise_kind"],
                depends_on=proposal["depends_on"],
            )
        elif kind == "premise_disposition":
            LIFECYCLE.disposition_premise(
                self.store,
                run_id,
                proposal["premise_id"],
                proposal["disposition"],
                proposal["basis"],
            )
        elif kind == "finding_disposition":
            LIFECYCLE.disposition_finding(
                self.store,
                run_id,
                proposal["finding_id"],
                proposal["disposition"],
                proposal["basis"],
            )
        else:
            raise ValueError("unsupported Thesis proposal kind")
        return LIFECYCLE.inspect(self.store, run_id)

    def _current_review_need(self, run_id: str) -> str | None:
        state = LIFECYCLE.inspect(self.store, run_id)
        req_gen = state["request_generation"]
        reviews = state["reviews"]
        if not any(
            row["phase"] == "SOURCE_FRONTIER"
            and row["request_generation"] == req_gen
            and row["status"] == "COMPLETE"
            for row in reviews
        ):
            return "SOURCE_FRONTIER"
        candidate = state["candidate"]
        if candidate is None:
            return None
        generation = state["generation"]
        if not any(
            row["phase"] == "CANDIDATE_COUNTEREXAMPLE"
            and row["request_generation"] == req_gen
            and row["candidate_generation"] == generation
            and row["status"] == "COMPLETE"
            for row in reviews
        ):
            return "CANDIDATE_COUNTEREXAMPLE"
        return None

    def drive_thesis(self, run_id: str) -> dict:
        if self.review_dispatcher is None:
            raise HostIntegrationUnavailable("REVIEW_DISPATCHER_UNAVAILABLE")
        phase = self._current_review_need(run_id)
        if phase is None:
            return LIFECYCLE.evaluate_closure(self.store, run_id)
        inputs = LIFECYCLE.required_review_inputs(self.store, run_id, phase)
        state = LIFECYCLE.inspect(self.store, run_id)
        candidate = state["candidate"]
        invocation_id = LIFECYCLE.begin_review(self.store, run_id, phase, inputs)
        try:
            result = self.review_dispatcher(phase, run_id, inputs, candidate)
        except BaseException as exc:
            # The STARTED ledger entry intentionally remains and blocks closure.
            raise HostIntegrationUnavailable(f"REVIEW_DISPATCH_FAILED:{exc}") from exc
        if not isinstance(result, dict):
            raise HostIntegrationUnavailable("REVIEW_DISPATCH_RETURNED_INVALID_RESULT")
        review_result = result.get("result")
        if not isinstance(review_result, dict) or not review_result:
            raise HostIntegrationUnavailable("REVIEW_RESULT_REQUIRED")
        finding_keys = LIFECYCLE.complete_review(
            self.store,
            invocation_id,
            result=review_result,
            frontier=result.get("frontier", []),
            findings=result.get("findings", []),
        )
        return {
            "invocation_id": invocation_id,
            "finding_keys": finding_keys,
            "state": LIFECYCLE.inspect(self.store, run_id),
        }

    def close_thesis(self, run_id: str, *, limitations: str = "") -> dict:
        if self.review_dispatcher is None:
            raise HostIntegrationUnavailable("REVIEW_DISPATCHER_UNAVAILABLE")
        state = LIFECYCLE.inspect(self.store, run_id)
        return LIFECYCLE.close_request(
            self.store,
            run_id,
            self.project_root,
            limitations=limitations,
            expected_generation=state["generation"],
        )

    def cancel_thesis(self, run_id: str) -> dict:
        LIFECYCLE.cancel(self.store, run_id)
        return LIFECYCLE.inspect(self.store, run_id)

    def set_current_request(self, request: str) -> dict:
        if not isinstance(request, str) or not request.strip():
            raise HostBoundaryError("TRUSTED_CURRENT_REQUEST_REQUIRED")
        self.current_request = request
        return {"status": "CURRENT_REQUEST_UPDATED"}

    def resume_thesis(self, run_id: str, request: str, *, budget_increment: int | None = None) -> dict:
        self.set_current_request(request)
        LIFECYCLE.resume(self.store, run_id, request, budget_increment=budget_increment)
        return LIFECYCLE.inspect(self.store, run_id)

    def admit_scope_bytes(self, *, role: str, scope_bytes: bytes, logical_path: str) -> dict:
        snapshot = self.store.capture_mapping(
            {logical_path: scope_bytes},
            kind="source",
            origin=f"host-admission:{role}",
        )
        return admit_fixed_scope(
            self.store,
            {"snapshot": snapshot, "path": logical_path},
            role=role,
            current_request=self.current_request,
            project_owner_uid=self.project_owner_uid,
        )

    def admit_and_start(self, *, role: str, scope_bytes: bytes, logical_path: str) -> dict:
        if self.role_dispatcher is None:
            raise HostIntegrationUnavailable("ROLE_DISPATCHER_UNAVAILABLE")
        admission = self.admit_scope_bytes(
            role=role,
            scope_bytes=scope_bytes,
            logical_path=logical_path,
        )
        invocation_id = "role-" + os.urandom(16).hex
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO host_role_invocations(invocation_id,role,admission_id,status,result_json,sequence) "
                "VALUES(?,?,?,'STARTED',NULL,?)",
                (
                    invocation_id,
                    role,
                    admission["admission_id"],
                    self.store.sequence_in(db, "host-role-start"),
                ),
            )
            db.execute("COMMIT")
        try:
            result = self.role_dispatcher(role, admission)
            if not isinstance(result, dict):
                raise TypeError("role dispatcher must return an object")
        except BaseException as exc:
            with self.store.connect() as db:
                db.execute(
                    "UPDATE host_role_invocations SET status='FAILED',result_json=? WHERE invocation_id=?",
                    (json.dumps({"error": str(exc)}, ensure_ascii=False), invocation_id),
                )
            raise
        with self.store.connect() as db:
            db.execute(
                "UPDATE host_role_invocations SET status='COMPLETE',result_json=? WHERE invocation_id=?",
                (json.dumps(result, ensure_ascii=False), invocation_id),
            )
        return {"admission": admission, "invocation_id": invocation_id, "result": result}

    def bind_assurance(self, baseline_path: Path, execution: dict) -> dict:
        if self.gate_runner is None or self.assurance_execution_base is None:
            raise HostIntegrationUnavailable("ASSURANCE_GATE_RUNNER_UNAVAILABLE")
        return ASSURANCE.bind(
            Path(baseline_path),
            self.store,
            self.project_root,
            execution,
            execution_base=self.assurance_execution_base,
            trusted_request=self.current_request,
            project_owner_uid=self.project_owner_uid,
        )

    def run_assurance_gate(self, baseline_path: Path, binding: dict, gate_id: str, output: Path) -> dict:
        if self.gate_runner is None:
            raise HostIntegrationUnavailable("ASSURANCE_GATE_RUNNER_UNAVAILABLE")
        return ASSURANCE.run_gate(
            Path(baseline_path),
            self.store,
            binding,
            gate_id,
            Path(output),
            runner=self.gate_runner,
        )

    def close_assurance(self, baseline_path: Path, binding: dict) -> dict:
        return ASSURANCE.close(Path(baseline_path), self.store, binding)

    # Worker RPC: deliberately excludes resume, current-request changes,
    # role admission/start and Assurance binding/execution.
    def handle(self, request: dict) -> dict:
        action = request.get("action")
        if action == "start":
            return self.start_thesis()
        if action == "inspect":
            return self.inspect_thesis(request["run_id"])
        if action == "submit_candidate":
            return self.submit_candidate(
                request["run_id"],
                base64.b64decode(request["content_b64"]),
                request["logical_path"],
                int(request["expected_generation"]),
            )
        if action == "propose":
            return self.apply_thesis_proposal(request["run_id"], request["proposal"])
        if action == "drive":
            return self.drive_thesis(request["run_id"])
        if action == "close":
            return self.close_thesis(request["run_id"], limitations=request.get("limitations", ""))
        if action == "cancel":
            return self.cancel_thesis(request["run_id"])
        raise ValueError("unsupported supervisor action")

    # Admin RPC: only the supervisor UID may connect.
    def handle_admin(self, request: dict) -> dict:
        action = request.get("action")
        if action == "start_thesis":
            return self.start_thesis(
                originals=request.get("originals"),
                profile=request.get("profile"),
                expected_prior=request.get("expected_prior"),
            )
        if action == "set_current_request":
            return self.set_current_request(request["request"])
        if action == "resume":
            return self.resume_thesis(
                request["run_id"],
                request["request"],
                budget_increment=request.get("budget_increment"),
            )
        if action == "admit":
            return self.admit_scope_bytes(
                role=request["role"],
                scope_bytes=base64.b64decode(request["scope_b64"]),
                logical_path=request["logical_path"],
            )
        if action == "admit_and_start":
            return self.admit_and_start(
                role=request["role"],
                scope_bytes=base64.b64decode(request["scope_b64"]),
                logical_path=request["logical_path"],
            )
        if action == "bind_assurance":
            return self.bind_assurance(Path(request["baseline_path"]), request["execution"])
        if action == "run_assurance_gate":
            return self.run_assurance_gate(
                Path(request["baseline_path"]),
                request["binding"],
                request["gate_id"],
                Path(request["output"]),
            )
        if action == "close_assurance":
            return self.close_assurance(Path(request["baseline_path"]), request["binding"])
        raise ValueError("unsupported admin action")

    @staticmethod
    def _read_request(connection: socket.socket) -> dict:
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = connection.recv(65536)
            if not chunk:
                break
            raw += chunk
        return json.loads(raw)

    @staticmethod
    def _send(connection: socket.socket, value: dict) -> None:
        connection.sendall((json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8"))

    def serve_unix(self, socket_path: Path) -> None:
        socket_path = Path(socket_path)
        socket_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        if socket_path.parent.is_symlink() or socket_path.parent.stat().st_uid != self.supervisor_uid:
            raise HostBoundaryError("SUPERVISOR_SOCKET_DIRECTORY_MUST_BE_SUPERVISOR_OWNED")
        os.chmod(socket_path.parent, 0o755)
        socket_path.unlink(missing_ok=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(socket_path))
            os.chmod(socket_path, 0o666)
            server.listen()
            while True:
                connection, _ = server.accept()
                with connection:
                    credentials = connection.getsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_PEERCRED,
                        struct.calcsize("3i"),
                    )
                    _pid, uid, _gid = struct.unpack("3i", credentials)
                    if uid != self.worker_uid:
                        self._send(connection, {"status": "BLOCKED", "reason": "UNAUTHORIZED_PEER"})
                        continue
                    try:
                        response = {"status": "OK", "result": self.handle(self._read_request(connection))}
                    except BaseException as exc:
                        response = {"status": "BLOCKED", "reason": str(exc)}
                    self._send(connection, response)

    def serve_admin_unix(self, socket_path: Path) -> None:
        socket_path = Path(socket_path)
        socket_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if socket_path.parent.is_symlink() or socket_path.parent.stat().st_uid != self.supervisor_uid:
            raise HostBoundaryError("ADMIN_SOCKET_DIRECTORY_MUST_BE_SUPERVISOR_OWNED")
        os.chmod(socket_path.parent, 0o700)
        socket_path.unlink(missing_ok=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            server.listen()
            while True:
                connection, _ = server.accept()
                with connection:
                    credentials = connection.getsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_PEERCRED,
                        struct.calcsize("3i"),
                    )
                    _pid, uid, _gid = struct.unpack("3i", credentials)
                    if uid != self.supervisor_uid:
                        self._send(connection, {"status": "BLOCKED", "reason": "UNAUTHORIZED_ADMIN_PEER"})
                        continue
                    try:
                        response = {"status": "OK", "result": self.handle_admin(self._read_request(connection))}
                    except BaseException as exc:
                        response = {"status": "BLOCKED", "reason": str(exc)}
                    self._send(connection, response)


class SupervisorClient:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = Path(socket_path)

    def request(self, payload: dict) -> dict:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(self.socket_path))
            client.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = client.recv(65536)
                if not chunk:
                    break
                raw += chunk
        value = json.loads(raw)
        if value.get("status") != "OK":
            raise HostIntegrationUnavailable(value.get("reason", "supervisor blocked request"))
        return value["result"]
