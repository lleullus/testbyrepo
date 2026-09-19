from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation" / "ready-verification" / "corrective_reuse_fixtures.py"


def load_fixtures():
    spec = importlib.util.spec_from_file_location("corrective_reuse_fixtures", FIXTURES)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load corrective reuse fixtures")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CorrectiveReuseFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = load_fixtures()

    def test_temporary_reproducer_is_preserved_and_remains_runnable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ephemeral = root / "ephemeral"
            script = self.fx.write_ephemeral_reproducer(ephemeral)
            content = script.read_bytes()
            shutil.rmtree(ephemeral)
            self.assertFalse(script.exists())

            durable = self.fx.preserve_reproducer(content, root / "evidence" / "cursor_repro.py")
            self.assertEqual(durable.read_bytes(), content)

            defective = root / "defective.json"
            corrected = root / "corrected.json"
            self.fx.write_target(defective, defective=True)
            self.fx.write_target(corrected, defective=False)
            bad = self.fx.run_reproducer(durable, defective)
            good = self.fx.run_reproducer(durable, corrected)
            self.assertEqual(bad.returncode, 23)
            self.assertIn("CURSOR_OVERRUN", bad.stdout)
            self.assertEqual(good.returncode, 0)
            self.assertIn("STREAM_CONTINUES", good.stdout)

    def test_promoted_regression_preserves_exact_discriminator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fx.write_ephemeral_reproducer(root / "probe")
            promoted = self.fx.promote_regression(source, root / "project" / "tests")
            self.assertEqual(promoted.read_bytes(), source.read_bytes())
            defective = root / "bad.json"
            corrected = root / "good.json"
            self.fx.write_target(defective, defective=True)
            self.fx.write_target(corrected, defective=False)
            self.assertNotEqual(self.fx.run_reproducer(promoted, defective).returncode, 0)
            self.assertEqual(self.fx.run_reproducer(promoted, corrected).returncode, 0)

    def test_same_assumption_sibling_sweep_is_bounded(self) -> None:
        origin = self.fx.SiblingPath("resume", "session", "cursor", True)
        candidates = (
            origin,
            self.fx.SiblingPath("flow-resume", "session", "cursor", True),
            self.fx.SiblingPath("create", "session", "create", True),
            self.fx.SiblingPath("unrelated-cursor", "other", "cursor", True),
            self.fx.SiblingPath("diagnostic", "session", "cursor", False),
        )
        self.assertEqual(
            self.fx.direct_same_assumption_siblings(origin, candidates),
            ("flow-resume",),
        )

    def test_execution_method_reuse_does_not_carry_scenario_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self.fx.ExecutionIdentity("runner-v1", "build-a", "config-a", "runtime-a")
            workspace = self.fx.ExecutionWorkspace(identity, root / "scenario-state.txt")
            workspace.write_state("dirty-from-previous-scenario")
            current = self.fx.ExecutionIdentity("runner-v1", "build-a", "config-a", "runtime-a")
            self.assertTrue(self.fx.reusable_execution_method(identity, current))
            self.assertEqual(workspace.read_state(), "dirty-from-previous-scenario")
            workspace.reset_state("clean")
            self.assertEqual(workspace.read_state(), "clean")
            stale_build = self.fx.ExecutionIdentity("runner-v1", "build-b", "config-a", "runtime-a")
            self.assertFalse(self.fx.reusable_execution_method(identity, stale_build))

    def test_no_effect_usage_error_can_be_corrected_without_duplicate_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = self.fx.InvocationCommandHarness(Path(directory) / "count.txt")
            status, readback = harness.run(("--typo",))
            self.assertEqual((status, readback), ("USAGE_ERROR_NO_EFFECT", 0))
            status, readback = harness.run(("--apply",))
            self.assertEqual((status, readback), ("APPLIED", 1))
            self.assertEqual(harness.authoritative_readback(), 1)

    def test_lost_response_requires_settlement_before_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = self.fx.InvocationCommandHarness(Path(directory) / "count.txt")
            status, response = harness.run(("--apply",), lose_response_after_apply=True)
            self.assertEqual((status, response), ("RESPONSE_LOST", None))
            self.assertEqual(harness.authoritative_readback(), 1)
            self.assertNotEqual(harness.authoritative_readback(), 0, "blind retry would duplicate the effect")

    def test_method_boundary_uses_current_premises_not_diff_size(self) -> None:
        current = self.fx.MethodPremise(
            "session-owner", "proc-stat", "none", "session-id", "signal-owner", "settled-child"
        )
        same_method = self.fx.MethodPremise(
            "session-owner", "proc-stat", "none", "session-id", "signal-owner", "settled-child"
        )
        new_owner = self.fx.MethodPremise(
            "foreground-group", "proc-stat", "none", "session-id", "signal-owner", "settled-child"
        )
        self.assertEqual(self.fx.method_change_kind(current, same_method), "SAME_METHOD")
        self.assertEqual(self.fx.method_change_kind(current, new_owner), "MATERIAL_METHOD_CHANGE")

    def test_evidence_reuse_and_broadening_controls(self) -> None:
        record = self.fx.EvidenceApplicability(
            obligation="legacy-output",
            original_target="target-a",
            original_invocation="observation-a",
            dependencies=frozenset({"legacy-reader"}),
            mechanism_id="harness-a",
            runtime_config_id="config-a",
        )
        common = dict(
            record=record,
            current_target="target-b",
            mechanism_id="harness-a",
            runtime_config_id="config-a",
            current_state_observed=True,
            dependency_span_bounded=True,
        )
        self.assertEqual(
            self.fx.evidence_action(changed_dependencies={"new-writer"}, **common),
            "FRESH_OBSERVATION",
        )
        self.assertEqual(
            self.fx.evidence_action(changed_dependencies={"legacy-reader"}, **common),
            "FRESH_OBSERVATION",
        )
        self.assertEqual(
            self.fx.evidence_action(
                changed_dependencies={"new-writer"},
                **{**common, "mechanism_id": "harness-b"},
            ),
            "FRESH_OBSERVATION",
        )
        self.assertEqual(
            self.fx.evidence_action(
                changed_dependencies={"new-writer"},
                **{**common, "dependency_span_bounded": False},
            ),
            "BROADEN_FRESH_ACQUISITION",
        )
        self.assertEqual(
            self.fx.evidence_action(changed_dependencies=(), **{**common, "current_target": "target-a"}),
            "RETAIN_WITH_ORIGINAL_ATTRIBUTION",
        )


    def test_repository_install_and_invocation_identity_are_distinct(self) -> None:
        self.assertTrue(
            self.fx.loaded_contract_matches(
                repository_identity="bundle-a",
                installed_identity="bundle-a",
                invocation_identity="bundle-a",
            )
        )
        self.assertFalse(
            self.fx.loaded_contract_matches(
                repository_identity="bundle-b",
                installed_identity="bundle-b",
                invocation_identity="bundle-a",
            )
        )


if __name__ == "__main__":
    unittest.main()
