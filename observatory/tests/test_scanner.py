from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from test_direct_scope import DirectScopeFixtures
from iis_observatory.model import Health, NextWorkKind
from iis_observatory.scanner import scan_repository


class ScannerTests(unittest.TestCase):
    def test_ready_scope_and_plan_presence_do_not_establish_delivery_stage(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            scope = fixture.scope()
            (scope.parent / "PLAN.md").write_text("# Existing method\n")
            state = scan_repository(fixture.root)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)
            self.assertEqual(state.current_scope.status, "ready")
            self.assertIsNone(state.current_increment)

    def test_draft_direct_scope_points_to_scope_shaper(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope(status="draft")
            state = scan_repository(fixture.root)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual(state.next_work.kind, NextWorkKind.SCOPE_SHAPER)

    def test_excluded_outcome_text_does_not_establish_fulfillment(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope(
                status="done",
                outcome="Excluded: Preserve member identity and Emit authoritative readback.",
            )
            state = scan_repository(fixture.root)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual({item["text"] for item in state.remaining_required_outcomes},
                             {"Preserve member identity", "Emit authoritative readback"})
            self.assertTrue(all(item["status"] == "unassessed" for item in state.remaining_required_outcomes))
            self.assertEqual(state.next_work.kind, NextWorkKind.SCOPE_SHAPER)

    def test_legacy_only_repository_is_stale_and_needs_transition(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.legacy_ticket("ready")
            state = scan_repository(fixture.root)
            self.assertEqual(state.health, Health.STALE)
            self.assertEqual(state.next_work.kind, NextWorkKind.TRANSITION_REQUIRED)
            self.assertFalse(state.direct_scope_mode)
            self.assertEqual(state.tickets, [])

    def test_completed_legacy_history_does_not_request_migration(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.legacy_ticket("done")
            state = scan_repository(fixture.root)
            self.assertEqual(state.transition_required, [])
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)

    def test_repository_without_planning_is_no_iis(self) -> None:
        with TemporaryDirectory() as temp:
            state = scan_repository(Path(temp) / "missing")
            self.assertEqual(state.health, Health.NO_IIS)


if __name__ == "__main__":
    unittest.main()
