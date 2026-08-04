from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import stat
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
execution_module = load("implementation_execution", ROOT / "implementation_execution.py")


def physical_entry(path: Path):
    if not path.exists() and not path.is_symlink():
        return None
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISDIR(info.st_mode):
        return {"kind": "directory", "mode": mode}
    if stat.S_ISREG(info.st_mode):
        return {
            "kind": "file",
            "mode": mode,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    if stat.S_ISLNK(info.st_mode):
        return {"kind": "symlink", "target": os.readlink(path)}
    raise AssertionError(path)


class TemporarySourceAdoption:
    conditional_mutation = True

    def __init__(self, before_linearization=None) -> None:
        self.before_linearization = before_linearization
        self.calls = 0

    def apply(self, project_root, workspace_root, changes) -> None:
        self.calls += 1
        for change in changes:
            relative = str(change["path"])
            target = project_root / relative
            source = workspace_root / relative
            if self.before_linearization is not None:
                self.before_linearization(target)
            if physical_entry(target) != change["expected"]:
                raise execution_module.AdoptionConflict(f"conditional adoption conflict at {relative}")
            intended = change["intended"]
            if intended is None:
                target.rmdir() if target.is_dir() else target.unlink()
            elif intended["kind"] == "directory":
                target.mkdir(parents=True, exist_ok=True)
                target.chmod(intended["mode"])
            elif intended["kind"] == "symlink":
                temporary = target.with_name(f".{target.name}.adoption")
                temporary.symlink_to(os.readlink(source))
                os.replace(temporary, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.adoption")
                shutil.copy2(source, temporary, follow_symlinks=False)
                os.replace(temporary, target)


class Worker:
    durable_identity = "worker-a"

    def __init__(self) -> None:
        self.calls = 0
        self.workspace = None


class TemporaryWorkerAdapter:
    isolation_enforced = True

    def __init__(self, external=None, interrupt=False, started=None, release=None) -> None:
        self.external = external
        self.interrupt = interrupt
        self.started = started
        self.release = release
        self.calls = 0

    def run(self, worker, work, workspace, assignment) -> None:
        self.calls += 1
        worker.calls += 1
        worker.workspace = workspace
        target = workspace / assignment["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(assignment["value"], encoding="utf-8")
        if self.external is not None:
            self.external()
        if self.started is not None:
            self.started.set()
        if self.release is not None:
            self.release.wait(timeout=5)
        if self.interrupt:
            self.interrupt = False
            raise InterruptedError("simulated Worker response loss")


class ImplementationExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "product"
        self.project.mkdir()
        (self.project / "app.txt").write_text("baseline", encoding="utf-8")
        (self.project / "notes.txt").write_text("preexisting user bytes", encoding="utf-8")
        self.spec = root / "SPEC.md"
        sections = "\n".join(
            f"## {name}\nvalue\n"
            for name in (
                "Problem",
                "Desired Outcome",
                "Requirements",
                "Non-Goals",
                "Implementation Constraints",
                "Verification Expectations",
                "UI / UX",
                "Open Questions",
            )
        )
        self.spec.write_text(
            f"# Spec\nStatus: approved\nOwner: owner\n\n{sections}",
            encoding="utf-8",
        )
        self.ticket = root / "TICKET.md"
        self.ticket.write_text(
            "# Ticket\n"
            "Status: ready\n"
            f"Parent-Spec: {self.spec}\n"
            f"Project-Root: {self.project}\n"
            "Worker: \n"
            "UI: no\n\n"
            "## Goal\nImplement app.\n\n"
            "## Acceptance Criteria\n- app is implemented\n\n"
            "## Scope\napp.txt\n\n"
            "## Non-Goals\nNone.\n\n"
            "## Blockers\nNone.\n\n"
            "## Verification\nRead app.txt.\n\n"
            "## References\nNone.\n",
            encoding="utf-8",
        )
        self.database = root / "state" / "durable.sqlite3"
        self.execution_root = root / "execution-state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def module(self, adoption, desired="implemented", worker_adapter=None, required=None):
        store = durable.DurableWorkStore(self.database)
        expected = {"app.txt": desired, **(required or {})}

        def review(work, source):
            for relative, value in expected.items():
                target = source / relative
                if not target.is_file() or target.read_text(encoding="utf-8") != value:
                    return {"path": relative, "value": value}
            return None

        execution = execution_module.ImplementationExecution(
            self.execution_root,
            store,
            worker_adapter or TemporaryWorkerAdapter(),
            adoption,
            review,
        )
        return interface.ImplementationVerificationModule(
            backend_module.DurableBackend(store, execution)
        )

    def test_private_worker_change_is_adopted_and_dirty_baseline_is_preserved(self) -> None:
        worker = Worker()
        result = self.module(TemporarySourceAdoption()).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertNotEqual(self.project, worker.workspace)
        self.assertEqual("implemented", (self.project / "app.txt").read_text(encoding="utf-8"))
        self.assertEqual("preexisting user bytes", (self.project / "notes.txt").read_text(encoding="utf-8"))
        self.assertEqual(("app.txt",), result.implementation_changes)
        self.assertIn("notes.txt", result.preserved_changes)
        retained = Path(result.source["retainedRoot"])
        self.assertEqual("implemented", (retained / "app.txt").read_text(encoding="utf-8"))

    def test_disjoint_live_change_is_preserved_beside_worker_change(self) -> None:
        worker = Worker()
        adapter = TemporaryWorkerAdapter(
            external=lambda: (self.project / "notes.txt").write_text("concurrent user", encoding="utf-8")
        )
        result = self.module(TemporarySourceAdoption(), worker_adapter=adapter).implement(self.ticket, worker)

        self.assertEqual("implemented", (self.project / "app.txt").read_text(encoding="utf-8"))
        self.assertEqual("concurrent user", (self.project / "notes.txt").read_text(encoding="utf-8"))
        self.assertEqual(("app.txt",), result.implementation_changes)
        self.assertIn("notes.txt", result.preserved_changes)

    def test_different_same_path_live_change_stops_without_overwrite(self) -> None:
        worker = Worker()
        adapter = TemporaryWorkerAdapter(
            external=lambda: (self.project / "app.txt").write_text("concurrent user", encoding="utf-8")
        )
        result = self.module(TemporarySourceAdoption(), worker_adapter=adapter).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual("concurrent user", (self.project / "app.txt").read_text(encoding="utf-8"))

    def test_same_final_live_change_is_preserved_without_worker_credit(self) -> None:
        worker = Worker()
        worker_adapter = TemporaryWorkerAdapter(
            external=lambda: (self.project / "app.txt").write_text("implemented", encoding="utf-8")
        )
        adoption = TemporarySourceAdoption()
        result = self.module(adoption, worker_adapter=worker_adapter).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual(0, adoption.calls)
        self.assertNotIn("app.txt", result.implementation_changes)
        self.assertIn("app.txt", result.preserved_changes)

    def test_worker_response_loss_reenters_workspace_without_duplicate_dispatch(self) -> None:
        worker = Worker()
        module = self.module(
            TemporarySourceAdoption(),
            worker_adapter=TemporaryWorkerAdapter(interrupt=True),
        )
        with self.assertRaises(InterruptedError):
            module.implement(self.ticket, worker)

        result = module.implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual(1, worker.calls)
        self.assertEqual("implemented", (self.project / "app.txt").read_text(encoding="utf-8"))

    def test_sequential_assignments_close_multiple_implementation_gaps(self) -> None:
        worker = Worker()
        result = self.module(
            TemporarySourceAdoption(),
            required={"config.txt": "configured"},
        ).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual(2, worker.calls)
        self.assertEqual("implemented", (self.project / "app.txt").read_text(encoding="utf-8"))
        self.assertEqual("configured", (self.project / "config.txt").read_text(encoding="utf-8"))
        self.assertEqual(("app.txt", "config.txt"), result.implementation_changes)

    def test_planning_change_before_second_assignment_stops_second_worker(self) -> None:
        changed = False

        def change_ticket() -> None:
            nonlocal changed
            if not changed:
                self.ticket.write_text(
                    self.ticket.read_text(encoding="utf-8") + "\n",
                    encoding="utf-8",
                )
                changed = True

        worker = Worker()
        result = self.module(
            TemporarySourceAdoption(),
            worker_adapter=TemporaryWorkerAdapter(external=change_ticket),
            required={"config.txt": "configured"},
        ).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(1, worker.calls)
        self.assertEqual("baseline", (self.project / "app.txt").read_text(encoding="utf-8"))
        self.assertFalse((self.project / "config.txt").exists())

    def test_module_owned_adapter_does_not_call_worker_code_against_canonical_source(self) -> None:
        class WorkerWithCanonicalWrite(Worker):
            def __init__(self) -> None:
                super().__init__()
                self.direct_run_called = False

            def run(self, work, workspace) -> None:
                self.direct_run_called = True
                (self.project / "notes.txt").write_text("overwritten", encoding="utf-8")

        worker = WorkerWithCanonicalWrite()
        worker.project = self.project
        result = self.module(TemporarySourceAdoption()).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertFalse(worker.direct_run_called)
        self.assertEqual("preexisting user bytes", (self.project / "notes.txt").read_text(encoding="utf-8"))

    def test_response_loss_without_workspace_change_stops_without_redispatch(self) -> None:
        class InterruptedBeforeMutation(TemporaryWorkerAdapter):
            def run(self, worker, work, workspace, assignment) -> None:
                self.calls += 1
                worker.calls += 1
                raise InterruptedError("simulated response loss before workspace mutation")

        worker = Worker()
        module = self.module(
            TemporarySourceAdoption(),
            worker_adapter=InterruptedBeforeMutation(),
        )
        with self.assertRaises(InterruptedError):
            module.implement(self.ticket, worker)

        result = module.implement(self.ticket, worker)

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(1, worker.calls)
        self.assertEqual("baseline", (self.project / "app.txt").read_text(encoding="utf-8"))

    def test_concurrent_same_request_keeps_one_private_worker_call(self) -> None:
        started = threading.Event()
        release = threading.Event()

        worker = Worker()
        module = self.module(
            TemporarySourceAdoption(),
            worker_adapter=TemporaryWorkerAdapter(started=started, release=release),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(module.implement, self.ticket, worker)
            self.assertTrue(started.wait(timeout=5))
            second = executor.submit(module.implement, self.ticket, worker)
            release.set()
            results = (first.result(timeout=5), second.result(timeout=5))

        self.assertEqual(1, worker.calls)
        self.assertEqual(1, len({result.result_identity for result in results}))

    def test_conditional_adoption_conflict_preserves_latest_live_bytes(self) -> None:
        adoption = TemporarySourceAdoption(
            lambda target: target.write_text("latest user", encoding="utf-8")
        )
        result = self.module(adoption).implement(self.ticket, Worker())

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual("latest user", (self.project / "app.txt").read_text(encoding="utf-8"))

    def test_adoption_interruption_reentry_performs_no_additional_write(self) -> None:
        calls = 0

        def interrupt(target):
            nonlocal calls
            calls += 1
            raise InterruptedError("simulated adoption interruption")

        module = self.module(TemporarySourceAdoption(interrupt))
        worker = Worker()
        with self.assertRaises(InterruptedError):
            module.implement(self.ticket, worker)

        result = module.implement(self.ticket, worker)

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(1, calls)
        self.assertEqual("baseline", (self.project / "app.txt").read_text(encoding="utf-8"))

    def test_retained_candidate_survives_live_drift_and_inspect_reports_it(self) -> None:
        module = self.module(TemporarySourceAdoption())
        candidate = module.implement(self.ticket, Worker())
        retained = Path(candidate.source["retainedRoot"])
        (self.project / "notes.txt").write_text("later user", encoding="utf-8")

        inspection = module.inspect(self.ticket)

        self.assertEqual(candidate, inspection.result)
        self.assertEqual(interface.Currentness.NOT_CURRENT, inspection.currentness)
        self.assertEqual("preexisting user bytes", (retained / "notes.txt").read_text(encoding="utf-8"))

    def test_retained_candidate_tamper_makes_inspect_nonconclusive(self) -> None:
        module = self.module(TemporarySourceAdoption())
        candidate = module.implement(self.ticket, Worker())
        retained = Path(candidate.source["retainedRoot"])
        (retained / "app.txt").write_text("tampered", encoding="utf-8")

        inspection = module.inspect(self.ticket)

        self.assertIsInstance(inspection.result, interface.NoConclusiveResult)
        self.assertEqual(interface.Currentness.UNKNOWN, inspection.currentness)

    def test_already_complete_source_publishes_zero_mutation_candidate(self) -> None:
        (self.project / "app.txt").write_text("implemented", encoding="utf-8")
        worker = Worker()
        result = self.module(TemporarySourceAdoption()).implement(self.ticket, worker)

        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual(0, worker.calls)
        self.assertEqual((), result.implementation_changes)


if __name__ == "__main__":
    unittest.main()
