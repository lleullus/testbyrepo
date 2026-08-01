from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("implementation_result", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImplementationResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "project"
        self.project.mkdir()
        (self.project / "app.txt").write_text("final source\n", encoding="utf-8")
        self.planning = root / "planning"
        self.planning.mkdir()
        self.ticket = self.planning / "TICKET.md"
        self.spec = self.planning / "SPEC.md"
        self.spec.write_text("# Spec\nStatus: approved\nOwner: user\n", encoding="utf-8")
        self.write_ticket("- The final source contains the approved marker.\n")
        self.capsule_root = root / "capsules"
        self.result_root = root / "results"
        self.capsules = implementation_result.baseline_capsule.CapsuleStore(self.capsule_root)
        self.handle = self.capsules.create(self.project)
        self.store = implementation_result.ResultStore(self.result_root, self.capsule_root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_ticket(self, acceptance_body: str) -> None:
        self.ticket.write_text(
            "# Ticket\n"
            "Status: ready\n"
            "Parent-Spec: SPEC.md\n"
            f"Project-Root: {self.project}\n"
            "Worker:\n"
            "UI: no\n\n"
            "## Goal\nResult.\n\n"
            "## Acceptance Criteria\n"
            f"{acceptance_body}\n"
            "## Scope\nProject.\n\n"
            "## Non-Goals\nNone\n\n"
            "## Blockers\nNone\n\n"
            "## Verification\nObserve the result.\n\n"
            "## References\nNone\n",
            encoding="utf-8",
        )

    def planning_seal(self) -> dict[str, object]:
        return {
            "ticketPath": str(self.ticket.resolve()),
            "ticketSha256": digest(self.ticket),
            "specPath": str(self.spec.resolve()),
            "specSha256": digest(self.spec),
            "blockerFiles": [],
        }

    def final_identity(self) -> str:
        return implementation_result.baseline_capsule.capture_identity(self.project)["sourceIdentity"]

    def request(self, kind: str = "SOURCE") -> dict[str, object]:
        seal = self.planning_seal()
        criteria = implementation_result.acceptance_criteria_from_ticket(self.ticket)
        final_identity = self.final_identity()
        requirement_id = "requirement-1"
        if kind == "SOURCE":
            evidence_id = "source-1"
            source_evidence = [
                {
                    "evidenceId": evidence_id,
                    "coveredRequirementIds": [requirement_id],
                    "authorityLocators": ["Ticket:Acceptance Criteria[1]"],
                    "authorityBindingRefs": [],
                    "sourceIdentity": final_identity,
                    "reviewSummary": "Current source contains the approved marker.",
                }
            ]
            runtime_observations = []
        else:
            evidence_id = "runtime-1"
            snapshot_identity = "sha256:" + "a" * 64
            source_evidence = []
            runtime_observations = [
                {
                    "observationId": evidence_id,
                    "coveredRequirementIds": [requirement_id],
                    "entryPointAuthority": {
                        "authorityLocators": ["Ticket:Verification", "repository:public-entry-point"],
                        "authorityBindingRefs": [],
                    },
                    "executionTargetBinding": {
                        "mode": "CURRENT_PROJECT_ROOT",
                        "authorityLocators": ["repository:run-command"],
                        "finalSourceIdentity": final_identity,
                        "targetIdentityOrRevision": final_identity,
                        "bindingSummaryOrDigest": "Current canonical project root at final identity.",
                    },
                    "redactedInvocationSummary": "Invoked the public entry point with task-owned input.",
                    "expectedEffectSummary": "The public result contains the approved marker.",
                    "observedEffectSummary": "The public result contained the approved marker.",
                    "observationMode": "DIRECT_RESULT",
                    "readbackSummaryOrDigest": "Direct returned result matched the expected value.",
                    "planningSealDigest": implementation_result.planning_seal_digest(seal),
                    "sourceIdentityBefore": final_identity,
                    "sourceIdentityAfter": final_identity,
                    "projectDeltaBinding": {
                        "ownershipSnapshotIdentityBefore": snapshot_identity,
                        "ownershipSnapshotIdentityAfter": snapshot_identity,
                        "changedPathCount": 0,
                        "deltaSummaryOrDigest": "No project-root path changed.",
                        "disposition": "CLEAR",
                    },
                    "cleanupDisposition": {
                        "required": False,
                        "state": "NOT_REQUIRED",
                        "authorityOrRationale": "Direct result created no persistent state.",
                        "readbackSummaryOrDigest": "",
                    },
                    "observedAt": "2026-08-01T00:00:00+00:00",
                }
            ]
        completion = {
            "acceptanceCriteriaDigest": implementation_result.acceptance_criteria_digest(criteria),
            "supplementalLocalAuthorityBindings": [],
            "coverage": [
                {
                    **criteria[0],
                    "state": "ESTABLISHED",
                    "evidenceRequirements": [
                        {
                            "requirementId": requirement_id,
                            "kind": kind,
                            "state": "ESTABLISHED",
                            "evidenceRefs": [evidence_id],
                        }
                    ],
                }
            ],
            "sourceEvidence": source_evidence,
            "runtimeObservations": runtime_observations,
            "unresolvedItems": [],
        }
        return {
            "protocolVersion": "implementation-result-v3",
            "projectRoot": str(self.project.resolve()),
            "planningSeal": seal,
            "capsuleRef": self.handle["capsuleRef"],
            "finalSourceIdentity": final_identity,
            "completionRecord": completion,
        }

    def assert_rejected(self, request: dict[str, object], code: str) -> None:
        with self.assertRaises(implementation_result.ResultError) as raised:
            self.store.publish(request)
        self.assertEqual(code, raised.exception.code)

    def mutating_store(self, stage: str, mutation) -> object:
        parent = self

        class MutatingStore(implementation_result.ResultStore):
            mutated = False

            def _publication_checkpoint(self, current_stage: str) -> None:
                if current_stage == stage and not self.mutated:
                    self.mutated = True
                    mutation()

        return MutatingStore(parent.result_root, parent.capsule_root)

    def assert_no_publication_artifact(self) -> None:
        self.assertEqual([], list(self.result_root.glob("*.json")))
        self.assertEqual([], list(self.result_root.glob(".pending-*")))

    def test_static_only_complete_record_publishes_v3_and_round_trips(self) -> None:
        request = self.request()
        result = self.store.publish(request)
        self.assertRegex(result["implementationResultRef"], r"^implementation:v3:[a-f0-9]{32}$")
        self.assertEqual("IMPLEMENTATION_COMPLETE", result["implementationStatus"])
        self.assertEqual([], result["completionRecord"]["runtimeObservations"])
        self.assertEqual(request["planningSeal"], result["planningSeal"])
        self.assertEqual(request["completionRecord"], result["completionRecord"])
        token = result["implementationResultRef"].split(":")[-1]
        stored = json.loads((self.result_root / f"{token}.json").read_text(encoding="utf-8"))
        self.assertEqual(result, stored)
        self.assertEqual(
            stored["planningSealDigest"],
            implementation_result.planning_seal_digest(stored["planningSeal"]),
        )

    def test_complete_runtime_record_publishes(self) -> None:
        self.write_ticket("- The public entry point returns the approved marker.\n")
        request = self.request("RUNTIME")
        result = self.store.publish(request)
        self.assertEqual(1, len(result["completionRecord"]["runtimeObservations"]))

    def test_bare_completion_and_missing_completion_record_are_rejected(self) -> None:
        request = self.request()
        request["implementationStatus"] = "IMPLEMENTATION_COMPLETE"
        self.assert_rejected(request, "MALFORMED_RESULT")
        request = self.request()
        del request["completionRecord"]
        self.assert_rejected(request, "MALFORMED_RESULT")

    def test_missing_duplicate_or_changed_criterion_is_rejected(self) -> None:
        request = self.request()
        request["completionRecord"]["coverage"] = []
        self.assert_rejected(request, "INCOMPLETE_COVERAGE")

        self.write_ticket("- First criterion.\n- Second criterion.\n")
        request = self.request()
        request["completionRecord"]["coverage"].append(copy.deepcopy(request["completionRecord"]["coverage"][0]))
        self.assert_rejected(request, "ACCEPTANCE_CRITERIA_MISMATCH")

        self.write_ticket("- The final source contains the approved marker.\n")
        request = self.request()
        request["completionRecord"]["coverage"][0]["criterionRawSha256"] = "0" * 64
        self.assert_rejected(request, "ACCEPTANCE_CRITERIA_MISMATCH")
        request = self.request()
        request["completionRecord"]["acceptanceCriteriaDigest"] = "0" * 64
        self.assert_rejected(request, "ACCEPTANCE_CRITERIA_MISMATCH")

    def test_unestablished_requirement_and_missing_evidence_are_rejected(self) -> None:
        request = self.request()
        request["completionRecord"]["coverage"][0]["state"] = "PARTIAL"
        self.assert_rejected(request, "INCOMPLETE_COVERAGE")
        request = self.request()
        request["completionRecord"]["coverage"][0]["evidenceRequirements"][0]["state"] = "UNPROVEN"
        self.assert_rejected(request, "INCOMPLETE_COVERAGE")
        request = self.request()
        request["completionRecord"]["sourceEvidence"] = []
        self.assert_rejected(request, "INCOMPLETE_COVERAGE")
        self.write_ticket("- The public entry point returns the approved marker.\n")
        request = self.request("RUNTIME")
        request["completionRecord"]["runtimeObservations"] = []
        self.assert_rejected(request, "INCOMPLETE_COVERAGE")

    def test_runtime_target_and_planning_bindings_are_required_and_current(self) -> None:
        self.write_ticket("- The public entry point returns the approved marker.\n")
        request = self.request("RUNTIME")
        del request["completionRecord"]["runtimeObservations"][0]["executionTargetBinding"]
        self.assert_rejected(request, "MALFORMED_RESULT")
        request = self.request("RUNTIME")
        request["completionRecord"]["runtimeObservations"][0]["executionTargetBinding"][
            "targetIdentityOrRevision"
        ] = "sha256:" + "b" * 64
        self.assert_rejected(request, "SOURCE_IDENTITY_MISMATCH")
        request = self.request("RUNTIME")
        request["completionRecord"]["runtimeObservations"][0]["planningSealDigest"] = "0" * 64
        self.assert_rejected(request, "PLANNING_INPUT_CHANGED")

    def test_evidence_source_and_project_delta_identities_must_be_final_and_clear(self) -> None:
        request = self.request()
        request["completionRecord"]["sourceEvidence"][0]["sourceIdentity"] = "sha256:" + "b" * 64
        self.assert_rejected(request, "SOURCE_IDENTITY_MISMATCH")
        self.write_ticket("- The public entry point returns the approved marker.\n")
        for key, value in (
            ("ownershipSnapshotIdentityAfter", "sha256:" + "b" * 64),
            ("changedPathCount", 1),
            ("disposition", "DIRTY"),
        ):
            request = self.request("RUNTIME")
            request["completionRecord"]["runtimeObservations"][0]["projectDeltaBinding"][key] = value
            self.assert_rejected(request, "PROJECT_DELTA_NOT_CLEAR")

    def test_cleanup_contract_is_enforced(self) -> None:
        self.write_ticket("- The public entry point persists the approved marker.\n")
        request = self.request("RUNTIME")
        cleanup = request["completionRecord"]["runtimeObservations"][0]["cleanupDisposition"]
        cleanup.update({"required": True, "state": "NOT_REQUIRED", "readbackSummaryOrDigest": ""})
        self.assert_rejected(request, "MALFORMED_RESULT")
        request = self.request("RUNTIME")
        cleanup = request["completionRecord"]["runtimeObservations"][0]["cleanupDisposition"]
        cleanup.update(
            {
                "required": True,
                "state": "COMPLETE",
                "authorityOrRationale": "Product delete command.",
                "readbackSummaryOrDigest": "Authoritative readback confirmed absence.",
            }
        )
        self.store.publish(request)

    def test_supplemental_authority_is_current_and_referenced(self) -> None:
        authority = self.planning / "UI.md"
        authority.write_text("approved UI authority\n", encoding="utf-8")
        request = self.request()
        request["completionRecord"]["supplementalLocalAuthorityBindings"] = [
            {
                "authorityBindingId": "ui-1",
                "role": "approved-ui-authority",
                "canonicalPath": str(authority.resolve()),
                "rawSha256": digest(authority),
            }
        ]
        request["completionRecord"]["sourceEvidence"][0]["authorityBindingRefs"] = ["ui-1"]
        self.store.publish(request)

        request = self.request()
        request["completionRecord"]["sourceEvidence"][0]["authorityBindingRefs"] = ["missing"]
        self.assert_rejected(request, "MALFORMED_RESULT")

        request = self.request()
        request["completionRecord"]["supplementalLocalAuthorityBindings"] = [
            {
                "authorityBindingId": "ui-1",
                "role": "approved-ui-authority",
                "canonicalPath": str(authority.resolve()),
                "rawSha256": digest(authority),
            }
        ]
        request["completionRecord"]["sourceEvidence"][0]["authorityBindingRefs"] = ["ui-1"]
        authority.write_text("changed\n", encoding="utf-8")
        self.assert_rejected(request, "AUTHORITY_CHANGED")

    def test_unresolved_unknown_and_oversized_payloads_are_rejected(self) -> None:
        request = self.request()
        request["completionRecord"]["unresolvedItems"] = ["gap"]
        self.assert_rejected(request, "UNRESOLVED_ITEMS")
        request = self.request()
        request["completionRecord"]["unknown"] = True
        self.assert_rejected(request, "MALFORMED_RESULT")
        request = self.request()
        request["completionRecord"]["sourceEvidence"][0]["reviewSummary"] = "x" * 4097
        self.assert_rejected(request, "MALFORMED_RESULT")
        request = self.request()
        request["padding"] = "x" * implementation_result.MAX_REQUEST_BYTES
        self.assert_rejected(request, "MALFORMED_RESULT")

    def test_planning_source_capsule_and_wire_spelling_currentness(self) -> None:
        request = self.request()
        self.ticket.write_text("changed\n", encoding="utf-8")
        self.assert_rejected(request, "PLANNING_INPUT_CHANGED")

        self.write_ticket("- The final source contains the approved marker.\n")
        request = self.request()
        (self.project / "app.txt").write_text("changed source\n", encoding="utf-8")
        self.assert_rejected(request, "SOURCE_IDENTITY_MISMATCH")

        (self.project / "app.txt").write_text("final source\n", encoding="utf-8")
        request = self.request()
        request["planningSeal"]["ticketSHA256"] = request["planningSeal"].pop("ticketSha256")
        self.assert_rejected(request, "MALFORMED_RESULT")

        other = self.project.parent / "other"
        other.mkdir()
        other_handle = self.capsules.create(other)
        request = self.request()
        request["capsuleRef"] = other_handle["capsuleRef"]
        self.assert_rejected(request, "CAPSULE_PROJECT_MISMATCH")

    def test_planning_seal_reordered_request_and_blocker_are_rejected(self) -> None:
        request = self.request()
        seal = request["planningSeal"]
        request["planningSeal"] = {
            "specPath": seal["specPath"],
            "specSha256": seal["specSha256"],
            "ticketPath": seal["ticketPath"],
            "ticketSha256": seal["ticketSha256"],
            "blockerFiles": [],
        }
        self.assert_rejected(request, "MALFORMED_RESULT")

        blocker = self.planning / "BLOCKER.md"
        blocker.write_text("# Blocker\nStatus: resolved\n", encoding="utf-8")
        request = self.request()
        request["planningSeal"]["blockerFiles"] = [
            {"status": "resolved", "path": str(blocker.resolve()), "sha256": digest(blocker)}
        ]
        self.assert_rejected(request, "MALFORMED_RESULT")

    def test_planning_seal_digest_uses_schema_order_not_mapping_order(self) -> None:
        seal = self.planning_seal()
        reordered = {key: seal[key] for key in reversed(tuple(seal))}
        self.assertEqual(
            implementation_result.planning_seal_digest(seal),
            implementation_result.planning_seal_digest(reordered),
        )

    def test_stored_planning_seal_and_blocker_preserve_canonical_key_order(self) -> None:
        blocker = self.planning / "BLOCKER.md"
        blocker.write_text("# Blocker\nStatus: resolved\n", encoding="utf-8")
        request = self.request()
        request["planningSeal"]["blockerFiles"] = [
            {"path": str(blocker.resolve()), "sha256": digest(blocker), "status": "resolved"}
        ]
        result = self.store.publish(request)
        token = result["implementationResultRef"].split(":")[-1]
        object_key_orders = []

        def capture_pairs(pairs):
            object_key_orders.append(tuple(key for key, _ in pairs))
            return dict(pairs)

        json.loads(
            (self.result_root / f"{token}.json").read_text(encoding="utf-8"),
            object_pairs_hook=capture_pairs,
        )
        self.assertIn(implementation_result.PLANNING_SEAL_FIELDS, object_key_orders)
        self.assertIn(implementation_result.BLOCKER_FIELDS, object_key_orders)

    def test_publication_detects_planning_mutation_and_leaves_no_success_artifact(self) -> None:
        request = self.request()
        store = self.mutating_store(
            "after_candidate_write",
            lambda: self.ticket.write_text("changed during publication\n", encoding="utf-8"),
        )
        self.assert_rejected_with_store(store, request, "PLANNING_INPUT_CHANGED")
        self.assert_no_publication_artifact()

    def test_publication_detects_source_mutation_and_leaves_no_success_artifact(self) -> None:
        request = self.request()
        store = self.mutating_store(
            "before_commit",
            lambda: (self.project / "app.txt").write_text("changed during publication\n", encoding="utf-8"),
        )
        self.assert_rejected_with_store(store, request, "SOURCE_IDENTITY_MISMATCH")
        self.assert_no_publication_artifact()

    def test_post_commit_authority_mutation_removes_success_artifact(self) -> None:
        authority = self.planning / "UI.md"
        authority.write_text("approved UI authority\n", encoding="utf-8")
        request = self.request()
        request["completionRecord"]["supplementalLocalAuthorityBindings"] = [
            {
                "authorityBindingId": "ui-1",
                "role": "approved-ui-authority",
                "canonicalPath": str(authority.resolve()),
                "rawSha256": digest(authority),
            }
        ]
        request["completionRecord"]["sourceEvidence"][0]["authorityBindingRefs"] = ["ui-1"]
        store = self.mutating_store(
            "after_commit",
            lambda: authority.write_text("changed during publication\n", encoding="utf-8"),
        )
        self.assert_rejected_with_store(store, request, "AUTHORITY_CHANGED")
        self.assert_no_publication_artifact()

    def test_post_link_failure_cleanup_is_directory_fsynced(self) -> None:
        request = self.request()
        store = self.mutating_store(
            "after_commit",
            lambda: self.ticket.write_text("changed during publication\n", encoding="utf-8"),
        )
        fsync_calls = 0
        original_fsync = implementation_result._fsync_directory

        def counted_fsync(path: Path) -> None:
            nonlocal fsync_calls
            fsync_calls += 1
            original_fsync(path)

        with mock.patch.object(implementation_result, "_fsync_directory", counted_fsync):
            self.assert_rejected_with_store(store, request, "PLANNING_INPUT_CHANGED")
        self.assertEqual(2, fsync_calls)
        self.assert_no_publication_artifact()

    def test_failed_publication_reports_cleanup_failure(self) -> None:
        request = self.request()
        store = self.mutating_store(
            "after_commit",
            lambda: self.ticket.write_text("changed during publication\n", encoding="utf-8"),
        )
        original_unlink = Path.unlink

        def fail_public_result_unlink(path: Path, *args, **kwargs) -> None:
            if path.parent == self.result_root and path.suffix == ".json":
                raise OSError("simulated cleanup failure")
            original_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", fail_public_result_unlink):
            self.assert_rejected_with_store(store, request, "PUBLICATION_CLEANUP_FAILED")
        for artifact in self.result_root.glob("*.json"):
            artifact.unlink()

    def test_acceptance_criterion_parser_preserves_raw_ranges_and_rejects_ambiguity(self) -> None:
        self.write_ticket("- First line.\r\n  continuation.\r\n\r\n- Second line.\r\n")
        criteria = implementation_result.acceptance_criteria_from_ticket(self.ticket)
        self.assertEqual([1, 2], [item["criterionIndex"] for item in criteria])
        first = b"- First line.\r\n  continuation.\r\n\r\n"
        self.assertEqual(hashlib.sha256(first).hexdigest(), criteria[0]["criterionRawSha256"])
        for malformed in (
            "Nested only.\n  - Child.\n",
            "* Wrong marker.\n",
            "- \n",
            "- Valid.\n\tcontinuation\n",
        ):
            with self.subTest(malformed=malformed):
                self.write_ticket(malformed)
                with self.assertRaisesRegex(implementation_result.ResultError, "MALFORMED_TICKET"):
                    implementation_result.acceptance_criteria_from_ticket(self.ticket)

    def test_existing_v2_artifact_is_not_changed_by_v3_publish(self) -> None:
        self.result_root.mkdir(parents=True, exist_ok=True)
        legacy = self.result_root / "legacy-v2.json"
        legacy.write_bytes(b'{"protocolVersion":"implementation-result-v2"}\n')
        before = legacy.read_bytes()
        self.store.publish(self.request())
        self.assertEqual(before, legacy.read_bytes())

    def test_result_store_inside_project_is_rejected_before_publication(self) -> None:
        store = implementation_result.ResultStore(self.project / "results", self.capsule_root)
        self.assert_rejected_with_store(store, self.request(), "INVALID_RESULT_ROOT")

    def assert_rejected_with_store(
        self, store: object, request: dict[str, object], code: str
    ) -> None:
        with self.assertRaises(implementation_result.ResultError) as raised:
            store.publish(request)
        self.assertEqual(code, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
