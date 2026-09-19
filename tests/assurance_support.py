from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("assurance_under_test", ROOT / "iis-workflow/tools/assurance.py")
assert spec is not None and spec.loader is not None
assurance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assurance)

life_spec = importlib.util.spec_from_file_location("thesis_lifecycle_for_assurance", ROOT / "product-thesis/tools/lifecycle.py")
assert life_spec is not None and life_spec.loader is not None
lifecycle = importlib.util.module_from_spec(life_spec)
life_spec.loader.exec_module(lifecycle)

from iis_artifacts.admission import admit_scope
from iis_artifacts.store import ArtifactStore


class AssuranceFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iis-assurance-")
        self.addCleanup(self.temp.cleanup)
        self.arena = Path(self.temp.name)
        self.root = self.arena / "product"
        self.root.mkdir(mode=0o700)
        self.store = ArtifactStore(self.arena / "store", "fixture")

        self.command = self.root / "main.py"
        self.command.write_text("print('actual-value')\n", encoding="utf-8")
        command_snapshot = self.store.capture_files(self.root, [self.command], kind="source", origin="fixture-command")
        self.command_ref = {"snapshot": command_snapshot, "path": "main.py"}

        self.thesis = self.root / "docs/planning/product-thesis/example/THESIS-001.md"
        self.thesis.parent.mkdir(parents=True)
        self.thesis.write_text("# Promise\nThe actual entry prints actual-value.\n", encoding="utf-8")
        original_snapshot = self.store.capture_files(self.root, [self.thesis], kind="source", origin="fixture-thesis-original")
        original_ref = {"snapshot": original_snapshot, "path": self.thesis.relative_to(self.root).as_posix()}
        thesis_run = lifecycle.start(
            self.store,
            "Adopt the supplied assurance fixture promise.",
            originals=[original_ref],
            budget=2,
        )
        lifecycle.add_frontier(
            self.store,
            thesis_run,
            item_id="fixture-promise",
            origin="fixture",
            question="Is the supplied promise the current product authority?",
            material_change="A different answer changes the assurance boundary.",
            decision_bearing=True,
        )
        lifecycle.disposition_frontier(
            self.store,
            thesis_run,
            "fixture-promise",
            "RESOLVED",
            "The unit fixture explicitly supplies this promise.",
        )
        source_inv = lifecycle.begin_review(
            self.store,
            thesis_run,
            "SOURCE_FRONTIER",
            lifecycle.required_review_inputs(self.store, thesis_run, "SOURCE_FRONTIER"),
        )
        lifecycle.complete_review(self.store, source_inv, result={"host_terminal": True, "fixture": "source"})
        candidate = lifecycle.submit_candidate(
            self.store,
            thesis_run,
            self.thesis,
            self.thesis.relative_to(self.root).as_posix(),
            expected_generation=0,
        )
        challenge_inv = lifecycle.begin_review(
            self.store,
            thesis_run,
            "CANDIDATE_COUNTEREXAMPLE",
            lifecycle.required_review_inputs(self.store, thesis_run, "CANDIDATE_COUNTEREXAMPLE"),
        )
        lifecycle.complete_review(self.store, challenge_inv, result={"host_terminal": True, "fixture": "challenge"})
        closed = lifecycle.close_request(
            self.store,
            thesis_run,
            self.root,
            expected_generation=1,
            limitations="Synthetic test precondition only.",
        )
        if closed["result"] != "CALIBRATED":
            raise RuntimeError(closed)
        self.thesis_ref = candidate

        self.scope = self.root / "docs/planning/work/example/SCOPE.md"
        self.scope.parent.mkdir(parents=True)
        sources = json.dumps([self.thesis_ref], ensure_ascii=False, indent=2)
        self.scope.write_text(
            f"# Scope\nSchema: iis-scope/v2\nProject-Root: {self.root}\nStatus: ready\n\n"
            f"## Product Authority\n```iis-sources\n{sources}\n```\n\n"
            "## Outcome\nPrint the promised value.\n\n"
            "## Acceptance\nThe actual entry prints actual-value.\n\n"
            "## Open Decisions\nNone\n",
            encoding="utf-8",
        )
        admission = admit_scope(
            self.store,
            self.scope,
            role="assurance",
            current_request="Run the exact assurance fixture.",
        )
        self.scope_ref = admission["scope"]

        self.baseline_path = self.arena / "baseline.json"
        self.baseline = {
            "schema": "iis-assurance/v2",
            "scope": self.scope_ref,
            "obligations": [{"anchor": "The actual entry prints actual-value.", "evidence": ["readback"]}],
            "gates": [{
                "id": "native",
                "argv": [sys.executable, "-B", str(self.command)],
                "cwd": str(self.root),
                "timeout": 5,
                "mechanisms": [self.command_ref],
                "jobs": [],
                "jobs_path": None,
            }],
            "observations": [{
                "id": "readback",
                "initial_state": "captured fixture",
                "trigger": "python -B main.py",
                "readback": "native stdout",
                "predicate": "stdout is actual-value",
            }],
            "surfaces": [],
            "lanes": [],
            "no_probe_reason": "Synthetic artifact control for helper contract tests",
        }
        self.execution = {
            "artifacts": [],
            "runtime": [],
            "mechanisms": [self.command_ref],
            "note": "Native Python source fixture; no service",
        }
        self.seal()

    def fixed_bytes(self, logical: str, data: bytes, *, kind: str = "evidence", invocation: str | None = None, run_id: str | None = None) -> dict:
        snapshot = self.store.capture_mapping(
            {logical: data},
            kind=kind,
            producer_run=run_id if run_id is not None else getattr(self, "binding", {}).get("run_id"),
            producer_invocation=invocation,
        )
        return {"snapshot": snapshot, "path": logical}

    def seal(self):
        self.baseline_path.write_text(json.dumps(self.baseline), encoding="utf-8")
        self.binding = assurance.bind(self.baseline_path, self.store, self.root, self.execution)

    def observation(self, *, outcome: str = "SATISFIED") -> dict:
        invocation = assurance.begin_host_invocation(self.store, self.binding, "observation", "readback")
        evidence = assurance.capture_invocation_evidence(
            self.store,
            self.binding,
            invocation,
            {"readback/stdout": b"actual-value\n"},
        )
        result = {
            "schema": "iis-assurance-result/v3",
            "kind": "observation",
            **self.baseline["observations"][0],
            "invocation": invocation,
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": evidence,
            "effects": [],
            "outcome": outcome,
        }
        assurance.complete_host_invocation(self.store, self.binding, invocation, result)
        return result

    def probe(self, lane_id: str, *, outcome: str, material: bool = False) -> dict:
        lane = next(row for row in self.baseline["lanes"] if row["id"] == lane_id)
        invocation = assurance.begin_host_invocation(self.store, self.binding, "probe", lane_id)
        evidence = assurance.capture_invocation_evidence(
            self.store,
            self.binding,
            invocation,
            {
                f"probe/{lane_id}/hypothesis.txt": b"alternate route may violate the promise\n",
                f"probe/{lane_id}/readback.txt": b"observed result\n",
            },
        )
        action = {
            "surface": lane["surfaces"][0],
            "hypothesis": "alternate route may violate the promise",
            "initial_state": "fixed execution fixture",
            "trigger": "alternate route",
            "readback": "observed result",
            "evidence": evidence,
        }
        findings = []
        if material:
            findings.append({
                "anchor": "The actual entry prints actual-value.",
                "materiality": "MATERIAL",
                "disposition": "OPEN",
                "evidence": evidence,
            })
        result = {
            "schema": "iis-assurance-result/v3",
            "kind": "probe",
            "id": lane_id,
            "invocation": invocation,
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": evidence,
            "effects": [],
            "outcome": outcome,
            "hypotheses": evidence,
            "actions": [action],
            "findings": findings,
        }
        assurance.complete_host_invocation(self.store, self.binding, invocation, result)
        return result

    def evidence(self, *, observation_outcome: str = "SATISFIED"):
        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        obs = self.observation(outcome=observation_outcome)
        return gate, obs

    def closure(self):
        return assurance.close(self.baseline_path, self.store, self.binding)
