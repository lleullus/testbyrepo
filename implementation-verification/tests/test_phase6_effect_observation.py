from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
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
durable = load("durable_work", ROOT / "durable_work.py")
backend_module = load("durable_backend", ROOT / "durable_backend.py")
effect_module = load("effect_observation", ROOT / "effect_observation.py")
implementation_module = load("implementation_execution", ROOT / "implementation_execution.py")
verification_module = load("verification_execution", ROOT / "verification_execution.py")


def effect_observation(
    occurrence: str = "occurrence-1",
    *,
    cleanup: bool = False,
    action: bool = True,
):
    action_request = {"operation": "create", "occurrence": occurrence} if action else None
    readback = {"operation": "read", "occurrence": occurrence}
    cleanup_request = {"operation": "remove", "occurrence": occurrence} if cleanup else None
    cleanup_readback = {"operation": "read-absent", "occurrence": occurrence}
    effect = {
        "adapterIdentity": "fixed-test-effect",
        "intent": "create-test-target",
        "target": {"environment": "test", "resource": "target-1"},
        "occurrence": occurrence,
        "actionRequest": action_request,
        "readbackRequests": [readback],
        "cleanupRequest": cleanup_request,
        "cleanupReadbackRequests": [cleanup_readback] if cleanup else [],
        "finalDisposition": "RESTORE" if cleanup else "RETAIN",
        "safetyProperty": "NO_REPLAY",
    }
    return {
        "observationIdentity": "effect-check",
        "kind": "EFFECT",
        "criterionIndexes": [1],
        "requests": effect_module.effect_requests(effect),
        "expected": "created",
        "effect": effect,
    }


class FixedEffectAdapter:
    identity = "fixed-test-effect"
    fixed_requests_enforced = True
    authoritative_readback_enforced = True
    redaction_enforced = True

    def __init__(self) -> None:
        self.authorized = True
        self.allow_new_occurrence = False
        self.readback_complete = True
        self.cleanup_complete = True
        self.response_loss = False
        self.redaction_safe = True
        self.after_dispatch = None
        self.calls = []
        self.markers = []

    def canonicalize(self, effect):
        return {
            "targetIdentity": f"test-target:{effect['target']['resource']}",
            "consequenceIdentity": (
                f"{effect['intent']}:{effect['target']['resource']}:"
                f"{effect['finalDisposition']}"
            ),
            "occurrenceIdentity": str(effect["occurrence"]),
        }

    def authority(self, binding, effect, canonical_effect):
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
            "canonicalEffect": canonical_effect,
            "outsideWritableScope": True,
            "current": True,
            "credentialOpaque": True,
            "redactionEnforced": True,
            "allowNewOccurrence": self.allow_new_occurrence,
        }

    def dispatch(self, binding, effect, stage, request):
        if stage in {"ACTION", "CLEANUP"} and self.markers:
            assert self.markers[-1]["stage"] == stage
        self.calls.append((stage, request))
        if self.after_dispatch is not None:
            self.after_dispatch(stage)
        if stage == "ACTION" and self.response_loss:
            self.response_loss = False
            raise InterruptedError("simulated response loss")
        if stage == "READBACK":
            return {
                "status": "FINISHED",
                "authoritative": True,
                "matchesExpected": self.readback_complete,
                "finalDispositionConfirmed": self.readback_complete,
                "redacted": self.redaction_safe,
            }
        if stage == "CLEANUP_READBACK":
            return {
                "status": "FINISHED" if self.cleanup_complete else "TIMEOUT",
                "authoritative": self.cleanup_complete,
                "finalDispositionConfirmed": self.cleanup_complete,
                "redacted": self.redaction_safe,
            }
        return {
            "status": "FINISHED",
            "authoritative": False,
            "redacted": self.redaction_safe,
        }


class Context:
    identity = "fresh-verifier"

    def __init__(self, observations):
        self.observations = observations

    def plan(self, candidate, retained_source, supported_observations):
        return self.observations

    def assess(self, candidate, plan, evidence):
        complete = all(item["complete"] for item in evidence) and len(evidence) == len(
            plan["observations"]
        )
        return [
            {
                "criterionIndex": 1,
                "outcome": "SATISFIED" if complete else "UNDETERMINED",
                "evidenceObservationIdentities": [
                    item["observationIdentity"] for item in evidence
                ],
            }
        ]


class FreshVerifier:
    fresh_context_enforced = True
    read_only_enforced = True

    def __init__(self, observations):
        self.observations = observations
        self.effect_safety = []

    def open(self, candidate, retained_source, supported_observations, effect_safety):
        self.effect_safety.append(effect_safety)
        return Context(self.observations)


class ReadOnlyRunner:
    read_only_enforced = True
    authenticated_read_enforced = True
    effect_observation_enforced = False
    supported_observations = ("SOURCE", "LOCAL", "READ", "EFFECT")

    def __init__(self):
        self.calls = []
        self.read_authorized = True
        self.redaction_safe = True

    def read_authority(self, candidate, observation):
        if not self.read_authorized:
            return None
        return {
            "binding": {
                "work": str(candidate.work),
                "candidateIdentity": candidate.result_identity,
                "planning": candidate.planning,
                "sourceIdentity": candidate.source["identity"],
                "observationIdentity": observation["observationIdentity"],
                "requests": observation["requests"],
            },
            "outsideWritableScope": True,
            "current": True,
            "credentialOpaque": True,
            "redactionEnforced": True,
        }

    def run(self, candidate, retained_source, scratch_root, observation):
        self.calls.append(observation["kind"])
        return {
            "status": "COMPLETE",
            "subattempts": [
                {"request": request, "status": "FINISHED"}
                for request in observation["requests"]
            ],
            "observed": observation["expected"],
            "artifact": {"redacted": self.redaction_safe, "secret": "must-not-survive"},
            "redacted": self.redaction_safe,
        }


class NoWorker:
    durable_identity = "worker-a"


class NoWorkerAdapter:
    isolation_enforced = True

    def run(self, worker, work, workspace_root, assignment):
        raise AssertionError("already-complete source must not dispatch a Worker")


class NoAdoption:
    conditional_mutation = True

    def apply(self, project_root, workspace_root, changes, planning_is_current):
        raise AssertionError("already-complete source must not be adopted")


class Phase6EffectObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "product"
        self.project.mkdir()
        (self.project / "app.txt").write_text("implemented", encoding="utf-8")
        self.retained = root / "retained"
        shutil.copytree(self.project, self.retained)
        _, identity = implementation_module._capture(self.retained)
        self.ticket = (root / "TICKET.md").resolve()
        self.ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        self.store = durable.DurableWorkStore(root / "state" / "durable.sqlite3")
        self.state_root = root / "execution-state"
        candidate = interface.Candidate(
            work=self.ticket,
            planning={"projectRoot": str(self.project.resolve()), "ticket": "planning-1"},
            acceptance_criteria=("AC-1",),
            source={"identity": identity, "retainedRoot": str(self.retained)},
            implementation_changes=("app.txt",),
            preserved_changes=(),
        )
        transition = self.store.begin(
            self.ticket, "IMPLEMENT", {"worker": "worker-a"}, "implementation-progress"
        )
        self.candidate = self.store.publish(transition.transition_identity, candidate)
        self.adapter = FixedEffectAdapter()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def public_verification(self, observations, adapter=None, runner=None, currentness=None):
        selected_adapter = adapter or self.adapter
        observer = effect_module.EffectObservationModule(selected_adapter)
        verifier = FreshVerifier(observations)
        verification = verification_module.VerificationExecution(
            self.state_root,
            self.store,
            verifier,
            runner or ReadOnlyRunner(),
            currentness or (lambda result: interface.Currentness.CURRENT),
            observer,
        )
        execution = verification_module.ModuleExecution(object(), verification)
        return (
            interface.ImplementationVerificationModule(
                backend_module.DurableBackend(self.store, execution)
            ),
            verifier,
        )

    def ready_implementation_ticket(self, name):
        root = Path(self.temporary.name)
        spec = root / f"{name}-SPEC.md"
        spec.write_text(
            "# Spec\nStatus: approved\nOwner: owner\n\n"
            + "".join(
                f"## {section}\nvalue\n\n"
                for section in (
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
        ticket = root / f"{name}-TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {self.project}\n"
            "Worker: \nUI: no\n\n"
            "## Goal\nDone.\n\n## Acceptance Criteria\n- app is implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        return ticket

    def test_missing_external_authority_dispatches_nothing(self) -> None:
        self.adapter.authorized = False
        module, _ = self.public_verification([effect_observation()])

        result = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], self.adapter.calls)

    def test_authorized_action_is_marked_then_closed_by_authoritative_readback(self) -> None:
        self.adapter.markers = []
        observer = effect_module.EffectObservationModule(self.adapter)
        observation = effect_observation()

        result = observer.observe(
            self.candidate,
            observation,
            (),
            self.adapter.markers.append,
        )

        self.assertEqual("COMPLETE", result.raw["status"])
        self.assertIsNotNone(result.projection)
        self.assertEqual(["ACTION", "READBACK"], [stage for stage, _ in self.adapter.calls])
        self.assertEqual(
            ["ACTION"],
            [item["stage"] for item in result.raw["artifact"]["durableDispatchMarkers"]],
        )

    def test_response_loss_is_not_reexecuted_and_readback_can_resolve_it(self) -> None:
        self.adapter.response_loss = True
        observer = effect_module.EffectObservationModule(self.adapter)
        observation = effect_observation()
        first = observer.observe(
            self.candidate, observation, (), self.adapter.markers.append
        )

        alias = effect_observation()
        alias["effect"]["target"] = {
            "environment": "alias-for-test",
            "resource": "target-1",
        }
        second = observer.observe(
            self.candidate,
            alias,
            (first.projection,),
            self.adapter.markers.append,
        )

        self.assertEqual("COMPLETE", first.raw["status"])
        self.assertEqual("COMPLETE", second.raw["status"])
        self.assertEqual(1, [stage for stage, _ in self.adapter.calls].count("ACTION"))

    def test_same_occurrence_in_one_verification_dispatches_action_once(self) -> None:
        first = effect_observation()
        first["observationIdentity"] = "effect-1"
        second = effect_observation()
        second["observationIdentity"] = "effect-2"
        module, _ = self.public_verification([first, second])

        result = module.verify(self.candidate)

        stages = [stage for stage, _ in self.adapter.calls]
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, stages.count("ACTION"))
        self.assertEqual(2, stages.count("READBACK"))

    def test_pre_dispatch_effect_crash_reenters_as_undetermined(self) -> None:
        class PreDispatchCrashAdapter(FixedEffectAdapter):
            def __init__(self):
                super().__init__()
                self.crash = True

            def canonicalize(self, effect):
                if self.crash:
                    self.crash = False
                    raise SystemExit("simulated pre-dispatch crash")
                return super().canonicalize(effect)

        adapter = PreDispatchCrashAdapter()
        module, _ = self.public_verification([effect_observation()], adapter=adapter)
        with self.assertRaises(SystemExit):
            module.verify(self.candidate)

        result = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], adapter.calls)

    def test_inconclusive_readback_persists_and_blocks_same_and_new_candidate_action(self) -> None:
        self.adapter.response_loss = True
        self.adapter.readback_complete = False
        module, verifier = self.public_verification([effect_observation()])

        first = module.verify(self.candidate)
        repeated = module.verify(self.candidate)
        second_candidate_value = interface.Candidate(
            work=self.ticket,
            planning=self.candidate.planning,
            acceptance_criteria=self.candidate.acceptance_criteria,
            source=self.candidate.source,
            implementation_changes=self.candidate.implementation_changes,
            preserved_changes=self.candidate.preserved_changes,
        )
        transition = self.store.begin(
            self.ticket, "IMPLEMENT", {"worker": "worker-b"}, "second-implementation"
        )
        second_candidate = self.store.publish(
            transition.transition_identity, second_candidate_value
        )
        second = module.verify(second_candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, repeated.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, second.status)
        self.assertEqual(1, [stage for stage, _ in self.adapter.calls].count("ACTION"))
        self.assertEqual(["SUPPORTED", "UNSAFE", "UNSAFE"], verifier.effect_safety)
        self.assertTrue(self.store.effect_safety_facts(second_candidate))

    def test_cleanup_is_prefixed_authorized_marked_and_read_back(self) -> None:
        observer = effect_module.EffectObservationModule(self.adapter)
        result = observer.observe(
            self.candidate,
            effect_observation(cleanup=True),
            (),
            self.adapter.markers.append,
        )

        self.assertEqual("COMPLETE", result.raw["status"])
        self.assertEqual(
            ["ACTION", "READBACK", "CLEANUP", "CLEANUP_READBACK"],
            [stage for stage, _ in self.adapter.calls],
        )
        self.assertEqual(["ACTION", "CLEANUP"], [item["stage"] for item in self.adapter.markers])

    def test_cleanup_timeout_and_unsafe_redaction_remain_unresolved(self) -> None:
        self.adapter.cleanup_complete = False
        observer = effect_module.EffectObservationModule(self.adapter)
        cleanup = observer.observe(
            self.candidate,
            effect_observation(cleanup=True),
            (),
            self.adapter.markers.append,
        )
        self.assertEqual("UNRESOLVED_EFFECT", cleanup.raw["status"])
        self.adapter.cleanup_complete = True
        recovered = observer.observe(
            self.candidate,
            effect_observation(cleanup=True),
            (cleanup.unresolved,),
            self.adapter.markers.append,
        )
        self.assertEqual("COMPLETE", recovered.raw["status"])
        self.assertEqual(1, [stage for stage, _ in self.adapter.calls].count("CLEANUP"))

        other = FixedEffectAdapter()
        other.redaction_safe = False
        unsafe = effect_module.EffectObservationModule(other).observe(
            self.candidate,
            effect_observation(occurrence="occurrence-2"),
            (),
            other.markers.append,
        )
        self.assertEqual("UNRESOLVED_EFFECT", unsafe.raw["status"])
        self.assertNotIn("secret", str(unsafe.raw))

    def test_drift_after_action_still_finishes_cleanup_without_positive_result(self) -> None:
        currentness = [interface.Currentness.CURRENT]

        def drift(stage):
            if stage == "ACTION":
                currentness[0] = interface.Currentness.NOT_CURRENT

        self.adapter.after_dispatch = drift
        module, _ = self.public_verification(
            [effect_observation(cleanup=True)],
            currentness=lambda result: currentness[0],
        )

        result = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual(
            ["ACTION", "READBACK", "CLEANUP", "CLEANUP_READBACK"],
            [stage for stage, _ in self.adapter.calls],
        )

    def test_contradiction_still_resolves_prior_cleanup(self) -> None:
        self.adapter.cleanup_complete = False
        first_module, _ = self.public_verification([effect_observation(cleanup=True)])
        first = first_module.verify(self.candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)

        class ContradictingRunner(ReadOnlyRunner):
            def run(self, candidate, retained_source, scratch_root, observation):
                if observation["kind"] != "SOURCE":
                    return super().run(candidate, retained_source, scratch_root, observation)
                self.calls.append("SOURCE")
                return {
                    "status": "COMPLETE",
                    "subattempts": [
                        {"request": request, "status": "FINISHED"}
                        for request in observation["requests"]
                    ],
                    "observed": "contradiction",
                    "artifact": {"observed": "contradiction"},
                }

        source = {
            "observationIdentity": "source-contradiction",
            "kind": "SOURCE",
            "criterionIndexes": [1],
            "requests": [{"path": "app.txt"}],
            "expected": "implemented",
        }
        recovery = effect_observation(cleanup=True)

        class ContradictingContext:
            identity = "fresh-contradicting-context"

            def plan(self, candidate, retained_source, supported_observations):
                return [source, recovery]

            def assess(self, candidate, plan, evidence):
                complete_source = any(
                    item["observationIdentity"] == "source-contradiction"
                    and item["complete"]
                    for item in evidence
                )
                return [
                    {
                        "criterionIndex": 1,
                        "outcome": "NOT_SATISFIED" if complete_source else "UNDETERMINED",
                        "evidenceObservationIdentities": (
                            ["source-contradiction"] if complete_source else []
                        ),
                    }
                ]

        class ContradictingVerifier:
            fresh_context_enforced = True
            read_only_enforced = True

            def open(self, candidate, retained_source, supported_observations, effect_safety):
                return ContradictingContext()

        self.adapter.calls.clear()
        self.adapter.cleanup_complete = True
        verification = verification_module.VerificationExecution(
            self.state_root,
            self.store,
            ContradictingVerifier(),
            ContradictingRunner(),
            lambda result: interface.Currentness.CURRENT,
            effect_module.EffectObservationModule(self.adapter),
        )
        module = interface.ImplementationVerificationModule(
            backend_module.DurableBackend(
                self.store,
                verification_module.ModuleExecution(object(), verification),
            )
        )

        result = module.verify(self.candidate)

        stages = [stage for stage, _ in self.adapter.calls]
        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, result.status)
        self.assertNotIn("ACTION", stages)
        self.assertNotIn("CLEANUP", stages)
        self.assertEqual(["READBACK", "CLEANUP_READBACK"], stages)
        self.assertFalse(
            any(
                item.get("state") == "UNRESOLVED"
                for item in self.store.effect_safety_facts(self.candidate)
            )
        )

    def test_pure_authenticated_read_bypasses_effect_module(self) -> None:
        read = {
            "observationIdentity": "remote-read",
            "kind": "READ",
            "criterionIndexes": [1],
            "requests": [{"operation": "get"}],
            "expected": "created",
        }
        runner = ReadOnlyRunner()
        module, _ = self.public_verification([read], runner=runner)

        result = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(["READ"], runner.calls)
        self.assertEqual([], self.adapter.calls)

    def test_authenticated_read_without_authority_or_redaction_is_nonconclusive(self) -> None:
        read = {
            "observationIdentity": "remote-read",
            "kind": "READ",
            "criterionIndexes": [1],
            "requests": [{"operation": "get"}],
            "expected": "created",
        }
        runner = ReadOnlyRunner()
        runner.read_authorized = False
        module, _ = self.public_verification([read], runner=runner)
        missing = module.verify(self.candidate)

        runner.read_authorized = True
        runner.redaction_safe = False
        unsafe = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, missing.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, unsafe.status)
        self.assertEqual(["READ"], runner.calls)
        self.assertIsNone(unsafe.criterion_results[0].evidence[0]["artifact"])
        self.assertNotIn("must-not-survive", str(unsafe))

    def test_candidate_self_grant_is_not_an_effect_authority(self) -> None:
        proposed = effect_observation()
        proposed["effect"] = dict(proposed["effect"], authority={"allow": True})
        module, _ = self.public_verification([proposed])

        result = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], self.adapter.calls)

    def test_completed_implementation_effect_is_projected_and_verification_is_readback_only(self) -> None:
        root = Path(self.temporary.name)
        spec = root / "SPEC.md"
        spec.write_text(
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
        ticket = root / "IMPLEMENT-TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {self.project}\n"
            "Worker: \nUI: no\n\n"
            "## Goal\nDone.\n\n## Acceptance Criteria\n- app is implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        adapter = self.adapter
        observer = effect_module.EffectObservationModule(adapter)
        implementation = implementation_module.ImplementationExecution(
            self.state_root,
            self.store,
            NoWorkerAdapter(),
            NoAdoption(),
            lambda work, source: None,
            lambda work, source: [
                {
                    key: value
                    for key, value in effect_observation().items()
                    if key not in {"kind", "criterionIndexes"}
                }
            ],
            observer,
        )
        implementation_public = interface.ImplementationVerificationModule(
            backend_module.DurableBackend(self.store, implementation)
        )

        adapter.response_loss = True
        adapter.readback_complete = False
        stopped = implementation_public.implement(ticket, NoWorker())
        action_count = [stage for stage, _ in adapter.calls].count("ACTION")
        adapter.readback_complete = True
        candidate = implementation_public.implement(ticket, NoWorker())
        module, _ = self.public_verification(
            [effect_observation(action=False)], adapter=adapter
        )
        result = module.verify(candidate)

        self.assertIsInstance(stopped, interface.ImplementationStopped)
        self.assertIsInstance(candidate, interface.Candidate)
        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, action_count)
        self.assertEqual(action_count, [stage for stage, _ in adapter.calls].count("ACTION"))
        self.assertTrue(self.store.effect_safety_facts(candidate))

    def test_completed_implementation_effect_survives_stopped_candidate_publication(self) -> None:
        ticket = self.ready_implementation_ticket("STOPPED-EFFECT")
        drifted = False

        def drift_after_readback(stage):
            nonlocal drifted
            if stage == "READBACK" and not drifted:
                (self.project / "drift.txt").write_text("user change", encoding="utf-8")
                drifted = True

        self.adapter.after_dispatch = drift_after_readback
        observer = effect_module.EffectObservationModule(self.adapter)
        implementation = implementation_module.ImplementationExecution(
            self.state_root,
            self.store,
            NoWorkerAdapter(),
            NoAdoption(),
            lambda work, source: None,
            lambda work, source: [
                {
                    key: value
                    for key, value in effect_observation().items()
                    if key not in {"kind", "criterionIndexes"}
                }
            ],
            observer,
        )
        module = interface.ImplementationVerificationModule(
            backend_module.DurableBackend(self.store, implementation)
        )

        stopped = module.implement(ticket, NoWorker())
        facts_after_stop = self.store.effect_safety_facts_for_work(ticket)
        self.adapter.after_dispatch = None
        candidate = module.implement(ticket, NoWorker())

        self.assertIsInstance(stopped, interface.ImplementationStopped)
        self.assertTrue(any(item.get("state") == "COMPLETED" for item in facts_after_stop))
        self.assertIsInstance(candidate, interface.Candidate)
        self.assertEqual(1, [stage for stage, _ in self.adapter.calls].count("ACTION"))


if __name__ == "__main__":
    unittest.main()
