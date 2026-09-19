from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("assurance_under_test", ROOT / "iis-workflow/tools/assurance.py")
assert spec is not None and spec.loader is not None
assurance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assurance)

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

        thesis = self.root / "docs/planning/product-thesis/example/THESIS-001.md"
        thesis.parent.mkdir(parents=True)
        thesis.write_text("# Promise\nThe actual entry prints actual-value.\n", encoding="utf-8")
        thesis_snapshot = self.store.capture_files(self.root, [thesis], kind="source", origin="fixture-thesis")
        self.thesis_ref = {"snapshot": thesis_snapshot, "path": thesis.relative_to(self.root).as_posix()}

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
        scope_snapshot = self.store.capture_files(self.root, [self.scope], kind="source", origin="fixture-scope")
        self.scope_ref = {"snapshot": scope_snapshot, "path": self.scope.relative_to(self.root).as_posix()}

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

    def fixed_bytes(self, logical: str, data: bytes, *, kind: str = "evidence", invocation: str | None = None) -> dict:
        snapshot = self.store.capture_mapping(
            {logical: data},
            kind=kind,
            producer_run=getattr(self, "binding", {}).get("run_id") if hasattr(self, "binding") else None,
            producer_invocation=invocation,
        )
        return {"snapshot": snapshot, "path": logical}

    def seal(self):
        self.baseline_path.write_text(json.dumps(self.baseline), encoding="utf-8")
        self.binding = assurance.bind(self.baseline_path, self.store, self.root, self.execution)

    def evidence(self):
        gate = assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        obs = {
            "schema": "iis-assurance-result/v2",
            "kind": "observation",
            **self.baseline["observations"][0],
            "invocation": "observer-1",
            "binding": self.binding["binding_id"],
            "completion": "COMPLETE",
            "evidence": gate["evidence"],
            "effects": [],
            "outcome": "SATISFIED",
        }
        log_ref = self.fixed_bytes("activity/actions.log", b"native process settled; stdout read directly\n")
        activity = {
            "run_id": self.binding["run_id"],
            "evidence": [log_ref],
            "started": [
                {"kind": row["kind"], "id": row["id"], "invocation": row["invocation"]}
                for row in (gate, obs)
            ],
            "effects": [],
        }
        return activity, [gate, obs]

    def closure(self, activity, results):
        return assurance.close(self.baseline_path, self.store, self.binding, activity, results)
