from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
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
load("durable_work", ROOT / "durable_work.py")
load("durable_backend", ROOT / "durable_backend.py")
effect_module = load("effect_observation", ROOT / "effect_observation.py")
implementation = load("implementation_execution", ROOT / "implementation_execution.py")
load("verification_execution", ROOT / "verification_execution.py")
production = load("production_adapters", ROOT / "production_adapters.py")
entrypoint = load("production_entrypoint", ROOT / "production_entrypoint.py")


WORKER_SCRIPT = (
    "import json,pathlib,time;"
    "r=json.loads(pathlib.Path('/input/request.json').read_text());"
    "a=r['assignment'];time.sleep(float(a.get('delay',0)));"
    "p=pathlib.Path('/workspace')/a['path'];p.parent.mkdir(parents=True,exist_ok=True);"
    "p.write_text(a['value'])"
)


def verifier_script(expected: str, kind: str = "SOURCE", *, assess: str = "normal") -> str:
    return (
        "import json,pathlib;"
        "r=json.loads(pathlib.Path('/input/request.json').read_text());"
        f"expected={expected!r};kind={kind!r};mode={assess!r};"
        "\nif r['operation']=='plan':\n"
        " n=len(r['candidate']['acceptanceCriteria']);"
        " request={'path':'app.txt'} if kind in ('SOURCE','READ') else {'argv':['/usr/bin/false']};"
        " print(json.dumps([{'observationIdentity':'full-flow','kind':kind,'criterionIndexes':list(range(1,n+1)),'requests':[request],'expected':expected}]))\n"
        "else:\n"
        " evidence=r['evidence'];complete=[e for e in evidence if e.get('complete')];"
        " n=len(r['candidate']['acceptanceCriteria']);"
        " outcome=('UNDETERMINED' if mode=='missing' or not complete else ('SATISFIED' if all(e.get('observed')==expected for e in complete) else 'NOT_SATISFIED'));"
        " refs=[e['observationIdentity'] for e in evidence];"
        " print(json.dumps([{'criterionIndex':i,'outcome':outcome,'evidenceObservationIdentities':refs} for i in range(1,n+1)]))"
    )


class TestConformanceEffectAdapter:
    identity = "phase7-test-conformance-effect"
    fixed_requests_enforced = True
    authoritative_readback_enforced = True
    redaction_enforced = True

    def __init__(self) -> None:
        self.authorized = True
        self.readback = True
        self.cleanup = True
        self.response_loss = False
        self.calls: list[str] = []
        self.target = False
        self.after_stage = None

    def canonicalize(self, effect):
        return {
            "targetIdentity": "sandbox:target",
            "consequenceIdentity": "sandbox:create",
            "occurrenceIdentity": str(effect["occurrence"]),
        }

    def authority(self, binding, effect, canonical):
        if not self.authorized:
            return None
        return {
            "adapterIdentity": self.identity,
            "binding": binding,
            "intent": effect["intent"],
            "target": effect["target"],
            "occurrence": effect["occurrence"],
            "actionRequest": effect["actionRequest"],
            "cleanupRequest": effect["cleanupRequest"],
            "finalDisposition": effect["finalDisposition"],
            "safetyProperty": effect["safetyProperty"],
            "canonicalEffect": canonical,
            "outsideWritableScope": True,
            "current": True,
            "credentialOpaque": True,
            "redactionEnforced": True,
            "allowNewOccurrence": False,
        }

    def dispatch(self, binding, effect, stage, request):
        self.calls.append(stage)
        if stage == "ACTION":
            self.target = True
            if self.response_loss:
                self.response_loss = False
                raise InterruptedError("sandbox response loss")
        if stage == "CLEANUP":
            self.target = False
        if self.after_stage is not None:
            self.after_stage(stage)
        if stage == "READBACK":
            return {
                "status": "FINISHED",
                "authoritative": self.readback,
                "matchesExpected": self.target and self.readback,
                "finalDispositionConfirmed": self.target and self.readback,
                "redacted": True,
            }
        if stage == "CLEANUP_READBACK":
            return {
                "status": "FINISHED",
                "authoritative": self.cleanup,
                "finalDispositionConfirmed": not self.target and self.cleanup,
                "redacted": True,
            }
        return {"status": "FINISHED", "authoritative": False, "redacted": True}


class TestSourceAdoptionAdapter:
    """Test-only source adapter used for deterministic public-flow coverage."""

    conditional_mutation = True

    def apply(self, project_root, workspace_root, changes, planning_is_current) -> None:
        if not planning_is_current():
            raise implementation.AdoptionConflict("planning changed at source adoption")
        for change in changes:
            relative = Path(str(change["path"]))
            target = project_root / relative
            observed = (
                implementation._entry(target)
                if target.exists() or target.is_symlink()
                else None
            )
            if observed != change["expected"]:
                raise implementation.AdoptionConflict(
                    f"conditional adoption conflict at {relative.as_posix()}"
                )
            source = workspace_root / relative
            intended = change["intended"]
            if intended is None:
                target.unlink()
            elif intended["kind"] == "file":
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.test-adopt")
                shutil.copy2(source, temporary, follow_symlinks=False)
                os.replace(temporary, target)
            elif intended["kind"] == "symlink":
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.test-adopt")
                temporary.symlink_to(os.readlink(source))
                os.replace(temporary, target)
            else:
                target.mkdir(parents=True, exist_ok=True)
                target.chmod(intended["mode"])


class Phase7PublicContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "product"
        self.project.mkdir()
        (self.project / "app.txt").write_text("baseline", encoding="utf-8")
        (self.project / "notes.txt").write_text("dirty-user", encoding="utf-8")
        self.spec = self.root / "SPEC.md"
        self.spec.write_text(
            "# Spec\nStatus: approved\nOwner: owner\n\n"
            + "".join(
                f"## {name}\nvalue\n\n"
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
            ),
            encoding="utf-8",
        )
        self.ticket = self.root / "TICKET.md"
        self.ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {self.spec}\nProject-Root: {self.project}\n"
            "Worker: \nUI: no\n\n## Goal\nImplement.\n\n"
            "## Acceptance Criteria\n- app is implemented\n- user changes survive\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead app.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        self.state = self.root / "module-state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def worker(identity: str = "worker-a"):
        return production.ProcessWorker(identity, ("/usr/bin/python3", "-c", WORKER_SCRIPT))

    def review(self, desired: str = "implemented", *, delay: float = 0, blocker: str | None = None):
        def check(work, source):
            if blocker is not None:
                return implementation.ImplementationBlocker(blocker)
            path = source / "app.txt"
            if not path.is_file() or path.read_text(encoding="utf-8") != desired:
                return {"path": "app.txt", "value": desired, "delay": delay}
            return None

        return check

    def module(
        self,
        *,
        desired: str = "implemented",
        expected: str = "implemented",
        kind: str = "SOURCE",
        assess: str = "normal",
        blocker: str | None = None,
    ):
        return entrypoint._compose_module(
            self.state,
            self.review(desired, blocker=blocker),
            production.LinuxWorkerAdapter(),
            TestSourceAdoptionAdapter(),
            production.LinuxFreshVerifierAdapter(
                production.ProcessVerifier(("/usr/bin/python3", "-c", verifier_script(expected, kind, assess=assess)))
            ),
            production.LinuxEvidenceRunnerAdapter(),
        )

    def composed(self, review, verifier_argv):
        return entrypoint._compose_module(
            self.state,
            review,
            production.LinuxWorkerAdapter(),
            TestSourceAdoptionAdapter(),
            production.LinuxFreshVerifierAdapter(production.ProcessVerifier(verifier_argv)),
            production.LinuxEvidenceRunnerAdapter(),
        )

    def implement(self, module=None):
        selected = module or self.module()
        return selected.implement(self.ticket, self.worker())

    def test_flow_01_dirty_source_success(self) -> None:
        result = self.implement()
        self.assertEqual("implemented", (self.project / "app.txt").read_text())
        self.assertEqual("dirty-user", (self.project / "notes.txt").read_text())
        self.assertEqual(("app.txt",), result.implementation_changes)
        self.assertIn("notes.txt", result.preserved_changes)

    def test_flow_02_same_path_overlap_stop(self) -> None:
        module = self.composed(
            self.review(delay=0.2),
            ("/usr/bin/python3", "-c", verifier_script("implemented")),
        )
        thread = threading.Thread(
            target=lambda: (time.sleep(0.05), (self.project / "app.txt").write_text("live-user"))
        )
        thread.start()
        result = module.implement(self.ticket, self.worker())
        thread.join()
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual("live-user", (self.project / "app.txt").read_text())

    def test_flow_03_same_final_value_non_attribution(self) -> None:
        module = self.composed(
            self.review(delay=0.2),
            ("/usr/bin/python3", "-c", verifier_script("implemented")),
        )
        thread = threading.Thread(
            target=lambda: (time.sleep(0.05), (self.project / "app.txt").write_text("implemented"))
        )
        thread.start()
        result = module.implement(self.ticket, self.worker())
        thread.join()
        self.assertNotIn("app.txt", result.implementation_changes)
        self.assertIn("app.txt", result.preserved_changes)

    def test_flow_04_zero_mutation_candidate(self) -> None:
        (self.project / "app.txt").write_text("implemented")
        result = self.implement()
        self.assertEqual((), result.implementation_changes)
        self.assertTrue(result.independent_verification_pending)

    def test_flow_05_known_gap_or_check_failure(self) -> None:
        before = (self.project / "app.txt").read_bytes()
        result = self.implement(self.module(blocker="mandatory implementation gap"))
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(before, (self.project / "app.txt").read_bytes())

    def test_flow_06_fresh_full_ac_positive(self) -> None:
        module = self.module()
        candidate = self.implement(module)
        result = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(candidate.acceptance_criteria, tuple(item.criterion for item in result.criterion_results))

    def test_flow_07_disconnected_missing_observation(self) -> None:
        module = self.module(kind="LOCAL", assess="missing")
        result = module.verify(self.implement(module))
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)

    def test_flow_08_direct_contradiction(self) -> None:
        module = self.module(expected="different")
        result = module.verify(self.implement(module))
        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, result.status)

    def test_flow_09_tool_evidence_failure(self) -> None:
        module = self.module(kind="LOCAL")
        result = module.verify(self.implement(module))
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)

    def test_flow_10_source_non_mutation(self) -> None:
        module = self.module()
        candidate = self.implement(module)
        retained = Path(candidate.source["retainedRoot"])
        before = implementation._capture(retained)[1]
        module.verify(candidate)
        self.assertEqual(before, implementation._capture(retained)[1])

    def test_flow_11_fresh_namespace(self) -> None:
        # Physical canary visibility is exercised by the production conformance test;
        # this public flow proves the same production launcher reaches a fresh result.
        module = self.module()
        candidate = self.implement(module)
        first = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, first.status)

    def test_flow_12_candidate_commit_response_loss(self) -> None:
        module = self.module()
        store = module._backend._store
        original = store.publish
        lost = True

        def publish(*args, **kwargs):
            nonlocal lost
            result = original(*args, **kwargs)
            if isinstance(result, interface.Candidate) and lost:
                lost = False
                raise InterruptedError("candidate response lost")
            return result

        store.publish = publish
        with self.assertRaises(InterruptedError):
            self.implement(module)
        candidate = module.inspect(self.ticket).result
        result = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        second_ticket = self.root / "TICKET-OVERLAP.md"
        second_ticket.write_text(self.ticket.read_text().replace("# Ticket", "# Overlap"))
        (self.project / "app.txt").write_text("overlap-live")
        overlapping = module.implement(second_ticket, self.worker("worker-overlap"))
        self.assertIsInstance(overlapping, interface.Candidate)

    def test_flow_13_verification_result_commit_response_loss(self) -> None:
        module = self.module(assess="missing")
        candidate = self.implement(module)
        store = module._backend._store
        original = store.publish
        lost = True

        def publish(*args, **kwargs):
            nonlocal lost
            result = original(*args, **kwargs)
            if isinstance(result, interface.VerificationResult) and lost:
                lost = False
                raise InterruptedError("verification response lost")
            return result

        store.publish = publish
        with self.assertRaises(InterruptedError):
            module.verify(candidate)
        inspected = module.inspect(self.ticket)
        self.assertIsInstance(inspected.result, interface.VerificationResult)
        self.assertEqual(candidate, inspected.result.candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, inspected.result.status)
        fresh = self.module()
        retried = fresh.verify(inspected.result.candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, retried.status)
        self.assertNotEqual(inspected.result.result_identity, retried.result_identity)

    def test_flow_14_retained_candidate_plus_canonical_drift(self) -> None:
        module = self.module(expected="implemented")
        candidate = self.implement(module)
        (self.project / "app.txt").write_text("live-B")
        restarted = self.module(expected="implemented")
        result = restarted.verify(candidate)
        inspected = restarted.inspect(self.ticket)
        self.assertNotEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(interface.Currentness.NOT_CURRENT, inspected.currentness)
        evidence = result.criterion_results[0].evidence[0]
        self.assertEqual("implemented", evidence["observed"])

    def test_flow_15_no_complete_result(self) -> None:
        module = self.module()
        store = module._backend._store
        store.begin(self.ticket, "IMPLEMENT", {"worker": "partial"}, "partial")
        self.assertIsInstance(module.inspect(self.ticket).result, interface.NoConclusiveResult)

    def test_flow_16_no_actual_authority_no_dispatch(self) -> None:
        self.assertEqual((), entrypoint.ENABLED_PRODUCTION_EFFECT_ADAPTERS)
        module = self.module(kind="EFFECT")
        result = module.verify(self.implement(module))
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)

    def test_flow_17_authenticated_read_without_production_authority_is_undetermined(self) -> None:
        read_root = self.root / "authenticated-read"
        read_root.mkdir()
        (read_root / "app.txt").write_text("remote-value")
        projection = {
            "path": "app.txt",
            "sha256": __import__("hashlib").sha256(b"remote-value").hexdigest(),
            "byteCount": len(b"remote-value"),
        }
        module = self.module(kind="READ", expected=projection)
        result = module.verify(self.implement(module))
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual((), entrypoint.ENABLED_PRODUCTION_EFFECT_ADAPTERS)

    def effect_observation(self, *, cleanup: bool = False, action: bool = True):
        effect = {
            "adapterIdentity": "phase7-test-conformance-effect",
            "intent": "sandbox-create",
            "target": {"class": "temporary-test-sandbox", "name": "target"},
            "occurrence": "occurrence-1",
            "actionRequest": {"op": "create"} if action else None,
            "readbackRequests": [{"op": "read"}],
            "cleanupRequest": {"op": "remove"} if cleanup else None,
            "cleanupReadbackRequests": [{"op": "read-absent"}] if cleanup else [],
            "finalDisposition": "REMOVE" if cleanup else "RETAIN",
            "safetyProperty": "NO_REPLAY",
        }
        return {
            "observationIdentity": "effect",
            "kind": "EFFECT",
            "criterionIndexes": [1, 2],
            "requests": effect_module.effect_requests(effect),
            "expected": "created",
            "effect": effect,
        }

    def test_flow_18_timeout_plus_authoritative_readback(self) -> None:
        adapter = TestConformanceEffectAdapter()
        adapter.response_loss = True
        result = self._effect_public(adapter, self.effect_observation())
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, adapter.calls.count("ACTION"))

    def test_flow_19_ambiguous_non_reexecution(self) -> None:
        adapter = TestConformanceEffectAdapter()
        adapter.response_loss = True
        adapter.readback = False
        module, candidate = self._effect_module(adapter, self.effect_observation())
        first = module.verify(candidate)
        second = module.verify(candidate)
        (self.project / "app.txt").write_text("drift-for-new-candidate")
        new_candidate = module.implement(self.ticket, self.worker("worker-new-candidate"))
        third = module.verify(new_candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, second.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, third.status)
        self.assertEqual(1, adapter.calls.count("ACTION"))

    def test_flow_20_completed_implementation_occurrence(self) -> None:
        adapter = TestConformanceEffectAdapter()
        (self.project / "app.txt").write_text("implemented")
        implementation_observation = self.effect_observation()
        verification_observation = self.effect_observation(action=False)
        observer = effect_module.EffectObservationModule(adapter)

        class Context:
            identity = "fresh-readback-context"

            def plan(self, candidate, retained_source, supported):
                return [verification_observation]

            def assess(self, candidate, plan, evidence):
                complete = bool(evidence) and evidence[0]["complete"]
                return [
                    {
                        "criterionIndex": index,
                        "outcome": "SATISFIED" if complete else "UNDETERMINED",
                        "evidenceObservationIdentities": ["effect"] if evidence else [],
                    }
                    for index in range(1, len(candidate.acceptance_criteria) + 1)
                ]

        class Verifier:
            fresh_context_enforced = True
            read_only_enforced = True

            def open(self, candidate, retained_source, supported, safety):
                return Context()

        implementation_effect = {
            key: value
            for key, value in implementation_observation.items()
            if key not in {"kind", "criterionIndexes"}
        }
        module = entrypoint._compose_module(
            self.state,
            self.review(),
            production.LinuxWorkerAdapter(),
            TestSourceAdoptionAdapter(),
            Verifier(),
            production.LinuxEvidenceRunnerAdapter(),
            observer,
            implementation_effects=lambda work, source: [implementation_effect],
        )
        candidate = self.implement(module)
        action_count = adapter.calls.count("ACTION")
        result = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, action_count)
        self.assertEqual(action_count, adapter.calls.count("ACTION"))

    def test_flow_21_cleanup_final_disposition(self) -> None:
        adapter = TestConformanceEffectAdapter()
        result = self._effect_public(adapter, self.effect_observation(cleanup=True))
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertFalse(adapter.target)
        self.assertEqual(1, adapter.calls.count("CLEANUP"))
        incomplete_adapter = TestConformanceEffectAdapter()
        incomplete_adapter.cleanup = False
        self.state = self.root / "module-state-incomplete-cleanup"
        module, candidate = self._effect_module(
            incomplete_adapter,
            self.effect_observation(cleanup=True),
        )
        incomplete = module.verify(candidate)
        repeated = module.verify(candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, incomplete.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, repeated.status)
        self.assertEqual(1, incomplete_adapter.calls.count("CLEANUP"))

    def test_flow_22_contradiction_drift_containment(self) -> None:
        adapter = TestConformanceEffectAdapter()
        drifted = False

        def drift(stage):
            nonlocal drifted
            if stage == "ACTION" and not drifted:
                (self.project / "drift.txt").write_text("external drift")
                drifted = True

        adapter.after_stage = drift
        result = self._effect_public(adapter, self.effect_observation(cleanup=True))
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual(1, adapter.calls.count("ACTION"))
        self.assertEqual(1, adapter.calls.count("CLEANUP"))
        self.assertFalse(adapter.target)

    def test_flow_23_failed_result_to_new_candidate(self) -> None:
        first_module = self.module(expected="different")
        first_candidate = self.implement(first_module)
        failed = first_module.verify(first_candidate)
        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, failed.status)
        second_module = self.module(desired="fixed", expected="fixed")
        second_candidate = second_module.implement(self.ticket, self.worker("worker-b"))
        self.assertNotEqual(first_candidate.result_identity, second_candidate.result_identity)
        self.assertEqual(interface.VerificationStatus.VERIFIED, second_module.verify(second_candidate).status)

    def test_flow_24_authority_delta_stop(self) -> None:
        module = self.module(blocker="new planning decision required")
        before = (self.project / "app.txt").read_bytes()
        result = self.implement(module)
        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(before, (self.project / "app.txt").read_bytes())

    def _effect_module(self, adapter, observation):
        # This uses the real composition function but the adapter is explicitly
        # conformance-only and is never in ENABLED_PRODUCTION_EFFECT_ADAPTERS.
        (self.project / "app.txt").write_text("implemented")
        observer = effect_module.EffectObservationModule(adapter)

        class Context:
            identity = "fresh-conformance-context"

            def plan(self, candidate, retained_source, supported):
                return [observation]

            def assess(self, candidate, plan, evidence):
                complete = bool(evidence) and all(item["complete"] for item in evidence)
                return [
                    {
                        "criterionIndex": index,
                        "outcome": "SATISFIED" if complete else "UNDETERMINED",
                        "evidenceObservationIdentities": ["effect"] if evidence else [],
                    }
                    for index in range(1, len(candidate.acceptance_criteria) + 1)
                ]

        class Verifier:
            fresh_context_enforced = True
            read_only_enforced = True

            def open(self, candidate, retained_source, supported, safety):
                return Context()

        module = entrypoint._compose_module(
            self.state,
            self.review(),
            production.LinuxWorkerAdapter(),
            TestSourceAdoptionAdapter(),
            Verifier(),
            production.LinuxEvidenceRunnerAdapter(),
            observer,
        )
        return module, self.implement(module)

    def _effect_public(self, adapter, observation):
        module, candidate = self._effect_module(adapter, observation)
        return module.verify(candidate)


if __name__ == "__main__":
    unittest.main()
