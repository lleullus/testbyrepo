from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_PATH = ROOT / "iis_ephemeral_transport.py"
TRANSPORT_SPEC = importlib.util.spec_from_file_location("iis_ephemeral_transport", TRANSPORT_PATH)
assert TRANSPORT_SPEC and TRANSPORT_SPEC.loader
transport = importlib.util.module_from_spec(TRANSPORT_SPEC)
TRANSPORT_SPEC.loader.exec_module(transport)

COVERAGE_GATE_PATH = ROOT / "verification-lead/coverage_gate.py"
COVERAGE_GATE_SPEC = importlib.util.spec_from_file_location("coverage_gate", COVERAGE_GATE_PATH)
assert COVERAGE_GATE_SPEC and COVERAGE_GATE_SPEC.loader
coverage_gate = importlib.util.module_from_spec(COVERAGE_GATE_SPEC)
COVERAGE_GATE_SPEC.loader.exec_module(coverage_gate)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EphemeralTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir(mode=0o700)
        self.project = Path(self.temporary.name) / "project"
        self.planning = self.project / "docs/planning"
        self.behavior = self.planning / "behavior/contexts"
        self.ticket_dir = self.planning / "tickets"
        self.behavior.mkdir(parents=True)
        self.ticket_dir.mkdir()
        self.anchor = self.project / "app.py"
        self.anchor.write_text("current anchor\n", encoding="utf-8")
        self.behavior_path = self.behavior / "checkout.md"
        self.behavior_path.write_text(
            "# Checkout Behavior\n"
            "Status: approved\n\n"
            "## Rules\n\n"
            "- Trigger checkout\n"
            "  - Show success\n",
            encoding="utf-8",
        )
        self.spec_path = self.planning / "SPEC.md"
        self.spec_path.write_text(
            "# Checkout Spec\n"
            "Status: approved\n\n"
            "## Desired Outcome\n\nCheckout is observable.\n\n"
            "## Requirements\n\nPreserve behavior.\n\n"
            "## Non-Goals\n\nNone.\n\n"
            "## Implementation Constraints\n\nNone.\n\n"
            "## Verification Expectations\n\nObserve checkout.\n\n"
            "## Behavior Authorities\n\n"
            "- docs/planning/behavior/contexts/checkout.md | Scope: checkout\n\n"
            "## UI / UX\n\nNot applicable\n\n"
            "## Open Questions\n\nNone\n",
            encoding="utf-8",
        )
        self.ticket = self.ticket_dir / "TICKET-001.md"
        self.ticket.write_text(
            "# TICKET-001\n"
            "Status: ready\n"
            "Parent-Spec: docs/planning/SPEC.md\n"
            f"Project-Root: {self.project}\n"
            "UI: no\n\n"
            "## Acceptance Criteria\n\n"
            "- Checkout shows success.\n\n"
            "## Verification\n\n"
            "- Trigger checkout and observe success.\n\n"
            "## Behavior Authorities\n\n"
            "- docs/planning/behavior/contexts/checkout.md | Scope: checkout\n",
            encoding="utf-8",
        )
        self.model = self.project / "coverage-model.json"
        self.model.write_text(
            json.dumps(
                {
                    "units": [
                        {
                            "id": "U1",
                            "root_ids": ["AC:01", "V:01"],
                            "predicate": "Checkout shows success.",
                            "qualifier_binding_ids": ["Q1"],
                            "disposition": "PLANNED",
                        }
                    ],
                    "qualifier_bindings": [
                        {
                            "id": "Q1",
                            "source": "docs/planning/behavior/contexts/checkout.md",
                            "source_text": "- Trigger checkout - Show success",
                            "unit_ids": ["U1"],
                            "meaning": "Checkout shows success.",
                        }
                    ],
                    "coverage_edges": [
                        {
                            "id": "E1",
                            "unit_id": "U1",
                            "scenario_id": "VS1",
                            "scenario_revision": "r1",
                            "trigger": "Trigger checkout",
                            "product_boundary": "Checkout boundary",
                            "expected_result": "Show success",
                            "forbidden_result": "No success",
                            "observation_readback": "Success readback",
                            "identity_correlation": "One checkout identity",
                            "decision_predicate": "Success is shown",
                        }
                    ],
                    "scenarios": [
                        {
                            "id": "VS1",
                            "revision": "r1",
                            "procedure": ["Trigger checkout and read success."],
                            "readiness": "READY",
                            "readiness_record_ids": ["F1"],
                            "preparation_scope": "None",
                        }
                    ],
                    "partial": None,
                }
            ),
            encoding="utf-8",
        )
        self.patch_home = patch.object(transport.Path, "home", return_value=self.home)
        self.patch_home.start()

    def tearDown(self) -> None:
        self.patch_home.stop()
        self.temporary.cleanup()

    @property
    def state_root(self) -> Path:
        return self.home / ".iis"

    @property
    def key(self) -> str:
        return transport.ticket_key(self.project, self.ticket)

    def gate_package(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        envelope = coverage_gate.build(self.ticket, self.model)
        receipt = coverage_gate.check_attestation(
            envelope,
            {
                "schema": "coverage-challenge/v1",
                "result": "PASS",
                "challenge_fp": envelope["fingerprints"]["challenge_fp"],
                "roots": [
                    {
                        "root_id": root["id"],
                        "checks": [
                            {
                                "predicate": "The root is accounted.",
                                "unit_ids": ["U1"],
                                "edge_ids": ["E1"],
                            }
                        ],
                    }
                    for root in envelope["canonical"]["roots"]
                ],
                "qualifier_binding_ids_checked": ["Q1"],
            },
            None,
        )
        return envelope, receipt, coverage_gate.approve(envelope, receipt)

    def test_plan_accepts_canonical_qualifier_source_over_general_text_limit(self) -> None:
        self.behavior_path.write_text(
            self.behavior_path.read_text(encoding="utf-8") + "x" * 5_000,
            encoding="utf-8",
        )
        envelope, receipt, approval = self.gate_package()

        transport.publish_plan_envelope(
            self.project, self.ticket, envelope, receipt, approval
        )

        plan = transport.read_plan_envelope(self.project, self.ticket)
        source = next(
            item
            for item in plan["coverage_gate_envelope"]["canonical"]["qualifier_sources"]
            if item["path"] == "docs/planning/behavior/contexts/checkout.md"
        )
        self.assertGreater(len(source["content"]), transport._MAX_TEXT_LENGTH)

    def publish_plan_and_approval(self) -> tuple[dict[str, object], dict[str, object]]:
        envelope, receipt, approval = self.gate_package()
        transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        transport.publish_user_approval(self.project, self.ticket, "2026-08-10T12:00:00Z")
        return transport.read_plan_envelope(self.project, self.ticket), transport.read_user_approval(
            self.project, self.ticket
        )

    def route_inputs(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        navigation = [
            {
                "route_id": "R1",
                "startup_or_execution_path": "checkout-entry",
                "trigger_boundary": "checkout-boundary",
                "source_integration_anchors": [
                    {"path": "app.py", "sha256": sha256(self.anchor)}
                ],
                "outcome_readback": "checkout-readback",
            }
        ]
        provenance = [
            {
                "route_id": "R1",
                "execution_surface": "checkout-entry",
                "trigger_boundary": "checkout-boundary",
                "outcome_readback": "checkout-readback",
                "observed_class": "GROSS_NOMINAL_BOUNDARY_REACHED",
            }
        ]
        return navigation, provenance

    def failure_origin(self) -> dict[str, object]:
        plan = transport.read_plan_envelope(self.project, self.ticket)
        ac_id = next(
            root["id"]
            for root in plan["coverage_gate_envelope"]["canonical"]["roots"]
            if root["kind"] == "AC"
        )
        return {
            "target_ac_ids": [ac_id],
            "observed_product_boundary": "checkout-boundary",
            "expected_actual_difference": "Expected success but observed failure.",
            "direct_evidence_refs": ["EV1"],
            "relevant_source_anchors": [{"path": "app.py", "sha256": sha256(self.anchor)}],
        }

    def proposal(self, suffix: str = "1") -> dict[str, object]:
        return {
            "target_ac_ids": [self.failure_origin()["target_ac_ids"][0]],
            "hypothesis": f"Hypothesis{suffix}",
            "authorized_seam": f"Seam{suffix}",
            "minimum_change": f"Change{suffix}",
        }

    def authorization(self, suffix: str = "1") -> dict[str, str]:
        return {"authorization_id": f"AUTH{suffix}", "authorized_at": "2026-08-10T12:01:00Z"}

    def anchors(self) -> list[dict[str, str]]:
        return [{"path": "app.py", "sha256": sha256(self.anchor)}]

    def mutation_report(self, cycle: int = 1) -> dict[str, object]:
        reported_at = {
            1: "2026-08-10T12:02:00Z",
            2: "2026-08-10T12:03:30Z",
            3: "2026-08-10T12:05:00Z",
        }[cycle]
        return {
            "reported_at": reported_at,
            "changed_anchors": self.anchors(),
            "summary": "Applied authorized change.",
        }

    def reconciliation(self, cycle: int = 1) -> dict[str, object]:
        ac_id = self.failure_origin()["target_ac_ids"][0]
        reconciled_at = {
            1: "2026-08-10T12:03:00Z",
            2: "2026-08-10T12:04:30Z",
            3: "2026-08-10T12:06:00Z",
        }[cycle]
        return {
            "reconciled_at": reconciled_at,
            "target_ac_ids": [ac_id],
            "affected_ac_ids": [ac_id],
            "result": "NOT_SATISFIED",
            "direct_evidence_refs": [f"EV{cycle + 1}"],
        }

    def reconciliation_with(self, result: str, cycle: int = 1) -> dict[str, object]:
        reconciliation = self.reconciliation(cycle)
        reconciliation["result"] = result
        return reconciliation

    def final_outcome(self, *, lineage: object = None) -> dict[str, object]:
        try:
            plan = transport.read_plan_envelope(self.project, self.ticket)
            approval = transport.read_user_approval(self.project, self.ticket)
        except transport.ArtifactNotFound:
            plan, approval = self.publish_plan_and_approval()
        ac_id = next(
            root["id"]
            for root in plan["coverage_gate_envelope"]["canonical"]["roots"]
            if root["kind"] == "AC"
        )
        return {
            "schema": "iis-final-outcome/v1",
            "verification_execution_id": plan["verification_execution_id"],
            "binding": plan["binding"],
            "plan_fp": plan["gate_approval"]["plan_fp"],
            "gate_approval_id": plan["gate_approval"]["approval_id"],
            "approval_projection_sha256": approval["approval_projection_sha256"],
            "declared_dependency_bindings": [
                {
                    "id": "D1",
                    "kind": "canonical-source",
                    "identity": "ticket",
                    "sha256": sha256(self.ticket),
                }
            ],
            "evidence_records": [
                {
                    "id": evidence_id,
                    "type": "direct-evidence",
                    "scenario_id": "VS1",
                    "scenario_revision": "r1",
                    "source": "product-observation",
                    "execution_surface": "checkout-boundary",
                    "decision_boundary": "checkout-boundary",
                    "ac_ids": [ac_id],
                    "dependency_binding_refs": ["D1"],
                    "recorded_at": observed_at,
                    "reference": reference,
                    "type_details": {
                        "post_approval_observation": "NEW_AFTER_APPROVAL",
                        "observed_at": observed_at,
                    },
                }
                for evidence_id, observed_at, reference in (
                    ("EV1", "2026-08-10T12:01:30Z", "observation-ref"),
                    ("EV2", "2026-08-10T12:02:30Z", "reconciliation-1-ref"),
                    ("EV3", "2026-08-10T12:04:00Z", "reconciliation-2-ref"),
                    ("EV4", "2026-08-10T12:05:30Z", "reconciliation-3-ref"),
                )
            ],
            "ac_rows": [
                {
                    "ac_id": ac_id,
                    "verdict": "SATISFIED",
                    "obligation_ids": ["U1"],
                    "verification_flow_ids": [
                        next(
                            root["id"]
                            for root in plan["coverage_gate_envelope"]["canonical"]["roots"]
                            if root["kind"] == "V"
                        )
                    ],
                    "scenario_revisions": [{"scenario_id": "VS1", "revision": "r1"}],
                    "evidence_refs": ["EV1"],
                }
            ],
            "closure": {"result": "COMPLETE", "closed_at": "2026-08-10T12:06:00Z"},
            "final_remediation_lineage": lineage,
            "published_at": "2026-08-10T12:06:00Z",
        }

    def test_creates_only_private_fixed_slot_directories_and_files(self) -> None:
        navigation, provenance = self.route_inputs()
        transport.publish_route_navigation(
            self.project,
            self.ticket,
            navigation,
            provenance,
            now=dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc),
        )

        route_file = self.state_root / "route-navigation" / f"{self.key}.json"
        self.assertTrue(route_file.is_file())
        self.assertEqual(stat.S_IMODE(self.state_root.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(route_file.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(route_file.stat().st_mode), 0o600)
        self.assertEqual(route_file.stat().st_uid, os.geteuid())
        self.assertEqual(len(list(self.state_root.rglob("active.json"))), 0)
        self.assertEqual(len(list(self.state_root.rglob("outcome-*.json"))), 0)
        self.assertEqual(len(list(self.state_root.rglob("evidence"))), 0)

    def test_rejects_unsafe_root_and_file_surfaces(self) -> None:
        self.state_root.mkdir(mode=0o700)
        self.state_root.chmod(0o755)
        navigation, provenance = self.route_inputs()
        with self.assertRaises(transport.TransportError):
            transport.publish_route_navigation(self.project, self.ticket, navigation, provenance)

        self.state_root.chmod(0o700)
        route_dir = self.state_root / "route-navigation"
        route_dir.mkdir(mode=0o700)
        route_path = route_dir / f"{self.key}.json"
        route_path.symlink_to(self.anchor)
        with self.assertRaises(transport.TransportError):
            transport.read_primary_navigation_view(self.project, self.ticket)

    def test_route_views_are_quarantined_and_anchor_freshness_is_semantic(self) -> None:
        navigation, provenance = self.route_inputs()
        transport.publish_route_navigation(self.project, self.ticket, navigation, provenance)

        primary = transport.read_primary_navigation_view(self.project, self.ticket)
        lead = transport.read_lead_producer_provenance_view(self.project, self.ticket)
        rendered_primary = json.dumps(primary, sort_keys=True)
        rendered_lead = json.dumps(lead, sort_keys=True)
        self.assertNotIn("producer_run_nonce", rendered_primary)
        self.assertNotIn("observed_class", rendered_primary)
        self.assertNotIn("source_integration_anchors", rendered_lead)
        self.assertNotIn("navigation_view", rendered_lead)

        self.anchor.write_text("changed anchor\n", encoding="utf-8")
        with self.assertRaises(transport.TransportError):
            transport.read_primary_navigation_view(self.project, self.ticket)

    def test_route_publish_rejects_semantic_provenance_route_ids(self) -> None:
        for index, route_id in enumerate(("SATISFIED", "readiness-route")):
            with self.subTest(route_id=route_id):
                if index:
                    self.tearDown()
                    self.setUp()
                navigation, provenance = self.route_inputs()
                navigation[0]["route_id"] = route_id
                provenance[0]["route_id"] = route_id
                with self.assertRaises(transport.TransportError):
                    transport.publish_route_navigation(
                        self.project, self.ticket, navigation, provenance
                    )
                with self.assertRaises(transport.ArtifactNotFound):
                    transport.read_lead_producer_provenance_view(
                        self.project, self.ticket
                    )

    def test_route_retention_is_mechanical_only_and_terminal_grace_is_seven_days(self) -> None:
        navigation, provenance = self.route_inputs()
        created = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
        transport.publish_route_navigation(
            self.project, self.ticket, navigation, provenance, now=created
        )
        self.assertFalse(
            transport.cleanup_expired_route_navigation(
                self.project,
                self.ticket,
                now=created + dt.timedelta(days=29),
            )
        )
        transport.mark_route_navigation_terminal(
            self.project, self.ticket, "2026-09-01T00:00:00Z"
        )
        self.assertFalse(
            transport.cleanup_expired_route_navigation(
                self.project,
                self.ticket,
                now=dt.datetime(2026, 9, 7, tzinfo=dt.timezone.utc),
            )
        )
        self.assertTrue(
            transport.cleanup_expired_route_navigation(
                self.project,
                self.ticket,
                now=dt.datetime(2026, 9, 8, tzinfo=dt.timezone.utc),
            )
        )

    def test_plan_requires_accepted_complete_gate_chain_and_fresh_execution_nonce(self) -> None:
        envelope, receipt, approval = self.gate_package()
        first = transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        second = transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        self.assertNotEqual(first["verification_execution_id"], second["verification_execution_id"])

        invalid = dict(approval)
        invalid["mode"] = "OPEN"
        with self.assertRaises(transport.TransportError):
            transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, invalid)

    def test_approval_binds_the_complete_deterministic_projection(self) -> None:
        envelope, receipt, approval = self.gate_package()
        transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        disclosure = transport.render_approval_disclosure(self.project, self.ticket)
        transport.publish_user_approval(self.project, self.ticket, "2026-08-10T12:00:00Z")
        receipt_value = transport.read_user_approval(self.project, self.ticket)
        self.assertEqual(
            disclosure,
            json.dumps(
                receipt_value["approval_projection"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        self.assertEqual(
            receipt_value["approval_projection"]["scenarios"][0]["procedure"],
            ["Trigger checkout and read success."],
        )
        approval_path = self.state_root / "verification" / self.key / "user-approval.json"
        payload = json.loads(approval_path.read_text(encoding="utf-8"))
        payload["approval_projection"]["scenarios"][0]["procedure"] = ["Tampered procedure."]
        payload["approval_projection_sha256"] = transport._json_digest(
            payload["approval_projection"]
        )
        approval_path.write_text(json.dumps(payload), encoding="utf-8")
        approval_path.chmod(0o600)
        with self.assertRaises(transport.TransportError):
            transport.read_user_approval(self.project, self.ticket)

    def test_directory_creation_symlink_race_fails_without_chmodding_target(self) -> None:
        target = Path(self.temporary.name) / "target"
        target.mkdir(mode=0o755)
        target.chmod(0o755)
        original_mkdir = Path.mkdir

        def race_mkdir(path: Path, *args: object, **kwargs: object) -> None:
            if path == self.state_root:
                path.symlink_to(target, target_is_directory=True)
                raise FileExistsError(path)
            original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", new=race_mkdir):
            with self.assertRaises(transport.TransportError):
                transport._state_root(create=True)
        self.assertTrue(self.state_root.is_symlink())
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)

    def test_remediation_allows_only_current_completion_next_append_and_three_cycles(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        with self.assertRaises(transport.TransportError):
            transport.append_remediation_cycle(
                self.project, self.ticket, self.proposal("2"), self.authorization("2"), self.anchors()
            )
        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        transport.record_remediation_reconciliation(self.project, self.ticket, self.reconciliation())
        transport.append_remediation_cycle(
            self.project, self.ticket, self.proposal("2"), self.authorization("2"), self.anchors()
        )
        checkpoint = transport.read_remediation_current(self.project, self.ticket)
        self.assertEqual(len(checkpoint["cycles"]), 2)
        first_cycle = json.dumps(checkpoint["cycles"][0], sort_keys=True)
        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        self.assertEqual(
            first_cycle,
            json.dumps(transport.read_remediation_current(self.project, self.ticket)["cycles"][0], sort_keys=True),
        )

    def test_remediation_rejects_satisfied_or_undetermined_successor_cycles(self) -> None:
        for index, result in enumerate(("SATISFIED", "UNDETERMINED")):
            with self.subTest(result=result):
                if index:
                    self.tearDown()
                    self.setUp()
                self.publish_plan_and_approval()
                transport.begin_remediation(
                    self.project,
                    self.ticket,
                    self.failure_origin(),
                    self.proposal(),
                    self.authorization(),
                    self.anchors(),
                )
                transport.record_remediation_mutation(
                    self.project, self.ticket, self.mutation_report()
                )
                transport.record_remediation_reconciliation(
                    self.project, self.ticket, self.reconciliation_with(result)
                )
                with self.assertRaises(transport.TransportError):
                    transport.append_remediation_cycle(
                        self.project,
                        self.ticket,
                        self.proposal("2"),
                        self.authorization("2"),
                        self.anchors(),
                    )

    def test_remediation_rejects_a_fourth_cycle_and_mutated_prior_cycle(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        for cycle in (1, 2):
            transport.record_remediation_mutation(
                self.project, self.ticket, self.mutation_report(cycle)
            )
            transport.record_remediation_reconciliation(
                self.project, self.ticket, self.reconciliation(cycle)
            )
            if cycle == 1:
                transport.append_remediation_cycle(
                    self.project,
                    self.ticket,
                    self.proposal("2"),
                    self.authorization("2"),
                    self.anchors(),
                )
        transport.append_remediation_cycle(
            self.project,
            self.ticket,
            self.proposal("3"),
            self.authorization("3"),
            self.anchors(),
        )
        transport.record_remediation_mutation(
            self.project, self.ticket, self.mutation_report(3)
        )
        transport.record_remediation_reconciliation(
            self.project, self.ticket, self.reconciliation(3)
        )
        with self.assertRaises(transport.TransportError):
            transport.append_remediation_cycle(
                self.project,
                self.ticket,
                self.proposal("4"),
                self.authorization("4"),
                self.anchors(),
            )

        remediation_path, checkpoint, plan, approval = transport._read_remediation(
            self.project,
            self.ticket,
            require_current_pre_mutation_anchors=False,
        )
        altered = json.loads(json.dumps(checkpoint))
        altered["cycles"][0]["remediation_agent_proposal"]["hypothesis"] = "Changed"
        with self.assertRaises(transport.TransportError):
            transport._write_remediation_update(
                remediation_path, checkpoint, altered, plan, approval
            )

        transport.publish_final_outcome(
            self.project, self.ticket, self.final_outcome(lineage=checkpoint)
        )
        self.assertEqual(
            len(
                transport.read_final_outcome(self.project, self.ticket)[
                    "final_remediation_lineage"
                ]["cycles"]
            ),
            3,
        )

    def test_remediation_rejects_origin_or_prior_cycle_evidence_reuse(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.record_remediation_mutation(
            self.project, self.ticket, self.mutation_report(1)
        )
        reused_origin = self.reconciliation(1)
        reused_origin["direct_evidence_refs"] = ["EV1"]
        with self.assertRaises(transport.TransportError):
            transport.record_remediation_reconciliation(
                self.project, self.ticket, reused_origin
            )

        transport.record_remediation_reconciliation(
            self.project, self.ticket, self.reconciliation(1)
        )
        transport.append_remediation_cycle(
            self.project,
            self.ticket,
            self.proposal("2"),
            self.authorization("2"),
            self.anchors(),
        )
        transport.record_remediation_mutation(
            self.project, self.ticket, self.mutation_report(2)
        )
        reused_cycle = self.reconciliation(2)
        reused_cycle["direct_evidence_refs"] = ["EV2"]
        with self.assertRaises(transport.TransportError):
            transport.record_remediation_reconciliation(
                self.project, self.ticket, reused_cycle
            )

    def test_final_remediation_rejects_observation_outside_cycle_window(self) -> None:
        for index, observed_at in enumerate(
            (
                "2026-08-10T12:01:59Z",
                "2026-08-10T12:02:00Z",
                "2026-08-10T12:03:01Z",
            )
        ):
            with self.subTest(observed_at=observed_at):
                if index:
                    self.tearDown()
                    self.setUp()
                self.publish_plan_and_approval()
                transport.begin_remediation(
                    self.project,
                    self.ticket,
                    self.failure_origin(),
                    self.proposal(),
                    self.authorization(),
                    self.anchors(),
                )
                transport.record_remediation_mutation(
                    self.project, self.ticket, self.mutation_report(1)
                )
                transport.record_remediation_reconciliation(
                    self.project, self.ticket, self.reconciliation(1)
                )
                outcome = self.final_outcome(
                    lineage=transport.read_remediation_current(self.project, self.ticket)
                )
                outcome["evidence_records"][1]["type_details"]["observed_at"] = observed_at
                with self.assertRaises(transport.TransportError):
                    transport.publish_final_outcome(self.project, self.ticket, outcome)

    def test_final_outcome_requires_complete_rows_and_incorporates_active_remediation(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        transport.record_remediation_reconciliation(self.project, self.ticket, self.reconciliation())
        checkpoint = transport.read_remediation_current(self.project, self.ticket)
        outcome = self.final_outcome(lineage=checkpoint)
        transport.publish_final_outcome(self.project, self.ticket, outcome)
        self.assertEqual(transport.read_final_outcome(self.project, self.ticket)["ac_rows"][0]["verdict"], "SATISFIED")
        with self.assertRaises(transport.ArtifactNotFound):
            transport.read_remediation_current(self.project, self.ticket)

        bad = self.final_outcome()
        bad["ac_rows"] = []
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, bad)

    def test_final_outcome_rejects_incomplete_remediation_cycles(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(
                self.project,
                self.ticket,
                self.final_outcome(lineage=transport.read_remediation_current(self.project, self.ticket)),
            )

        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(
                self.project,
                self.ticket,
                self.final_outcome(lineage=transport.read_remediation_current(self.project, self.ticket)),
            )

    def test_terminal_execution_blocks_all_remediation_mutation_steps(self) -> None:
        outcome = self.final_outcome()
        transport.publish_final_outcome(self.project, self.ticket, outcome)
        with self.assertRaises(transport.TransportError):
            transport.begin_remediation(
                self.project,
                self.ticket,
                self.failure_origin(),
                self.proposal(),
                self.authorization(),
                self.anchors(),
            )

    def test_final_outcome_rejects_stale_execution_and_non_direct_evidence_shape(self) -> None:
        outcome = self.final_outcome()
        outcome["verification_execution_id"] = "vx-" + "0" * 32
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, outcome)

        outcome = self.final_outcome()
        outcome["evidence_records"][0]["type_details"] = {"unexpected": "shape"}
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, outcome)

    def test_final_outcome_rejects_direct_evidence_outside_approval_publication_window(self) -> None:
        for evidence_index in range(4):
            with self.subTest(phase="before_approval", evidence_index=evidence_index):
                before_approval = self.final_outcome()
                before_approval["evidence_records"][evidence_index]["type_details"]["observed_at"] = (
                    "2026-08-10T12:00:00Z"
                )
                with self.assertRaises(transport.TransportError):
                    transport.publish_final_outcome(self.project, self.ticket, before_approval)
            with self.subTest(phase="after_publication", evidence_index=evidence_index):
                after_publication = self.final_outcome()
                after_publication["evidence_records"][evidence_index]["type_details"]["observed_at"] = (
                    "2026-08-10T12:06:01Z"
                )
                with self.assertRaises(transport.TransportError):
                    transport.publish_final_outcome(self.project, self.ticket, after_publication)

    def test_final_outcome_is_exactly_once_per_execution_and_new_execution_replaces_old_slot(self) -> None:
        first = self.final_outcome()
        transport.publish_final_outcome(self.project, self.ticket, first)

        changed = self.final_outcome()
        changed["ac_rows"][0]["verdict"] = "NOT_SATISFIED"
        changed["closure"]["closed_at"] = "2026-08-10T12:07:00Z"
        changed["published_at"] = "2026-08-10T12:07:00Z"
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, changed)
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, first)

        old_execution_id = first["verification_execution_id"]
        envelope, receipt, approval = self.gate_package()
        transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        transport.publish_user_approval(self.project, self.ticket, "2026-08-10T12:10:00Z")
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, first)

        replacement = self.final_outcome()
        for record in replacement["evidence_records"]:
            record["type_details"]["observed_at"] = "2026-08-10T12:11:00Z"
            record["recorded_at"] = "2026-08-10T12:11:00Z"
        replacement["closure"]["closed_at"] = "2026-08-10T12:12:00Z"
        replacement["published_at"] = "2026-08-10T12:12:00Z"
        self.assertNotEqual(replacement["verification_execution_id"], old_execution_id)
        transport.publish_final_outcome(self.project, self.ticket, replacement)
        self.assertEqual(
            transport.read_final_outcome(self.project, self.ticket)["verification_execution_id"],
            replacement["verification_execution_id"],
        )

    def test_safe_abandonment_is_retained_and_never_removed_by_route_cleanup(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.abandon_remediation(
            self.project,
            self.ticket,
            {
                "established_at": "2026-08-10T12:02:00Z",
                "mutation_state": "MUTATION_NOT_RUN",
                "reason": "Explicit safe abandonment.",
            },
        )
        self.assertEqual(
            transport.read_remediation_current(self.project, self.ticket)["state"],
            "SAFE_ABANDONED",
        )
        with self.assertRaises(transport.TransportError):
            transport.begin_remediation(
                self.project,
                self.ticket,
                self.failure_origin(),
                self.proposal(),
                self.authorization(),
                self.anchors(),
            )

    def test_safe_abandonment_rejects_uncertainty_and_supersedes_under_new_execution(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        with self.assertRaises(transport.TransportError):
            transport.abandon_remediation(
                self.project,
                self.ticket,
                {
                    "established_at": "2026-08-10T12:02:00Z",
                    "mutation_state": "MUTATION_STATE_UNCERTAIN",
                    "reason": "Unknown.",
                },
            )
        transport.abandon_remediation(
            self.project,
            self.ticket,
            {
                "established_at": "2026-08-10T12:02:00Z",
                "mutation_state": "MUTATION_NOT_RUN",
                "reason": "Anchors prove mutation did not run.",
            },
        )
        prior = transport.read_remediation_current(self.project, self.ticket)
        envelope, receipt, approval = self.gate_package()
        transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        transport.publish_user_approval(self.project, self.ticket, "2026-08-10T12:10:00Z")
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal("2"),
            self.authorization("2"),
            self.anchors(),
        )
        self.assertNotEqual(
            prior["verification_execution_id"],
            transport.read_remediation_current(self.project, self.ticket)["verification_execution_id"],
        )

    def test_safe_abandonment_supersedes_after_ticket_digest_changes(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.abandon_remediation(
            self.project,
            self.ticket,
            {
                "established_at": "2026-08-10T12:02:00Z",
                "mutation_state": "MUTATION_NOT_RUN",
                "reason": "Anchors prove mutation did not run.",
            },
        )
        prior = transport.read_remediation_current(self.project, self.ticket)
        self.ticket.write_text(
            self.ticket.read_text(encoding="utf-8") + "\nTicket change retained in source.\n",
            encoding="utf-8",
        )
        envelope, receipt, approval = self.gate_package()
        transport.publish_plan_envelope(self.project, self.ticket, envelope, receipt, approval)
        transport.publish_user_approval(self.project, self.ticket, "2026-08-10T12:10:00Z")
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal("2"),
            self.authorization("2"),
            self.anchors(),
        )
        self.assertNotEqual(
            prior["verification_execution_id"],
            transport.read_remediation_current(self.project, self.ticket)["verification_execution_id"],
        )

    def test_final_rows_and_lineage_close_structural_references(self) -> None:
        outcome = self.final_outcome()
        outcome["ac_rows"][0]["obligation_ids"] = ["unknown"]
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, outcome)

        outcome = self.final_outcome()
        outcome["ac_rows"][0]["scenario_revisions"] = []
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, outcome)

        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        transport.record_remediation_reconciliation(self.project, self.ticket, self.reconciliation())
        lineage = transport.read_remediation_current(self.project, self.ticket)
        lineage["failure_origin"]["direct_evidence_refs"] = ["missing"]
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(
                self.project, self.ticket, self.final_outcome(lineage=lineage)
            )

        outcome = self.final_outcome()
        outcome["evidence_records"][0]["ac_ids"] = ["AC:99:missing"]
        with self.assertRaises(transport.TransportError):
            transport.publish_final_outcome(self.project, self.ticket, outcome)

    def test_concurrent_remediation_begin_allows_exactly_one_checkpoint(self) -> None:
        self.publish_plan_and_approval()
        start = threading.Barrier(3)
        successes: list[str] = []
        failures: list[BaseException] = []
        result_lock = threading.Lock()

        def begin() -> None:
            try:
                start.wait(timeout=5)
                transport.begin_remediation(
                    self.project,
                    self.ticket,
                    self.failure_origin(),
                    self.proposal(),
                    self.authorization(),
                    self.anchors(),
                )
            except BaseException as exc:
                with result_lock:
                    failures.append(exc)
            else:
                with result_lock:
                    successes.append("begin")

        workers = [threading.Thread(target=begin) for _ in range(2)]
        for worker in workers:
            worker.start()
        start.wait(timeout=5)
        for worker in workers:
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
        self.assertEqual(successes, ["begin"])
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], transport.TransportError)
        checkpoint = transport.read_remediation_current(self.project, self.ticket)
        self.assertEqual(checkpoint["state"], "ACTIVE")
        self.assertEqual(len(checkpoint["cycles"]), 1)

    def test_terminal_publish_serializes_against_remediation_update(self) -> None:
        self.publish_plan_and_approval()
        transport.begin_remediation(
            self.project,
            self.ticket,
            self.failure_origin(),
            self.proposal(),
            self.authorization(),
            self.anchors(),
        )
        transport.record_remediation_mutation(self.project, self.ticket, self.mutation_report())
        transport.record_remediation_reconciliation(self.project, self.ticket, self.reconciliation())
        outcome = self.final_outcome(lineage=transport.read_remediation_current(self.project, self.ticket))
        original_write = transport._write_artifact
        final_entered = threading.Event()
        release_final = threading.Event()
        update_started = threading.Event()
        successes: list[str] = []
        failures: list[BaseException] = []
        result_lock = threading.Lock()

        def delayed_write(path: Path, value: dict[str, object], label: str) -> None:
            if label == "final outcome":
                final_entered.set()
                release_final.wait(timeout=5)
            original_write(path, value, label)

        def publish() -> None:
            try:
                transport.publish_final_outcome(self.project, self.ticket, outcome)
            except BaseException as exc:
                with result_lock:
                    failures.append(exc)
            else:
                with result_lock:
                    successes.append("final")

        def append() -> None:
            update_started.set()
            try:
                transport.append_remediation_cycle(
                    self.project,
                    self.ticket,
                    self.proposal("2"),
                    self.authorization("2"),
                    self.anchors(),
                )
            except BaseException as exc:
                with result_lock:
                    failures.append(exc)
            else:
                with result_lock:
                    successes.append("append")

        with patch.object(transport, "_write_artifact", side_effect=delayed_write):
            final_worker = threading.Thread(target=publish)
            final_worker.start()
            self.assertTrue(final_entered.wait(timeout=5))
            update_worker = threading.Thread(target=append)
            update_worker.start()
            self.assertTrue(update_started.wait(timeout=5))
            release_final.set()
            final_worker.join(timeout=5)
            update_worker.join(timeout=5)
        self.assertFalse(final_worker.is_alive())
        self.assertFalse(update_worker.is_alive())
        self.assertEqual(successes, ["final"])
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], transport.ArtifactNotFound)
        self.assertEqual(
            transport.read_final_outcome(self.project, self.ticket)["verification_execution_id"],
            outcome["verification_execution_id"],
        )
        with self.assertRaises(transport.ArtifactNotFound):
            transport.read_remediation_current(self.project, self.ticket)

    def test_public_verification_readers_are_generation_consistent(self) -> None:
        for index, reader_name in enumerate(("plan", "approval", "remediation", "final")):
            with self.subTest(reader=reader_name):
                if index:
                    self.tearDown()
                    self.setUp()
                if reader_name == "plan":
                    envelope, receipt, gate_approval = self.gate_package()
                    transport.publish_plan_envelope(
                        self.project, self.ticket, envelope, receipt, gate_approval
                    )
                    reader = transport.read_plan_envelope
                else:
                    self.publish_plan_and_approval()
                    if reader_name == "approval":
                        reader = transport.read_user_approval
                    elif reader_name == "remediation":
                        transport.begin_remediation(
                            self.project,
                            self.ticket,
                            self.failure_origin(),
                            self.proposal(),
                            self.authorization(),
                            self.anchors(),
                        )
                        transport.abandon_remediation(
                            self.project,
                            self.ticket,
                            {
                                "established_at": "2026-08-10T12:02:00Z",
                                "mutation_state": "MUTATION_NOT_RUN",
                                "reason": "Generation consistency fixture.",
                            },
                        )
                        reader = transport.read_remediation_current
                    else:
                        transport.publish_final_outcome(
                            self.project, self.ticket, self.final_outcome()
                        )
                        reader = transport.read_final_outcome

                execution_a = transport.read_plan_envelope(
                    self.project, self.ticket
                )["verification_execution_id"]
                envelope, receipt, gate_approval = self.gate_package()
                plan_read = threading.Event()
                release_reader = threading.Event()
                publisher_started = threading.Event()
                publisher_done = threading.Event()
                reader_results: list[dict[str, object]] = []
                publisher_results: list[dict[str, str]] = []
                failures: list[BaseException] = []
                result_lock = threading.Lock()
                original_read_plan = transport._read_plan_envelope_unlocked

                def delayed_read_plan(
                    project_root: Path, ticket_path: Path
                ) -> dict[str, object]:
                    plan = original_read_plan(project_root, ticket_path)
                    if threading.current_thread().name == "generation-reader":
                        plan_read.set()
                        release_reader.wait(timeout=5)
                    return plan

                def run_reader() -> None:
                    try:
                        result = reader(self.project, self.ticket)
                    except BaseException as exc:
                        with result_lock:
                            failures.append(exc)
                    else:
                        with result_lock:
                            reader_results.append(result)

                def publish_next_plan() -> None:
                    publisher_started.set()
                    try:
                        result = transport.publish_plan_envelope(
                            self.project,
                            self.ticket,
                            envelope,
                            receipt,
                            gate_approval,
                        )
                    except BaseException as exc:
                        with result_lock:
                            failures.append(exc)
                    else:
                        with result_lock:
                            publisher_results.append(result)
                    finally:
                        publisher_done.set()

                with patch.object(
                    transport,
                    "_read_plan_envelope_unlocked",
                    side_effect=delayed_read_plan,
                ):
                    reader_thread = threading.Thread(
                        name="generation-reader", target=run_reader
                    )
                    reader_thread.start()
                    self.assertTrue(plan_read.wait(timeout=5))
                    publisher_thread = threading.Thread(target=publish_next_plan)
                    publisher_thread.start()
                    self.assertTrue(publisher_started.wait(timeout=5))
                    self.assertFalse(publisher_done.wait(timeout=0.1))
                    self.assertTrue(publisher_thread.is_alive())
                    release_reader.set()
                    reader_thread.join(timeout=5)
                    publisher_thread.join(timeout=5)

                self.assertFalse(reader_thread.is_alive())
                self.assertFalse(publisher_thread.is_alive())
                self.assertEqual(failures, [])
                self.assertEqual(len(reader_results), 1)
                self.assertEqual(len(publisher_results), 1)
                self.assertEqual(
                    reader_results[0]["verification_execution_id"], execution_a
                )
                execution_b = publisher_results[0]["verification_execution_id"]
                self.assertNotEqual(execution_b, execution_a)
                self.assertEqual(
                    transport.read_plan_envelope(self.project, self.ticket)[
                        "verification_execution_id"
                    ],
                    execution_b,
                )

    def test_route_mutators_do_not_replace_or_delete_a_new_generation(self) -> None:
        navigation, provenance = self.route_inputs()
        transport.publish_route_navigation(
            self.project,
            self.ticket,
            navigation,
            provenance,
            now=dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc),
        )
        original_write = transport._write_artifact
        entered = threading.Event()
        release = threading.Event()
        failures: list[BaseException] = []

        def run(worker: object, *args: object) -> None:
            try:
                worker(*args)  # type: ignore[operator]
            except BaseException as exc:
                failures.append(exc)

        def delayed_write(path: Path, value: dict[str, object], label: str) -> None:
            if label == "route navigation" and value["retention"]["terminal_published_at"]:
                entered.set()
                release.wait(timeout=5)
            original_write(path, value, label)

        with patch.object(transport, "_write_artifact", side_effect=delayed_write):
            marker = threading.Thread(
                target=run,
                args=(transport.mark_route_navigation_terminal, self.project, self.ticket, "2026-08-10T12:00:00Z"),
            )
            marker.start()
            self.assertTrue(entered.wait(timeout=5))
            publisher = threading.Thread(
                target=run,
                args=(transport.publish_route_navigation, self.project, self.ticket, navigation, provenance),
            )
            publisher.start()
            release.set()
            marker.join(timeout=5)
            publisher.join(timeout=5)
        self.assertFalse(marker.is_alive())
        self.assertFalse(publisher.is_alive())
        self.assertEqual(failures, [])
        sidecar = json.loads(
            (self.state_root / "route-navigation" / f"{self.key}.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(sidecar["retention"]["terminal_published_at"])

    def test_route_cleanup_cannot_unlink_a_generation_published_after_its_read(self) -> None:
        navigation, provenance = self.route_inputs()
        transport.publish_route_navigation(
            self.project,
            self.ticket,
            navigation,
            provenance,
            now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        original_remove = transport._remove_artifact
        entered = threading.Event()
        release = threading.Event()
        failures: list[BaseException] = []

        def run(worker: object, *args: object, **kwargs: object) -> None:
            try:
                worker(*args, **kwargs)  # type: ignore[operator]
            except BaseException as exc:
                failures.append(exc)

        def delayed_remove(path: Path, label: str) -> None:
            entered.set()
            release.wait(timeout=5)
            original_remove(path, label)

        with patch.object(transport, "_remove_artifact", side_effect=delayed_remove):
            cleaner = threading.Thread(
                target=run,
                args=(transport.cleanup_expired_route_navigation, self.project, self.ticket),
                kwargs={"now": dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)},
            )
            cleaner.start()
            self.assertTrue(entered.wait(timeout=5))
            publisher = threading.Thread(
                target=run,
                args=(transport.publish_route_navigation, self.project, self.ticket, navigation, provenance),
            )
            publisher.start()
            release.set()
            cleaner.join(timeout=5)
            publisher.join(timeout=5)
        self.assertFalse(cleaner.is_alive())
        self.assertFalse(publisher.is_alive())
        self.assertEqual(failures, [])
        self.assertTrue((self.state_root / "route-navigation" / f"{self.key}.json").is_file())

    def test_public_surface_has_no_generic_storage_or_legacy_architecture_api(self) -> None:
        public = set(transport.__all__)
        forbidden = {
            "list",
            "inspect",
            "history",
            "replay",
            "recover",
            "takeover",
            "retry",
            "read_artifact",
            "write_artifact",
            "active",
            "latest",
            "predecessor",
        }
        self.assertFalse({name for name in public if any(token in name for token in forbidden)})
        self.assertFalse(hasattr(transport, "main"))


if __name__ == "__main__":
    unittest.main()
