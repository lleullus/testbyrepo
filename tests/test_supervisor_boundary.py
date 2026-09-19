from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

from iis_artifacts.supervisor import HostBoundaryError, HostIntegrationUnavailable, HostSupervisor


@unittest.skipUnless(hasattr(socket, "SO_PEERCRED"), "Linux peer credentials required")
class SupervisorBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="iis-supervisor-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir(mode=0o700)

    def supervisor(self, **kwargs):
        return HostSupervisor(
            store_base=self.root / "store",
            project_id="project",
            project_root=self.project,
            worker_uid=os.geteuid() + 10000,
            current_request="Trusted current request.",
            review_budget=2,
            **kwargs,
        )

    def test_same_uid_cannot_claim_enforced_supervisor_worker_separation(self) -> None:
        with self.assertRaisesRegex(HostBoundaryError, "UID_MUST_DIFFER"):
            HostSupervisor(
                store_base=self.root / "store",
                project_id="project",
                project_root=self.project,
                worker_uid=os.geteuid(),
                current_request="Trusted current request.",
                review_budget=2,
            )

    def test_no_review_dispatcher_means_no_enforced_thesis_progress_or_close(self) -> None:
        supervisor = self.supervisor()
        state = supervisor.start_thesis()
        with self.assertRaisesRegex(HostIntegrationUnavailable, "REVIEW_DISPATCHER_UNAVAILABLE"):
            supervisor.drive_thesis(state["run_id"])
        with self.assertRaisesRegex(HostIntegrationUnavailable, "REVIEW_DISPATCHER_UNAVAILABLE"):
            supervisor.close_thesis(state["run_id"])

    def test_no_role_dispatcher_means_no_role_start(self) -> None:
        supervisor = self.supervisor(
            review_dispatcher=lambda phase, run, inputs, candidate: {"result": {"completion": "COMPLETE"}}
        )
        with self.assertRaisesRegex(HostIntegrationUnavailable, "ROLE_DISPATCHER_UNAVAILABLE"):
            supervisor.admit_and_start(
                role="scope-plan",
                scope_bytes=b"not parsed because dispatcher availability is checked first",
                logical_path="docs/planning/work/demo/SCOPE.md",
            )

    def test_worker_rpc_cannot_supply_new_current_request_resume_or_role_start(self) -> None:
        supervisor = self.supervisor()
        with self.assertRaisesRegex(ValueError, "unsupported supervisor action"):
            supervisor.handle({"action": "resume", "run_id": "x", "request": "forged"})
        with self.assertRaisesRegex(ValueError, "unsupported supervisor action"):
            supervisor.handle({
                "action": "admit_and_start",
                "role": "scope-plan",
                "scope_b64": "",
                "logical_path": "docs/planning/work/demo/SCOPE.md",
                "current_request": "forged",
            })
        state = supervisor.handle({"action": "start", "request": "worker-forged request"})
        with supervisor.store.connect() as db:
            row = db.execute("SELECT request_text FROM thesis_runs WHERE run_id=?", (state["run_id"],)).fetchone()
        self.assertEqual(row["request_text"], "Trusted current request.")

    def test_worker_clis_cannot_mint_enforced_credentials_without_supervisor(self) -> None:
        thesis = subprocess.run(
            [sys.executable, "-B", str(ROOT / "product-thesis/tools/thesis.py"), "start"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={key: value for key, value in os.environ.items() if key != "IIS_SUPERVISOR_SOCKET"},
        )
        self.assertEqual(thesis.returncode, 20)
        self.assertIn("HOST_SUPERVISOR_REQUIRED", thesis.stdout)

        admission = subprocess.run(
            [sys.executable, "-B", "-m", "iis_artifacts.admission"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(admission.returncode, 20)
        self.assertIn("HOST_SUPERVISOR_REQUIRED", admission.stdout)

        assurance = subprocess.run(
            [sys.executable, "-B", str(ROOT / "iis-workflow/tools/assurance.py"), "bind"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(assurance.returncode, 20)
        self.assertIn("HOST_SUPERVISOR_REQUIRED", assurance.stdout)

    def test_unix_socket_rejects_peer_uid_not_owned_by_worker(self) -> None:
        supervisor = self.supervisor()
        socket_path = self.root / "supervisor.sock"
        thread = threading.Thread(target=supervisor.serve_unix, args=(socket_path,), daemon=True)
        thread.start()
        for _ in range(100):
            if socket_path.exists():
                break
            time.sleep(0.01)
        self.assertTrue(socket_path.exists())
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(socket_path))
            client.sendall(b'{"action":"inspect","run_id":"missing"}\n')
            raw = b""
            while not raw.endswith(b"\n"):
                raw += client.recv(4096)
        result = json.loads(raw)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "UNAUTHORIZED_PEER")

    def test_failed_review_requires_trusted_settlement_before_retry(self):
        import base64
        def failed(*args):
            raise RuntimeError("review process failed")
        supervisor = self.supervisor(review_dispatcher=failed)
        run_id = supervisor.start_thesis()["run_id"]
        with self.assertRaisesRegex(HostIntegrationUnavailable, "DISPATCH_FAILED"):
            supervisor.drive_thesis(run_id)
        review = supervisor.inspect_thesis(run_id)["reviews"][0]
        with self.assertRaisesRegex(HostIntegrationUnavailable, "SETTLEMENT_REQUIRED"):
            supervisor.drive_thesis(run_id)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            supervisor.handle({"action":"settle_thesis_review", "invocation_id":review["invocation_id"]})
        supervisor.handle_admin({"action":"settle_thesis_review", "invocation_id":review["invocation_id"], "evidence_b64":{"exit.txt":base64.b64encode(b"Callback returned; no process or effects started.").decode()}})
        supervisor.review_dispatcher = lambda *args: {"result":{"completion":"COMPLETE"}}
        supervisor.drive_thesis(run_id)
        self.assertEqual([item["status"] for item in supervisor.inspect_thesis(run_id)["reviews"]], ["SETTLED", "COMPLETE"])

    def test_blocked_review_is_not_successful_completion(self):
        supervisor = self.supervisor(review_dispatcher=lambda *args: {"result":{"completion":"BLOCKED", "error":"Required input missing"}})
        run_id = supervisor.start_thesis()["run_id"]
        supervisor.drive_thesis(run_id)
        self.assertNotEqual(supervisor.close_thesis(run_id)["result"], "CALIBRATED")
        self.assertEqual(supervisor.inspect_thesis(run_id)["reviews"][0]["status"], "BLOCKED")

    def test_partial_control_frame_times_out_without_hanging_next_read(self):
        receiver, sender = socket.socketpair()
        with receiver, sender:
            sender.sendall(b'{"action":')
            with self.assertRaises(TimeoutError):
                HostSupervisor._read_request(receiver, timeout=0.02)
        receiver, sender = socket.socketpair()
        with receiver, sender:
            sender.sendall(b'{"action":"inspect"}\n')
            self.assertEqual(HostSupervisor._read_request(receiver)["action"], "inspect")


if __name__ == "__main__":
    unittest.main()
