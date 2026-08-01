from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ownership_snapshot = load_module(
    "pilot_ownership_snapshot",
    IMPLEMENTATION_ROOT / "tools/task-ownership-snapshot/ownership_snapshot.py",
)
implementation_result = load_module(
    "pilot_implementation_result",
    IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConcurrentScratchPilotTests(unittest.TestCase):
    def test_disjoint_planning_work_can_be_preserved_through_result_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            current = project / ".scratch" / "current-work"
            current.mkdir(parents=True)
            spec = current / "SPEC.md"
            ticket = current / "tickets" / "TICKET-001.md"
            ticket.parent.mkdir()
            spec.write_text("approved spec\n", encoding="utf-8")
            ticket.write_text("ready ticket\n", encoding="utf-8")
            app = project / "app.py"
            app.write_text("VALUE = 1\n", encoding="utf-8")

            capsule_root = root / "capsules"
            capsule_store = implementation_result.baseline_capsule.CapsuleStore(capsule_root)
            capsule = capsule_store.create(project)
            before = ownership_snapshot.capture(project)

            app.write_text("VALUE = 2\n", encoding="utf-8")
            other = project / ".scratch" / "wp-002-routing-queue"
            other.mkdir()
            (other / "SPEC.md").write_text("concurrent spec\n", encoding="utf-8")
            other_ticket = other / "tickets" / "TICKET-001.md"
            other_ticket.parent.mkdir()
            other_ticket.write_text("concurrent ticket\n", encoding="utf-8")

            after = ownership_snapshot.capture(project)
            delta = ownership_snapshot.compare(
                before,
                after,
                allowed_mutation_scopes=["app.py"],
            )

            self.assertEqual("OUTSIDE_ENVELOPE", delta["scopeState"])
            self.assertEqual("NOT_ESTABLISHED", delta["actorAttribution"])
            self.assertEqual(["app.py"], delta["inScopePaths"])
            self.assertTrue(delta["outOfScopePaths"])
            self.assertTrue(
                all(path.startswith(".scratch/wp-002-routing-queue") for path in delta["outOfScopePaths"])
            )
            self.assertNotIn(str(ticket.relative_to(project)), delta["changedPaths"])
            self.assertNotIn(str(spec.relative_to(project)), delta["changedPaths"])

            preservation_readback = ownership_snapshot.capture(project)
            self.assertEqual(after["identity"], preservation_readback["identity"])
            self.assertEqual("VALUE = 2\n", app.read_text(encoding="utf-8"))
            self.assertEqual("concurrent spec\n", (other / "SPEC.md").read_text(encoding="utf-8"))

            final_review_start = implementation_result.baseline_capsule.capture_identity(project)
            final_source = implementation_result.baseline_capsule.capture_identity(project)
            self.assertEqual(final_review_start["sourceIdentity"], final_source["sourceIdentity"])

            result_root = root / "results"
            result_store = implementation_result.ResultStore(result_root, capsule_root)
            published = result_store.publish(
                {
                    "protocolVersion": "implementation-result-v2",
                    "implementationStatus": "IMPLEMENTATION_COMPLETE",
                    "projectRoot": str(project.resolve()),
                    "planningSeal": {
                        "ticketPath": str(ticket.resolve()),
                        "ticketSha256": digest(ticket),
                        "specPath": str(spec.resolve()),
                        "specSha256": digest(spec),
                        "blockerFiles": [],
                    },
                    "capsuleRef": capsule["capsuleRef"],
                    "finalSourceIdentity": final_source["sourceIdentity"],
                }
            )

            token = published["implementationResultRef"].split(":")[-1]
            readback = json.loads((result_root / f"{token}.json").read_text(encoding="utf-8"))
            current_identity = implementation_result.baseline_capsule.capture_identity(project)
            self.assertEqual("IMPLEMENTATION_COMPLETE", readback["implementationStatus"])
            self.assertEqual(capsule["baselineSourceIdentity"], readback["baselineSourceIdentity"])
            self.assertEqual(current_identity["sourceIdentity"], readback["finalSourceIdentity"])


if __name__ == "__main__":
    unittest.main()
