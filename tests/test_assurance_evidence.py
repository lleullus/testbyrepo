import json
import sys
import unittest

from assurance_support import AssuranceFixture, assurance


class EvidenceTests(AssuranceFixture, unittest.TestCase):
    def test_actual_native_output_supports_artifact_control(self):
        activity, results = self.evidence()
        output_ref = results[0]["capture"]["stdout"]
        self.assertEqual(self.store.read_bytes(output_ref), b"actual-value\n")
        self.assertEqual(self.closure(activity, results)["status"], "EVIDENCE_COMPLETE")

    def test_success_boolean_without_native_capture_is_not_evidence(self):
        activity, results = self.evidence()
        results[0].pop("capture")
        results[0]["gate_passed"] = True
        self.assertEqual(self.closure(activity, results)["status"], "BLOCKED")

    def test_live_output_file_edit_does_not_rewrite_executor_owned_evidence(self):
        activity, results = self.evidence()
        live = next(self.arena.glob("native-capture-*/stdout"))
        live.write_text("forged\n")
        self.assertEqual(self.store.read_bytes(results[0]["capture"]["stdout"]), b"actual-value\n")
        self.assertEqual(self.closure(activity, results)["status"], "EVIDENCE_COMPLETE")

    def test_zero_exit_does_not_hide_skipped_required_job(self):
        jobs = self.arena / "jobs.json"
        self.baseline["gates"][0].update(jobs=["integration"], jobs_path=str(jobs))
        self.seal()
        jobs.write_text(json.dumps({
            "run_id": self.binding["run_id"],
            "gate_id": "native",
            "jobs": {"integration": "SKIPPED"},
        }))
        activity, results = self.evidence()
        self.assertIn("REQUIRED_JOB_NOT_SUCCESSFUL", self.closure(activity, results)["reasons"])

    def test_nonzero_native_command_blocks_closure(self):
        self.baseline["gates"][0]["argv"] = [sys.executable, "-B", "-c", "raise SystemExit(7)"]
        self.seal()
        activity, results = self.evidence()
        self.assertEqual(results[0]["capture"]["returncode"], 7)
        self.assertIn("GATE_FAILED", self.closure(activity, results)["reasons"])

    def test_new_runtime_capture_requires_new_binding_identity(self):
        runtime = self.arena / "runtime.json"
        runtime.write_text('{"instance":"a"}')
        old_ref = self.fixed_bytes("runtime/current.json", runtime.read_bytes(), kind="source")
        self.execution["runtime"] = [old_ref]
        self.seal()
        old_binding = self.binding["binding_id"]
        runtime.write_text('{"instance":"b"}')
        new_ref = self.fixed_bytes("runtime/new.json", runtime.read_bytes(), kind="source")
        self.execution["runtime"] = [new_ref]
        self.seal()
        self.assertNotEqual(self.binding["binding_id"], old_binding)
        self.assertEqual(self.store.read_bytes(old_ref), b'{"instance":"a"}')


if __name__ == "__main__":
    unittest.main()
