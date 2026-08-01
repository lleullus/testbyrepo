from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("implementation_result", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImplementationResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "project"
        self.project.mkdir()
        self.ticket = self.project / "TICKET.md"
        self.spec = self.project / "SPEC.md"
        self.ticket.write_text("ticket\n", encoding="utf-8")
        self.spec.write_text("spec\n", encoding="utf-8")
        (self.project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.capsule_root = root / "capsules"
        self.result_root = root / "results"
        self.capsules = implementation_result.baseline_capsule.CapsuleStore(self.capsule_root)
        self.handle = self.capsules.create(self.project)
        self.store = implementation_result.ResultStore(self.result_root, self.capsule_root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self) -> dict[str, object]:
        return {
            "protocolVersion": "implementation-result-v2",
            "implementationStatus": "IMPLEMENTATION_COMPLETE",
            "projectRoot": str(self.project),
            "planningSeal": {
                "ticketPath": str(self.ticket),
                "ticketSha256": digest(self.ticket),
                "specPath": str(self.spec),
                "specSha256": digest(self.spec),
                "blockerFiles": [],
            },
            "capsuleRef": self.handle["capsuleRef"],
            "finalSourceIdentity": implementation_result.baseline_capsule.capture_identity(self.project)["sourceIdentity"],
        }

    def test_publishes_result_bound_to_capsule_planning_and_source(self) -> None:
        result = self.store.publish(self.request())
        self.assertRegex(result["implementationResultRef"], r"^implementation:v2:[a-f0-9]{32}$")
        self.assertEqual("IMPLEMENTATION_COMPLETE", result["implementationStatus"])
        self.assertEqual(self.handle["baselineSourceIdentity"], result["baselineSourceIdentity"])
        token = result["implementationResultRef"].split(":")[-1]
        self.assertTrue((self.result_root / f"{token}.json").is_file())

    def test_source_change_rejects_stale_final_identity(self) -> None:
        request = self.request()
        (self.project / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(implementation_result.ResultError, "SOURCE_IDENTITY_MISMATCH"):
            self.store.publish(request)

    def test_planning_change_is_rejected(self) -> None:
        request = self.request()
        self.ticket.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(implementation_result.ResultError, "PLANNING_INPUT_CHANGED"):
            self.store.publish(request)

    def test_capsule_from_other_project_is_rejected(self) -> None:
        other = self.project.parent / "other"
        other.mkdir()
        other_handle = self.capsules.create(other)
        request = self.request()
        request["capsuleRef"] = other_handle["capsuleRef"]
        with self.assertRaisesRegex(implementation_result.ResultError, "CAPSULE_PROJECT_MISMATCH"):
            self.store.publish(request)

    def test_noncomplete_status_cannot_be_published(self) -> None:
        request = self.request()
        request["implementationStatus"] = "BLOCKED"
        with self.assertRaisesRegex(implementation_result.ResultError, "INVALID_IMPLEMENTATION_STATUS"):
            self.store.publish(request)


if __name__ == "__main__":
    unittest.main()
