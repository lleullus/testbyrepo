from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


ownership_snapshot = load_module(
    "greenfield_ownership_snapshot",
    IMPLEMENTATION_ROOT / "tools/task-ownership-snapshot/ownership_snapshot.py",
)
implementation_result = load_module(
    "greenfield_implementation_result",
    IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py",
)


class GreenfieldAdmissionPilotTests(unittest.TestCase):
    def test_all_fixed_bootstrap_completes_without_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "product"
            project.mkdir()
            (project / "user-note.txt").write_text("preserve me\n", encoding="utf-8")
            planning = root / "planning"
            planning.mkdir()
            spec = planning / "SPEC.md"
            ticket = planning / "TICKET.md"
            spec.write_text(
                "# Fixed bootstrap\nStatus: approved\nOwner: user\n\n"
                "## Problem\nThe target is absent.\n\n"
                "## Desired Outcome\nThe fixed readiness marker exists.\n\n"
                "## Requirements\n- First product artifacts are authorized in this scope.\n"
                "- No external identity applies.\n\n"
                "## Non-Goals\n- No external effect.\n\n"
                "## Implementation Constraints\n- Every material bootstrap choice is fixed: create `READY` with exact bytes `ready\\n`.\n\n"
                "## Verification Expectations\nRead the fixed marker and preserved note.\n\n"
                "## UI / UX\nNot applicable\n\n"
                "## Open Questions\nNone\n",
                encoding="utf-8",
            )
            ticket.write_text(
                "# Fixed bootstrap\nStatus: ready\nParent-Spec: SPEC.md\n"
                f"Project-Root: {project}\nWorker:\nUI: no\n\n"
                "## Goal\nCreate the fixed readiness marker.\n\n"
                "## Acceptance Criteria\n- `READY` contains exact bytes `ready\\n` and the user note is unchanged.\n\n"
                "## Scope\nThe fixed readiness marker.\n\n"
                "## Non-Goals\n- External effects.\n\n"
                "## Blockers\nNone\n\n"
                "## Verification\nRead the marker and user note.\n\n"
                "## References\nNone\n",
                encoding="utf-8",
            )
            self.assertNotIn("delegat", spec.read_text(encoding="utf-8").lower())

            capsule_root = root / "capsules"
            capsules = implementation_result.baseline_capsule.CapsuleStore(capsule_root)
            capsule = capsules.create(project)
            (project / "READY").write_bytes(b"ready\n")
            self.assertEqual(b"ready\n", (project / "READY").read_bytes())
            self.assertEqual("preserve me\n", (project / "user-note.txt").read_text(encoding="utf-8"))

            final_identity = implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"]
            seal = {
                "ticketPath": str(ticket.resolve()),
                "ticketSha256": digest(ticket),
                "specPath": str(spec.resolve()),
                "specSha256": digest(spec),
                "blockerFiles": [],
            }
            criteria = implementation_result.acceptance_criteria_from_ticket(ticket)
            request = {
                "protocolVersion": "implementation-result-v3",
                "projectRoot": str(project.resolve()),
                "planningSeal": seal,
                "capsuleRef": capsule["capsuleRef"],
                "finalSourceIdentity": final_identity,
                "completionRecord": {
                    "acceptanceCriteriaDigest": implementation_result.acceptance_criteria_digest(criteria),
                    "supplementalLocalAuthorityBindings": [],
                    "coverage": [
                        {
                            **criteria[0],
                            "state": "ESTABLISHED",
                            "evidenceRequirements": [
                                {
                                    "requirementId": "source-requirement-1",
                                    "kind": "SOURCE",
                                    "state": "ESTABLISHED",
                                    "evidenceRefs": ["source-evidence-1"],
                                }
                            ],
                        }
                    ],
                    "sourceEvidence": [
                        {
                            "evidenceId": "source-evidence-1",
                            "coveredRequirementIds": ["source-requirement-1"],
                            "authorityLocators": ["Ticket:Acceptance Criteria[1]"],
                            "authorityBindingRefs": [],
                            "sourceIdentity": final_identity,
                            "reviewSummary": "Fixed marker and preserved note bytes match authority.",
                        }
                    ],
                    "runtimeObservations": [],
                    "unresolvedItems": [],
                },
            }
            result = implementation_result.ResultStore(root / "results", capsule_root).publish(request)
            self.assertEqual("IMPLEMENTATION_COMPLETE", result["implementationStatus"])

    def test_nonempty_root_without_target_readiness_uses_delegated_private_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "product"
            project.mkdir()
            preexisting = project / "user-note.txt"
            preexisting.write_text("preserve me\n", encoding="utf-8")
            planning = root / "planning"
            tickets = planning / "tickets"
            tickets.mkdir(parents=True)
            spec = planning / "SPEC.md"
            ticket = tickets / "TICKET-001.md"
            spec.write_text(
                "# First runnable behavior\nStatus: approved\nOwner: user\n\n"
                "## Problem\nThe current scope has no runnable product target.\n\n"
                "## Desired Outcome\nA user can run the first approved behavior.\n\n"
                "## Requirements\n- First product artifacts are authorized in this scope.\n- No external, public, registry, deployment, or persisted identity applies.\n\n"
                "## Non-Goals\n- No publication or external resource creation.\n\n"
                "## Implementation Constraints\n- Remaining private bootstrap choices are delegated to Implementation Lead and Worker.\n\n"
                "## Verification Expectations\nRun the public local entry point and observe `ready`.\n\n"
                "## UI / UX\nNot applicable\n\n"
                "## Open Questions\nNone\n",
                encoding="utf-8",
            )
            ticket.write_text(
                "# First runnable behavior\nStatus: ready\nParent-Spec: ../SPEC.md\n"
                f"Project-Root: {project}\nWorker:\nUI: no\n\n"
                "## Goal\nProvide the first runnable product behavior.\n\n"
                "## Acceptance Criteria\n- The public local entry point returns `ready` and the pre-existing user note remains unchanged.\n\n"
                "## Scope\nThe first runnable behavior in the current product scope.\n\n"
                "## Non-Goals\n- Package publication, external resources, and changes to pre-existing user files.\n\n"
                "## Blockers\nNone\n\n"
                "## Verification\nRun the public local entry point and observe `ready`; read back the user note.\n\n"
                "## References\nNone\n",
                encoding="utf-8",
            )
            self.assertNotIn("module identity", ticket.read_text(encoding="utf-8"))
            self.assertNotIn("app.py", ticket.read_text(encoding="utf-8"))

            capsule_root = root / "capsules"
            capsules = implementation_result.baseline_capsule.CapsuleStore(capsule_root)
            capsule = capsules.create(project)

            # Represents the selected Worker's bounded, implementation-owned bootstrap choice.
            app = project / "app.py"
            app.write_text('print("ready")\n', encoding="utf-8")
            self.assertEqual("preserve me\n", preexisting.read_text(encoding="utf-8"))
            final_identity = implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"]
            before = ownership_snapshot.capture(project)
            effect = subprocess.run(
                [sys.executable, "-B", str(app)],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual((0, "ready\n"), (effect.returncode, effect.stdout))
            self.assertEqual("preserve me\n", preexisting.read_text(encoding="utf-8"))
            after = ownership_snapshot.capture(project)
            self.assertEqual(before["identity"], after["identity"])

            seal = {
                "ticketPath": str(ticket.resolve()),
                "ticketSha256": digest(ticket),
                "specPath": str(spec.resolve()),
                "specSha256": digest(spec),
                "blockerFiles": [],
            }
            criteria = implementation_result.acceptance_criteria_from_ticket(ticket)
            observation = {
                "observationId": "runtime-observation-1",
                "coveredRequirementIds": ["runtime-requirement-1"],
                "entryPointAuthority": {
                    "authorityLocators": ["Ticket:Verification", "repository:public local entry point"],
                    "authorityBindingRefs": [],
                },
                "executionTargetBinding": {
                    "mode": "CURRENT_PROJECT_ROOT",
                    "authorityLocators": ["repository:python -B app.py"],
                    "finalSourceIdentity": final_identity,
                    "targetIdentityOrRevision": final_identity,
                    "bindingSummaryOrDigest": "Canonical current project root at final identity.",
                },
                "redactedInvocationSummary": "Ran the public local entry point.",
                "expectedEffectSummary": "Entry point returns ready and preserves the note.",
                "observedEffectSummary": "Entry point returned ready and note readback was unchanged.",
                "observationMode": "INDEPENDENT_READBACK",
                "readbackSummaryOrDigest": "Pre-existing note bytes remained unchanged.",
                "planningSealDigest": implementation_result.planning_seal_digest(seal),
                "sourceIdentityBefore": final_identity,
                "sourceIdentityAfter": final_identity,
                "projectDeltaBinding": {
                    "ownershipSnapshotIdentityBefore": before["identity"],
                    "ownershipSnapshotIdentityAfter": after["identity"],
                    "changedPathCount": 0,
                    "deltaSummaryOrDigest": "No project path changed during final exercise.",
                    "disposition": "CLEAR",
                },
                "cleanupDisposition": {
                    "required": False,
                    "state": "NOT_REQUIRED",
                    "authorityOrRationale": "The read-only exercise created no state.",
                    "readbackSummaryOrDigest": "",
                },
                "observedAt": "2026-08-01T00:00:00+00:00",
            }
            request = {
                "protocolVersion": "implementation-result-v3",
                "projectRoot": str(project.resolve()),
                "planningSeal": seal,
                "capsuleRef": capsule["capsuleRef"],
                "finalSourceIdentity": final_identity,
                "completionRecord": {
                    "acceptanceCriteriaDigest": implementation_result.acceptance_criteria_digest(criteria),
                    "supplementalLocalAuthorityBindings": [],
                    "coverage": [
                        {
                            **criteria[0],
                            "state": "ESTABLISHED",
                            "evidenceRequirements": [
                                {
                                    "requirementId": "runtime-requirement-1",
                                    "kind": "RUNTIME",
                                    "state": "ESTABLISHED",
                                    "evidenceRefs": ["runtime-observation-1"],
                                }
                            ],
                        }
                    ],
                    "sourceEvidence": [],
                    "runtimeObservations": [observation],
                    "unresolvedItems": [],
                },
            }
            result = implementation_result.ResultStore(root / "results", capsule_root).publish(request)
            self.assertEqual("IMPLEMENTATION_COMPLETE", result["implementationStatus"])
            self.assertEqual(str(ticket.resolve()), result["planningSeal"]["ticketPath"])
            self.assertEqual(final_identity, result["finalSourceIdentity"])


if __name__ == "__main__":
    unittest.main()
