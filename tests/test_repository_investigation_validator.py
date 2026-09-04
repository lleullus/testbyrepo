from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "companion-skills" / "repository-investigation" / "tools"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prepare_module = _load_module("repository_investigation_prepare", TOOLS / "prepare_investigation_workspace.py")
validator_module = _load_module("repository_investigation_validator", TOOLS / "validate_investigation.py")


def _artifact(project: Path, revision: str = "INV-001", *, status: str = "complete") -> str:
    completion = status.upper()
    if status == "partial":
        handoff_unknowns = "- Dynamic plugin registration could still change routing."
        decision_unknowns = "Dynamic plugin registration remains unresolved"
    else:
        handoff_unknowns = "- None"
        decision_unknowns = "None"

    return f"""# Wrapper Routing Repository Investigation

Artifact-Type: repository-investigation
Format-Version: 1
Status: {status}
Project-Root: {project}
Repository-Root: {project}
Investigation-Slug: wrapper-routing
Investigation-Revision: {revision}
Observed-At: 2026-09-04T18:00:00+09:00
Git-Branch: main
Git-Head: 0123456789abcdef0123456789abcdef01234567
Working-Tree-Before-Artifact: clean
Evidence-Authority: repository evidence only; not IIS planning authority

## Evidence Handoff

### Investigation Answer

Answer: The wrapper normalizes input and delegates lifecycle ownership to core.dispatch.
Based On: Finding 1

### Observed Current Product State

- State: CLI traffic reaches core.dispatch through the wrapper.
  Supporting Findings: Finding 1

### Existing Product Surfaces And Readbacks

- Trigger: invoke wrapper command
  Observable surface: CLI result
  Authoritative readback: CLI status output
  Supporting Findings: Finding 1

### State And Authority

- Statement: Lifecycle state is owned by core.dispatch.
  Supporting Findings: Finding 1

### Planning Constraint Candidates

- None

### Product Dependency Candidates

- None

### Material Unknowns

{handoff_unknowns}

### Load-Bearing Anchors

- A1 | SOURCE | src/wrapper.py | Wrapper.call | 01234567 | ANCHOR_LOCAL

## Investigation Charter

### Original Request

Investigate the wrapper before planning.

### Investigation Objective

Determine what the wrapper owns versus forwards.

### Decision Context

Establish a stable evidence baseline for later planning.

### Explicit Exclusions

- None

## Repository Binding

Relevant Modified Paths:
- None

Relevant Untracked Paths:
- None

Connected Repository Surface:
- src/wrapper.py
- src/core.py

## Investigation Frontier

| Area | Question | Disposition | Result |
| --- | --- | --- | --- |
| FLOW_AND_READBACK | Where does the wrapper route calls? | INVESTIGATE | Delegates to core.dispatch. |
| STATE_AND_AUTHORITY | Who owns lifecycle state? | INVESTIGATE | core.dispatch owns it. |
| ALTERNATE_PATHS | Is there a direct bypass? | INVESTIGATE | No bypass found in bounded registrations. |
| EVIDENCE_ALIGNMENT | Do code and tests agree? | INVESTIGATE | Current assertions match the source path. |

## Current System Model

### Entry And Execution Flow

CLI -> wrapper -> core.dispatch -> CLI status readback.

### State, Data And Lifecycle Ownership

core.dispatch owns lifecycle state.

### Configuration And Extension Boundaries

The inspected registrations bind the CLI to the wrapper.

### Observable Results And Readbacks

CLI status output is the current observable readback.

## Verified Findings

### Finding 1 — Wrapper delegates lifecycle work

Classification: FACT
Statement: Wrapper.call normalizes input and calls core.dispatch.
Primary Evidence: A1
Counterevidence Checked: Direct CLI registrations and adjacent dispatch entrypoints were inspected for a bypass.
Boundary / Limitation: Dynamic runtime plugin registration was outside this source-only fixture.
Planning Relevance Candidate: CURRENT_STATE
Freshness Sensitivity: ANCHOR_LOCAL

## Inferences

None

## Alternate, Legacy And Bypass Paths

- Direct CLI registrations were checked; no separate path was found in that bounded universe.

## Documentation, Tests And Runtime Alignment

- Fixture source and assertions describe the same delegation boundary.

## Absence Claims

None

## Contradictions And Surprises

- None

## Coverage Boundary

Inspected:
- wrapper entry and direct dispatcher relationship

Not Inspected:
- production-only dynamic plugin registry

Why Current Coverage Is Sufficient Or Insufficient:
The bounded fixture directly establishes the ownership fact used by this investigation answer.

## Completion

Investigation Completion: {completion}
Decision-Critical Unknowns: {decision_unknowns}
"""


class RepositoryInvestigationValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        result = prepare_module.prepare(str(self.project), "wrapper-routing")
        self.path = Path(result["artifactPath"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, text: str) -> None:
        self.path.write_text(text, encoding="utf-8")

    def test_accepts_complete_bounded_evidence_artifact(self) -> None:
        self._write(_artifact(self.project))
        validator_module.validate(self.path)

    def test_prepare_allocates_next_immutable_revision(self) -> None:
        self._write(_artifact(self.project))
        second = prepare_module.prepare(str(self.project), "wrapper-routing")
        self.assertTrue(second["artifactPath"].endswith("/INV-002.md"))
        self.assertEqual(second["investigationRevision"], "INV-002")
        self.assertTrue(self.path.is_file())

    def test_rejects_complete_artifact_with_decision_critical_unknown(self) -> None:
        text = _artifact(self.project).replace(
            "### Material Unknowns\n\n- None",
            "### Material Unknowns\n\n- Dynamic plugin route remains unresolved.",
        ).replace(
            "Decision-Critical Unknowns: None",
            "Decision-Critical Unknowns: Dynamic plugin route remains unresolved",
        )
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "complete artifact requires"):
            validator_module.validate(self.path)

    def test_accepts_partial_artifact_when_decisive_unknown_is_explicit(self) -> None:
        self._write(_artifact(self.project, status="partial"))
        validator_module.validate(self.path)

    def test_rejects_fact_that_does_not_reference_defined_anchor(self) -> None:
        text = _artifact(self.project).replace("Primary Evidence: A1", "Primary Evidence: A9")
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "defined anchors"):
            validator_module.validate(self.path)

    def test_rejects_handoff_reference_to_undefined_finding(self) -> None:
        text = _artifact(self.project).replace(
            "Supporting Findings: Finding 1",
            "Supporting Findings: Finding 99",
            1,
        )
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "undefined Finding 99"):
            validator_module.validate(self.path)

    def test_rejects_handoff_reference_to_undefined_inference(self) -> None:
        text = _artifact(self.project).replace("Based On: Finding 1", "Based On: Inference 99")
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "undefined Inference 99"):
            validator_module.validate(self.path)

    def test_rejects_investigation_answer_without_based_on(self) -> None:
        text = _artifact(self.project).replace("Based On: Finding 1\n", "")
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "Based On"):
            validator_module.validate(self.path)

    def test_rejects_state_and_authority_without_supporting_reference(self) -> None:
        text = _artifact(self.project).replace(
            "- Statement: Lifecycle state is owned by core.dispatch.\n  Supporting Findings: Finding 1",
            "- Statement: Lifecycle state is owned by core.dispatch.",
        )
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "Supporting Findings"):
            validator_module.validate(self.path)

    def test_rejects_planning_candidate_without_supporting_reference(self) -> None:
        text = _artifact(self.project).replace(
            "### Planning Constraint Candidates\n\n- None",
            """### Planning Constraint Candidates

- Candidate: persisted lifecycle owner is core.dispatch.
  Authority: evidence candidate only""",
        )
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "Supporting Findings"):
            validator_module.validate(self.path)

    def test_accepts_handoff_reference_to_defined_inference(self) -> None:
        text = _artifact(self.project).replace("Based On: Finding 1", "Based On: Finding 1, Inference 1").replace(
            "## Inferences\n\nNone",
            """## Inferences

### Inference 1 — Runtime extensions could alter the bounded routing model

Statement: A runtime extension could introduce another routing path outside the inspected fixture.
Supported By: Finding 1
Plausible Alternative: No runtime extension is registered in the deployed environment.
Evidence Needed To Disprove: Inspect the deployed runtime extension registry and current routing readback.
Planning Relevance Candidate: CURRENT_STATE""",
        )
        self._write(text)
        validator_module.validate(self.path)

    def test_rejects_complete_artifact_with_path_template_placeholder(self) -> None:
        text = _artifact(self.project).replace("src/wrapper.py | Wrapper.call", "<path> | Wrapper.call")
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "template placeholders"):
            validator_module.validate(self.path)

    def test_rejects_complete_artifact_with_bounded_result_template_placeholder(self) -> None:
        text = _artifact(self.project).replace("Delegates to core.dispatch.", "<bounded result>", 1)
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "template placeholders"):
            validator_module.validate(self.path)

    def test_rejects_absence_claim_without_search_universe(self) -> None:
        text = _artifact(self.project).replace(
            "## Absence Claims\n\nNone",
            """## Absence Claims

### Absence Claim 1

Claim: No bypass exists.
Method: searched registrations
Result: none found
Boundary: source registrations only""",
        )
        self._write(text)
        with self.assertRaisesRegex(validator_module.ValidationError, "Search Universe"):
            validator_module.validate(self.path)

    def test_rejects_symlinked_artifact(self) -> None:
        target = self.project / "outside.md"
        target.write_text(_artifact(self.project), encoding="utf-8")
        self.path.symlink_to(target)
        with self.assertRaisesRegex(validator_module.ValidationError, "non-symlink regular file"):
            validator_module.validate(self.path)

    def test_prepare_rejects_noncanonical_investigation_slug(self) -> None:
        with self.assertRaises(prepare_module.InvestigationWorkspaceError):
            prepare_module.prepare(str(self.project), "Wrapper Routing")


if __name__ == "__main__":
    unittest.main()
