from __future__ import annotations

import sqlite3
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tests.test_phase7_public_contract import (
    Phase7PublicContractTests,
    TestConformanceEffectAdapter,
    TestSourceAdoptionAdapter,
    entrypoint,
    implementation,
    interface,
    production,
)


class Phase7FaultBoundaryTests(Phase7PublicContractTests):
    def test_fault_01_concurrent_work_has_one_external_owner(self) -> None:
        dispatch_file = self.project / "dispatch-count.txt"
        code = (
            "import fcntl,json,pathlib,time;"
            "r=json.loads(pathlib.Path('/input/request.json').read_text());"
            "p=pathlib.Path('/workspace/dispatch-count.txt');p.touch();"
            "f=p.open('r+');fcntl.flock(f.fileno(),fcntl.LOCK_EX);"
            "v=int(f.read() or '0')+1;f.seek(0);f.truncate();f.write(str(v));f.flush();"
            "time.sleep(.2);"
            "a=r['assignment'];q=pathlib.Path('/workspace')/a['path'];q.write_text(a['value'])"
        )
        worker = production.ProcessWorker("worker-concurrent", ("/usr/bin/python3", "-c", code))
        module = self.module()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: module.implement(self.ticket, worker), range(2)))
        self.assertEqual("1", dispatch_file.read_text())
        self.assertEqual(1, len({item.result_identity for item in results}))
    def test_fault_02_overlapping_mutation_domain_has_one_winner(self) -> None:
        second = self.root / "TICKET-2.md"
        second.write_text(self.ticket.read_text().replace("# Ticket", "# Ticket 2"))
        first_module = self.composed(
            self.review(delay=.2),
            ("/usr/bin/python3", "-c", __import__("tests.test_phase7_public_contract", fromlist=["verifier_script"]).verifier_script("implemented")),
        )
        second_module = self.composed(
            self.review(desired="other", delay=.2),
            ("/usr/bin/python3", "-c", __import__("tests.test_phase7_public_contract", fromlist=["verifier_script"]).verifier_script("other")),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = (
                executor.submit(first_module.implement, self.ticket, self.worker("worker-a")),
                executor.submit(second_module.implement, second, self.worker("worker-b")),
            )
            results = tuple(future.result() for future in futures)
        self.assertEqual(1, sum(isinstance(item, interface.Candidate) for item in results))
        self.assertIn((self.project / "app.txt").read_text(), {"implemented", "other"})

    def test_fault_03_user_write_after_occupancy_recheck_stops(self) -> None:
        module = self.module()
        store = module._backend._store
        original = store.occupy_mutation_domain

        def occupy(*args, **kwargs):
            decision = original(*args, **kwargs)
            if decision.acquired:
                (self.project / "app.txt").write_text("post-occupancy-user")
            return decision

        store.occupy_mutation_domain = occupy
        result = self.implement(module)
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual("post-occupancy-user", (self.project / "app.txt").read_text())

    def test_fault_04_expected_state_competing_write_preserved(self) -> None:
        project = self.root / "cas-project"
        workspace = self.root / "cas-workspace"
        project.mkdir()
        workspace.mkdir()
        target = project / "app.txt"
        source = workspace / "app.txt"
        target.write_text("expected")
        source.write_text("intended")
        expected = production._physical_entry(target)
        intended = production._physical_entry(source)
        target.write_text("latest-user")
        with self.assertRaises(implementation.AdoptionConflict):
            production.LinuxSourceAdoptionAdapter().apply(
                project,
                workspace,
                ({"path": "app.txt", "expected": expected, "intended": intended},),
                lambda: True,
            )
        self.assertEqual("latest-user", target.read_text())

    def test_fault_05_worker_may_have_run_response_loss_no_redispatch(self) -> None:
        calls = self.project / "worker-calls.txt"
        code = (
            "import fcntl,json,pathlib;"
            "p=pathlib.Path('/workspace/worker-calls.txt');p.touch();f=p.open('r+');fcntl.flock(f.fileno(),fcntl.LOCK_EX);"
            "v=int(f.read() or '0')+1;f.seek(0);f.truncate();f.write(str(v));f.flush();"
            "r=json.loads(pathlib.Path('/input/request.json').read_text());a=r['assignment'];"
            "(pathlib.Path('/workspace')/a['path']).write_text(a['value']);raise SystemExit(17)"
        )
        worker = production.ProcessWorker("worker-loss", ("/usr/bin/python3", "-c", code))
        module = self.module()
        with self.assertRaises(RuntimeError):
            module.implement(self.ticket, worker)
        recovered = module.implement(self.ticket, worker)
        self.assertIsInstance(recovered, (interface.Candidate, interface.ImplementationStopped))
        self.assertEqual("1", calls.read_text())

    def test_fault_06_source_adoption_fails_closed_before_mutation(self) -> None:
        class InterruptingAdoption(production.LinuxSourceAdoptionAdapter):
            calls = 0

            def apply(self, *args, **kwargs):
                self.calls += 1
                raise InterruptedError("may have started")

        adapter = InterruptingAdoption()
        module = entrypoint._compose_module(
            self.state,
            self.review(),
            production.LinuxWorkerAdapter(),
            adapter,
            production.LinuxFreshVerifierAdapter(
                production.ProcessVerifier(("/usr/bin/python3", "-c", "print('[]')"))
            ),
            production.LinuxEvidenceRunnerAdapter(),
        )
        result = self.implement(module)
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(0, adapter.calls)
        self.assertEqual("baseline", (self.project / "app.txt").read_text())

    def test_fault_07_atomic_publication_boundaries(self) -> None:
        module = self.module()
        store = module._backend._store
        original = store.publish
        fail = True

        def publish(*args, **kwargs):
            nonlocal fail
            if fail:
                fail = False
                with store._transaction() as connection:
                    connection.execute(
                        "CREATE TRIGGER fail_phase7_head BEFORE UPDATE OF head_result_ref ON work_streams "
                        "WHEN NEW.head_result_ref IS NOT NULL BEGIN SELECT RAISE(ABORT, 'phase7 precommit'); END"
                    )
            return original(*args, **kwargs)

        store.publish = publish
        with self.assertRaises(sqlite3.IntegrityError):
            self.implement(module)
        self.assertIsInstance(module.inspect(self.ticket).result, interface.NoConclusiveResult)

    def test_fault_08_effect_marker_dispatch_boundaries(self) -> None:
        adapter = TestConformanceEffectAdapter()
        adapter.response_loss = True
        adapter.readback = False
        module, candidate = self._effect_module(adapter, self.effect_observation())
        first = module.verify(candidate)
        second = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, second.status)
        self.assertEqual(1, adapter.calls.count("ACTION"))

    def test_fault_09_live_owner_not_reclassified_by_competing_publication(self) -> None:
        module = self.module()
        started = threading.Event()
        release = threading.Event()
        original = module._backend._execution._verification._runner.run

        def blocking(*args, **kwargs):
            started.set()
            release.wait(timeout=5)
            return original(*args, **kwargs)

        candidate = self.implement(module)
        module._backend._execution._verification._runner.run = blocking
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(module.verify, candidate)
            self.assertTrue(started.wait(timeout=5))
            second = executor.submit(module.verify, candidate)
            time.sleep(.05)
            self.assertFalse(second.done())
            release.set()
            results = (first.result(), second.result())
        self.assertEqual(1, len({item.result_identity for item in results}))


def load_tests(loader, tests, pattern):
    names = [
        f"{__name__}.Phase7FaultBoundaryTests.test_fault_{index:02d}_{suffix}"
        for index, suffix in (
            (1, "concurrent_work_has_one_external_owner"),
            (2, "overlapping_mutation_domain_has_one_winner"),
            (3, "user_write_after_occupancy_recheck_stops"),
            (4, "expected_state_competing_write_preserved"),
            (5, "worker_may_have_run_response_loss_no_redispatch"),
            (6, "source_adoption_fails_closed_before_mutation"),
            (7, "atomic_publication_boundaries"),
            (8, "effect_marker_dispatch_boundaries"),
            (9, "live_owner_not_reclassified_by_competing_publication"),
        )
    ]
    return loader.loadTestsFromNames(names)
