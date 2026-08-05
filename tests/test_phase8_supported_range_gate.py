from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "phase8_supported_range_gate.py"
SPEC = importlib.util.spec_from_file_location("phase8_supported_range_gate", GATE)
assert SPEC and SPEC.loader
phase8_supported_range_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase8_supported_range_gate)


class Phase8SupportedRangeGateTests(unittest.TestCase):
    def test_worktree_identity_binds_untracked_path_and_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tracked.txt").write_text("tracked", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Phase 8 test",
                    "-c",
                    "user.email=phase8@example.test",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                cwd=root,
                check=True,
            )
            (root / "untracked.txt").write_text("first", encoding="utf-8")

            first, first_errors = phase8_supported_range_gate._worktree_identity(root)

            (root / "untracked.txt").write_text("second", encoding="utf-8")
            second, second_errors = phase8_supported_range_gate._worktree_identity(root)

        self.assertEqual([], first_errors)
        self.assertEqual([], second_errors)
        self.assertEqual([{"path": "untracked.txt", "sha256": first["untrackedFiles"][0]["sha256"]}], first["untrackedFiles"])
        self.assertNotEqual(first["identitySha256"], second["identitySha256"])

    def test_strict_smoke_semantics_rejects_extra_or_changed_values(self) -> None:
        expected = {
            "candidateImplementationChanges": 0,
            "canonicalSource": "implemented",
            "inspectionCurrentness": "CURRENT",
            "inspectionResult": "VerificationResult",
            "verificationStatus": "VERIFIED",
        }

        self.assertIsNone(phase8_supported_range_gate._expect_exact("smoke", expected, expected))
        self.assertEqual(
            "JSON_OUTPUT_SEMANTICS_INVALID",
            phase8_supported_range_gate._expect_exact(
                "smoke", {**expected, "unexpected": True}, expected
            )["code"],
        )

    def test_census_requires_current_head_and_no_observation_errors(self) -> None:
        census = {
            "schemaVersion": "phase8-removal-census-v1",
            "inventory": {
                "revision": "head",
                "errors": [],
                "legacySourceFiles": [],
                "mechanismCoupledTestFiles": [],
                "filesystemLegacyFiles": [],
                "residueFiles": [],
                "emptyLegacyDirectories": [],
            },
            "results": {"errors": [], "items": [{"relativePath": "one.json"}]},
            "capsules": {"errors": [], "referenced": [{"capsuleRef": "capsule:v1:" + "a" * 32}]},
            "installedCallers": {"errors": []},
            "legacyProcesses": {"available": True, "matches": []},
        }

        self.assertIsNone(phase8_supported_range_gate._valid_census(census, "head"))
        census["results"]["items"][0]["error"] = {"code": "RESULT_JSON_UNREADABLE"}
        self.assertEqual(
            "CENSUS_SEMANTICS_INVALID",
            phase8_supported_range_gate._valid_census(census, "head")["code"],
        )

    def test_census_requires_zero_inventory_processes_and_installed_callers(self) -> None:
        healthy = {
            "schemaVersion": "phase8-removal-census-v1",
            "inventory": {
                "revision": "head",
                "errors": [],
                "legacySourceFiles": [],
                "mechanismCoupledTestFiles": [],
                "filesystemLegacyFiles": [],
                "residueFiles": [],
                "emptyLegacyDirectories": [],
            },
            "results": {"errors": [], "items": []},
            "capsules": {"errors": [], "referenced": []},
            "installedCallers": {"errors": []},
            "legacyProcesses": {"available": True, "matches": []},
        }
        fields = (
            ("legacySourceFiles", ["retired.py"]),
            ("mechanismCoupledTestFiles", ["retired_test.py"]),
            ("filesystemLegacyFiles", ["retired.pyc"]),
            ("residueFiles", ["retired.pyc"]),
            ("emptyLegacyDirectories", ["retired"]),
        )
        for field, value in fields:
            with self.subTest(field=field):
                candidate = json.loads(json.dumps(healthy))
                candidate["inventory"][field] = value
                self.assertIsNotNone(phase8_supported_range_gate._valid_census(candidate, "head"))

        for processes in ({"available": False, "matches": []}, {"available": True, "matches": [{"pid": 1}]}):
            with self.subTest(processes=processes):
                candidate = json.loads(json.dumps(healthy))
                candidate["legacyProcesses"] = processes
                self.assertIsNotNone(phase8_supported_range_gate._valid_census(candidate, "head"))

        for installed in (None, {"errors": [{"code": "mismatch"}]}):
            with self.subTest(installed=installed):
                candidate = json.loads(json.dumps(healthy))
                candidate["installedCallers"] = installed
                self.assertIsNotNone(phase8_supported_range_gate._valid_census(candidate, "head"))

        candidate = json.loads(json.dumps(healthy))
        del candidate["installedCallers"]
        self.assertIsNotNone(phase8_supported_range_gate._valid_census(candidate, "head"))

        malformed = json.loads(json.dumps(healthy))
        malformed["results"]["items"] = "not a list"
        self.assertIsNotNone(phase8_supported_range_gate._valid_census(malformed, "head"))

        malformed = json.loads(json.dumps(healthy))
        malformed["installedCallers"]["errors"] = ""
        self.assertIsNotNone(phase8_supported_range_gate._valid_census(malformed, "head"))

    def test_gate_cli_requires_installed_skill_root(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(GATE),
                "--repo-root",
                str(ROOT),
                "--state-root",
                "/tmp/phase8-test-state",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--installed-skill-root", completed.stderr)


if __name__ == "__main__":
    unittest.main()
