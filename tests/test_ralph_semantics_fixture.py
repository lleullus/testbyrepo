from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class RalphSemanticsFixtureTests(unittest.TestCase):
    """Exercise the desired loop semantics without claiming agent/leaf execution."""

    def test_same_delivery_unit_repeats_until_all_current_acceptance_rows_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            product = Path(temporary) / "product-state.json"
            product.write_text(
                json.dumps({"outcome_1": False, "outcome_2": False}, sort_keys=True),
                encoding="utf-8",
            )

            def observe() -> tuple[bool, bool]:
                state = json.loads(product.read_text(encoding="utf-8"))
                return state["outcome_1"], state["outcome_2"]

            def bounded_correction(outcome: str) -> None:
                state = json.loads(product.read_text(encoding="utf-8"))
                state[outcome] = True
                product.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

            initial = observe()
            self.assertEqual(initial, (False, False))

            # First implementation iteration on the same conceptual Ticket.
            bounded_correction("outcome_1")
            after_first = observe()
            self.assertEqual(after_first, (True, False))
            self.assertFalse(all(after_first), "partial improvement must not complete the Goal")

            # A newly exposed defect remains the same delivery unit, not a new Goal.
            bounded_correction("outcome_2")
            after_second = observe()
            self.assertEqual(after_second, (True, True))

            # Final completion is derived from a new read, not the implementation narration.
            fresh_final = observe()
            self.assertTrue(all(fresh_final))

    def test_regression_after_a_correction_returns_the_same_goal_to_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            product = Path(temporary) / "product-state.json"
            product.write_text(
                json.dumps({"owned": True, "preserved": True}, sort_keys=True),
                encoding="utf-8",
            )

            def observe() -> dict[str, bool]:
                return json.loads(product.read_text(encoding="utf-8"))

            state = observe()
            state["owned"] = True
            state["preserved"] = False
            product.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

            current = observe()
            self.assertTrue(current["owned"])
            self.assertFalse(current["preserved"])
            self.assertFalse(all(current.values()), "a preserved-Behavior regression keeps the Goal open")


if __name__ == "__main__":
    unittest.main()
