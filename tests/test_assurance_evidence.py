import json
import sys
import subprocess
import unittest

from assurance_support import AssuranceFixture, assurance


class EvidenceTests(AssuranceFixture, unittest.TestCase):
    def test_native_gate_executes_captured_source_copy(self):
        gate, _obs = self.evidence()
        capture = gate["capture"]
        self.assertTrue(capture["executed_cwd"].startswith(self.binding["execution_root"]))
        self.assertIn(self.binding["execution_root"], " ".join(capture["executed_argv"]))
        self.assertEqual(self.store.read_bytes(capture["stdout"]), b"actual-value\n")
        self.assertEqual(self.closure()["status"], "EVIDENCE_COMPLETE")

    def test_live_source_change_and_restore_during_gate_cannot_change_executed_bytes(self):
        original = self.command.read_bytes()

        def runner(argv, cwd, env, timeout):
            self.command.write_text("print('live-attack')\n", encoding="utf-8")
            try:
                completed = subprocess.run(
                    argv,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    check=False,
                )
                return completed.returncode, completed.stdout, completed.stderr, None
            finally:
                self.command.write_bytes(original)

        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
            runner=runner,
        )
        self.observation()
        self.assertEqual(self.store.read_bytes(gate["capture"]["stdout"]), b"actual-value\n")
        self.assertEqual(self.closure()["status"], "EVIDENCE_COMPLETE")

    def test_live_output_file_edit_does_not_rewrite_executor_owned_evidence(self):
        gate, _obs = self.evidence()
        live = next(self.arena.glob("native-capture-*/stdout"))
        live.write_text("forged\n")
        self.assertEqual(self.store.read_bytes(gate["capture"]["stdout"]), b"actual-value\n")
        self.assertEqual(self.closure()["status"], "EVIDENCE_COMPLETE")

    def test_evidence_from_another_invocation_cannot_be_relabelled(self):
        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        invocation = assurance.begin_host_invocation(self.store, self.binding, "observation", "readback")
        forged = {
            "schema": "iis-assurance-result/v3",
            "kind": "observation",
            **self.baseline["observations"][0],
            "invocation": invocation,
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": gate["evidence"],
            "effects": [],
            "outcome": "SATISFIED",
        }
        with self.assertRaisesRegex(Exception, "EVIDENCE_INVOCATION_MISMATCH"):
            assurance.complete_host_invocation(self.store, self.binding, invocation, forged)

    def test_evidence_from_another_run_cannot_be_relabelled(self):
        invocation = assurance.begin_host_invocation(self.store, self.binding, "observation", "readback")
        foreign = self.fixed_bytes(
            "foreign/readback.txt",
            b"actual-value\n",
            invocation=invocation,
            run_id="run-foreign",
        )
        forged = {
            "schema": "iis-assurance-result/v3",
            "kind": "observation",
            **self.baseline["observations"][0],
            "invocation": invocation,
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": [foreign],
            "effects": [],
            "outcome": "SATISFIED",
        }
        with self.assertRaisesRegex(Exception, "EVIDENCE_RUN_MISMATCH"):
            assurance.complete_host_invocation(self.store, self.binding, invocation, forged)

    def test_zero_exit_does_not_hide_skipped_required_job(self):
        jobs = self.arena / "jobs.json"
        self.baseline["gates"][0].update(jobs=["integration"], jobs_path=str(jobs))
        self.baseline["gates"][0]["argv"] = [sys.executable, "-B", "-c",
            "import os,json; from pathlib import Path; "
            "Path(os.environ['IIS_ASSURANCE_JOBS_PATH']).write_text(json.dumps({"
            "'run_id':os.environ['IIS_ASSURANCE_RUN_ID'],'gate_id':os.environ['IIS_ASSURANCE_GATE_ID'],"
            "'invocation_id':os.environ['IIS_ASSURANCE_INVOCATION_ID'],'jobs':{'integration':'SKIPPED'}}))"]
        self.seal()
        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        self.observation()
        self.assertEqual(gate["capture"]["returncode"], 0)
        self.assertIn("REQUIRED_JOB_NOT_SUCCESSFUL", self.closure()["reasons"])

    def test_nonzero_native_command_blocks_closure(self):
        self.baseline["gates"][0]["argv"] = [sys.executable, "-B", "-c", "raise SystemExit(7)"]
        self.seal()
        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        self.observation()
        self.assertEqual(gate["capture"]["returncode"], 7)
        self.assertIn("GATE_FAILED", self.closure()["reasons"])

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
