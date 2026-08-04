from __future__ import annotations

import importlib.util
import shutil
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
implementation_module = load("implementation_execution", ROOT / "implementation_execution.py")
verification_module = load("verification_execution", ROOT / "verification_execution.py")


class StubImplementation:
    def __init__(self) -> None:
        self.currentness = interface.Currentness.CURRENT

    def implement(self, work, worker, transition_identity, *, reenter):
        raise AssertionError("verification must not dispatch a Worker")

    def observe_currentness(self, result):
        candidate = result.candidate if isinstance(result, interface.VerificationResult) else result
        implementation_module.ImplementationExecution._validate_retained_source(candidate)
        return self.currentness


class VerifierContext:
    def __init__(self, identity, observations, claims_override=None) -> None:
        self.identity = identity
        self.observations = observations
        self.claims_override = claims_override

    def plan(self, candidate, retained_source, supported_observations):
        return self.observations

    def assess(self, candidate, plan, evidence):
        if self.claims_override is not None:
            return self.claims_override
        claims = []
        for index in range(1, len(candidate.acceptance_criteria) + 1):
            obligations = [
                item["observationIdentity"]
                for item in plan["observations"]
                if index in item["criterionIndexes"]
            ]
            available = [
                item for item in evidence if item["observationIdentity"] in obligations
            ]
            complete = [item for item in available if item["complete"]]
            if any(item["observed"] != item["expected"] for item in complete):
                outcome = "NOT_SATISFIED"
                references = [item["observationIdentity"] for item in complete]
            elif len(complete) == len(obligations):
                outcome = "SATISFIED"
                references = [item["observationIdentity"] for item in complete]
            else:
                outcome = "UNDETERMINED"
                references = [item["observationIdentity"] for item in available]
            claims.append(
                {
                    "criterionIndex": index,
                    "outcome": outcome,
                    "evidenceObservationIdentities": references,
                }
            )
        return claims


class FreshVerifier:
    fresh_context_enforced = True
    read_only_enforced = True

    def __init__(self, observations, claims_override=None) -> None:
        self.observations = observations
        self.claims_override = claims_override
        self.opens = 0
        self.effect_safety = []
        self.inputs = []

    def open(self, candidate, retained_source, supported_observations, effect_safety):
        self.opens += 1
        self.effect_safety.append(effect_safety)
        self.inputs.append((candidate, retained_source, supported_observations))
        return VerifierContext(
            f"fresh-context-{self.opens}",
            self.observations,
            self.claims_override,
        )


class Runner:
    read_only_enforced = True
    effect_observation_enforced = True
    supported_observations = ("SOURCE", "LOCAL", "EFFECT")

    def __init__(self, results=None, after_run=None) -> None:
        self.results = results or {}
        self.after_run = after_run
        self.calls = []

    def run(self, candidate, retained_source, scratch_root, observation):
        identity = observation["observationIdentity"]
        self.calls.append(identity)
        configured = self.results.get(identity)
        if isinstance(configured, BaseException):
            self.results[identity] = None
            raise configured
        if callable(configured):
            raw = configured(candidate, retained_source, scratch_root, observation)
        elif configured is not None:
            raw = configured
        elif observation["kind"] == "SOURCE":
            request = observation["requests"][0]
            observed = (retained_source / request["path"]).read_text(encoding="utf-8")
            raw = self.complete(observation, observed)
        else:
            raw = self.complete(observation, observation["expected"])
        if self.after_run is not None:
            self.after_run(identity)
        return raw

    @staticmethod
    def complete(observation, observed):
        return {
            "status": "COMPLETE",
            "subattempts": [
                {"request": request, "status": "FINISHED"}
                for request in observation["requests"]
            ],
            "observed": observed,
            "artifact": {"observed": observed},
        }


def observation(identity, kind, criteria, expected, *requests):
    return {
        "observationIdentity": identity,
        "kind": kind,
        "criterionIndexes": list(criteria),
        "requests": list(requests),
        "expected": expected,
    }


class VerificationExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "product"
        self.project.mkdir()
        (self.project / "app.txt").write_text("implemented", encoding="utf-8")
        self.retained = root / "retained"
        shutil.copytree(self.project, self.retained)
        _, identity = implementation_module._capture(self.retained)
        self.ticket = root / "TICKET.md"
        self.ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        self.database = root / "state" / "durable.sqlite3"
        self.state_root = root / "execution-state"
        self.store = durable.DurableWorkStore(self.database)
        candidate = interface.Candidate(
            work=self.ticket.resolve(),
            planning={"projectRoot": str(self.project.resolve()), "ticket": "planning-1"},
            acceptance_criteria=("AC-1", "AC-2"),
            source={"identity": identity, "retainedRoot": str(self.retained)},
            implementation_changes=("app.txt",),
            preserved_changes=(),
        )
        transition = self.store.begin(
            self.ticket,
            "IMPLEMENT",
            {"worker": "worker-a"},
            "implementation-progress",
        )
        self.candidate = self.store.publish(transition.transition_identity, candidate)
        self.implementation = StubImplementation()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def module(self, verifier, runner):
        verification = verification_module.VerificationExecution(
            self.state_root,
            self.store,
            verifier,
            runner,
            self.implementation.observe_currentness,
        )
        execution = verification_module.ModuleExecution(self.implementation, verification)
        return interface.ImplementationVerificationModule(
            backend_module.DurableBackend(self.store, execution)
        )

    def two_observations(self):
        return [
            observation("source", "SOURCE", (1,), "implemented", {"path": "app.txt"}),
            observation("local", "LOCAL", (2,), "ok", {"argv": ["product", "--check"]}),
        ]

    def test_fresh_source_and_local_evidence_publish_verified(self) -> None:
        verifier = FreshVerifier(self.two_observations())
        result = self.module(verifier, Runner()).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, verifier.opens)
        self.assertEqual(self.candidate, verifier.inputs[0][0])
        for criterion in result.criterion_results:
            self.assertEqual(interface.CriterionOutcome.SATISFIED, criterion.outcome)
            self.assertTrue(criterion.evidence[0]["complete"])
            self.assertIsNotNone(criterion.evidence[0]["artifactIdentity"])

    def test_plan_without_full_ac_coverage_runs_no_evidence(self) -> None:
        verifier = FreshVerifier(self.two_observations()[:1])
        runner = Runner()
        result = self.module(verifier, runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], runner.calls)
        self.assertTrue(
            all(item.outcome is interface.CriterionOutcome.UNDETERMINED for item in result.criterion_results)
        )

    def test_tool_failure_is_undetermined_not_product_failure(self) -> None:
        failed = {
            "status": "TOOL_ERROR",
            "subattempts": [{"request": {"path": "app.txt"}, "status": "TOOL_ERROR"}],
            "observed": None,
            "artifact": None,
        }
        observations = [observation("source", "SOURCE", (1, 2), "implemented", {"path": "app.txt"})]
        result = self.module(FreshVerifier(observations), Runner({"source": failed})).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertNotIn(
            interface.CriterionOutcome.NOT_SATISFIED,
            tuple(item.outcome for item in result.criterion_results),
        )

    def test_direct_contradiction_stops_not_yet_started_effect(self) -> None:
        observations = [
            observation("source", "SOURCE", (1,), "implemented", {"path": "app.txt"}),
            observation("effect", "EFFECT", (2,), "created", {"action": "create"}),
        ]
        runner = Runner({"source": Runner.complete(observations[0], "wrong")})
        result = self.module(FreshVerifier(observations), runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, result.status)
        self.assertEqual(["source"], runner.calls)
        self.assertEqual(interface.CriterionOutcome.NOT_SATISFIED, result.criterion_results[0].outcome)
        self.assertEqual(interface.CriterionOutcome.UNDETERMINED, result.criterion_results[1].outcome)

    def test_positive_observation_after_drift_is_undetermined(self) -> None:
        observations = [observation("source", "SOURCE", (1, 2), "implemented", {"path": "app.txt"})]
        runner = Runner(after_run=lambda _: setattr(self.implementation, "currentness", interface.Currentness.NOT_CURRENT))
        result = self.module(FreshVerifier(observations), runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)

    def test_complete_contradiction_before_detected_drift_is_preserved(self) -> None:
        observations = [observation("source", "SOURCE", (1, 2), "expected", {"path": "app.txt"})]
        runner = Runner(
            {"source": Runner.complete(observations[0], "contradiction")},
            after_run=lambda _: setattr(self.implementation, "currentness", interface.Currentness.NOT_CURRENT),
        )
        result = self.module(FreshVerifier(observations), runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, result.status)

    def test_runner_without_read_only_isolation_executes_nothing(self) -> None:
        observations = [observation("source", "SOURCE", (1, 2), "implemented", {"path": "app.txt"})]
        runner = Runner()
        runner.read_only_enforced = False
        before = (self.retained / "app.txt").read_bytes()
        result = self.module(FreshVerifier(observations), runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], runner.calls)
        self.assertEqual(before, (self.retained / "app.txt").read_bytes())

    def test_local_response_loss_closes_undetermined_without_duplicate_then_retries_fresh(self) -> None:
        observations = [observation("local", "LOCAL", (1, 2), "ok", {"argv": ["check"]})]
        verifier = FreshVerifier(observations)
        runner = Runner({"local": InterruptedError("simulated response loss")})
        module = self.module(verifier, runner)
        with self.assertRaises(InterruptedError):
            module.verify(self.candidate)

        incomplete = module.verify(self.candidate)
        completed = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, incomplete.status)
        self.assertEqual(interface.VerificationStatus.VERIFIED, completed.status)
        self.assertEqual(["local", "local"], runner.calls)
        self.assertEqual(2, verifier.opens)

    def test_unresolved_effect_blocks_all_later_same_candidate_effects(self) -> None:
        observations = [observation("effect", "EFFECT", (1, 2), "created", {"action": "create"})]
        unresolved = {
            "status": "UNRESOLVED_EFFECT",
            "subattempts": [{"request": {"action": "create"}, "status": "UNKNOWN"}],
            "observed": None,
            "artifact": None,
            "target": {"resource": "target-1"},
            "liveOwnerAbsent": True,
        }
        verifier = FreshVerifier(observations)
        runner = Runner({"effect": unresolved})
        module = self.module(verifier, runner)

        first = module.verify(self.candidate)
        second = module.verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, first.status)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, second.status)
        self.assertEqual(["effect"], runner.calls)
        self.assertEqual(["SUPPORTED", "UNSAFE"], verifier.effect_safety)
        self.assertEqual(1, len(self.store.unresolved_observations(self.candidate)))

    def test_effect_response_loss_stays_fail_closed_without_reexecution(self) -> None:
        observations = [observation("effect", "EFFECT", (1, 2), "created", {"action": "create"})]
        runner = Runner({"effect": InterruptedError("simulated effect response loss")})
        module = self.module(FreshVerifier(observations), runner)
        with self.assertRaises(InterruptedError):
            module.verify(self.candidate)
        with self.assertRaisesRegex(RuntimeError, "may have run"):
            module.verify(self.candidate)

        self.assertEqual(["effect"], runner.calls)
        self.assertEqual(self.candidate, module.inspect(self.ticket).result)

    def test_effect_observation_without_phase_six_owned_seam_is_not_executed(self) -> None:
        observations = [observation("effect", "EFFECT", (1, 2), "created", {"action": "create"})]
        runner = Runner()
        runner.effect_observation_enforced = False
        result = self.module(FreshVerifier(observations), runner).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual([], runner.calls)

    def test_subattempt_request_substitution_downgrades_conclusive_claim(self) -> None:
        observations = [observation("local", "LOCAL", (1, 2), "ok", {"argv": ["fixed"]})]
        substituted = {
            "status": "COMPLETE",
            "subattempts": [{"request": {"argv": ["changed"]}, "status": "FINISHED"}],
            "observed": "ok",
            "artifact": {"observed": "ok"},
        }
        result = self.module(FreshVerifier(observations), Runner({"local": substituted})).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)

    def test_complete_evidence_keeps_all_prefixed_heterogeneous_subattempts(self) -> None:
        action = {"action": "start"}
        readback = {"readback": "status"}
        observations = [observation("flow", "LOCAL", (1, 2), "ok", action, readback)]
        bundled = {
            "status": "COMPLETE",
            "subattempts": [
                {"request": action, "status": "TIMED_OUT"},
                {"request": readback, "status": "FINISHED"},
            ],
            "observed": "ok",
            "artifact": {"readback": "ok"},
        }
        result = self.module(FreshVerifier(observations), Runner({"flow": bundled})).verify(self.candidate)

        self.assertEqual(interface.VerificationStatus.VERIFIED, result.status)
        evidence = result.criterion_results[0].evidence[0]
        self.assertEqual([action, readback], [item["request"] for item in evidence["subattempts"]])

    def test_concurrent_same_candidate_verification_runs_one_fresh_context_and_runner(self) -> None:
        started = threading.Event()
        release = threading.Event()
        observations = [observation("local", "LOCAL", (1, 2), "ok", {"argv": ["check"]})]

        class BlockingRunner(Runner):
            def run(self, candidate, retained_source, scratch_root, item):
                self.calls.append(item["observationIdentity"])
                started.set()
                release.wait(timeout=5)
                return self.complete(item, item["expected"])

        verifier = FreshVerifier(observations)
        runner = BlockingRunner()
        module = self.module(verifier, runner)
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(module.verify, self.candidate)
            self.assertTrue(started.wait(timeout=5))
            second = executor.submit(module.verify, self.candidate)
            release.set()
            results = (first.result(timeout=5), second.result(timeout=5))

        self.assertEqual(1, verifier.opens)
        self.assertEqual(["local"], runner.calls)
        self.assertEqual(1, len({item.result_identity for item in results}))

    def test_final_verifier_assessment_cannot_mutate_retained_candidate_and_publish(self) -> None:
        observations = [observation("source", "SOURCE", (1, 2), "implemented", {"path": "app.txt"})]

        class MutatingContext(VerifierContext):
            def __init__(self, retained):
                super().__init__("mutating-context", observations)
                self.retained = retained
                self.assessment_calls = 0

            def assess(self, candidate, plan, evidence):
                self.assessment_calls += 1
                if self.assessment_calls == 2:
                    (self.retained / "app.txt").write_text("mutated by verifier", encoding="utf-8")
                return super().assess(candidate, plan, evidence)

        class MutatingVerifier(FreshVerifier):
            def open(self, candidate, retained_source, supported_observations, effect_safety):
                self.opens += 1
                return MutatingContext(retained_source)

        module = self.module(MutatingVerifier(observations), Runner())
        with self.assertRaises(durable.DurableResultIntegrityError):
            module.verify(self.candidate)

        self.assertNotIsInstance(module.inspect(self.ticket).result, interface.VerificationResult)

    def test_verification_commit_response_loss_reads_committed_result_without_rerun(self) -> None:
        observations = [observation("source", "SOURCE", (1, 2), "implemented", {"path": "app.txt"})]
        verifier = FreshVerifier(observations)
        runner = Runner()
        original_publish = self.store.publish
        lose_response = True

        def publish(*args, **kwargs):
            nonlocal lose_response
            result = original_publish(*args, **kwargs)
            if isinstance(result, interface.VerificationResult) and lose_response:
                lose_response = False
                raise InterruptedError("simulated committed result response loss")
            return result

        self.store.publish = publish
        module = self.module(verifier, runner)
        with self.assertRaises(InterruptedError):
            module.verify(self.candidate)

        inspected = module.inspect(self.ticket).result
        repeated = module.verify(self.candidate)

        self.assertIsInstance(inspected, interface.VerificationResult)
        self.assertEqual(inspected, repeated)
        self.assertEqual(1, verifier.opens)
        self.assertEqual(["source"], runner.calls)


if __name__ == "__main__":
    unittest.main()
