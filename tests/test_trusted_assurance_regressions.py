from __future__ import annotations

import base64
import json
import os
import socket
import stat
import sys
import unittest

from assurance_support import AssuranceFixture, assurance
from iis_artifacts.publication import publish_ref
from iis_artifacts.host import HostSupervisor
from iis_artifacts.store import ArtifactStore


class TrustedAssuranceRegressionTests(AssuranceFixture, unittest.TestCase):
    def enforced_supervisor(self) -> HostSupervisor:
        return HostSupervisor(
            store_base=self.arena / "store",
            project_id="fixture",
            project_root=self.root,
            worker_uid=os.geteuid() + 10000,
            current_request="Run the exact assurance fixture.",
            review_budget=1,
            gate_runner=assurance._native_runner,
        )

    def test_embedded_live_source_path_is_rejected_before_invocation_start(self) -> None:
        self.baseline["gates"][0]["argv"] = [
            sys.executable,
            "-B",
            "-c",
            f"exec(open({str(self.command)!r}).read())",
        ]
        self.seal()
        supervisor = self.enforced_supervisor()
        with self.assertRaisesRegex(ValueError, "UNSAFE_EMBEDDED_SOURCE_PATH"):
            supervisor.run_assurance_gate(
                self.baseline_path,
                self.binding,
                "native",
                self.arena / ("unsafe-capture-" + self.binding["run_id"]),
            )
        with self.store.connect() as db:
            count = db.execute(
                "SELECT COUNT(*) AS value FROM assurance_invocations WHERE binding_id=?",
                (self.binding["binding_id"],),
            ).fetchone()["value"]
        self.assertEqual(count, 0)

    def test_settled_effect_requires_nonempty_evidence(self) -> None:
        supervisor = self.enforced_supervisor()
        with self.assertRaisesRegex(ValueError, "MISSING_EVIDENCE"):
            supervisor.record_assurance_effect(
                self.binding,
                "external-write",
                owner="host",
                state="SETTLED",
                evidence=[],
            )

    def test_result_effect_must_exist_in_host_ledger(self) -> None:
        supervisor = self.enforced_supervisor()
        supervisor.run_assurance_gate(
            self.baseline_path,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        invocation = assurance.begin_host_invocation(
            self.store,
            self.binding,
            "observation",
            "readback",
        )
        evidence = assurance.capture_invocation_evidence(
            self.store,
            self.binding,
            invocation,
            {"readback/stdout": b"actual-value\n"},
        )
        result = {
            "schema": "iis-assurance-result/v3",
            "kind": "observation",
            **self.baseline["observations"][0],
            "invocation": invocation,
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": evidence,
            "effects": ["external-write"],
            "outcome": "SATISFIED",
        }
        assurance.complete_host_invocation(
            self.store,
            self.binding,
            invocation,
            result,
        )
        closure = supervisor.close_assurance(self.baseline_path, self.binding)
        self.assertIn("UNRECORDED_EFFECT", closure["reasons"])


    @unittest.skipUnless(hasattr(socket, "SO_PEERCRED"), "Linux peer credentials required")
    def test_supervisor_admin_completes_observation_and_settled_effect(self) -> None:
        supervisor = self.enforced_supervisor()
        supervisor.run_assurance_gate(
            self.baseline_path,
            self.binding,
            "native",
            self.arena / ("admin-native-capture-" + self.binding["run_id"]),
        )
        started = supervisor.handle_admin({
            "action": "begin_assurance_invocation",
            "binding": self.binding,
            "kind": "observation",
            "item_id": "readback",
        })
        invocation = started["invocation_id"]
        captured = supervisor.handle_admin({
            "action": "capture_assurance_evidence",
            "binding": self.binding,
            "invocation_id": invocation,
            "files_b64": {
                "readback/stdout": base64.b64encode(b"actual-value\n").decode("ascii"),
            },
        })["evidence"]
        supervisor.handle_admin({
            "action": "record_assurance_effect",
            "binding": self.binding,
            "effect_id": "readback-effect",
            "owner": "observation",
            "state": "SETTLED",
            "evidence": captured,
        })
        supervisor.handle_admin({
            "action": "complete_assurance_invocation",
            "binding": self.binding,
            "invocation_id": invocation,
            "result": {
                "schema": "iis-assurance-result/v3",
                "kind": "observation",
                **self.baseline["observations"][0],
                "invocation": invocation,
                "binding": self.binding["binding_id"],
                "completion": "COMPLETE",
                "evidence": captured,
                "effects": ["readback-effect"],
                "outcome": "SATISFIED",
            },
        })
        closure = supervisor.handle_admin({
            "action": "close_assurance",
            "baseline_path": str(self.baseline_path),
            "binding": self.binding,
        })
        self.assertEqual(closure["status"], "EVIDENCE_COMPLETE")

    def test_publication_is_owned_by_project_owner_and_read_only(self) -> None:
        project = self.arena / "publication-project"
        project.mkdir(mode=0o700)
        store = ArtifactStore(self.arena / "publication-store", "project")
        logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        snapshot = store.capture_mapping(
            {logical: (b"# Product Thesis\n", 0o644)},
            kind="candidate",
        )
        publish_ref(
            store,
            {"snapshot": snapshot, "path": logical},
            project,
            logical,
            expected_prior=None,
        )
        target = project / logical
        self.assertEqual(target.stat().st_uid, project.stat().st_uid)
        self.assertEqual(target.stat().st_gid, project.stat().st_gid)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o444)
        self.assertEqual(target.parent.stat().st_uid, project.stat().st_uid)
        self.assertEqual(target.read_text(encoding="utf-8"), "# Product Thesis\n")

    def test_scope_for_another_project_never_reaches_role_dispatch(self):
        foreign = self.arena / "foreign"
        foreign.mkdir(mode=0o700)
        source = self.scope.read_text().replace(str(self.root), str(foreign))
        supervisor = self.enforced_supervisor()
        calls = []
        supervisor.role_dispatcher = lambda *args: calls.append(args)
        with self.assertRaisesRegex(RuntimeError, "FOREIGN_PROJECT"):
            supervisor.admit_and_start(role="scope-implement", scope_bytes=source.encode(), logical_path="docs/planning/work/example/SCOPE.md")
        self.assertEqual(calls, [])

    def test_changed_current_request_blocks_existing_binding(self):
        supervisor = self.enforced_supervisor()
        supervisor.set_current_request("Stop this work and reassess the meaning.")
        with self.assertRaisesRegex(ValueError, "CURRENT_REQUEST_MISMATCH"):
            supervisor.run_assurance_gate(self.baseline_path, self.binding, "native", self.arena / "changed-request")
        self.assertIn("ADMISSION_CURRENT_REQUEST_MISMATCH", supervisor.close_assurance(self.baseline_path, self.binding)["reasons"])

    def test_prelaunch_output_collision_can_be_corrected_without_new_binding(self):
        supervisor = self.enforced_supervisor()
        output = self.arena / "existing-output"
        output.mkdir()
        with self.assertRaises(FileExistsError):
            supervisor.run_assurance_gate(self.baseline_path, self.binding, "native", output)
        gate = supervisor.run_assurance_gate(self.baseline_path, self.binding, "native", self.arena / "fresh-output")
        self.observation()
        self.assertEqual(self.store.read_bytes(gate["capture"]["stdout"]), b"actual-value\n")
        self.assertEqual(supervisor.close_assurance(self.baseline_path, self.binding)["status"], "EVIDENCE_COMPLETE")

    def test_job_export_must_be_new_and_belong_to_actual_invocation(self):
        jobs = self.arena / "jobs.json"
        self.baseline["gates"][0].update(jobs=["integration"], jobs_path=str(jobs))
        self.baseline["gates"][0]["argv"] = [sys.executable, "-B", "-c",
            "import os,json; from pathlib import Path; "
            "Path(os.environ['IIS_ASSURANCE_JOBS_PATH']).write_text(json.dumps({"
            "'run_id':os.environ['IIS_ASSURANCE_RUN_ID'],'gate_id':os.environ['IIS_ASSURANCE_GATE_ID'],"
            "'invocation_id':os.environ['IIS_ASSURANCE_INVOCATION_ID'],'jobs':{'integration':'SUCCESS'}}))"]
        self.seal()
        jobs.write_text(json.dumps({"run_id":self.binding["run_id"], "gate_id":"native", "jobs":{"integration":"SUCCESS"}}))
        supervisor = self.enforced_supervisor()
        with self.assertRaisesRegex(ValueError, "JOB_EXPORT_ALREADY_EXISTS"):
            supervisor.run_assurance_gate(self.baseline_path, self.binding, "native", self.arena / "seeded-export")
        jobs.unlink()
        supervisor.run_assurance_gate(self.baseline_path, self.binding, "native", self.arena / "actual-export")
        self.observation()
        self.assertEqual(supervisor.close_assurance(self.baseline_path, self.binding)["status"], "EVIDENCE_COMPLETE")

    def test_unregistered_producer_cannot_settle_effect(self):
        ref = self.fixed_bytes("effect/claimed.txt", b"settled", invocation="never-started")
        with self.assertRaisesRegex(ValueError, "EFFECT_EVIDENCE_INVOCATION_UNKNOWN"):
            self.enforced_supervisor().record_assurance_effect(self.binding, "write", owner="observer", state="SETTLED", evidence=[ref])

    def test_missing_evidence_returns_blocked_instead_of_exception(self):
        gate, _ = self.evidence()
        self.store.delete_snapshot(gate["capture"]["stdout"]["snapshot"])
        closure = self.enforced_supervisor().close_assurance(self.baseline_path, self.binding)
        self.assertEqual(closure["status"], "BLOCKED")
        self.assertIn("snapshot reference is not registered", closure["reasons"])

    def test_admin_observation_completion_cannot_forge_native_gate(self):
        invocation = assurance._begin_invocation(self.store, self.binding, "gate", "native")
        with self.assertRaisesRegex(ValueError, "NATIVE_GATE_CAPTURE_REQUIRED"):
            self.enforced_supervisor().complete_assurance_invocation(self.binding, invocation, {})


if __name__ == "__main__":
    unittest.main()
