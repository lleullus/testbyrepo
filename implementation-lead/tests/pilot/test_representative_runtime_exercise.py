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
    "runtime_exercise_ownership_snapshot",
    IMPLEMENTATION_ROOT / "tools/task-ownership-snapshot/ownership_snapshot.py",
)
implementation_result = load_module(
    "runtime_exercise_implementation_result",
    IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py",
)


CLI_SOURCE = """\
import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
commands = parser.add_subparsers(dest="command", required=True)
put = commands.add_parser("put")
put.add_argument("--state", required=True)
put.add_argument("--key", required=True)
put.add_argument("--value", required=True)
get = commands.add_parser("get")
get.add_argument("--state", required=True)
get.add_argument("--key", required=True)
args = parser.parse_args()
state = Path(args.state)

if args.command == "put":
    values = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    values[args.key] = args.value
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(values, sort_keys=True), encoding="utf-8")
    print("stored")
else:
    print(json.loads(state.read_text(encoding="utf-8"))[args.key])
"""


class RepresentativeRuntimeExercisePilotTests(unittest.TestCase):
    def test_cli_effect_readback_cleanup_and_source_stability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            cli = project / "cli.py"
            cli.write_text(CLI_SOURCE, encoding="utf-8")
            scratch = project / ".scratch" / "runtime-exercise"
            ticket = scratch / "tickets" / "TICKET-001.md"
            ticket.parent.mkdir(parents=True)
            spec = scratch / "SPEC.md"
            ticket.write_text("ready ticket\n", encoding="utf-8")
            spec.write_text("approved spec\n", encoding="utf-8")
            state = root / "task-owned-state.json"

            capsule_root = root / "capsules"
            capsule_store = implementation_result.baseline_capsule.CapsuleStore(capsule_root)
            capsule = capsule_store.create(project)
            before = ownership_snapshot.capture(project)

            put = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "put",
                    "--state",
                    str(state),
                    "--key",
                    "color",
                    "--value",
                    "blue",
                ],
                cwd=project,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(0, put.returncode, put.stderr)
            self.assertEqual("stored\n", put.stdout)

            readback = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "get",
                    "--state",
                    str(state),
                    "--key",
                    "color",
                ],
                cwd=project,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(0, readback.returncode, readback.stderr)
            self.assertEqual("blue\n", readback.stdout)

            after = ownership_snapshot.capture(project)
            delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=[])
            self.assertEqual("WITHIN_ENVELOPE", delta["scopeState"])
            self.assertEqual([], delta["changedPaths"])
            self.assertEqual(before["identity"], after["identity"])

            state.unlink()
            self.assertFalse(state.exists())

            final_source = implementation_result.baseline_capsule.capture_identity(project)
            result_store = implementation_result.ResultStore(root / "results", capsule_root)
            published = result_store.publish(
                {
                    "protocolVersion": "implementation-result-v2",
                    "implementationStatus": "IMPLEMENTATION_COMPLETE",
                    "projectRoot": str(project.resolve()),
                    "planningSeal": {
                        "ticketPath": str(ticket.resolve()),
                        "ticketSha256": digest(ticket),
                        "specPath": str(spec.resolve()),
                        "specSha256": digest(spec),
                        "blockerFiles": [],
                    },
                    "capsuleRef": capsule["capsuleRef"],
                    "finalSourceIdentity": final_source["sourceIdentity"],
                }
            )
            self.assertEqual("IMPLEMENTATION_COMPLETE", published["implementationStatus"])
            self.assertNotIn("VERIFIED", published.values())
            self.assertEqual(
                final_source["sourceIdentity"],
                implementation_result.baseline_capsule.capture_identity(project)["sourceIdentity"],
            )


if __name__ == "__main__":
    unittest.main()
