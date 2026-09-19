from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assurance_under_test", ROOT / "iis-workflow/tools/assurance.py")
assurance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assurance)


class AssuranceFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iis-assurance-")
        self.addCleanup(self.temp.cleanup)
        self.arena = Path(self.temp.name)
        self.root = self.arena / "product"
        self.root.mkdir(mode=0o700)
        self.command = self.root / "main.py"
        self.command.write_text("print('actual-value')\n")
        thesis = self.root / "docs/planning/product-thesis/example/THESIS-001.md"
        thesis.parent.mkdir(parents=True)
        thesis.write_text("# Promise\nThe actual entry prints actual-value.\n")
        self.scope = self.root / "docs/planning/work/example/SCOPE.md"
        self.scope.parent.mkdir(parents=True)
        self.scope.write_text(f"# Scope\n\nSchema: iis-scope/v1\nProject-Root: {self.root}\nStatus: ready\n\n## Product Authority\n- {thesis} sha256:{assurance.file_ref(thesis)['sha256']}\n\n## Outcome\nPrint the promised value.\n\n## Acceptance\nThe actual entry prints actual-value.\n")
        environment = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")):
            subprocess.run(["git", "-C", str(self.root), *args], env=environment, check=True, capture_output=True)
        self.base = assurance.git(self.root, "rev-parse", "HEAD").decode().strip()
        self.baseline_path = self.arena / "baseline.json"
        self.baseline = {"schema": "iis-assurance/v1", "scope": assurance.file_ref(self.scope),
                         "obligations": [{"anchor": "The actual entry prints actual-value.", "evidence": ["readback"]}],
                         "gates": [{"id": "native", "argv": [sys.executable, "-B", str(self.command)], "cwd": str(self.root), "timeout": 5, "mechanisms": [assurance.file_ref(self.command)], "jobs": [], "jobs_path": None}],
                         "observations": [{"id": "readback", "initial_state": "committed fixture", "trigger": "python -B main.py", "readback": "native stdout", "predicate": "stdout is actual-value"}],
                         "surfaces": [], "lanes": [], "no_probe_reason": "Synthetic artifact control for helper contract tests"}
        self.execution = {"artifacts": [], "runtime": [], "mechanisms": [assurance.file_ref(self.command)], "note": "Native Python source fixture; no service"}
        self.seal()

    def seal(self):
        self.baseline_path.write_text(json.dumps(self.baseline))
        self.binding = assurance.bind(self.baseline_path, self.root, self.base, self.execution)

    def evidence(self):
        gate = assurance.run_gate(self.baseline_path, self.binding, "native", self.arena / "native-capture")
        obs = {"schema": "iis-assurance-result/v1", "kind": "observation", **self.baseline["observations"][0],
               "invocation": "observer-1", "binding": assurance.identity(self.binding), "completion": "COMPLETE",
               "evidence": gate["evidence"], "effects": [], "outcome": "SATISFIED"}
        log = self.arena / "actions.log"
        log.write_text("native process settled; stdout read directly\n")
        activity = {"run_id": self.binding["run_id"], "evidence": [assurance.file_ref(log)],
                    "started": [{"kind": row["kind"], "id": row["id"], "invocation": row["invocation"]} for row in (gate, obs)], "effects": []}
        return activity, [gate, obs]

    def closure(self, activity, results):
        return assurance.close(self.baseline_path, self.binding, activity, results)
