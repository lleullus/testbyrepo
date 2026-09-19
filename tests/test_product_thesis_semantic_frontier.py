from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "product-thesis" / "SKILL.md"
EXPLORATION = ROOT / "product-thesis" / "references" / "exploration.md"
SCENARIOS = ROOT / "evaluation" / "product-thesis" / "refinement-scenarios.md"
CASES = ROOT / "evaluation" / "product-thesis" / "cases.json"
RUN = ROOT / "evaluation" / "product-thesis" / "run.py"
ROLE_FIXTURE_IDS = {
    "S16-plan-preserves-thesis-decision",
    "S19-local-implementation-discretion",
    "S20-irreversible-effect-precondition",
}

NEW_CASE_IDS = {
    "S1-frontier-persistence",
    "S2-existing-meaning-defect-reuse",
    "S3-evidence-limit-not-policy-choice",
    "S4-identity-false-success",
    "S5-failure-preservation-adjacency",
    "S6-small-frontier-control",
    "S7-artifact-only-control",
    "S8-existing-thesis-reuse-frontier",
    "S9-genuine-user-owned-retry-choice",
    "S10-material-exclusion-basis",
    "S11-premature-depth-stop",
    "S12-clear-draft-no-investigation",
    "S13-grounded-construction-adoption",
    "S14-authority-versus-asset-preservation",
    "S15-marker-only-false-success",
    "S16-plan-preserves-thesis-decision",
    "S17-refuted-construction-reentry",
    "S18-probe-invalidates-upstream-premise",
    "S19-local-implementation-discretion",
    "S20-irreversible-effect-precondition",
}


def load_run():
    spec = importlib.util.spec_from_file_location("product_thesis_run", RUN)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Product Thesis evaluator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProductThesisSemanticFrontierContractTests(unittest.TestCase):
    def test_minimum_semantic_sufficiency_and_frontier_are_operationalized(self) -> None:
        skill = PRODUCT.read_text(encoding="utf-8")
        exploration = EXPLORATION.read_text(encoding="utf-8")

        for phrase in (
            "## Minimum semantic sufficiency",
            "bounded **semantic frontier**",
            "two or more semantic outcomes genuinely remain",
            "set of compliant product behaviors changes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

        for phrase in (
            "## Semantic frontier calibration",
            "**Inclusion test:**",
            "**Minimum discriminator:**",
            "**Breadth closure:**",
            "**Depth entry:**",
            "**Depth stop:**",
            "semantic unknown",
            "behavioral contract-delta test",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, exploration)

    def test_contract_does_not_create_new_stage_artifact_or_mandatory_brief(self) -> None:
        skill = PRODUCT.read_text(encoding="utf-8")
        exploration = EXPLORATION.read_text(encoding="utf-8")
        combined = skill + "\n" + exploration

        self.assertIn("not a fixed list", skill)
        self.assertIn("no fixed headings or second artifact", exploration)
        self.assertIn("Brief is not a prerequisite", exploration)
        self.assertNotIn("Semantic Frontier artifact", combined)
        self.assertNotIn("independent Product Thesis reviewer", combined)

    def test_refinement_scenarios_remain_synthetic_and_not_run(self) -> None:
        scenarios = SCENARIOS.read_text(encoding="utf-8")
        self.assertIn("Status: NOT_RUN", scenarios)
        for number in range(15, 41):
            self.assertIn(f"### R{number:02d} —", scenarios)
        self.assertIn('not whether the agent printed "Breadth", "Depth"', scenarios)
        self.assertIn("Only scenario design is recorded here", scenarios)

    def test_new_case_inventory_is_unique_and_oracles_do_not_enter_actor_prompt(self) -> None:
        cohort = json.loads(CASES.read_text(encoding="utf-8"))
        ids = [case["id"] for case in cohort["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(NEW_CASE_IDS.issubset(ids))

        run = load_run()
        with tempfile.TemporaryDirectory() as directory:
            arena = Path(directory)
            for case_id in sorted(NEW_CASE_IDS):
                case = next(case for case in cohort["cases"] if case["id"] == case_id)
                metadata_path = run.prepare(
                    case_id,
                    arena,
                    cohort["protocol"]["variants"][0],
                    cohort["protocol"]["repetitions"][0],
                )
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                prompt = metadata["prompt"]
                self.assertEqual(metadata["case_id"], case_id)
                self.assertEqual(metadata["required_observations"], case["required_observations"])
                self.assertEqual(metadata["forbidden_observations"], case["forbidden_observations"])
                for oracle in [*case["required_observations"], *case["forbidden_observations"]]:
                    self.assertNotIn(oracle, prompt)
                self.assertEqual(
                    metadata["prompt_sha256"],
                    hashlib.sha256(prompt.encode()).hexdigest(),
                )
                for fixture in metadata.get("fixture_files", []):
                    fixture_path = Path(metadata["project_root"]) / fixture["path"]
                    self.assertTrue(fixture_path.is_file())
                    self.assertEqual(fixture["sha256"], hashlib.sha256(fixture_path.read_bytes()).hexdigest())

    def test_fixture_paths_reject_traversal_absolute_and_symlinks(self) -> None:
        run = load_run()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            with self.assertRaises(ValueError):
                run.materialize_fixture_files(project, [{"path": "../escape.txt", "content": "x"}])
            with self.assertRaises(ValueError):
                run.materialize_fixture_files(project, [{"path": str(root / "absolute.txt"), "content": "x"}])

            outside = root / "outside"
            outside.mkdir()
            link = project / "linked"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                run.materialize_fixture_files(project, [{"path": "linked/escape.txt", "content": "x"}])

            broken_target = outside / "missing.txt"
            broken_link = project / "broken.txt"
            broken_link.symlink_to(broken_target)
            with self.assertRaises(ValueError):
                run.materialize_fixture_files(project, [{"path": "broken.txt", "content": "x"}])
            self.assertFalse(broken_target.exists())

    def test_role_fixtures_materialize_canonical_admission_inputs(self) -> None:
        cohort = json.loads(CASES.read_text(encoding="utf-8"))
        run = load_run()
        with tempfile.TemporaryDirectory() as directory:
            arena = Path(directory)
            for case_id in sorted(ROLE_FIXTURE_IDS):
                metadata_path = run.prepare(
                    case_id,
                    arena,
                    cohort["protocol"]["variants"][0],
                    cohort["protocol"]["repetitions"][0],
                )
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                role = metadata["role_fixture"]
                self.assertIsNotNone(role)
                prompt = metadata["prompt"]

                for name in ("thesis", "scope"):
                    ref = role[name]
                    path = Path(ref["path"])
                    self.assertTrue(path.is_file())
                    self.assertEqual(ref["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                    self.assertIn(str(path), prompt)

                scope_check = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(ROOT / "scope-shaper" / "tools" / "validate_scope.py"),
                        role["scope"]["path"],
                        "--json",
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(scope_check.returncode, 0, scope_check.stderr or scope_check.stdout)

                if role["kind"] == "implementer":
                    plan = Path(role["plan"]["path"])
                    self.assertTrue(plan.is_file())
                    self.assertEqual(role["plan"]["sha256"], hashlib.sha256(plan.read_bytes()).hexdigest())
                    self.assertIn(str(plan), prompt)
                    baseline_check = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            str(ROOT / "iis-workflow" / "tools" / "assurance.py"),
                            "validate",
                            str(plan),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(baseline_check.returncode, 0, baseline_check.stderr or baseline_check.stdout)
                    self.assertIn('"status": "VALID"', baseline_check.stdout)
                else:
                    destination = Path(role["plan_destination"])
                    self.assertFalse(destination.exists())
                    self.assertIn(str(destination), prompt)

    def test_cases_cover_material_omission_and_non_overreach_controls(self) -> None:
        cases = {
            case["id"]: case
            for case in json.loads(CASES.read_text(encoding="utf-8"))["cases"]
            if case["id"] in NEW_CASE_IDS
        }
        for case_id in (
            "S1-frontier-persistence",
            "S4-identity-false-success",
            "S5-failure-preservation-adjacency",
            "S9-genuine-user-owned-retry-choice",
            "S11-premature-depth-stop",
            "S6-small-frontier-control",
            "S7-artifact-only-control",
            "S12-clear-draft-no-investigation",
            "S13-grounded-construction-adoption",
            "S14-authority-versus-asset-preservation",
            "S15-marker-only-false-success",
            "S16-plan-preserves-thesis-decision",
            "S17-refuted-construction-reentry",
            "S18-probe-invalidates-upstream-premise",
            "S19-local-implementation-discretion",
            "S20-irreversible-effect-precondition",
        ):
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, cases)


if __name__ == "__main__":
    unittest.main()
