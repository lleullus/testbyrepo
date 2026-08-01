from __future__ import annotations

import hashlib
import importlib.util
import shutil
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
    "runtime_exercise_ownership_snapshot",
    IMPLEMENTATION_ROOT / "tools/task-ownership-snapshot/ownership_snapshot.py",
)
implementation_result = load_module(
    "runtime_exercise_implementation_result",
    IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py",
)


DISCONNECTED_SOURCE = """\
import sys


def helper():
    return "connected"


if sys.argv[1] == "helper-check":
    print(helper())
else:
    print("bypassed")
"""


CONNECTED_SOURCE = DISCONNECTED_SOURCE.replace('print("bypassed")', "print(helper())")


PERSISTENT_SOURCE = """\
import json
import sys
from pathlib import Path


command, state_value = sys.argv[1:3]
state = Path(state_value)
if command == "put":
    state.write_text(json.dumps({"value": "stored"}), encoding="utf-8")
    print("stored")
elif command == "get":
    print(json.loads(state.read_text(encoding="utf-8"))["value"])
elif command == "delete":
    state.unlink()
    print("deleted")
"""


class RepresentativeRuntimeExercisePilotTests(unittest.TestCase):
    def planning(self, root: Path, project: Path, criterion: str) -> tuple[Path, Path, dict[str, object]]:
        planning = root / "planning"
        planning.mkdir()
        spec = planning / "SPEC.md"
        ticket = planning / "TICKET.md"
        spec.write_text("# Spec\nStatus: approved\nOwner: user\n", encoding="utf-8")
        ticket.write_text(
            "# Ticket\n"
            "Status: ready\n"
            "Parent-Spec: SPEC.md\n"
            f"Project-Root: {project}\n"
            "Worker:\n"
            "UI: no\n\n"
            "## Goal\nExpose the connected product behavior.\n\n"
            "## Acceptance Criteria\n"
            f"- {criterion}\n\n"
            "## Scope\nThe public entry point.\n\n"
            "## Non-Goals\nNone\n\n"
            "## Blockers\nNone\n\n"
            "## Verification\nRun the public entry point and observe its result.\n\n"
            "## References\nNone\n",
            encoding="utf-8",
        )
        seal = {
            "ticketPath": str(ticket.resolve()),
            "ticketSha256": digest(ticket),
            "specPath": str(spec.resolve()),
            "specSha256": digest(spec),
            "blockerFiles": [],
        }
        return ticket, spec, seal

    def runtime_request(
        self,
        project: Path,
        ticket: Path,
        seal: dict[str, object],
        capsule: dict[str, object],
        observation: dict[str, object] | None,
    ) -> dict[str, object]:
        final_identity = implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"]
        criteria = implementation_result.acceptance_criteria_from_ticket(ticket)
        return {
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
                "runtimeObservations": [] if observation is None else [observation],
                "unresolvedItems": [],
            },
        }

    def observation(
        self,
        final_identity: str,
        seal: dict[str, object],
        before_identity: str,
        after_identity: str,
        *,
        mode: str,
        target_summary: str,
        observation_mode: str,
        cleanup_required: bool,
        cleanup_readback: str,
    ) -> dict[str, object]:
        return {
            "observationId": "runtime-observation-1",
            "coveredRequirementIds": ["runtime-requirement-1"],
            "entryPointAuthority": {
                "authorityLocators": ["Ticket:Verification", "repository:app.py public CLI"],
                "authorityBindingRefs": [],
            },
            "executionTargetBinding": {
                "mode": mode,
                "authorityLocators": ["repository:python -B app.py"],
                "finalSourceIdentity": final_identity,
                "targetIdentityOrRevision": final_identity,
                "bindingSummaryOrDigest": target_summary,
            },
            "redactedInvocationSummary": "Ran the public CLI with task-owned non-production input.",
            "expectedEffectSummary": "The public result is connected.",
            "observedEffectSummary": "The public result was connected.",
            "observationMode": observation_mode,
            "readbackSummaryOrDigest": "Authoritative result matched the expected value.",
            "planningSealDigest": implementation_result.planning_seal_digest(seal),
            "sourceIdentityBefore": final_identity,
            "sourceIdentityAfter": final_identity,
            "projectDeltaBinding": {
                "ownershipSnapshotIdentityBefore": before_identity,
                "ownershipSnapshotIdentityAfter": after_identity,
                "changedPathCount": 0,
                "deltaSummaryOrDigest": "No project-root path changed during the final exercise.",
                "disposition": "CLEAR",
            },
            "cleanupDisposition": {
                "required": cleanup_required,
                "state": "COMPLETE" if cleanup_required else "NOT_REQUIRED",
                "authorityOrRationale": (
                    "Task-owned state and source materialization were removed."
                    if cleanup_required
                    else "The direct result created no persistent state."
                ),
                "readbackSummaryOrDigest": cleanup_readback,
            },
            "observedAt": "2026-08-01T00:00:00+00:00",
        }

    def test_helper_success_cannot_replace_lead_owned_final_entry_point_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            app = project / "app.py"
            app.write_text(DISCONNECTED_SOURCE, encoding="utf-8")
            ticket, _, seal = self.planning(root, project, "The public CLI returns `connected`.")
            capsules = implementation_result.baseline_capsule.CapsuleStore(root / "capsules")
            capsule = capsules.create(project)
            store = implementation_result.ResultStore(root / "results", root / "capsules")

            helper = subprocess.run(
                [sys.executable, "-B", str(app), "helper-check"],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual((0, "connected\n"), (helper.returncode, helper.stdout))
            actual = subprocess.run(
                [sys.executable, "-B", str(app), "run"],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual("bypassed\n", actual.stdout)
            with self.assertRaisesRegex(implementation_result.ResultError, "INCOMPLETE_COVERAGE"):
                store.publish(self.runtime_request(project, ticket, seal, capsule, None))

            app.write_text(CONNECTED_SOURCE, encoding="utf-8")
            final_identity = implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"]
            materialized = root / "final-source-materialization"
            materialized.mkdir(mode=0o700)
            shutil.copy2(app, materialized / "app.py")
            self.assertEqual(
                final_identity,
                implementation_result.baseline_capsule.capture_identity(materialized)["sourceIdentity"],
            )
            before = ownership_snapshot.capture(project)
            final_actual = subprocess.run(
                [sys.executable, "-B", str(materialized / "app.py"), "run"],
                cwd=materialized,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual((0, "connected\n"), (final_actual.returncode, final_actual.stdout))
            shutil.rmtree(materialized)
            self.assertFalse(materialized.exists())
            after = ownership_snapshot.capture(project)
            self.assertEqual(before["identity"], after["identity"])
            observation = self.observation(
                final_identity,
                seal,
                before["identity"],
                after["identity"],
                mode="SOURCE_BOUND_MATERIALIZATION",
                target_summary="Materialized source identity exactly equaled final source identity.",
                observation_mode="DIRECT_RESULT",
                cleanup_required=True,
                cleanup_readback="Materialization path was absent after cleanup.",
            )
            published = store.publish(self.runtime_request(project, ticket, seal, capsule, observation))
            self.assertEqual("IMPLEMENTATION_COMPLETE", published["implementationStatus"])
            request = self.runtime_request(project, ticket, seal, capsule, observation)
            request["completionRecord"]["runtimeObservations"][0].pop("projectDeltaBinding")
            with self.assertRaisesRegex(implementation_result.ResultError, "MALFORMED_RESULT"):
                store.publish(request)

    def test_persistent_effect_requires_readback_cleanup_and_clear_project_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            app = project / "app.py"
            app.write_text(PERSISTENT_SOURCE, encoding="utf-8")
            ticket, _, seal = self.planning(root, project, "The public CLI stores and retrieves `stored`.")
            capsules = implementation_result.baseline_capsule.CapsuleStore(root / "capsules")
            capsule = capsules.create(project)
            state = root / "task-state.json"
            before = ownership_snapshot.capture(project)
            put = subprocess.run(
                [sys.executable, "-B", str(app), "put", str(state)], capture_output=True, text=True, check=False
            )
            readback = subprocess.run(
                [sys.executable, "-B", str(app), "get", str(state)], capture_output=True, text=True, check=False
            )
            cleanup = subprocess.run(
                [sys.executable, "-B", str(app), "delete", str(state)], capture_output=True, text=True, check=False
            )
            self.assertEqual(("stored\n", "stored\n", "deleted\n"), (put.stdout, readback.stdout, cleanup.stdout))
            self.assertFalse(state.exists())
            after = ownership_snapshot.capture(project)
            self.assertEqual(before["identity"], after["identity"])
            final_identity = implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"]
            observation = self.observation(
                final_identity,
                seal,
                before["identity"],
                after["identity"],
                mode="CURRENT_PROJECT_ROOT",
                target_summary="The non-writing public command used the canonical final project root.",
                observation_mode="INDEPENDENT_READBACK",
                cleanup_required=True,
                cleanup_readback="The task-owned state path was absent after product-supported deletion.",
            )
            store = implementation_result.ResultStore(root / "results", root / "capsules")
            published = store.publish(self.runtime_request(project, ticket, seal, capsule, observation))
            self.assertEqual("INDEPENDENT_READBACK", published["completionRecord"]["runtimeObservations"][0]["observationMode"])


if __name__ == "__main__":
    unittest.main()
