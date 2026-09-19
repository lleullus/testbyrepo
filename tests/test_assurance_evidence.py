import json
import sys
import unittest

from assurance_support import AssuranceFixture, assurance


class EvidenceTests(AssuranceFixture, unittest.TestCase):
    def test_actual_native_output_supports_artifact_control(self):
        activity, results = self.evidence()
        self.assertEqual((self.arena / "native-capture/stdout").read_text(), "actual-value\n")
        self.assertEqual(self.closure(activity, results)["status"], "EVIDENCE_COMPLETE")

    def test_success_boolean_without_native_capture_is_not_evidence(self):
        activity, results = self.evidence()
        results[0].pop("capture")
        results[0]["gate_passed"] = True
        self.assertEqual(self.closure(activity, results)["status"], "BLOCKED")

    def test_raw_output_changed_after_run_blocks_closure(self):
        activity, results = self.evidence()
        (self.arena / "native-capture/stdout").write_text("forged\n")
        self.assertEqual(self.closure(activity, results)["status"], "BLOCKED")

    def test_zero_exit_does_not_hide_skipped_required_job(self):
        jobs = self.arena / "jobs.json"
        self.baseline["gates"][0].update(jobs=["integration"], jobs_path=str(jobs))
        self.seal()
        jobs.write_text(json.dumps({"run_id": self.binding["run_id"], "gate_id": "native", "jobs": {"integration": "SKIPPED"}}))
        activity, results = self.evidence()
        self.assertIn("REQUIRED_JOB_NOT_SUCCESSFUL", self.closure(activity, results)["reasons"])

    def test_nonzero_native_command_blocks_closure(self):
        self.baseline["gates"][0]["argv"] = [sys.executable, "-B", "-c", "raise SystemExit(7)"]
        self.seal()
        activity, results = self.evidence()
        self.assertEqual(results[0]["capture"]["returncode"], 7)
        self.assertIn("GATE_FAILED", self.closure(activity, results)["reasons"])

    def test_runtime_identity_drift_invalidates_existing_results(self):
        runtime = self.arena / "runtime.json"
        runtime.write_text('{"instance":"a"}')
        self.execution["runtime"] = [assurance.file_ref(runtime)]
        self.seal()
        activity, results = self.evidence()
        runtime.write_text('{"instance":"b"}')
        self.assertEqual(self.closure(activity, results)["status"], "BLOCKED")
