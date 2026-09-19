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


if __name__ == "__main__":
    unittest.main()
