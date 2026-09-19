import json
import unittest

from assurance_support import AssuranceFixture, assurance


class BaselineTests(AssuranceFixture, unittest.TestCase):
    def test_unmapped_authored_acceptance_is_rejected(self):
        self.baseline["obligations"] = []
        with self.assertRaisesRegex(ValueError, "ACCEPTANCE_COVERAGE_MISMATCH"):
            assurance.validate_baseline(self.baseline, self.store)

    def test_surface_cannot_be_assigned_only_to_optional_lane(self):
        self.baseline.update(
            surfaces=[{"id": "entry", "boundary": "actual CLI"}],
            lanes=[{
                "id": "scout",
                "surfaces": ["entry"],
                "required": False,
                "min_actions": 1,
                "budget": "one trace",
                "safety": "read-only",
            }],
            no_probe_reason=None,
        )
        with self.assertRaisesRegex(ValueError, "UNASSIGNED_SURFACE"):
            assurance.validate_baseline(self.baseline, self.store)

    def test_assurance_binding_requires_registered_host_admission(self):
        with self.store.connect() as db:
            db.execute("DELETE FROM admissions")
        with self.assertRaisesRegex(Exception, "HOST_ADMISSION_REQUIRED"):
            assurance.bind(self.baseline_path, self.store, self.root, self.execution)

    def test_dirty_working_source_can_bind_but_later_drift_blocks(self):
        self.command.write_text("print('captured-value')\n", encoding="utf-8")
        command_snapshot = self.store.capture_files(self.root, [self.command], kind="source")
        self.command_ref = {"snapshot": command_snapshot, "path": "main.py"}
        self.baseline["gates"][0]["mechanisms"] = [self.command_ref]
        self.execution["mechanisms"] = [self.command_ref]
        self.seal()
        self.command.write_text("print('different-after-bind')\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "TARGET_DRIFT"):
            assurance.current(self.baseline_path, self.store, self.binding)

    def test_binding_dict_cannot_be_rewritten_as_a_new_execution(self):
        forged = dict(self.binding)
        forged["run_id"] = "run-forged"
        with self.assertRaisesRegex(ValueError, "BINDING_RECORD_MISMATCH"):
            assurance.current(self.baseline_path, self.store, forged)

    def test_exact_plan_block_is_usable_without_self_identity_field(self):
        plan = self.arena / "PLAN.md"
        block = json.dumps(self.baseline) + "\n"
        plan.write_text("# Method\n\n## Assurance Baseline\n```iis-assurance\n" + block + "```\n")
        parsed, raw = assurance.load_baseline(plan, self.store)
        self.assertEqual(parsed, self.baseline)
        self.assertEqual(raw, block.encode())

    def test_status_recording_rejects_acceptance_change(self):
        ready = self.scope.read_bytes()
        done = ready.replace(b"Status: ready", b"Status: done")
        self.assertTrue(assurance.recording(ready, done)["status_only"])
        with self.assertRaisesRegex(ValueError, "NOT_STATUS_ONLY"):
            assurance.recording(ready, done.replace(b"actual-value", b"wrong-value"))


if __name__ == "__main__":
    unittest.main()
