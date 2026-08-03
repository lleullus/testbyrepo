from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE = IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("greenfield_handoff", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


class GreenfieldAdmissionPilotTests(unittest.TestCase):
    def run_greenfield(self, *, delegated: bool) -> dict[str, object]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        project = root / "product"
        project.mkdir()
        note = project / "user-note.txt"
        note.write_text("preserve me\n", encoding="utf-8")
        planning = root / "planning"
        planning.mkdir()
        spec = planning / "SPEC.md"
        ticket = planning / "TICKET.md"
        disposition = (
            "Remaining private bootstrap choices are explicitly delegated."
            if delegated
            else "Every material bootstrap choice is fixed."
        )
        spec.write_text(f"# Spec\nStatus: approved\n\n{disposition}\n", encoding="utf-8")
        ticket.write_text(
            "# Ticket\n\n## Acceptance Criteria\n\n"
            "- The first local entry point returns ready and preserves the user note.\n\n"
            "## Scope\n\nFirst local product target.\n",
            encoding="utf-8",
        )
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
            task_id="bootstrap",
            criterion_refs=criteria,
            allowed_paths=["READY" if not delegated else "app.py"],
            forbidden_paths=["user-note.txt"],
        )
        publisher.transactions.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        target = project / ("app.py" if delegated else "READY")
        target.write_text('print("ready")\n' if delegated else "ready\n", encoding="utf-8")
        check = publisher.transactions.run_check(
            transaction_capability=transaction["transactionCapability"],
            executable="python3",
            argv=[
                "-c",
                "from pathlib import Path; assert Path('user-note.txt').read_text() == 'preserve me\\n'",
            ],
            cwd=project,
        )
        self.assertEqual(0, check["result"]["exitCode"])
        publisher.transactions.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        publisher.transactions.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": [target.name],
                "externalPaths": [],
                "preservedUserChanges": [],
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
                "criterionAccounting": [{**criteria[0], "taskIds": ["bootstrap"]}],
                "unresolvedImplementationItems": [],
            }
        )
        return {
            "handoff": handoff,
            "prepared": prepared,
            "note": note,
            "target": target,
            "transaction": publisher.transactions.read_transaction(transaction["transactionRef"]),
        }

    def test_all_fixed_bootstrap_closes_to_handoff_without_final_verdict(self) -> None:
        result = self.run_greenfield(delegated=False)
        self.assertEqual("ready\n", result["target"].read_text(encoding="utf-8"))
        self.assertEqual("preserve me\n", result["note"].read_text(encoding="utf-8"))
        self.assertEqual("IMPLEMENTATION_HANDOFF_COMPLETE", result["handoff"]["implementationStatus"])
        self.assertNotIn("verificationStatus", result["handoff"])

    def test_delegated_private_bootstrap_records_check_but_verification_remains_pending(self) -> None:
        result = self.run_greenfield(delegated=True)
        self.assertEqual('print("ready")\n', result["target"].read_text(encoding="utf-8"))
        self.assertEqual(1, len(result["transaction"]["checks"]))
        self.assertEqual("CLOSED_WITH_HANDOFF", result["transaction"]["state"])
        self.assertNotIn("criterionResults", result["handoff"])


if __name__ == "__main__":
    unittest.main()
