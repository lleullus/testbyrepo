from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evaluation/ready-verification/fixture_catalog.py"
TARGET_MODULE = ROOT / "delivery-runtime/ready-ticket-implement/src/verification-target.js"
CALIBRATE = ROOT / "evaluation/ready-verification/calibrate.py"


def load_catalog():
    spec = importlib.util.spec_from_file_location("calibration_fixture_boundaries", CATALOG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_calibrate():
    sys.path.insert(0, str(CATALOG.parent))
    try:
        spec = importlib.util.spec_from_file_location("calibration_probe_challenges", CALIBRATE)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load calibration challenge dispatcher")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class FixtureBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = load_catalog()
        self.environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.calibrate = load_calibrate()

    def probe_metadata(self, case_id: str, variant: str) -> dict[str, object]:
        case_root = Path(tempfile.mkdtemp(dir=self.root))
        metadata = self.catalog.materialize(
            {"case_id": case_id, "family": "probe-admission", "variant": variant},
            case_root / "product", case_root / "support", port=12345,
        )
        metadata["case_id"] = case_id
        return metadata

    @staticmethod
    def probe_binding(metadata: dict[str, object]) -> dict[str, object]:
        return {
            "schema": "iis-ready-probe-handoff/v1",
            "implementation_target": {
                "digest": "bound-target-identity",
                "target_paths": metadata["target_paths"],
                "allowed_output_paths": metadata["allowed_output_paths"],
            },
            "probe_completion": "COMPLETE",
            "cleanup": "CLOSED",
            "admitted_lanes": [],
            "lane_terminals": [],
        }

    def test_materialized_source_change_is_not_exempted_as_generated_output(self):
        metadata = self.catalog.materialize(
            {"family": "runtime-correct", "variant": "core"},
            self.root / "product", self.root / "support", port=12345,
        )
        project = metadata["project_root"]
        for argv in (
            ["git", "-c", "core.hooksPath=/dev/null", "init", "--quiet"],
            ["git", "add", "--all"],
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost", "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Initial state"],
        ):
            subprocess.run(argv, cwd=project, env=self.environment, check=True, capture_output=True)
        program = """
import fs from 'node:fs';
const module = await import(process.argv[1]);
const metadata = JSON.parse(process.argv[2]);
const binding = module.captureVerificationTarget({projectRoot: metadata.project_root,
    targetPaths: metadata.target_paths, allowedOutputPaths: metadata.allowed_output_paths});
fs.appendFileSync(metadata.target_paths.at(-1), '\\n# Changed product source.\\n');
console.log(JSON.stringify(module.checkVerificationTarget(binding)));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", program, TARGET_MODULE.as_uri(), json.dumps(metadata)],
            cwd=project, env=self.environment, check=True, text=True, capture_output=True,
        )
        observed = json.loads(result.stdout)
        self.assertFalse(observed["current"])
        self.assertIn("engine.py", observed["changed"])

    def test_holdout_helper_passes_while_actual_entrypoint_contradicts_it(self):
        metadata = self.catalog.materialize(
            {"family": "wrong-entry", "variant": "holdout"},
            self.root / "product", self.root / "support", port=12345,
        )
        helper = subprocess.run(
            [sys.executable, str(Path(metadata["project_root"]) / "tests/test_helper.py")],
            env=self.environment, capture_output=True, text=True,
        )
        actual = subprocess.run(metadata["trigger_argv"], env=self.environment, check=True, capture_output=True, text=True)
        self.assertEqual(helper.returncode, 0, helper.stderr)
        self.assertEqual(json.loads(actual.stdout), {"value": "original-value", "input": "sample"})

    def test_current_claim_challenge_preserves_target_identity_and_product_source(self):
        metadata = self.probe_metadata("probe-current-claim-core", "current-claim-core")
        run_root = self.root / "current-claim-run"
        prompt = self.calibrate.stage_prompt("probe", metadata, run_root)
        self.assertNotIn("expected", metadata)
        self.assertNotIn("fixture_contract", metadata)
        self.assertNotIn("probe-current-claim-core", prompt)
        self.assertNotIn("VERIFIED", prompt)
        binding_path = run_root / "probe-binding.json"
        binding_path.parent.mkdir()
        binding = self.probe_binding(metadata)
        before = json.dumps(binding, indent=2).encode("utf-8")
        binding_path.write_bytes(before)
        probe_observation = run_root / "probe" / "observation.json"
        probe_observation.parent.mkdir()
        probe_observation.write_text(json.dumps({"probe_completion": "COMPLETE"}), encoding="utf-8")
        target_path = Path(metadata["target_paths"][-1])
        source_before = target_path.read_bytes()

        applied = self.calibrate.apply_challenge(metadata, run_root)

        after = json.loads(binding_path.read_text(encoding="utf-8"))
        challenge = json.loads((run_root / "challenge.json").read_text(encoding="utf-8"))
        self.assertTrue(applied["applied"])
        self.assertEqual(after["implementation_target"], binding["implementation_target"])
        self.assertEqual(target_path.read_bytes(), source_before)
        self.assertEqual((run_root / "probe-binding.before-challenge.json").read_bytes(), before)
        self.assertEqual(challenge["binding_before_sha256"], hashlib.sha256(before).hexdigest())
        self.assertNotEqual(challenge["binding_before_sha256"], challenge["binding_after_sha256"])

    def test_malformed_json_challenge_retains_original_and_records_actual_byte_change(self):
        metadata = self.probe_metadata("probe-malformed-json-core", "malformed-json-core")
        run_root = self.root / "malformed-json-run"
        binding_path = run_root / "probe-binding.json"
        binding_path.parent.mkdir()
        binding = self.probe_binding(metadata)
        before = json.dumps(binding, indent=2).encode("utf-8")
        binding_path.write_bytes(before)
        probe_observation = run_root / "probe" / "observation.json"
        probe_observation.parent.mkdir()
        probe_observation.write_text(json.dumps({"probe_completion": "COMPLETE"}), encoding="utf-8")
        target_path = Path(metadata["target_paths"][-1])
        source_before = target_path.read_bytes()

        applied = self.calibrate.apply_challenge(metadata, run_root)

        after = binding_path.read_bytes()
        challenge = json.loads((run_root / "challenge.json").read_text(encoding="utf-8"))
        with self.assertRaises(json.JSONDecodeError):
            json.loads(after)
        self.assertTrue(after.endswith(b",\n}\n"))
        self.assertEqual((run_root / "probe-binding.before-challenge.json").read_bytes(), before)
        self.assertEqual(challenge["binding_before_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(challenge["binding_after_sha256"], hashlib.sha256(after).hexdigest())
        self.assertNotEqual(challenge["binding_before_sha256"], challenge["binding_after_sha256"])
        self.assertTrue(applied["applied"])
        self.assertEqual(target_path.read_bytes(), source_before)

    def test_probe_controls_do_not_apply_without_an_actual_completed_probe(self):
        for case_id, variant in (("probe-current-claim-core", "current-claim-core"),
                                 ("probe-malformed-json-core", "malformed-json-core")):
            with self.subTest(case_id=case_id):
                metadata = self.probe_metadata(case_id, variant)
                run_root = self.root / f"{case_id}-incomplete"
                binding_path = run_root / "probe-binding.json"
                binding_path.parent.mkdir()
                before = json.dumps(self.probe_binding(metadata), indent=2).encode("utf-8")
                binding_path.write_bytes(before)

                applied = self.calibrate.apply_challenge(metadata, run_root)

                self.assertFalse(applied["applied"])
                self.assertEqual(binding_path.read_bytes(), before)

    def test_natural_language_rebind_remains_a_stale_target_challenge(self):
        metadata = self.probe_metadata("probe-natural-language-rebind-holdout", "rebind-holdout")
        run_root = self.root / "natural-language-rebind-run"
        binding_path = run_root / "probe-binding.json"
        binding_path.parent.mkdir()
        binding_path.write_text(json.dumps(self.probe_binding(metadata)), encoding="utf-8")
        target_path = Path(metadata["target_paths"][-1])
        self.assertIn("revised-value", target_path.read_text(encoding="utf-8"))

        applied = self.calibrate.apply_challenge(metadata, run_root)

        self.assertTrue(applied["applied"])
        self.assertIn("next-value", target_path.read_text(encoding="utf-8"))



if __name__ == "__main__":
    unittest.main()
