from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "verification-lead/tools/verification-run/verification_run.py"
SPEC = importlib.util.spec_from_file_location("verification_run", MODULE)
assert SPEC and SPEC.loader
verification_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verification_run)


class VerificationRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temporary = Path(self.temporary.name)
        self.project = temporary / "project"
        self.project.mkdir()
        self.ticket = self.project / "TICKET.md"
        self.ticket.write_text(
            "# Ticket\n\n## Acceptance Criteria\n\n- command exposes the intended result\n\n## Scope\n\nLocal fixture.\n",
            encoding="utf-8",
        )
        self.spec_file = self.project / "SPEC.md"
        self.spec_file.write_text("# Spec\n\nApproved local behavior.\n", encoding="utf-8")
        self.product_file = self.project / "product.txt"
        self.product_file.write_text("stable\n", encoding="utf-8")
        self.workflow_root = temporary / "workflow"
        self.service = verification_run.VerificationService(self.workflow_root)
        self.handoff_module = verification_run.handoff_contract
        self.workflow_module = verification_run.workflow_store
        self.criteria = self.handoff_module.acceptance_criteria_from_ticket(self.ticket)
        self.planning_seal = {
            "ticketPath": str(self.ticket.resolve()),
            "ticketSha256": self._file_sha(self.ticket),
            "specPath": str(self.spec_file.resolve()),
            "specSha256": self._file_sha(self.spec_file),
            "blockerFiles": [],
        }
        self.planning = self.handoff_module.planning_seal_digest(self.planning_seal)
        self.source = verification_run.baseline_capsule.capture_identity(self.project)["sourceIdentity"]
        self.handoff_ref = self.workflow_module.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.handoff_payload = {
            "protocolVersion": "implementation-handoff-v1",
            "implementationHandoffRef": self.handoff_ref,
            "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
            "projectRoot": str(self.project.resolve()),
            "planningSeal": self.planning_seal,
            "planningSealDigest": self.planning,
            "baselineCapsuleRef": "capsule:v1:" + "1" * 32,
            "baselineSourceIdentity": self.source,
            "finalSourceIdentity": self.source,
            "implementationDeltaRef": "implementation:delta:v1:" + "2" * 32,
            "criterionAccounting": [{**self.criteria[0], "taskIds": ["task-1"]}],
            "unresolvedImplementationItems": [],
            "completedAt": "2026-08-03T00:00:00+00:00",
        }
        self.service.workflow.publish_initial_handoff(
            node_ref=self.handoff_ref,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            payload=self.handoff_payload,
        )
        self.invocation = self.service.workflow.start_invocation(
            root_ref=self.handoff_ref,
            elapsed_seconds=600,
            limits=self.budget(workerCalls=10, remediationTransactions=10, effectfulActions=50, toolCostUnits=200, closureOperations=100),
        )
        self.coordinator = self.invocation["coordinator"]
        self.anchor = verification_run.basis_anchor(
            self.ticket,
            1,
            len(self.ticket.read_bytes().splitlines(keepends=True)),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _file_sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def budget(**overrides: int) -> dict[str, int]:
        result = {field: 0 for field in verification_run.workflow_store.BUDGET_FIELDS}
        result.update(overrides)
        return result

    def open(self, *, effectful: int = 10, tool_cost: int = 30):
        return self.service.open_verification(
            coordinator_capability=self.coordinator["capability"],
            implementation_handoff_ref=self.handoff_ref,
            spend_budget=self.budget(effectfulActions=effectful, toolCostUnits=tool_cost),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )

    def step(
        self,
        step_id: str,
        role: str,
        code: str,
        *,
        argv_extra: list[str] | None = None,
        poll_attempts: int = 1,
        interval_ms: int = 0,
    ) -> dict[str, object]:
        argv = ["-c", code]
        if argv_extra:
            argv.extend(argv_extra)
        return {
            "stepId": step_id,
            "role": role,
            "executorKind": "PROCESS",
            "executable": str(Path(sys.executable).resolve()),
            "argv": argv,
            "cwd": str(self.project.resolve()),
            "environmentDelta": {},
            "inputRefs": [],
            "sourceBinding": {
                "mode": "CURRENT_PROJECT_ROOT",
                "finalSourceIdentity": self.source,
                "targetIdentityOrRevision": str(self.project.resolve()),
                "bindingBasisAnchors": [],
            },
            "pollPolicy": (
                {"maxAttempts": poll_attempts, "intervalMs": interval_ms}
                if role == "READBACK"
                else None
            ),
        }

    def draft(
        self,
        flows: list[dict[str, object]],
        *,
        flow_ids: list[str] | None = None,
        source_reviews: list[dict[str, object]] | None = None,
        source_review_ids: list[str] | None = None,
        authorizations: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        return {
            "authorizationRefs": authorizations or [],
            "criteria": [
                {
                    **self.criteria[0],
                    "sourceReviewIds": source_review_ids or [],
                    "flowIds": flow_ids if flow_ids is not None else [str(flow["flowId"]) for flow in flows],
                }
            ],
            "sourceReviews": source_reviews or [],
            "flows": flows,
        }

    def flow(
        self,
        flow_id: str,
        steps: list[dict[str, object]],
        *,
        requirement: str = "NOT_APPLICABLE",
        bindings: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        return {
            "flowId": flow_id,
            "criterionRefs": self.criteria,
            "claim": "The intended command behavior is observable.",
            "expectedTerminalObservation": "The process artifact contains the intended result.",
            "basisAnchors": [self.anchor],
            "productTargetRequirement": requirement,
            "steps": steps,
            "optionalCorrelationBindings": bindings or [],
        }

    def seal(self, opened, draft):
        return self.service.seal_run(
            assessor_capability=opened["assessor"]["capability"],
            claim_ref=opened["claim"]["claimRef"],
            implementation_handoff_ref=self.handoff_ref,
            verification_draft=draft,
        )

    def assessment(self, verdict: str) -> list[dict[str, object]]:
        return [
            {
                **self.criteria[0],
                "verdict": verdict,
                "semanticRationale": "The tool-owned observation is evaluated against the exact criterion.",
            }
        ]

    def remediate_failed_result(
        self,
        failed: dict[str, object],
        *,
        product_text: str,
        task_id: str,
    ) -> tuple[dict[str, object], dict[str, object], object]:
        remediation_open = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=str(failed["verificationResultRef"]),
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        capsule_root = Path(self.temporary.name) / "capsules"
        transaction_store = verification_run.handoff_contract.implementation_transaction.ImplementationTransactionStore(
            self.workflow_root,
            capsule_root,
        )
        transaction = transaction_store.start_remediation(
            remediator_capability=remediation_open["remediator"]["capability"],
            worker_capability=remediation_open["worker"]["capability"],
            claim_ref=remediation_open["claim"]["claimRef"],
            project_root=self.project,
            admission={
                "disposition": "ADMITTED",
                "criterionRefs": self.criteria,
                "authorityDeltaDigest": "c" * 64,
                "desiredOutcomeUnchanged": True,
                "acceptanceMeaningUnchanged": True,
                "scopeAndNonGoalsUnchanged": True,
                "materialProductDecisionRequired": False,
                "safetyAndOwnershipAuthorized": True,
            },
        )
        envelope = transaction_store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id=task_id,
            criterion_refs=self.criteria,
            allowed_paths=["product.txt"],
            forbidden_paths=[],
        )
        transaction_store.begin_worker_call(
            worker_capability=remediation_open["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.product_file.write_text(product_text, encoding="utf-8")
        transaction_store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        transaction_store.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": ["product.txt"],
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )
        transaction_store.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        self.service.workflow.consume_budget(
            actor_capability=remediation_open["remediator"]["capability"],
            reservation_ref=remediation_open["budgetReservation"]["reservationRef"],
            category="CLOSURE",
            amounts=self.budget(closureOperations=1),
        )
        publisher = verification_run.handoff_contract.HandoffPublisher(
            self.workflow_root,
            capsule_root,
        )
        successor = publisher.publish(
            {
                "protocolVersion": "implementation-handoff-v1",
                "implementationTransactionRef": transaction["transactionRef"],
                "actorCapability": remediation_open["remediator"]["capability"],
                "planningSeal": self.planning_seal,
                "criterionAccounting": [{**self.criteria[0], "taskIds": [task_id]}],
                "unresolvedImplementationItems": [],
            }
        )
        return successor, remediation_open, transaction_store

    def assert_code(self, code: str, operation) -> None:
        with self.assertRaises(verification_run.VerificationError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)

    def test_direct_result_process_is_verified_and_artifact_is_runner_owned(self) -> None:
        opened = self.open()
        flow = self.flow("direct", [self.step("action", "ACTION", "print('INTENDED-RESULT')")])
        sealed = self.seal(opened, self.draft([flow]))
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="direct",
            step_id="action",
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )

        self.assertEqual("VERIFIED", result["verificationStatus"])
        self.assertEqual([], result["reasonCodes"])
        artifact = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=execution["attempts"][0]["artifactRef"],
        )
        self.assertIn("INTENDED-RESULT", artifact["payload"]["stdout"]["text"])
        run = self.service.read_run(sealed["verificationRunRef"])
        self.assertEqual("CLOSED", run["state"])
        self.assertEqual(result["verificationResultRef"], run["closure"]["verificationResultRef"])

    def test_process_execution_ignores_environment_added_after_seal(self) -> None:
        variable = "UNSEALED_OVERRIDE"
        sealed_variable = "SEALED_OVERRIDE"
        process_step = self.step(
            "observe-environment",
            "READBACK",
            (
                "import os; "
                f"print(os.environ.get('{variable}', 'ABSENT')); "
                f"print(os.environ.get('{sealed_variable}', 'ABSENT'))"
            ),
        )
        process_step["environmentDelta"] = {sealed_variable: "sealed-value"}
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "closed-environment",
                        [process_step],
                    )
                ]
            ),
        )
        previous = os.environ.get(variable)
        previous_sealed = os.environ.get(sealed_variable)
        os.environ[variable] = "injected-after-seal"
        os.environ[sealed_variable] = "ambient-value"
        try:
            execution = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="closed-environment",
                step_id="observe-environment",
            )
        finally:
            if previous is None:
                os.environ.pop(variable, None)
            else:
                os.environ[variable] = previous
            if previous_sealed is None:
                os.environ.pop(sealed_variable, None)
            else:
                os.environ[sealed_variable] = previous_sealed
        artifact = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=execution["attempts"][0]["artifactRef"],
        )
        self.assertEqual("ABSENT\nsealed-value\n", artifact["payload"]["stdout"]["text"])
        public_step = sealed["plan"]["flows"][0]["steps"][0]
        self.assertEqual("process-v2", public_step["executorVersion"])
        self.assertEqual("SEALED_EMPTY_BASE_V1", public_step["environmentPolicy"])
        self.assertNotIn("sealed-value", json.dumps(sealed["plan"], sort_keys=True))

    def test_public_plan_redacts_argv_without_changing_sealed_execution(self) -> None:
        sentinel = "secret-argv-sentinel"
        step = self.step(
            "redacted-argv",
            "READBACK",
            "import sys; print(sys.argv[1])",
            argv_extra=[sentinel],
        )
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft([self.flow("redacted-plan", [step])]),
        )
        self.assertNotIn(sentinel, json.dumps(sealed["plan"], sort_keys=True))
        public_argv = sealed["plan"]["flows"][0]["steps"][0]["canonicalRequest"]["argv"]
        self.assertEqual(
            hashlib.sha256(sentinel.encode("utf-8")).hexdigest(),
            public_argv[-1]["valueSha256"],
        )
        self.assertEqual(len(sentinel.encode("utf-8")), public_argv[-1]["byteCount"])
        self.assertNotIn(
            sentinel,
            json.dumps(self.service.read_run(sealed["verificationRunRef"]), sort_keys=True),
        )

        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="redacted-plan",
            step_id="redacted-argv",
        )
        artifact = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=execution["attempts"][0]["artifactRef"],
        )
        self.assertEqual(f"{sentinel}\n", artifact["payload"]["stdout"]["text"])
        self.assertEqual(
            sealed["plan"]["flows"][0]["steps"][0]["canonicalRequestDigest"],
            execution["attempts"][0]["canonicalRequestDigest"],
        )

    def test_only_the_exact_owning_assessor_can_read_raw_artifacts(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [self.flow("artifact-owner", [self.step("produce", "READBACK", "print('owned')")])]
            ),
        )
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="artifact-owner",
            step_id="produce",
        )
        artifact_ref = execution["attempts"][0]["artifactRef"]
        owned = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=artifact_ref,
        )
        self.assertEqual("owned\n", owned["payload"]["stdout"]["text"])

        fresh_assessor = self.service.workflow.issue_actor(
            coordinator_capability=self.coordinator["capability"],
            role="ASSESSOR",
        )
        self.assert_code(
            "ARTIFACT_NOT_FOUND",
            lambda: self.service.read_artifact(
                assessor_capability=fresh_assessor["capability"],
                artifact_ref=artifact_ref,
            ),
        )

    def test_source_only_criterion_is_verified_from_exact_current_basis_anchor(self) -> None:
        opened = self.open(effectful=0, tool_cost=0)
        review = {
            "sourceReviewId": "source-contract",
            "criterionRefs": self.criteria,
            "basisAnchors": [self.anchor],
        }
        sealed = self.seal(
            opened,
            self.draft(
                [],
                flow_ids=[],
                source_reviews=[review],
                source_review_ids=["source-contract"],
            ),
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )

        self.assertEqual("VERIFIED", result["verificationStatus"])
        self.assertEqual([], self.service.read_run(sealed["verificationRunRef"])["attempts"])

    def test_result_publication_retry_preserves_assessments_and_closure_budget(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft([self.flow("retry", [self.step("action", "ACTION", "print('ok')")])]),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="retry",
            step_id="action",
        )
        original_publish = self.service.workflow.publish_successor

        def fail_once(**_kwargs):
            raise verification_run.workflow_store.WorkflowStoreError(
                "SIMULATED_PUBLICATION_INTERRUPTION", "result publication was interrupted"
            )

        self.service.workflow.publish_successor = fail_once
        try:
            self.assert_code(
                "SIMULATED_PUBLICATION_INTERRUPTION",
                lambda: self.service.publish_result(
                    assessor_capability=opened["assessor"]["capability"],
                    verification_run_ref=sealed["verificationRunRef"],
                    criterion_assessments=self.assessment("SATISFIED"),
                ),
            )
        finally:
            self.service.workflow.publish_successor = original_publish

        self.assert_code(
            "RESULT_RETRY_MISMATCH",
            lambda: self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("INCONCLUSIVE"),
            ),
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])
        connection = self.service.workflow._connect()
        try:
            reservation = connection.execute(
                "SELECT closure_used_json FROM budget_reservations WHERE reservation_ref = ?",
                (opened["budgetReservation"]["reservationRef"],),
            ).fetchone()
            closure_used = self.service.workflow._stored_budget(
                reservation["closure_used_json"], "reservation.closureUsed"
            )
        finally:
            connection.close()
        self.assertEqual(1, closure_used["closureOperations"])

    def test_forged_satisfied_assessment_without_execution_is_rejected(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft([self.flow("required", [self.step("action", "ACTION", "print('ok')")])]),
        )
        self.assert_code(
            "FORGED_OUTCOME_WITHOUT_EXECUTION",
            lambda: self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("SATISFIED"),
            ),
        )
        self.assertEqual(self.handoff_ref, self.service.workflow.current_tip(self.handoff_ref)["nodeRef"])

    def test_step_cardinality_and_sealed_request_are_not_caller_replaceable(self) -> None:
        opened = self.open()
        original = self.step("action", "ACTION", "print('SEALED')")
        draft = self.draft([self.flow("flow", [original])])
        sealed = self.seal(opened, draft)
        original["argv"] = ["-c", "raise SystemExit('SUBSTITUTED')"]
        first = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="flow",
            step_id="action",
        )
        artifact = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=first["attempts"][0]["artifactRef"],
        )
        self.assertIn("SEALED", artifact["payload"]["stdout"]["text"])
        self.assert_code(
            "STEP_CARDINALITY_EXCEEDED",
            lambda: self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="flow",
                step_id="action",
            ),
        )

    def test_readback_polling_preserves_every_attempt_and_one_request_digest(self) -> None:
        state = Path(self.temporary.name) / "poll-state"
        code = (
            "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
            "n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n)); "
            "print('observed' if n >= 3 else 'miss'); raise SystemExit(0 if n >= 3 else 7)"
        )
        opened = self.open(tool_cost=10)
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "poll",
                        [self.step("read", "READBACK", code, argv_extra=[str(state)], poll_attempts=3)],
                    )
                ]
            ),
        )
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="poll",
            step_id="read",
        )
        self.assertEqual(3, len(execution["attempts"]))
        self.assertEqual(1, len({item["canonicalRequestDigest"] for item in execution["attempts"]}))
        exits = [item["result"]["exitCode"] for item in execution["attempts"]]
        self.assertEqual([7, 7, 0], exits)
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])

    def test_post_hoc_or_disconnected_mapping_cannot_supply_missing_required_flow(self) -> None:
        opened = self.open()
        first = self.flow("producer", [self.step("produce", "ACTION", "print('producer')")])
        second = self.flow("consumer", [self.step("consume", "ACTION", "print('consumer')")])
        sealed = self.seal(opened, self.draft([first, second]))
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="producer",
            step_id="produce",
        )
        self.assert_code(
            "FORGED_OUTCOME_WITHOUT_EXECUTION",
            lambda: self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("SATISFIED"),
            ),
        )

        other = self.open() if False else None
        self.assertIsNone(other)  # the active claim remains; no competing post-hoc run can start

    def test_invalid_bidirectional_mapping_releases_only_unstarted_claim(self) -> None:
        opened = self.open()
        malformed = self.flow("mapped", [self.step("action", "ACTION", "print('ok')")])
        malformed["criterionRefs"] = []
        self.assert_code(
            "MALFORMED_VERIFICATION_DRAFT",
            lambda: self.seal(opened, self.draft([malformed])),
        )
        self.assertIsNone(self.service.workflow.active_claim(self.handoff_ref))

        started = self.open()
        sealed = self.seal(
            started,
            self.draft([self.flow("sealed", [self.step("action", "ACTION", "print('ok')")])]),
        )
        with self.assertRaises(verification_run.workflow_store.WorkflowStoreError) as raised:
            self.service.workflow.release_unstarted_claim(
                claimant_capability=started["assessor"]["capability"],
                claim_ref=started["claim"]["claimRef"],
            )
        self.assertEqual("CLAIM_HAS_DURABLE_FACTS", raised.exception.code)
        self.assertEqual("SEALED", self.service.read_run(sealed["verificationRunRef"])["state"])

    def test_retain_without_executed_terminal_readback_cannot_be_verified(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "retained",
                        [
                            self.step("action", "ACTION", "print('created')"),
                            self.step("cleanup", "CLEANUP", "print('cleaned')"),
                        ],
                        requirement="RETAIN",
                    )
                ]
            ),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="retained",
            step_id="action",
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="retained",
            step_id="cleanup",
        )
        self.assert_code(
            "STEP_CARDINALITY_EXCEEDED",
            lambda: self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="retained",
                step_id="cleanup",
            ),
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("RETAIN_TERMINAL_READBACK_MISSING", result["reasonCodes"])

    def test_start_identity_mismatch_publishes_preflight_incomplete_with_zero_actions(self) -> None:
        opened = self.open()
        (self.project / "external-change.txt").write_text("changed\n", encoding="utf-8")
        draft = self.draft(
            [self.flow("flow", [self.step("action", "ACTION", "print('must-not-run')")])]
        )
        original_publish = self.service.workflow.publish_successor

        def fail_once(**_kwargs):
            raise verification_run.workflow_store.WorkflowStoreError(
                "SIMULATED_PUBLICATION_INTERRUPTION", "preflight publication was interrupted"
            )

        self.service.workflow.publish_successor = fail_once
        try:
            self.assert_code(
                "SIMULATED_PUBLICATION_INTERRUPTION",
                lambda: self.seal(opened, draft),
            )
        finally:
            self.service.workflow.publish_successor = original_publish

        result = self.seal(opened, draft)
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIsNone(result["sealedPlanDigest"])
        self.assertEqual(["CANDIDATE_IDENTITY_UNAVAILABLE_AT_START"], result["reasonCodes"])
        run = self.service.read_run(result["verificationRunRef"])
        self.assertEqual([], run["attempts"])
        self.assertEqual("CLOSED", run["state"])
        connection = self.service.workflow._connect()
        try:
            reservation = connection.execute(
                "SELECT closure_used_json FROM budget_reservations WHERE reservation_ref = ?",
                (opened["budgetReservation"]["reservationRef"],),
            ).fetchone()
            closure_used = self.service.workflow._stored_budget(
                reservation["closure_used_json"], "reservation.closureUsed"
            )
        finally:
            connection.close()
        self.assertEqual(1, closure_used["closureOperations"])

    def test_identity_drift_stops_execution_and_forbids_verified(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft([self.flow("flow", [self.step("action", "ACTION", "print('must-not-run')")])]),
        )
        (self.project / "drift.txt").write_text("drift\n", encoding="utf-8")
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="flow",
            step_id="action",
        )
        self.assertEqual("IDENTITY_DRIFT", execution["attempts"][0]["status"])
        self.assert_code(
            "FORGED_OUTCOME_WITHOUT_EXECUTION",
            lambda: self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("SATISFIED"),
            ),
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("INCONCLUSIVE"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("SOURCE_IDENTITY_DRIFT", result["reasonCodes"])

    def test_unknown_authorization_preflight_is_blocked_and_no_step_runs(self) -> None:
        opened = self.open()
        unknown = {
            "authorizationRef": f"authorization:v1:{uuid.uuid4().hex}",
            "scopeSha256": "a" * 64,
        }
        result = self.seal(
            opened,
            self.draft(
                [self.flow("flow", [self.step("action", "ACTION", "print('must-not-run')")])],
                authorizations=[unknown],
            ),
        )
        self.assertEqual("BLOCKED", result["verificationStatus"])
        self.assertEqual(["AUTHORIZATION_UNAVAILABLE"], result["reasonCodes"])
        self.assertEqual([], self.service.read_run(result["verificationRunRef"])["attempts"])

    def test_role_capabilities_are_not_interchangeable(self) -> None:
        opened = self.open()
        draft = self.draft([self.flow("flow", [self.step("action", "ACTION", "print('ok')")])])
        self.assert_code(
            "ROLE_CAPABILITY_MISMATCH",
            lambda: self.service.seal_run(
                assessor_capability=self.coordinator["capability"],
                claim_ref=opened["claim"]["claimRef"],
                implementation_handoff_ref=self.handoff_ref,
                verification_draft=draft,
            ),
        )
        sealed = self.seal(opened, draft)
        self.assert_code(
            "ROLE_CAPABILITY_MISMATCH",
            lambda: self.service.execute_step(
                assessor_capability=self.coordinator["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="flow",
                step_id="action",
            ),
        )

    def test_failure_publication_remediation_handoff_and_fresh_full_ac_verification(self) -> None:
        first_open = self.open()
        first_sealed = self.seal(
            first_open,
            self.draft(
                [
                    self.flow(
                        "detect-defect",
                        [self.step("observe-defect", "ACTION", "print('observed contradiction')")],
                    )
                ]
            ),
        )
        first_execution = self.service.execute_step(
            assessor_capability=first_open["assessor"]["capability"],
            verification_run_ref=first_sealed["verificationRunRef"],
            flow_id="detect-defect",
            step_id="observe-defect",
        )
        failed = self.service.publish_result(
            assessor_capability=first_open["assessor"]["capability"],
            verification_run_ref=first_sealed["verificationRunRef"],
            criterion_assessments=self.assessment("CONTRADICTED"),
        )
        self.assertEqual("VERIFICATION_FAILED", failed["verificationStatus"])

        remediation_open = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=failed["verificationResultRef"],
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        capsule_root = Path(self.temporary.name) / "capsules"
        transaction_store = verification_run.handoff_contract.implementation_transaction.ImplementationTransactionStore(
            self.workflow_root,
            capsule_root,
        )
        transaction = transaction_store.start_remediation(
            remediator_capability=remediation_open["remediator"]["capability"],
            worker_capability=remediation_open["worker"]["capability"],
            claim_ref=remediation_open["claim"]["claimRef"],
            project_root=self.project,
            admission={
                "disposition": "ADMITTED",
                "criterionRefs": self.criteria,
                "authorityDeltaDigest": "c" * 64,
                "desiredOutcomeUnchanged": True,
                "acceptanceMeaningUnchanged": True,
                "scopeAndNonGoalsUnchanged": True,
                "materialProductDecisionRequired": False,
                "safetyAndOwnershipAuthorized": True,
            },
        )
        envelope = transaction_store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="remediation-1",
            criterion_refs=self.criteria,
            allowed_paths=["product.txt"],
            forbidden_paths=[],
        )
        transaction_store.begin_worker_call(
            worker_capability=remediation_open["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.product_file.write_text("fixed\n", encoding="utf-8")
        check = transaction_store.run_check(
            transaction_capability=transaction["transactionCapability"],
            executable="python3",
            argv=["-c", "from pathlib import Path; assert Path('product.txt').read_text() == 'fixed\\n'"],
            cwd=self.project,
        )
        self.assertEqual(0, check["result"]["exitCode"])
        transaction_store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        transaction_store.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": ["product.txt"],
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )
        prepared = transaction_store.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        self.service.workflow.consume_budget(
            actor_capability=remediation_open["remediator"]["capability"],
            reservation_ref=remediation_open["budgetReservation"]["reservationRef"],
            category="CLOSURE",
            amounts=self.budget(closureOperations=1),
        )
        publisher = verification_run.handoff_contract.HandoffPublisher(
            self.workflow_root,
            capsule_root,
        )
        successor = publisher.publish(
            {
                "protocolVersion": "implementation-handoff-v1",
                "implementationTransactionRef": transaction["transactionRef"],
                "actorCapability": remediation_open["remediator"]["capability"],
                "planningSeal": self.planning_seal,
                "criterionAccounting": [{**self.criteria[0], "taskIds": ["remediation-1"]}],
                "unresolvedImplementationItems": [],
            }
        )
        self.assertEqual(self.source, successor["baselineSourceIdentity"])
        self.assertEqual(prepared["finalSourceIdentity"], successor["finalSourceIdentity"])
        self.assertNotEqual(self.source, successor["finalSourceIdentity"])

        self.handoff_ref = successor["implementationHandoffRef"]
        self.handoff_payload = successor
        self.source = successor["finalSourceIdentity"]
        second_open = self.open()
        second_sealed = self.seal(
            second_open,
            self.draft(
                [
                    self.flow(
                        "fresh-full-ac",
                        [self.step("observe-fixed", "ACTION", "print('fixed behavior')")],
                    )
                ]
            ),
        )
        self.assertNotEqual(first_open["assessor"]["actorRef"], second_open["assessor"]["actorRef"])
        self.service.execute_step(
            assessor_capability=second_open["assessor"]["capability"],
            verification_run_ref=second_sealed["verificationRunRef"],
            flow_id="fresh-full-ac",
            step_id="observe-fixed",
        )
        verified = self.service.publish_result(
            assessor_capability=second_open["assessor"]["capability"],
            verification_run_ref=second_sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", verified["verificationStatus"])
        second_run = self.service.read_run(second_sealed["verificationRunRef"])
        self.assertEqual(1, len(second_run["attempts"]))
        self.assertNotEqual(
            first_execution["attempts"][0]["artifactRef"],
            second_run["attempts"][0]["artifactRef"],
        )
        self.assertEqual(
            [self.criteria[0]],
            [
                {
                    "criterionIndex": item["criterionIndex"],
                    "criterionRawSha256": item["criterionRawSha256"],
                }
                for item in second_run["sealedPlan"]["criteria"]
            ],
        )

    def test_remediation_cannot_open_before_failed_result_is_published(self) -> None:
        opened = self.open()
        self.seal(
            opened,
            self.draft([self.flow("flow", [self.step("action", "ACTION", "print('contradiction')")])]),
        )
        self.assert_code(
            "REMEDIATION_REQUIRES_PUBLISHED_FAILURE",
            lambda: self.service.open_remediation(
                coordinator_capability=self.coordinator["capability"],
                failed_verification_result_ref=self.workflow_module.allocate_ref("VERIFICATION_RESULT"),
                spend_budget=self.budget(remediationTransactions=1, workerCalls=1),
                closure_budget=self.budget(closureOperations=1),
            ),
        )

    def test_ambiguous_cross_run_effect_is_blocked_until_exact_idempotency_authority(self) -> None:
        executable = Path(self.temporary.name) / "effect-command"

        def install_executable() -> None:
            executable.write_text("#!/bin/sh\nprintf 'effect-attempt\\n'\n", encoding="utf-8")
            executable.chmod(0o700)

        install_executable()
        ambiguous_step = self.step("effect", "ACTION", "print('unused')")
        ambiguous_step["executable"] = str(executable.resolve())
        ambiguous_step["argv"] = []
        first_open = self.open()
        first_sealed = self.seal(
            first_open,
            self.draft([self.flow("effect-flow", [ambiguous_step])]),
        )
        executable.unlink()
        first_execution = self.service.execute_step(
            assessor_capability=first_open["assessor"]["capability"],
            verification_run_ref=first_sealed["verificationRunRef"],
            flow_id="effect-flow",
            step_id="effect",
        )
        self.assertEqual("TOOL_ERROR", first_execution["attempts"][0]["status"])
        incomplete = self.service.publish_result(
            assessor_capability=first_open["assessor"]["capability"],
            verification_run_ref=first_sealed["verificationRunRef"],
            criterion_assessments=self.assessment("INCONCLUSIVE"),
        )
        self.assertEqual("INCOMPLETE", incomplete["verificationStatus"])

        install_executable()
        second_step = self.step("effect", "ACTION", "print('unused')")
        second_step["executable"] = str(executable.resolve())
        second_step["argv"] = []
        blocked_open = self.open()
        blocked = self.seal(
            blocked_open,
            self.draft([self.flow("effect-flow", [second_step])]),
        )
        self.assertEqual("BLOCKED", blocked["verificationStatus"])
        self.assertEqual(
            ["AMBIGUOUS_PRIOR_EFFECT_REPLAY_FORBIDDEN"],
            blocked["reasonCodes"],
        )
        self.assertEqual([], self.service.read_run(blocked["verificationRunRef"])["attempts"])

        third_step = self.step("effect", "ACTION", "print('unused')")
        third_step["executable"] = str(executable.resolve())
        third_step["argv"] = []
        preview = self.service.preview_process_step(
            step=third_step,
            project_root=self.project,
            final_source_identity=self.source,
        )
        scope = self.service.replay_authorization_scope(
            mechanism="EXACT_IDEMPOTENCY",
            prior_run_ref=first_sealed["verificationRunRef"],
            prior_flow_id="effect-flow",
            prior_step_id="effect",
            new_request_digest=preview["canonicalRequestDigest"],
            target_binding_digest=preview["sourceBindingDigest"],
        )
        authorization = self.service.workflow.issue_authorization(
            coordinator_capability=self.coordinator["capability"],
            scope_sha256=scope,
        )
        authorized_open = self.open()
        authorized = self.seal(
            authorized_open,
            self.draft(
                [self.flow("effect-flow", [third_step])],
                authorizations=[
                    {
                        "authorizationRef": authorization["authorizationRef"],
                        "scopeSha256": authorization["scopeSha256"],
                    }
                ],
            ),
        )
        self.assertEqual("SEALED", authorized["state"])
        self.service.execute_step(
            assessor_capability=authorized_open["assessor"]["capability"],
            verification_run_ref=authorized["verificationRunRef"],
            flow_id="effect-flow",
            step_id="effect",
        )
        verified = self.service.publish_result(
            assessor_capability=authorized_open["assessor"]["capability"],
            verification_run_ref=authorized["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", verified["verificationStatus"])

    def test_exact_structured_repeat_stops_second_automatic_remediation_only_on_match(self) -> None:
        def publish_same_failure() -> tuple[dict[str, object], dict[str, object]]:
            opened = self.open()
            sealed = self.seal(
                opened,
                self.draft(
                    [
                        self.flow(
                            "repeat-flow",
                            [self.step("repeat-action", "ACTION", "print('same-terminal-fact')")],
                        )
                    ]
                ),
            )
            self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="repeat-flow",
                step_id="repeat-action",
            )
            failed = self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("CONTRADICTED"),
            )
            return failed, sealed

        first_failed, _ = publish_same_failure()
        successor, _, transaction_store = self.remediate_failed_result(
            first_failed,
            product_text="first-remediation\n",
            task_id="first-remediation",
        )
        self.handoff_ref = successor["implementationHandoffRef"]
        self.handoff_payload = successor
        self.source = successor["finalSourceIdentity"]

        second_failed, _ = publish_same_failure()
        product_before = self.product_file.read_bytes()
        second_open = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=second_failed["verificationResultRef"],
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        with self.assertRaises(
            verification_run.handoff_contract.implementation_transaction.TransactionError
        ) as raised:
            transaction_store.start_remediation(
                remediator_capability=second_open["remediator"]["capability"],
                worker_capability=second_open["worker"]["capability"],
                claim_ref=second_open["claim"]["claimRef"],
                project_root=self.project,
                admission={
                    "disposition": "ADMITTED",
                    "criterionRefs": self.criteria,
                    "authorityDeltaDigest": "d" * 64,
                    "desiredOutcomeUnchanged": True,
                    "acceptanceMeaningUnchanged": True,
                    "scopeAndNonGoalsUnchanged": True,
                    "materialProductDecisionRequired": False,
                    "safetyAndOwnershipAuthorized": True,
                },
            )
        self.assertEqual("EXACT_REPEAT_REMEDIATION_STOP", raised.exception.code)
        self.assertEqual(product_before, self.product_file.read_bytes())
        self.assertIsNone(self.service.workflow.active_claim(self.service.workflow.read_node(self.handoff_ref)["rootRef"]))
        self.assertEqual(
            second_failed["verificationResultRef"],
            self.service.workflow.current_tip(self.service.workflow.read_node(self.handoff_ref)["rootRef"])["nodeRef"],
        )

    def test_remediation_cannot_reuse_an_ancestor_source_identity(self) -> None:
        def publish_failure(message: str) -> dict[str, object]:
            opened = self.open()
            sealed = self.seal(
                opened,
                self.draft(
                    [
                        self.flow(
                            "ancestor-check",
                            [self.step("ancestor-action", "ACTION", f"print({message!r})")],
                        )
                    ]
                ),
            )
            self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="ancestor-check",
                step_id="ancestor-action",
            )
            return self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("CONTRADICTED"),
            )

        first_failed = publish_failure("first contradiction")
        successor, _, transaction_store = self.remediate_failed_result(
            first_failed,
            product_text="intermediate\n",
            task_id="first-progress",
        )
        original_handoff = self.service.workflow.read_node(self.handoff_ref)
        self.handoff_ref = successor["implementationHandoffRef"]
        self.handoff_payload = successor
        self.source = successor["finalSourceIdentity"]

        second_failed = publish_failure("different contradiction")
        remediation_open = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=second_failed["verificationResultRef"],
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        transaction = transaction_store.start_remediation(
            remediator_capability=remediation_open["remediator"]["capability"],
            worker_capability=remediation_open["worker"]["capability"],
            claim_ref=remediation_open["claim"]["claimRef"],
            project_root=self.project,
            admission={
                "disposition": "ADMITTED",
                "criterionRefs": self.criteria,
                "authorityDeltaDigest": "e" * 64,
                "desiredOutcomeUnchanged": True,
                "acceptanceMeaningUnchanged": True,
                "scopeAndNonGoalsUnchanged": True,
                "materialProductDecisionRequired": False,
                "safetyAndOwnershipAuthorized": True,
            },
        )
        self.assertEqual("NO_MATCH", transaction["exactRepeatDisposition"])
        envelope = transaction_store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="revert-to-ancestor",
            criterion_refs=self.criteria,
            allowed_paths=["product.txt"],
            forbidden_paths=[],
        )
        transaction_store.begin_worker_call(
            worker_capability=remediation_open["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.product_file.write_text("stable\n", encoding="utf-8")
        transaction_store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        transaction_store.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": ["product.txt"],
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )
        with self.assertRaises(
            verification_run.handoff_contract.implementation_transaction.TransactionError
        ) as raised:
            transaction_store.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            )
        self.assertEqual("ANCESTOR_SOURCE_REUSED", raised.exception.code)
        self.assertEqual(
            second_failed["verificationResultRef"],
            self.service.workflow.current_tip(original_handoff["rootRef"])["nodeRef"],
        )
        self.assertEqual(
            "OPEN", transaction_store.read_transaction(transaction["transactionRef"])["state"]
        )
        self.assertEqual(original_handoff, self.service.workflow.read_node(original_handoff["nodeRef"]))

    def test_declared_contradiction_stops_later_actions_but_closes_with_not_run_ledger(self) -> None:
        opened = self.open()
        first = self.flow(
            "first-obligation",
            [self.step("first-action", "ACTION", "print('contradiction')")],
        )
        second = self.flow(
            "later-obligation",
            [self.step("later-action", "ACTION", "print('must-not-run')")],
        )
        sealed = self.seal(opened, self.draft([first, second]))
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="first-obligation",
            step_id="first-action",
        )
        declaration = self.service.declare_contradiction(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_ref=self.criteria[0],
        )
        self.assertEqual(self.criteria[0]["criterionRawSha256"], declaration["criterionRawSha256"])
        self.assert_code(
            "ACTION_STOPPED_AFTER_CONTRADICTION",
            lambda: self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="later-obligation",
                step_id="later-action",
            ),
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("CONTRADICTED"),
        )
        self.assertEqual("VERIFICATION_FAILED", result["verificationStatus"])
        run = self.service.read_run(sealed["verificationRunRef"])
        later = [item for item in run["attempts"] if item["stepId"] == "later-action"]
        self.assertEqual(["NOT_RUN"], [item["status"] for item in later])
        self.assertEqual("NOT_RUN_PRIOR_CONTRADICTION", later[0]["result"]["reason"])

    def test_action_timeout_can_be_satisfied_by_sealed_authoritative_readback(self) -> None:
        state = Path(self.temporary.name) / "timeout-effect"
        action_code = (
            "from pathlib import Path; import sys,time; "
            "Path(sys.argv[1]).write_text('effect'); time.sleep(2)"
        )
        read_code = (
            "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
            "print(p.read_text()); raise SystemExit(0 if p.read_text() == 'effect' else 9)"
        )
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "timeout-readback",
                        [
                            self.step("action", "ACTION", action_code, argv_extra=[str(state)]),
                            self.step("read", "READBACK", read_code, argv_extra=[str(state)]),
                        ],
                    )
                ]
            ),
        )
        original_timeout = verification_run.MAX_PROCESS_TIMEOUT_SECONDS
        verification_run.MAX_PROCESS_TIMEOUT_SECONDS = 1
        try:
            action = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="timeout-readback",
                step_id="action",
            )
        finally:
            verification_run.MAX_PROCESS_TIMEOUT_SECONDS = original_timeout
        self.assertEqual("TIMED_OUT", action["attempts"][0]["status"])
        readback = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="timeout-readback",
            step_id="read",
        )
        self.assertEqual(0, readback["attempts"][0]["result"]["exitCode"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])
        self.assertEqual([], result["reasonCodes"])

    def test_action_timeout_without_later_readback_is_incomplete(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "unresolved-action",
                        [self.step("action", "ACTION", "import time; time.sleep(0.2)")],
                    )
                ]
            ),
        )
        original_timeout = verification_run.MAX_PROCESS_TIMEOUT_SECONDS
        verification_run.MAX_PROCESS_TIMEOUT_SECONDS = 0.05
        try:
            execution = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="unresolved-action",
                step_id="action",
            )
        finally:
            verification_run.MAX_PROCESS_TIMEOUT_SECONDS = original_timeout
        self.assertEqual("TIMED_OUT", execution["attempts"][0]["status"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("PROCESS_OBSERVATION_INCONCLUSIVE", result["reasonCodes"])

    def test_retain_terminal_readback_timeout_is_incomplete(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "retained-timeout",
                        [self.step("terminal-readback", "READBACK", "import time; time.sleep(0.2)")],
                        requirement="RETAIN",
                    )
                ]
            ),
        )
        original_timeout = verification_run.MAX_PROCESS_TIMEOUT_SECONDS
        verification_run.MAX_PROCESS_TIMEOUT_SECONDS = 0.05
        try:
            execution = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="retained-timeout",
                step_id="terminal-readback",
            )
        finally:
            verification_run.MAX_PROCESS_TIMEOUT_SECONDS = original_timeout
        self.assertEqual("TIMED_OUT", execution["attempts"][0]["status"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("PROCESS_OBSERVATION_INCONCLUSIVE", result["reasonCodes"])
        self.assertIn("RETAIN_TERMINAL_READBACK_INCONCLUSIVE", result["reasonCodes"])

    def test_retain_terminal_readback_tool_error_is_incomplete(self) -> None:
        readback_tool = Path(self.temporary.name) / "readback-tool"
        readback_tool.write_text("#!/bin/sh\nprintf 'readback'\n", encoding="utf-8")
        readback_tool.chmod(0o700)
        readback = self.step("terminal-readback", "READBACK", "print('unused')")
        readback["executable"] = str(readback_tool.resolve())
        readback["argv"] = []
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [self.flow("retained-tool-error", [readback], requirement="RETAIN")]
            ),
        )
        readback_tool.unlink()
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="retained-tool-error",
            step_id="terminal-readback",
        )
        self.assertEqual("TOOL_ERROR", execution["attempts"][0]["status"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("PROCESS_OBSERVATION_INCONCLUSIVE", result["reasonCodes"])
        self.assertIn("RETAIN_TERMINAL_READBACK_INCONCLUSIVE", result["reasonCodes"])

    def test_readback_timeout_can_be_resolved_by_later_identical_poll(self) -> None:
        state = Path(self.temporary.name) / "readback-timeout-state"
        code = (
            "from pathlib import Path; import sys,time; p=Path(sys.argv[1]); "
            "first=not p.exists(); p.write_text('started'); "
            "time.sleep(0.2) if first else None; print('ready')"
        )
        opened = self.open(tool_cost=10)
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "readback-retry",
                        [
                            self.step(
                                "read",
                                "READBACK",
                                code,
                                argv_extra=[str(state)],
                                poll_attempts=2,
                            )
                        ],
                    )
                ]
            ),
        )
        original_timeout = verification_run.MAX_PROCESS_TIMEOUT_SECONDS
        verification_run.MAX_PROCESS_TIMEOUT_SECONDS = 0.05
        try:
            execution = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="readback-retry",
                step_id="read",
            )
        finally:
            verification_run.MAX_PROCESS_TIMEOUT_SECONDS = original_timeout
        self.assertEqual(["TIMED_OUT", "EXITED"], [item["status"] for item in execution["attempts"]])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])
        self.assertEqual([], result["reasonCodes"])

    def test_cleanup_tool_error_is_incomplete(self) -> None:
        cleanup_tool = Path(self.temporary.name) / "cleanup-tool"
        cleanup_tool.write_text("#!/bin/sh\nprintf 'cleanup'\n", encoding="utf-8")
        cleanup_tool.chmod(0o700)
        cleanup = self.step("cleanup", "CLEANUP", "print('unused')")
        cleanup["executable"] = str(cleanup_tool.resolve())
        cleanup["argv"] = []
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "cleanup-error",
                        [self.step("action", "ACTION", "print('created')"), cleanup],
                    )
                ]
            ),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="cleanup-error",
            step_id="action",
        )
        cleanup_tool.unlink()
        cleanup_execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="cleanup-error",
            step_id="cleanup",
        )
        self.assertEqual("TOOL_ERROR", cleanup_execution["attempts"][0]["status"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("PROCESS_OBSERVATION_INCONCLUSIVE", result["reasonCodes"])

    def test_cleanup_timeout_is_incomplete(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "cleanup-timeout",
                        [
                            self.step("action", "ACTION", "print('created')"),
                            self.step("cleanup", "CLEANUP", "import time; time.sleep(0.2)"),
                        ],
                    )
                ]
            ),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="cleanup-timeout",
            step_id="action",
        )
        original_timeout = verification_run.MAX_PROCESS_TIMEOUT_SECONDS
        verification_run.MAX_PROCESS_TIMEOUT_SECONDS = 0.05
        try:
            cleanup = self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="cleanup-timeout",
                step_id="cleanup",
            )
        finally:
            verification_run.MAX_PROCESS_TIMEOUT_SECONDS = original_timeout
        self.assertEqual("TIMED_OUT", cleanup["attempts"][0]["status"])
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("INCOMPLETE", result["verificationStatus"])
        self.assertIn("PROCESS_OBSERVATION_INCONCLUSIVE", result["reasonCodes"])

    def test_legacy_ambient_environment_plan_cannot_execute_under_process_v2(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [self.flow("legacy-policy", [self.step("read", "READBACK", "print('unused')")])]
            ),
        )
        with self.service.workflow._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM verification_runs WHERE run_ref = ?",
                (sealed["verificationRunRef"],),
            ).fetchone()
            plan = self.service._load_plan(row)
            stored_step = plan["flows"][0]["steps"][0]
            stored_step.pop("executorVersion")
            stored_step.pop("environmentPolicy")
            encoded = verification_run._canonical_json(plan)
            connection.execute(
                "UPDATE verification_runs SET sealed_plan_json = ?, sealed_plan_sha256 = ? WHERE run_ref = ?",
                (
                    encoded,
                    hashlib.sha256(encoded).hexdigest(),
                    sealed["verificationRunRef"],
                ),
            )
        self.assert_code(
            "SEALED_EXECUTOR_POLICY_RETIRED",
            lambda: self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id="legacy-policy",
                step_id="read",
            ),
        )

    def test_started_action_requires_every_presealed_cleanup_before_result_closure(self) -> None:
        opened = self.open()
        sealed = self.seal(
            opened,
            self.draft(
                [
                    self.flow(
                        "cleanup-flow",
                        [
                            self.step("action", "ACTION", "print('created')"),
                            self.step("cleanup", "CLEANUP", "print('cleaned')"),
                        ],
                    )
                ]
            ),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="cleanup-flow",
            step_id="action",
        )
        self.assert_code(
            "REQUIRED_CLEANUP_NOT_EXECUTED",
            lambda: self.service.publish_result(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                criterion_assessments=self.assessment("INCONCLUSIVE"),
            ),
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="cleanup-flow",
            step_id="cleanup",
        )
        result = self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=self.assessment("SATISFIED"),
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])


if __name__ == "__main__":
    unittest.main()
