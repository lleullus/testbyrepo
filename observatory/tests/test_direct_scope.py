from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from iis_observatory.cli import main
from iis_observatory.model import Health, NextWorkKind
from iis_observatory.render import render_state
from iis_observatory.scanner import scan_repository


class DirectScopeFixtures:
    def __init__(self, root: Path) -> None:
        (root / ".git").mkdir(parents=True, exist_ok=True)
        self.root = root
        self.thesis = root / "docs/planning/product-thesis/member/THESIS-001.md"
        self.thesis.parent.mkdir(parents=True, exist_ok=True)
        self.thesis.write_text(
            "# Member Thesis\n\n"
            "## Required Outcomes / Means\n"
            "- Preserve member identity\n"
            "- Emit authoritative readback\n",
            encoding="utf-8",
        )

    def scope(self, slug: str = "member", status: str = "ready", *, outcome: str = "Preserve member identity.") -> Path:
        path = self.root / f"docs/planning/work/{slug}/SCOPE.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        source = {
            "snapshot": "snap-" + "a" * 32,
            "path": self.thesis.relative_to(self.root).as_posix(),
        }
        path.write_text(
            f"# {slug}\n"
            "Schema: iis-scope/v2\n"
            f"Project-Root: {self.root}\n"
            f"Status: {status}\n\n"
            "## Product Authority\n"
            "```iis-sources\n"
            + json.dumps([source], indent=2)
            + "\n```\n\n"
            "## Outcome\n"
            f"{outcome}\n\n"
            "## Acceptance\n"
            "Read the authoritative member result.\n\n"
            "## Open Decisions\n"
            "None\n",
            encoding="utf-8",
        )
        return path

    def legacy_ticket(self, status: str = "done") -> Path:
        path = self.root / "docs/planning/work/old/tickets/TICKET-001.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# TKT-001\nStatus: {status}\n", encoding="utf-8")
        return path


class DirectScopeScannerTests(unittest.TestCase):
    def test_ready_scope_is_current_without_inventing_delivery_stage(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            scope = fixture.scope()
            state = scan_repository(fixture.root)
            self.assertTrue(state.direct_scope_mode)
            self.assertEqual(state.current_scope.path, scope)
            self.assertEqual(state.current_scope.status, "ready")
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)
            self.assertEqual(state.health, Health.PLANNING)
            payload = state.to_dict()
            self.assertEqual(payload["scope"]["status"], "ready")
            self.assertEqual(payload["current"]["increment"], None)

    def test_done_scope_with_remaining_thesis_outcome_points_to_new_scope(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope(status="done")
            state = scan_repository(fixture.root)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual({item["status"] for item in state.remaining_required_outcomes}, {"unassessed"})
            self.assertEqual(state.next_work.kind, NextWorkKind.SCOPE_SHAPER)
            self.assertEqual(state.next_work.leaf, "Scope Shaper")

    def test_old_history_and_new_scope_do_not_reactivate_legacy_ticket(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            old = fixture.legacy_ticket("ready")
            state = scan_repository(fixture.root)
            self.assertTrue(state.direct_scope_mode)
            self.assertIsNone(state.current_spec)
            self.assertEqual(state.tickets, [])
            self.assertIn(old, [item.path for item in state.legacy_history])
            self.assertIn(old, [item.path for item in state.transition_required])
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)
            self.assertIn("Legacy History (read-only)", render_state(state))
            self.assertIn("Transition Required:", render_state(state))

    def test_legacy_incomplete_work_requires_explicit_transition(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            old = fixture.legacy_ticket("ready")
            state = scan_repository(fixture.root)
            self.assertFalse(state.direct_scope_mode)
            self.assertEqual(state.health, Health.STALE)
            self.assertEqual(state.next_work.kind, NextWorkKind.TRANSITION_REQUIRED)
            self.assertIn(old, [item.path for item in state.transition_required])
            self.assertNotIn("Ask Matt", render_state(state))
            self.assertNotIn("TKT-001 구현", render_state(state))

    def test_live_thesis_change_does_not_fake_fixed_source_currentness(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            fixture.thesis.write_text("# Changed Thesis\n", encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                code = main(["scan", str(fixture.root), "--fail-on-inconsistent"])
            self.assertEqual(code, 0)
            self.assertNotIn("IIS513", output.getvalue())
            self.assertIn("admission", output.getvalue().lower())

    def test_duplicate_active_scope_is_reported_by_doctor_command(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope("one", "ready")
            fixture.scope("two", "draft")
            output = StringIO()
            with redirect_stdout(output):
                code = main(["doctor", str(fixture.root)])
            self.assertEqual(code, 3)
            self.assertIn("IIS502", output.getvalue())

    def test_json_keeps_direct_scope_and_legacy_history_separate(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            fixture.legacy_ticket("done")
            output = StringIO()
            with redirect_stdout(output):
                code = main(["scan", str(fixture.root), "--format", "json"])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["authority_mode"], "direct-scope")
            self.assertEqual(payload["scope"]["status"], "ready")
            self.assertTrue(payload["legacy"]["history"])
            self.assertFalse(payload["legacy"]["automatic_migration"])


if __name__ == "__main__":
    unittest.main()
