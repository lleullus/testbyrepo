from __future__ import annotations

import importlib.util
import sqlite3
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


class DurableWorkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.ticket = root / "TICKET.md"
        self.ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        self.work = self.ticket.resolve()
        self.database = root / "state/durable.sqlite3"
        self.store = durable.DurableWorkStore(self.database)
        self.candidate = interface.Candidate(
            work=self.work,
            planning={"ticket": self.work},
            acceptance_criteria=("AC-1",),
            source="source-1",
            implementation_changes=("app.py",),
            preserved_changes=("notes.txt",),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def begin(self, *, semantic="request-1", progress="private-progress"):
        return self.store.begin(self.work, "IMPLEMENT", semantic, progress)

    def test_inspect_without_store_is_read_only_and_nonconclusive(self) -> None:
        inspection = self.store.inspect(self.work)

        self.assertIsInstance(inspection.result, interface.NoConclusiveResult)
        self.assertEqual(interface.Currentness.UNKNOWN, inspection.currentness)
        self.assertFalse(self.database.exists())

    def test_concurrent_same_request_has_one_start_and_restart_reenters(self) -> None:
        barrier = threading.Barrier(2)

        def attempt():
            barrier.wait()
            return durable.DurableWorkStore(self.database).begin(
                self.work, "IMPLEMENT", "same-request", "progress"
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            decisions = list(executor.map(lambda _: attempt(), range(2)))

        self.assertEqual(
            [durable.TransitionDisposition.REENTER, durable.TransitionDisposition.STARTED],
            sorted((item.disposition for item in decisions), key=lambda value: value.value),
        )
        self.assertEqual(1, len({item.transition_identity for item in decisions}))
        restarted = durable.DurableWorkStore(self.database).begin(
            self.work, "IMPLEMENT", "same-request", "progress"
        )
        self.assertEqual(durable.TransitionDisposition.REENTER, restarted.disposition)
        competing = self.store.begin(self.work, "VERIFY", "other-request", "other-progress")
        self.assertEqual(durable.TransitionDisposition.BUSY, competing.disposition)

    def test_candidate_publication_is_durable_idempotent_and_inspectable(self) -> None:
        transition = self.begin()

        published = self.store.publish(transition.transition_identity, self.candidate)
        repeated = self.store.publish(transition.transition_identity, self.candidate)
        inspection = durable.DurableWorkStore(self.database).inspect(
            self.work,
            lambda _: interface.Currentness.NOT_CURRENT,
        )

        self.assertIsInstance(published, interface.Candidate)
        self.assertEqual(published.result_identity, repeated.result_identity)
        self.assertEqual(published, inspection.result)
        self.assertEqual(interface.Currentness.NOT_CURRENT, inspection.currentness)
        state = self.store.transition_state(transition.transition_identity)
        self.assertEqual("CLOSED", state["state"])
        completed = self.store.begin(self.work, "IMPLEMENT", "request-1", "new-progress")
        self.assertEqual(durable.TransitionDisposition.COMPLETED, completed.disposition)
        self.assertEqual(published, completed.result)

    def test_publication_failure_rolls_back_result_head_and_transition_close(self) -> None:
        transition = self.begin()
        with self.store._transaction() as connection:
            connection.execute(
                """CREATE TRIGGER fail_head_advance BEFORE UPDATE OF head_result_ref ON work_streams
                   WHEN NEW.head_result_ref IS NOT NULL
                   BEGIN SELECT RAISE(ABORT, 'simulated publication failure'); END"""
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.store.publish(transition.transition_identity, self.candidate)

        inspection = self.store.inspect(self.work)
        self.assertIsInstance(inspection.result, interface.NoConclusiveResult)
        self.assertEqual("ACTIVE", self.store.transition_state(transition.transition_identity)["state"])

    def test_verification_result_recovers_its_exact_durable_candidate(self) -> None:
        implementation = self.begin()
        candidate = self.store.publish(implementation.transition_identity, self.candidate)
        verification = self.store.begin(
            self.work,
            "VERIFY",
            {"candidate": candidate.result_identity},
            "verification-progress",
        )
        result = interface.VerificationResult(
            candidate,
            (
                interface.CriterionResult(
                    "AC-1",
                    interface.CriterionOutcome.SATISFIED,
                    ("evidence-1",),
                ),
            ),
        )

        published = self.store.publish(verification.transition_identity, result)
        recovered = durable.DurableWorkStore(self.database).inspect(self.work).result

        self.assertIsInstance(published, interface.VerificationResult)
        self.assertEqual(published, recovered)
        self.assertEqual(candidate.result_identity, recovered.candidate.result_identity)
        self.assertEqual(interface.VerificationStatus.VERIFIED, recovered.status)

    def test_verification_publication_rejects_candidate_content_changed_under_durable_identity(self) -> None:
        implementation = self.begin()
        candidate = self.store.publish(implementation.transition_identity, self.candidate)
        verification = self.store.begin(
            self.work,
            "VERIFY",
            {"candidate": candidate.result_identity},
            "verification-progress",
        )
        changed = interface.Candidate(
            work=candidate.work,
            planning=candidate.planning,
            acceptance_criteria=candidate.acceptance_criteria,
            source="changed-source",
            implementation_changes=candidate.implementation_changes,
            preserved_changes=candidate.preserved_changes,
            result_identity=candidate.result_identity,
        )
        result = interface.VerificationResult(
            changed,
            (
                interface.CriterionResult(
                    "AC-1",
                    interface.CriterionOutcome.SATISFIED,
                    ("evidence-for-changed-source",),
                ),
            ),
        )

        with self.assertRaisesRegex(durable.DurableWorkError, "not durable"):
            self.store.publish(verification.transition_identity, result)

        self.assertEqual(candidate, self.store.inspect(self.work).result)
        self.assertEqual("ACTIVE", self.store.transition_state(verification.transition_identity)["state"])

    def test_overlapping_mutation_domain_has_one_winner_and_atomic_release(self) -> None:
        root = Path(self.temporary.name)
        second_ticket = root / "TICKET-002.md"
        second_ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        product = root / "product"
        nested = product / "nested"
        nested.mkdir(parents=True)
        first = self.begin()
        second = self.store.begin(second_ticket, "IMPLEMENT", "request-2", "progress-2")
        observed: list[Path] = []

        first_occupancy = self.store.occupy_mutation_domain(
            first.transition_identity,
            product,
            "source-1",
            lambda path: observed.append(path) or "source-1",
        )
        second_occupancy = self.store.occupy_mutation_domain(
            second.transition_identity,
            nested,
            "source-2",
            lambda path: observed.append(path) or "source-2",
        )

        self.assertTrue(first_occupancy.acquired)
        self.assertTrue(first_occupancy.source_matches)
        self.assertFalse(second_occupancy.acquired)
        self.assertEqual([product.resolve()], observed)

        self.store.close_without_result(first.transition_identity)
        acquired_after_release = self.store.occupy_mutation_domain(
            second.transition_identity,
            nested,
            "source-2",
            lambda path: observed.append(path) or "changed-source",
        )
        self.assertTrue(acquired_after_release.acquired)
        self.assertFalse(acquired_after_release.source_matches)
        self.assertEqual(str(nested.resolve()), self.store.transition_state(second.transition_identity)["mutationDomain"])
        self.store.close_without_result(second.transition_identity)
        self.assertIsNone(self.store.transition_state(second.transition_identity)["mutationDomain"])


if __name__ == "__main__":
    unittest.main()
