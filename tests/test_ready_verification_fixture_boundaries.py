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
BOUNDARY_MODULE = ROOT / "delivery-tools/ready-ticket/src/core.js"
CALIBRATE = ROOT / "evaluation/ready-verification/calibrate.py"


def load_catalog():
    spec = importlib.util.spec_from_file_location("calibration_fixture_boundaries", CATALOG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_calibrate():
    sys.path.insert(0, str(CATALOG.parent))
    try:
        spec = importlib.util.spec_from_file_location("calibration_verification_challenges", CALIBRATE)
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
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const module = await import(process.argv[1]);
const metadata = JSON.parse(process.argv[2]);
const executeArgv = async (argv, options) => {
  const result = await promisify(execFile)(argv[0], argv.slice(1), {cwd: options.cwd});
  return {...result, exitCode: 0, interrupted: false, terminationState: 'settled'};
};
const captured = await module.captureVerification({projectRoot: metadata.project_root,
    ticketPath: metadata.ticket_path, stableTargetPaths: metadata.target_paths,
    bindingPath: process.argv[3], executeArgv});
fs.appendFileSync(metadata.target_paths.at(-1), '\\n# Changed product source.\\n');
console.log(JSON.stringify(await module.checkVerificationCurrentness(captured.binding)));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", program, BOUNDARY_MODULE.as_uri(), json.dumps(metadata), str(self.root / "binding.json")],
            cwd=project, env=self.environment, check=True, text=True, capture_output=True,
        )
        observed = json.loads(result.stdout)
        self.assertFalse(observed["current"])
        self.assertIn("engine.py", observed["stable_target_changed"])

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

    def test_external_drift_requires_successful_bound_event_and_preserves_attribution(self):
        metadata = self.catalog.materialize(
            {"family": "verification-drift", "variant": "target", "case_id": "verification-target-drift-core"},
            self.root / "product", self.root / "support", port=12345)
        metadata["case_id"] = "verification-target-drift-core"
        run_root = self.root / "run"
        run_root.mkdir()
        prompt = self.calibrate.stage_prompt("verify", metadata, run_root)
        self.assertNotIn("verification-target-drift-core", prompt)
        self.assertNotIn("next-value", prompt)
        target = Path(metadata["target_paths"][-1])
        before = target.read_bytes()
        call = {"type": "tool_execution_start", "toolCallId": "bind", "toolName": "ready_contract", "args": {"action": "capture_verification"}}
        details = {"binding_path": str(self.root / "captured-binding.json"), "binding_sha256": "a" * 64,
                   "binding": {"stable_target_paths": metadata["target_paths"]}}
        rejected = {"type": "tool_execution_end", "toolCallId": "bind", "isError": True, "result": {"details": details}}
        self.assertIsNone(self.calibrate.apply_challenge(metadata, run_root, [call, rejected]))
        self.assertEqual(target.read_bytes(), before)
        accepted = {**rejected, "isError": False}
        result = self.calibrate.apply_challenge(metadata, run_root, [call, accepted])
        self.assertTrue(result["applied"])
        self.assertIn("next-value", target.read_text())
        self.assertEqual(result["before"][str(target)], hashlib.sha256(before).hexdigest())
        self.assertIsNone(self.calibrate.apply_challenge(metadata, run_root, [call, accepted]))

    def test_stable_target_drift_after_capture_blocks_verified_status_progression(self):
        metadata = self.catalog.materialize(
            {"family": "runtime-correct", "variant": "core"},
            self.root / "product", self.root / "support", port=12345,
        )
        program = """
import fs from 'node:fs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const module = await import(process.argv[1]);
const metadata = JSON.parse(process.argv[2]);
const executeArgv = async (argv, options) => {
  try {
    const result = await promisify(execFile)(argv[0], argv.slice(1), {cwd: options.cwd, timeout: options.timeout});
    return {...result, exitCode: 0, interrupted: false, terminationState: 'settled'};
  } catch (error) {
    return {exitCode: typeof error.code === 'number' ? error.code : null, interrupted: !!error.killed,
            terminationState: error.killed ? 'unknown' : 'settled', stdout: error.stdout || '', stderr: error.stderr || error.message};
  }
};
const captured = await module.captureVerification({projectRoot: metadata.project_root,
    ticketPath: metadata.ticket_path, stableTargetPaths: metadata.target_paths,
    bindingPath: process.argv[3], executeArgv});
const verifierTerminal = {schema: 'iis-ready-host-terminal/v1', handle: 'drift-terminal',
    owner_id: 'Verifier', verifier_model: 'test/verifier', project_root: captured.binding.project_root,
    ticket_path: captured.binding.ticket_path, verification_binding: captured.binding_path,
    verification_binding_sha256: captured.binding_sha256,
    stable_target_paths: captured.binding.stable_target_paths,
    scenario_effect_paths: captured.binding.scenario_effect_paths,
    verification_verdict: 'VERIFIED', ticket_progression: 'PENDING CALLER FINALIZATION',
    observed_ticket_status: 'ready'};
fs.appendFileSync(metadata.target_paths.at(-1), '\\n# evaluator drift after immutable capture\\n');
const result = await module.finalizeVerification({acceptedTerminal: verifierTerminal,
    bundleIdentity: captured.binding.bundle_identity, executeArgv});
console.log(JSON.stringify(result));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", program, BOUNDARY_MODULE.as_uri(), json.dumps(metadata),
             str(self.root / "drift-binding.json")],
            cwd=metadata["project_root"], env=self.environment, check=False, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed["verification_verdict"], "VERIFIED")
        self.assertEqual(observed["ticket_progression"], "FAILED")
        self.assertEqual(observed["ticket_status_after"], "ready")
        self.assertIn("verification target/authority changed", observed["progression_detail"])


if __name__ == "__main__":
    unittest.main()
