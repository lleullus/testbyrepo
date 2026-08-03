from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE = IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("provisional_check_handoff", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


class ProvisionalImplementationCheckPilotTests(unittest.TestCase):
    def test_worker_check_is_durable_but_not_a_final_verification_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            app = project / "app.py"
            app.write_text('print("before")\n', encoding="utf-8")
            ticket = root / "TICKET.md"
            spec = root / "SPEC.md"
            ticket.write_text(
                "# Ticket\n\n## Acceptance Criteria\n\n- The public command returns ready.\n",
                encoding="utf-8",
            )
            spec.write_text("# Spec\nStatus: approved\n", encoding="utf-8")
            seal = {
                "ticketPath": str(ticket.resolve()),
                "ticketSha256": hashlib.sha256(ticket.read_bytes()).hexdigest(),
                "specPath": str(spec.resolve()),
                "specSha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
                "blockerFiles": [],
            }
            criteria = implementation_result.acceptance_criteria_from_ticket(ticket)
            publisher = implementation_result.HandoffPublisher(root / "workflow", root / "capsules")
            transaction = publisher.transactions.start_initial(
                project_root=project,
                planning_identity=implementation_result.planning_seal_digest(seal),
                selected_worker="pilot-worker",
            )
            envelope = publisher.transactions.freeze_envelope(
                transaction_capability=transaction["transactionCapability"],
                task_id="command",
                criterion_refs=criteria,
                allowed_paths=["app.py"],
                forbidden_paths=[],
            )
            publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            app.write_text('print("ready")\n', encoding="utf-8")
            check = publisher.transactions.run_check(
                transaction_capability=transaction["transactionCapability"],
                executable="python3",
                argv=["app.py"],
                cwd=project,
            )
            self.assertEqual("ready\n", check["result"]["stdout"]["text"])
            publisher.transactions.capture_after(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            publisher.transactions.reconcile_envelope(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
                reconciliation={
                    "disposition": "CONTINUE",
                    "workerAttributablePaths": ["app.py"],
                    "externalPaths": [],
                    "preservedUserChanges": [],
                    "externalEffectState": "CLEAR",
                },
            )
            publisher.transactions.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            )
            handoff = publisher.publish(
                {
                    "protocolVersion": "implementation-handoff-v1",
                    "implementationTransactionRef": transaction["transactionRef"],
                    "actorCapability": None,
                    "planningSeal": seal,
                    "criterionAccounting": [{**criteria[0], "taskIds": ["command"]}],
                    "unresolvedImplementationItems": [],
                }
            )
            transaction_view = publisher.transactions.read_transaction(transaction["transactionRef"])

            self.assertEqual(1, len(transaction_view["checks"]))
            self.assertNotIn("runtimeObservations", handoff)
            self.assertNotIn("criterionResults", handoff)
            self.assertNotIn("verificationStatus", handoff)

    def test_caller_authored_runtime_v3_cannot_be_published(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            publisher = implementation_result.HandoffPublisher(Path(temporary) / "workflow")
            with self.assertRaises(implementation_result.HandoffError) as raised:
                publisher.publish(
                    {
                        "protocolVersion": "implementation-result-v3",
                        "completionRecord": {
                            "runtimeObservations": [{"callerAuthored": True, "claimedSuccess": True}]
                        },
                    }
                )
            self.assertEqual("PROTOCOL_RETIRED", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
