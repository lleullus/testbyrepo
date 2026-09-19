import json
import unittest

from assurance_support import AssuranceFixture, assurance


class BaselineTests(AssuranceFixture, unittest.TestCase):
    def test_unmapped_authored_acceptance_is_rejected(self):
        self.baseline["obligations"] = []
        with self.assertRaisesRegex(ValueError, "ACCEPTANCE_COVERAGE_MISMATCH"):
            assurance.validate_baseline(self.baseline)

    def test_surface_cannot_be_assigned_only_to_optional_lane(self):
        self.baseline.update(surfaces=[{"id": "entry", "boundary": "actual CLI"}], lanes=[{"id": "scout", "surfaces": ["entry"], "required": False, "min_actions": 1, "budget": "one trace", "safety": "read-only"}], no_probe_reason=None)
        with self.assertRaisesRegex(ValueError, "UNASSIGNED_SURFACE"):
            assurance.validate_baseline(self.baseline)

    def test_uncommitted_target_is_not_labeled_as_head(self):
        self.command.write_text("print('different')\n")
        self.baseline["gates"][0]["mechanisms"] = [assurance.file_ref(self.command)]
        self.execution["mechanisms"] = [assurance.file_ref(self.command)]
        with self.assertRaisesRegex(ValueError, "TARGET_NOT_SEALED"):
            self.seal()

    def test_exact_plan_block_is_usable_without_hash_self_reference(self):
        plan = self.arena / "PLAN.md"
        block = json.dumps(self.baseline) + "\n"
        plan.write_text("# Method\n\n## Assurance Baseline\n```iis-assurance\n" + block + "```\n")
        parsed, raw = assurance.load_baseline(plan)
        self.assertEqual(parsed, self.baseline)
        self.assertEqual(raw, block.encode())

    def test_status_recording_rejects_acceptance_change(self):
        ready = self.scope.read_bytes()
        done = ready.replace(b"Status: ready", b"Status: done")
        self.assertTrue(assurance.recording(ready, done)["status_only"])
        with self.assertRaisesRegex(ValueError, "NOT_STATUS_ONLY"):
            assurance.recording(ready, done.replace(b"actual-value", b"wrong-value"))
