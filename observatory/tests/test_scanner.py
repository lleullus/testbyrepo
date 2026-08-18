from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from helpers import RepoBuilder
from iis_observatory.model import Health, NextWorkKind, Stage
from iis_observatory.render import render_state
from iis_observatory.scanner import scan_repository


class ScannerTests(unittest.TestCase):
    def test_ready_ticket_is_next_delivery_work(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "tax")
            builder.scope("INC-004", "vat-readback", "WP-002")
            builder.spec("vat-readback", source_increment="INC-004")
            for number in (1, 2, 3):
                builder.ticket(number, "done", slug="vat-readback", source_increment="INC-004")
            builder.ticket(4, "ready", slug="vat-readback", source_increment="INC-004")
            builder.ticket(5, "ready", slug="vat-readback", source_increment="INC-004")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.READY)
            self.assertEqual(state.stage, Stage.DELIVERY)
            self.assertEqual(state.current_increment.identifier, "INC-004")
            self.assertEqual(state.current_work_package.identifier, "WP-002")
            self.assertEqual(state.ticket_counts["done"], 3)
            self.assertEqual(state.ticket_counts["total"], 5)
            self.assertEqual(state.next_work.kind, NextWorkKind.TICKET_IMPLEMENT)
            self.assertEqual(state.next_work.target_id, "TKT-004")
            self.assertEqual(state.next_work.leaf, "delivery outside IIS")
            self.assertIn("Derived Delivery State: READY", render_state(state, color=False))

    def test_blocked_ticket_has_precedence_over_ready_ticket(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "watcher")
            builder.scope("INC-007", "release-alert", "WP-002")
            builder.spec("release-alert", source_increment="INC-007")
            builder.ticket(1, "ready", slug="release-alert", source_increment="INC-007")
            builder.ticket(3, "blocked", slug="release-alert", source_increment="INC-007")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.BLOCKED)
            self.assertEqual(state.next_work.kind, NextWorkKind.TICKET_UNBLOCK)
            self.assertEqual(state.next_work.target_id, "TKT-003")
            self.assertIn("Derived Delivery State: BLOCKED", render_state(state, color=False))

    def test_increment_without_spec_points_to_ask_matt(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "ima2")
            builder.scope("INC-012", "job-inspection", "WP-003")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual(state.next_work.kind, NextWorkKind.ASK_MATT)
            self.assertEqual(state.next_work.target_id, "INC-012")
            self.assertNotIn("Derived Delivery State:", render_state(state, color=False))

    def test_approved_spec_without_tickets_points_to_to_tickets(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope()
            builder.spec()

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.PLANNING)
            self.assertEqual(state.next_work.kind, NextWorkKind.TO_TICKETS)

    def test_draft_spec_points_to_to_spec(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope()
            builder.spec(status="draft")

            state = scan_repository(builder.repo)
            self.assertEqual(state.next_work.kind, NextWorkKind.TO_SPEC)

    def test_scope_without_increment_needs_scope(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "oracle")
            builder.scope(increment=None, slug=None, work_package="WP-003")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.NEEDS_SCOPE)
            self.assertEqual(state.stage, Stage.SHAPING)
            self.assertEqual(state.next_work.kind, NextWorkKind.SCOPE_SHAPER)

    def test_all_tickets_done_is_complete(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "legacy")
            builder.scope("INC-002", "cleanup")
            builder.spec("cleanup", source_increment="INC-002")
            builder.ticket(1, "done", slug="cleanup", source_increment="INC-002")
            builder.ticket(2, "done", slug="cleanup", source_increment="INC-002")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.COMPLETE)
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)

    def test_all_done_reports_authored_expansion_candidates_without_choosing_one(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "initiative")
            builder.scope("INC-004", "current-work", "WP-001")
            builder.write(
                "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
                """
# Scope Shaping Result
Status: confirmed
Work-Package: WP-001
Selected-Increment: INC-004
Suggested-Work-Slug: current-work

## Outcome Horizon

### Foundation
- WP-001

### Expansion
- WP-003
- WP-002

### Deferred
- WP-004
""",
            )
            for identifier, title in (
                ("WP-002", "Curated Explorer"),
                ("WP-003", "Automatic Collection"),
                ("WP-004", "Source-missing Reconciliation"),
            ):
                builder.write(
                    f"docs/planning/scope-shaping/current/work-packages/{identifier}.md",
                    f"""
# {identifier}: {title}
Status: scoped
Work-Package: {identifier}
""",
                )
            builder.spec("current-work", source_increment="INC-004")
            builder.ticket(1, "done", slug="current-work", source_increment="INC-004")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.COMPLETE)
            self.assertEqual(state.stage, Stage.COMPLETE)
            self.assertEqual(state.next_work.kind, NextWorkKind.SCOPE_SHAPER)
            self.assertEqual(state.next_work.leaf, "Scope Shaper")
            self.assertEqual(
                [item.identifier for item in state.next_candidate_work_packages],
                ["WP-003", "WP-002"],
            )
            self.assertEqual(
                [item.identifier for item in state.deferred_work_packages],
                ["WP-004"],
            )
            output = render_state(state, color=False)
            self.assertIn("Derived Delivery State: COMPLETE", output)
            self.assertIn("Next candidate Work Packages:", output)
            self.assertIn("- WP-003: Automatic Collection", output)
            self.assertIn("- WP-002: Curated Explorer", output)
            self.assertIn("Deferred:", output)
            self.assertIn("- WP-004: Source-missing Reconciliation", output)
            self.assertIn("Next Increment: not yet shaped", output)
            self.assertIn("Next Work: 다음 Increment 선택", output)
            self.assertIn("Next leaf: Scope Shaper", output)

    def test_deferred_only_does_not_become_next_candidate(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "deferred-only")
            builder.scope("INC-001", "current-work", "WP-001")
            builder.write(
                "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
                """
# Scope Shaping Result
Status: confirmed
Work-Package: WP-001
Selected-Increment: INC-001
Suggested-Work-Slug: current-work

## Outcome Horizon

### Foundation
- WP-001

### Deferred
- WP-004
""",
            )
            builder.write(
                "docs/planning/scope-shaping/current/work-packages/WP-004.md",
                """
# WP-004: Deferred Reconciliation
Status: scoped
Work-Package: WP-004
""",
            )
            builder.spec("current-work", source_increment="INC-001")
            builder.ticket(1, "done", slug="current-work", source_increment="INC-001")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.COMPLETE)
            self.assertEqual(state.next_work.kind, NextWorkKind.NONE)
            self.assertEqual(state.next_candidate_work_packages, [])
            self.assertEqual([item.identifier for item in state.deferred_work_packages], ["WP-004"])
            output = render_state(state, color=False)
            self.assertIn("Deferred:", output)
            self.assertNotIn("Next Increment: not yet shaped", output)
            self.assertIn("Next Work: 다음 단위 없음", output)

    def test_missing_selected_increment_is_inconsistent(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.write(
                "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
                """
# Scope
Status: confirmed
Selected-Increment: INC-999
""",
            )
            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.INCONSISTENT)
            self.assertTrue(any(issue.code == "IIS101" for issue in state.issues))
            self.assertEqual(state.next_work.kind, NextWorkKind.CONSISTENCY_CHECK)

    def test_multiple_ready_increments_are_inconsistent(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope("INC-001", "demo")
            builder.increment("INC-002", slug="second")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.INCONSISTENT)
            self.assertTrue(any(issue.code == "IIS102" for issue in state.issues))

    def test_ready_increments_in_other_scope_lineages_do_not_conflict(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.write(
                "docs/planning/scope-shaping/historical/SCOPE-SHAPING-RESULT.md",
                """
# Historical Scope
Status: approved
Selected-Increment: INC-001
Suggested-Work-Slug: historical-work
""",
            )
            builder.write(
                "docs/planning/scope-shaping/historical/increments/INC-001.md",
                """
# INC-001 Historical Increment
Status: ready-for-matt
Suggested-Work-Slug: historical-work
""",
            )
            builder.scope("INC-004", "current-work")
            builder.spec("current-work", source_increment="INC-004")
            builder.ticket(1, "ready", slug="current-work", source_increment="INC-004")

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.READY)
            self.assertEqual(state.current_increment.identifier, "INC-004")
            self.assertFalse(any(issue.code == "IIS102" for issue in state.issues))

    def test_duplicate_increment_ids_in_other_lineages_do_not_cross_associate_work(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope("INC-001", "current-work")
            builder.spec("current-work", source_increment="INC-001")
            builder.ticket(1, "ready", slug="current-work", source_increment="INC-001")
            builder.write(
                "docs/planning/scope-shaping/historical/SCOPE-SHAPING-RESULT.md",
                """
# Historical Scope
Status: approved
Selected-Increment: INC-001
Suggested-Work-Slug: historical-work
""",
            )
            builder.write(
                "docs/planning/scope-shaping/historical/increments/INC-001.md",
                """
# INC-001 Historical Increment
Status: ready-for-matt
Suggested-Work-Slug: historical-work
""",
            )
            builder.spec("historical-work", source_increment="INC-001")
            builder.ticket(1, "done", slug="historical-work", source_increment="INC-001")

            state = scan_repository(builder.repo)
            self.assertIn("scope-shaping/current/", state.current_increment.relative_path)
            self.assertEqual(state.current_work_slug, "current-work")
            self.assertEqual(state.current_spec.work_slug, "current-work")
            self.assertEqual(state.ticket_counts["total"], 1)
            self.assertEqual(state.ticket_counts["ready"], 1)
            self.assertEqual(state.health, Health.READY)

    def test_missing_ticket_status_is_inconsistent(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope()
            builder.spec()
            builder.ticket(1, "", include_status=False)

            state = scan_repository(builder.repo)
            self.assertEqual(state.health, Health.INCONSISTENT)
            self.assertTrue(any(issue.code == "IIS201" for issue in state.issues))

    def test_direct_work_without_increment_is_supported(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "direct")
            builder.spec("direct-work", source_increment=None)
            builder.ticket(1, "ready", slug="direct-work", source_increment=None)

            state = scan_repository(builder.repo)
            self.assertEqual(state.current_work_slug, "direct-work")
            self.assertIsNone(state.current_increment)
            self.assertEqual(state.health, Health.READY)
            self.assertEqual(state.next_work.target_id, "TKT-001")

    def test_broken_local_markdown_link_is_warning_not_error(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope()
            builder.spec()
            builder.write(
                "docs/planning/work/demo-work/notes.md",
                "# Notes\n[Missing](missing.md)",
            )
            # Unknown notes are intentionally not treated as canonical artifacts.
            state = scan_repository(builder.repo)
            self.assertNotEqual(state.health, Health.INCONSISTENT)

    def test_state_serializes_with_schema(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            builder.scope()
            state = scan_repository(builder.repo)
            payload = state.to_dict()
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(payload["current"]["increment"]["id"], "INC-001")
            self.assertIn("follow_up", payload)
            self.assertEqual(payload["follow_up"]["next_candidate_work_packages"], [])
            self.assertIn("next_work", payload)

    def test_observatory_and_adaptive_companions_are_not_canonical_artifacts(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope("INC-004", "current-work", "WP-001")
            builder.spec("current-work", source_increment="INC-004")
            builder.ticket(1, "ready", slug="current-work", source_increment="INC-004")
            builder.write(
                "docs/planning/adaptive/current/TICKET-999.md",
                "# TKT-999 Adaptive provenance lookalike\nStatus: ready\nSource-Increment: INC-004",
            )
            builder.write(
                "docs/planning/observatory/SPEC.md",
                "# Generated Overview Lookalike\nStatus: approved\nSource-Increment: INC-004",
            )

            state = scan_repository(builder.repo)
            self.assertEqual(state.current_increment.identifier, "INC-004")
            self.assertEqual(state.ticket_counts["total"], 1)
            self.assertEqual(state.current_spec.relative_path, "docs/planning/work/current-work/SPEC.md")
            self.assertEqual(state.health, Health.READY)

    def test_adaptive_reshape_selects_replacement_increment_and_ignores_old_work(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope("INC-005", "replacement-work", "WP-001")
            builder.write(
                "docs/planning/scope-shaping/current/INCREMENT-004.md",
                """
# INC-004: Superseded shape
Status: superseded
Parent-Work-Package: WP-001
Suggested-Work-Slug: old-work
""",
            )
            builder.spec("old-work", source_increment="INC-004", title="Old Spec")
            builder.ticket(1, "ready", slug="old-work", source_increment="INC-004")
            builder.spec("replacement-work", source_increment="INC-005", title="Replacement Spec")
            builder.ticket(1, "ready", slug="replacement-work", source_increment="INC-005")
            builder.write(
                "docs/planning/adaptive/current/ADAPTIVE-PLANNING-TRACE.md",
                """
# Adaptive Planning Trace
Current Mandate Revision: 2
## Material Events
### 001 — reshape current increment
Decision: INC-004 superseded; INC-005 selected
Re-entry / next leaf: Ask Matt
""",
            )

            state = scan_repository(builder.repo)
            self.assertEqual(state.current_increment.identifier, "INC-005")
            self.assertEqual(state.current_work_slug, "replacement-work")
            self.assertEqual(state.current_spec.title, "Replacement Spec")
            self.assertEqual(state.ticket_counts["total"], 1)
            self.assertEqual(state.ticket_counts["ready"], 1)
            self.assertEqual(state.health, Health.READY)


if __name__ == "__main__":
    unittest.main()
