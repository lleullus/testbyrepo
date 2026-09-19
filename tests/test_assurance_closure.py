import copy
import unittest

from assurance_support import AssuranceFixture, assurance


class ClosureTests(AssuranceFixture, unittest.TestCase):
    def test_failed_direct_readback_blocks_other_successes(self):
        activity, results = self.evidence()
        results[1]["outcome"] = "VIOLATED"
        self.assertIn("OBSERVATION_NOT_SATISFIED", self.closure(activity, results)["reasons"])

    def test_missing_result_is_not_removed_from_denominator(self):
        activity, results = self.evidence()
        self.assertIn("STARTED_RESULT_MISSING", self.closure(activity, results[:1])["reasons"])
        activity["started"] = activity["started"][:1]
        self.assertIn("REQUIRED_WORK_NOT_STARTED", self.closure(activity, results[:1])["reasons"])

    def test_result_cannot_be_reused_for_another_binding(self):
        activity, results = self.evidence()
        results[0]["binding"] = "bind-foreign"
        self.assertIn("RESULT_BINDING_MISMATCH", self.closure(activity, results)["reasons"])

    def test_duplicate_invocation_does_not_supply_two_results(self):
        activity, results = self.evidence()
        activity["started"][1]["invocation"] = activity["started"][0]["invocation"]
        self.assertIn("DUPLICATE_INVOCATION", self.closure(activity, results)["reasons"])

    def test_effect_unknown_blocks_even_when_checks_pass(self):
        activity, results = self.evidence()
        activity["effects"] = [{
            "id": "write",
            "owner": "native",
            "state": "UNKNOWN",
            "evidence": activity["evidence"],
        }]
        self.assertIn("UNSETTLED_EFFECT", self.closure(activity, results)["reasons"])

    def test_optional_started_lane_cannot_hide_a_material_finding(self):
        lane = {
            "id": "targeted",
            "surfaces": ["entry"],
            "required": True,
            "min_actions": 1,
            "budget": "one trace",
            "safety": "read-only",
        }
        optional = {**lane, "id": "scout", "required": False}
        self.baseline.update(
            surfaces=[{"id": "entry", "boundary": "actual CLI"}],
            lanes=[lane, optional],
            no_probe_reason=None,
        )
        self.seal()
        activity, results = self.evidence()
        trace = {
            "surface": "entry",
            "hypothesis": "alternate route uses old value",
            "initial_state": "same fixture",
            "trigger": "alternate CLI",
            "readback": "actual stdout",
            "evidence": activity["evidence"],
        }
        probe = {
            "schema": "iis-assurance-result/v2",
            "kind": "probe",
            "id": "targeted",
            "invocation": "probe-1",
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": activity["evidence"],
            "effects": [],
            "outcome": "NO_COUNTEREXAMPLE_WITHIN_BUDGET",
            "hypotheses": activity["evidence"],
            "actions": [trace],
            "findings": [],
        }
        results.append(probe)
        activity["started"].append({"kind": "probe", "id": "targeted", "invocation": "probe-1"})
        self.assertEqual(self.closure(activity, results)["status"], "EVIDENCE_COMPLETE")

        scout = copy.deepcopy(probe)
        scout.update(
            id="scout",
            invocation="probe-2",
            outcome="COUNTEREXAMPLE_FOUND",
            findings=[{
                "anchor": "The actual entry prints actual-value.",
                "materiality": "MATERIAL",
                "disposition": "OPEN",
                "evidence": activity["evidence"],
            }],
        )
        results.append(scout)
        activity["started"].append({"kind": "probe", "id": "scout", "invocation": "probe-2"})
        self.assertIn("UNRESOLVED_COUNTEREXAMPLE", self.closure(activity, results)["reasons"])

    def test_no_finding_requires_actual_assigned_surface_attempt(self):
        lane = {"surfaces": ["entry"], "min_actions": 1}
        hypothesis = self.fixed_bytes("probe/hypothesis.txt", b"try alternate entry\n")
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_ACTIONS"):
            assurance.check_probe(
                self.store,
                lane,
                {
                    "outcome": "NO_COUNTEREXAMPLE_WITHIN_BUDGET",
                    "hypotheses": [hypothesis],
                    "actions": [],
                    "findings": [],
                },
            )


if __name__ == "__main__":
    unittest.main()
