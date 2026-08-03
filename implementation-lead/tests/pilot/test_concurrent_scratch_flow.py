from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE = IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("scratch_handoff", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConcurrentScratchPilotTests(unittest.TestCase):
    def test_disjoint_concurrent_work_is_preserved_and_excluded_from_task_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            app = project / "app.py"
            app.write_text("VALUE = 1\n", encoding="utf-8")
            planning = project / ".scratch/current-work"
            (planning / "tickets").mkdir(parents=True)
            spec = planning / "SPEC.md"
            ticket = planning / "tickets/TICKET-001.md"
            spec.write_text("# Spec\nStatus: approved\n", encoding="utf-8")
            ticket.write_text(
                "# Ticket\n\n## Acceptance Criteria\n\n- The source value is 2.\n\n## Scope\n\napp.py\n",
                encoding="utf-8",
            )
            seal = {
                "ticketPath": str(ticket.resolve()),
                "ticketSha256": digest(ticket),
                "specPath": str(spec.resolve()),
                "specSha256": digest(spec),
                "blockerFiles": [],
            }
            planning_digest = implementation_result.planning_seal_digest(seal)
            criteria = implementation_result.acceptance_criteria_from_ticket(ticket)
            publisher = implementation_result.HandoffPublisher(
                root / "workflow",
                root / "capsules",
            )
            transaction = publisher.transactions.start_initial(
                project_root=project,
                planning_identity=planning_digest,
                selected_worker="pilot-worker",
            )
            envelope = publisher.transactions.freeze_envelope(
                transaction_capability=transaction["transactionCapability"],
                task_id="task-1",
                criterion_refs=criteria,
                allowed_paths=["app.py"],
                forbidden_paths=[],
            )
            publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            app.write_text("VALUE = 2\n", encoding="utf-8")
            concurrent = project / ".scratch/wp-002-routing-queue"
            concurrent.mkdir()
            (concurrent / "SPEC.md").write_text("concurrent spec\n", encoding="utf-8")
            after = publisher.transactions.capture_after(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            external = [
                path
                for path in after["delta"]["changedPaths"]
                if path.startswith(".scratch/wp-002-routing-queue")
            ]
            self.assertTrue(external)
            publisher.transactions.reconcile_envelope(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
                reconciliation={
                    "disposition": "CONTINUE",
                    "workerAttributablePaths": ["app.py"],
                    "externalPaths": external,
                    "preservedUserChanges": external,
                    "externalEffectState": "CLEAR",
                },
            )
            prepared = publisher.transactions.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            )
            handoff = publisher.publish(
                {
                    "protocolVersion": "implementation-handoff-v1",
                    "implementationTransactionRef": transaction["transactionRef"],
                    "actorCapability": None,
                    "planningSeal": seal,
                    "criterionAccounting": [{**criteria[0], "taskIds": ["task-1"]}],
                    "unresolvedImplementationItems": [],
                }
            )

            self.assertEqual("IMPLEMENTATION_HANDOFF_COMPLETE", handoff["implementationStatus"])
            self.assertEqual(prepared["finalSourceIdentity"], handoff["finalSourceIdentity"])
            self.assertEqual("VALUE = 2\n", app.read_text(encoding="utf-8"))
            self.assertEqual("concurrent spec\n", (concurrent / "SPEC.md").read_text(encoding="utf-8"))
            self.assertEqual(["task-1"], handoff["criterionAccounting"][0]["taskIds"])
            self.assertNotIn("verificationStatus", handoff)


if __name__ == "__main__":
    unittest.main()
