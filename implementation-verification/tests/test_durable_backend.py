from __future__ import annotations

import importlib.util
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


interface = load("implementation_verification", ROOT / "implementation_verification.py")
durable = load("durable_work", ROOT / "durable_work.py")
backend_module = load("durable_backend", ROOT / "durable_backend.py")


class RecordingExecution:
    def __init__(self, candidate_factory) -> None:
        self.candidate_factory = candidate_factory
        self.dispatch_count = 0
        self.workspace_result = None
        self.started = threading.Event()
        self.release = threading.Event()
        self.block_first_dispatch = False
        self.interrupt_first_dispatch = False
        self.criterion_results = ()
        self.verification_count = 0

    def preflight_implementation(self, work):
        return None

    def preflight_verification(self, candidate):
        return None

    def implement(self, work, worker, transition_identity, *, reenter):
        if reenter:
            self.started.wait(timeout=5)
            self.release.set()
            return self.workspace_result
        self.dispatch_count += 1
        self.workspace_result = self.candidate_factory()
        self.started.set()
        if self.interrupt_first_dispatch:
            self.interrupt_first_dispatch = False
            raise InterruptedError("simulated response loss")
        if self.block_first_dispatch:
            self.release.wait(timeout=5)
        return self.workspace_result

    def verify(self, candidate, transition_identity, *, reenter):
        self.verification_count += 1
        return self.criterion_results

    def observe_currentness(self, result):
        return interface.Currentness.CURRENT


class DurableBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.ticket = root / "TICKET.md"
        self.ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        self.work = self.ticket.resolve()
        self.database = root / "state/durable.sqlite3"

        def candidate_factory():
            return interface.Candidate(
                work=self.work,
                planning={"ticket": self.work},
                acceptance_criteria=("AC-1",),
                source="source-1",
                implementation_changes=("app.py",),
                preserved_changes=("notes.txt",),
            )

        self.execution = RecordingExecution(candidate_factory)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def module(self):
        backend = backend_module.DurableBackend(
            durable.DurableWorkStore(self.database),
            self.execution,
        )
        return interface.ImplementationVerificationModule(backend)

    def test_public_implement_is_durable_and_same_request_reuses_result(self) -> None:
        first = self.module().implement(self.ticket, "worker-a")
        repeated = self.module().implement(self.ticket, "worker-a")
        inspection = self.module().inspect(self.ticket)

        self.assertEqual(1, self.execution.dispatch_count)
        self.assertEqual(first.result_identity, repeated.result_identity)
        self.assertEqual(first, inspection.result)
        self.assertEqual(interface.Currentness.CURRENT, inspection.currentness)

    def test_concurrent_public_implement_dispatches_worker_once(self) -> None:
        self.execution.block_first_dispatch = True
        modules = [self.module(), self.module()]
        barrier = threading.Barrier(2)

        def implement(module):
            barrier.wait()
            return module.implement(self.ticket, "worker-a")

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(implement, modules))

        self.assertEqual(1, self.execution.dispatch_count)
        self.assertEqual(1, len({result.result_identity for result in results}))

    def test_public_implement_reenters_after_response_loss_without_redispatch(self) -> None:
        self.execution.interrupt_first_dispatch = True
        with self.assertRaises(InterruptedError):
            self.module().implement(self.ticket, "worker-a")

        recovered = self.module().implement(self.ticket, "worker-a")

        self.assertEqual(1, self.execution.dispatch_count)
        self.assertIsNotNone(recovered.result_identity)
        self.assertEqual(recovered, self.module().inspect(self.ticket).result)

    def test_public_verify_publishes_and_inspect_recovers_exact_candidate(self) -> None:
        candidate = self.module().implement(self.ticket, "worker-a")
        self.execution.criterion_results = (
            interface.CriterionResult(
                "AC-1",
                interface.CriterionOutcome.SATISFIED,
                ("evidence-1",),
            ),
        )

        result = self.module().verify(candidate)
        inspection = self.module().inspect(self.ticket)

        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(result, inspection.result)
        self.assertEqual(candidate.result_identity, inspection.result.candidate.result_identity)

    def test_public_verify_rejects_changed_candidate_before_execution_or_publication(self) -> None:
        candidate = self.module().implement(self.ticket, "worker-a")
        changed = interface.Candidate(
            work=candidate.work,
            planning=candidate.planning,
            acceptance_criteria=candidate.acceptance_criteria,
            source="changed-source",
            implementation_changes=candidate.implementation_changes,
            preserved_changes=candidate.preserved_changes,
            result_identity=candidate.result_identity,
        )

        with self.assertRaisesRegex(ValueError, "exact durable Candidate"):
            self.module().verify(changed)

        inspection = self.module().inspect(self.ticket)
        self.assertEqual(0, self.execution.verification_count)
        self.assertEqual(candidate, inspection.result)

    def test_undetermined_result_allows_fresh_verification_of_same_candidate(self) -> None:
        candidate = self.module().implement(self.ticket, "worker-a")
        self.execution.criterion_results = (
            interface.CriterionResult("AC-1", interface.CriterionOutcome.UNDETERMINED),
        )
        first = self.module().verify(candidate)
        self.execution.criterion_results = (
            interface.CriterionResult(
                "AC-1",
                interface.CriterionOutcome.SATISFIED,
                ("fresh-evidence",),
            ),
        )

        second = self.module().verify(candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)
        self.assertEqual(interface.VerificationStatus.VERIFIED, second.status)
        self.assertNotEqual(first.result_identity, second.result_identity)
        self.assertEqual(2, self.execution.verification_count)


if __name__ == "__main__":
    unittest.main()
