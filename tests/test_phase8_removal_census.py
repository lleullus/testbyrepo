from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "phase8_removal_census.py"
SPEC = importlib.util.spec_from_file_location("phase8_removal_census", CENSUS)
assert SPEC and SPEC.loader
phase8_removal_census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase8_removal_census)


LEGACY_SOURCE_FILES = (
    "verification-lead/tools/verification-run/executable_identity.py",
    "verification-lead/tools/verification-run/verification_run.py",
    "implementation-lead/tools/implementation-result/implementation_result.py",
    "implementation-lead/tools/implementation-transaction/implementation_transaction.py",
    "implementation-lead/tools/task-ownership-snapshot/ownership_snapshot.py",
    "implementation-lead/tools/workflow-store/workflow_store.py",
    "implementation-lead/tools/workflow-store/workflow_store_preopen.py",
    "baseline-capsule/.gitignore",
    "baseline-capsule/PROTOCOL.md",
    "baseline-capsule/README.md",
    "baseline-capsule/baseline_capsule.py",
    "baseline-capsule/run_tests.py",
    "baseline-capsule/tests/test_baseline_capsule.py",
)
COUPLED_TEST_FILES = (
    "baseline-capsule/tests/test_baseline_capsule.py",
    "implementation-lead/tests/implementation-result/test_implementation_result.py",
    "implementation-lead/tests/implementation-transaction/test_implementation_transaction.py",
    "implementation-lead/tests/pilot/test_concurrent_scratch_flow.py",
    "implementation-lead/tests/pilot/test_greenfield_admission_flow.py",
    "implementation-lead/tests/pilot/test_representative_runtime_exercise.py",
    "implementation-lead/tests/planning-workspace/test_planning_workspace.py",
    "implementation-lead/tests/task-ownership/test_ownership_snapshot.py",
    "implementation-lead/tests/workflow-store/fixtures/workflow-schema-v7.sql",
    "implementation-lead/tests/workflow-store/test_workflow_store.py",
    "implementation-lead/tests/workflow-store/test_workflow_store_preopen.py",
    "verification-lead/tests/pilot/test_process_verification_pilots.py",
    "verification-lead/tests/verification-run/test_executable_identity.py",
    "verification-lead/tests/verification-run/test_verification_run.py",
)


def tree_identity(root: Path) -> str:
    entries: list[tuple[str, str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append((relative, "symlink", str(path.readlink())))
        elif path.is_file():
            entries.append((relative, "file", hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path.is_dir():
            entries.append((relative, "directory", ""))
    return hashlib.sha256(json.dumps(entries, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


class Phase8RemovalCensusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        for relative in (*LEGACY_SOURCE_FILES, *COUPLED_TEST_FILES):
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding="utf-8")
        (self.repo / ".gitignore").write_text("__pycache__/\n*.py[cod]\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
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
            cwd=self.repo,
            check=True,
        )
        (self.repo / "implementation-lead" / "SKILL.md").write_text(
            "Implementation Verification Module contract", encoding="utf-8"
        )
        (self.repo / "verification-lead" / "SKILL.md").write_text(
            "Implementation Verification Module contract", encoding="utf-8"
        )
        (self.repo / "primary-verifier").mkdir()
        (self.repo / "primary-verifier" / "SKILL.md").write_text(
            "Primary Verifier contract", encoding="utf-8"
        )

        self.state = self.root / "state"
        self.results = self.state / "implementation-results"
        self.results.mkdir(parents=True)
        self.capsules = self.state / "baseline-capsules" / "capsules"
        self.capsule_id = "a" * 32
        (self.capsules / self.capsule_id / "root").mkdir(parents=True)
        (self.capsules / self.capsule_id / "root" / "source.txt").write_text("retained", encoding="utf-8")
        (self.capsules / ("b" * 32)).mkdir()
        self.result_payload = {
            "protocolVersion": "implementation-result-v3",
            "capsuleRef": f"capsule:v1:{self.capsule_id}",
        }
        (self.results / "complete.json").write_text(json.dumps(self.result_payload), encoding="utf-8")

        self.installed = self.root / "installed-skills"
        self.installed.mkdir()
        os.symlink(self.repo / "implementation-lead", self.installed / "implementation-lead", target_is_directory=True)
        os.symlink(self.repo / "verification-lead", self.installed / "verification-lead", target_is_directory=True)
        os.symlink(self.repo / "primary-verifier", self.installed / "primary-verifier", target_is_directory=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def census(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(CENSUS),
                "--repo-root",
                str(self.repo),
                "--state-root",
                str(self.state),
                "--installed-skill-root",
                str(self.installed),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_emits_complete_read_only_manifest(self) -> None:
        before = tuple(tree_identity(root) for root in (self.repo, self.state, self.installed))

        completed = self.census()

        after = tuple(tree_identity(root) for root in (self.repo, self.state, self.installed))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(before, after)
        manifest = json.loads(completed.stdout)
        self.assertEqual(manifest["schemaVersion"], "phase8-removal-census-v1")
        self.assertEqual(len(manifest["inventory"]["legacySourceFiles"]), 13)
        self.assertEqual(len(manifest["inventory"]["mechanismCoupledTestFiles"]), 14)
        self.assertEqual(manifest["results"]["items"][0]["relativePath"], "complete.json")
        self.assertEqual(manifest["results"]["items"][0]["protocolVersion"], "implementation-result-v3")
        self.assertEqual(manifest["results"]["items"][0]["capsuleRef"], self.result_payload["capsuleRef"])
        self.assertEqual(manifest["capsules"]["capsuleDirectoryCount"], 2)
        self.assertEqual(manifest["capsules"]["referenced"], [{"capsuleRef": self.result_payload["capsuleRef"], "exists": True}])
        skills = {skill["name"]: skill for skill in manifest["installedCallers"]["skills"]}
        self.assertEqual(manifest["installedCallers"]["errors"], [])
        self.assertTrue(skills["implementation-lead"]["exists"])
        self.assertTrue(skills["verification-lead"]["exists"])
        self.assertTrue(skills["primary-verifier"]["exists"])
        self.assertTrue(skills["primary-verifier"]["targetMatchesExpected"])
        self.assertTrue(skills["primary-verifier"]["contentMatchesExpected"])
        self.assertTrue(skills["implementation-lead"]["targetMatchesExpected"])
        self.assertTrue(skills["implementation-lead"]["contentMatchesExpected"])
        self.assertEqual(skills["implementation-lead"]["legacyTermsFound"], [])
        self.assertEqual(manifest["inventory"]["residueFiles"], [])
        self.assertEqual(manifest["inventory"]["emptyLegacyDirectories"], [])
        self.assertEqual(manifest["legacyProcesses"]["matches"], [])

    def test_reports_malformed_result_without_writing_any_surface(self) -> None:
        (self.results / "malformed.json").write_bytes(b"{not json")
        before = tuple(tree_identity(root) for root in (self.repo, self.state, self.installed))

        completed = self.census()

        after = tuple(tree_identity(root) for root in (self.repo, self.state, self.installed))
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(before, after)
        manifest = json.loads(completed.stdout)
        malformed = next(item for item in manifest["results"]["items"] if item["relativePath"] == "malformed.json")
        self.assertEqual(malformed["error"]["code"], "RESULT_JSON_UNREADABLE")

    def test_deleted_tracked_legacy_files_are_absent_from_effective_inventory(self) -> None:
        (self.repo / LEGACY_SOURCE_FILES[0]).unlink()
        (self.repo / COUPLED_TEST_FILES[0]).unlink()
        (self.repo / "baseline-capsule" / "tests").rmdir()

        completed = self.census()

        self.assertEqual(completed.returncode, 0, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertNotIn(LEGACY_SOURCE_FILES[0], manifest["inventory"]["legacySourceFiles"])
        self.assertNotIn(COUPLED_TEST_FILES[0], manifest["inventory"]["mechanismCoupledTestFiles"])
        self.assertEqual(manifest["inventory"]["residueFiles"], [])
        self.assertEqual(manifest["inventory"]["emptyLegacyDirectories"], [])

    def test_process_matching_accepts_only_exact_direct_or_option_free_python_script(self) -> None:
        self.assertEqual(
            phase8_removal_census._legacy_command(["/tmp/verification_run.py", "--help"]),
            "verification_run.py",
        )
        self.assertEqual(
            phase8_removal_census._legacy_command(["python3", "/tmp/workflow_store.py", "--help"]),
            "workflow_store.py",
        )
        self.assertIsNone(phase8_removal_census._legacy_command(["python3", "-c", "workflow_store.py"]))
        self.assertIsNone(
            phase8_removal_census._legacy_command(["python3", "-u", "/tmp/workflow_store.py"])
        )
        self.assertIsNone(
            phase8_removal_census._legacy_command(["unrelated-command", "workflow_store.py"])
        )

    def test_process_matching_detects_retired_pyc_invocations(self) -> None:
        self.assertEqual(
            phase8_removal_census._legacy_command(["/tmp/verification_run.pyc", "--help"]),
            "verification_run.pyc",
        )
        self.assertEqual(
            phase8_removal_census._legacy_command(["python3", "/tmp/baseline_capsule.cpython-312.pyc", "--help"]),
            "baseline_capsule.cpython-312.pyc",
        )
        self.assertEqual(
            phase8_removal_census._legacy_command(["python3", "/tmp/workflow_store.cpython-313.pyc"]),
            "workflow_store.cpython-313.pyc",
        )
        self.assertEqual(
            phase8_removal_census._legacy_command(["python3", "/tmp/workflow_store.cpython-312.opt-1.pyc"]),
            "workflow_store.cpython-312.opt-1.pyc",
        )
        self.assertEqual(
            phase8_removal_census._legacy_command(["/tmp/baseline_capsule.cpython-312.opt-2.pyc"]),
            "baseline_capsule.cpython-312.opt-2.pyc",
        )
        self.assertIsNone(
            phase8_removal_census._legacy_command(["python3", "-c", "baseline_capsule.cpython-312.pyc"])
        )
        self.assertIsNone(
            phase8_removal_census._legacy_command(["python3", "-u", "/tmp/verification_run.pyc"])
        )

    def test_untracked_legacy_source_is_filesystem_residue(self) -> None:
        (self.repo / "verification-lead" / "tools" / "verification-run" / "leftover.py").write_text(
            "leftover", encoding="utf-8"
        )

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertIn(
            "verification-lead/tools/verification-run/leftover.py", manifest["inventory"]["residueFiles"]
        )
        self.assertTrue(
            any(error["code"] == "LEGACY_FILESYSTEM_RESIDUE" for error in manifest["inventory"]["errors"])
        )

    def test_ignored_legacy_pyc_is_filesystem_residue(self) -> None:
        pyc = self.repo / "baseline-capsule" / "tests" / "__pycache__" / "test_baseline_capsule.cpython-312.pyc"
        pyc.parent.mkdir(parents=True)
        pyc.write_bytes(b"ignored bytecode")

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertIn(
            "baseline-capsule/tests/__pycache__/test_baseline_capsule.cpython-312.pyc",
            manifest["inventory"]["residueFiles"],
        )
        self.assertTrue(
            any(error["code"] == "LEGACY_FILESYSTEM_RESIDUE" for error in manifest["inventory"]["errors"])
        )

    def test_empty_legacy_directory_is_filesystem_residue(self) -> None:
        (self.repo / "baseline-capsule" / "tests" / "test_baseline_capsule.py").unlink()

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertIn("baseline-capsule/tests", manifest["inventory"]["emptyLegacyDirectories"])
        self.assertTrue(
            any(error["code"] == "LEGACY_FILESYSTEM_RESIDUE" for error in manifest["inventory"]["errors"])
        )

    def test_wrong_installed_target_or_content_is_fail_closed(self) -> None:
        (self.installed / "implementation-lead").unlink()
        (self.installed / "implementation-lead").mkdir()
        (self.installed / "implementation-lead" / "SKILL.md").write_text("stale copy", encoding="utf-8")

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        entry = next(
            skill for skill in manifest["installedCallers"]["skills"] if skill["name"] == "implementation-lead"
        )
        self.assertFalse(entry["targetMatchesExpected"])
        self.assertTrue(
            any(
                error["code"] == "INSTALLED_CALLER_MISMATCH"
                for error in manifest["installedCallers"]["errors"]
            )
        )

    def test_stale_installed_skill_with_legacy_terms_is_fail_closed(self) -> None:
        (self.installed / "implementation-lead").unlink()
        (self.installed / "implementation-lead").mkdir()
        (self.installed / "implementation-lead" / "SKILL.md").write_text(
            "still requires baseline-capsule and workflow-store", encoding="utf-8"
        )

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        entry = next(
            skill for skill in manifest["installedCallers"]["skills"] if skill["name"] == "implementation-lead"
        )
        self.assertEqual(entry["legacyTermsFound"], ["baseline-capsule", "workflow-store"])
        self.assertTrue(
            any(
                error["code"] == "INSTALLED_CALLER_MISMATCH"
                for error in manifest["installedCallers"]["errors"]
            )
        )

    def test_missing_installed_lead_is_fail_closed(self) -> None:
        (self.installed / "verification-lead").unlink()

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        entry = next(
            skill for skill in manifest["installedCallers"]["skills"] if skill["name"] == "verification-lead"
        )
        self.assertFalse(entry["exists"])
        self.assertTrue(
            any(
                error["code"] == "INSTALLED_CALLER_MISMATCH"
                for error in manifest["installedCallers"]["errors"]
            )
        )

    def test_git_execution_failure_is_manifest_observation_error(self) -> None:
        with patch.object(phase8_removal_census.subprocess, "run", side_effect=OSError("git missing")):
            output, error = phase8_removal_census._git_output(self.repo, ["rev-parse", "HEAD"])

        self.assertIsNone(output)
        self.assertEqual(error["code"], "GIT_EXECUTABLE_UNAVAILABLE")

    def test_census_fails_for_process_match_and_unavailable_observation(self) -> None:
        for process_observation in (
            {"available": True, "matches": [{"pid": 123, "executable": "workflow_store.py", "argv": []}]},
            {"available": False, "matches": []},
        ):
            with self.subTest(process_observation=process_observation), patch.object(
                phase8_removal_census, "_process_observation", return_value=process_observation
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    code = phase8_removal_census.main(
                        [
                            "--repo-root",
                            str(self.repo),
                            "--state-root",
                            str(self.state),
                            "--installed-skill-root",
                            str(self.installed),
                        ]
                    )
                self.assertEqual(code, 2)

    def test_nested_symlink_file_and_directory_are_residue_without_traversal(self) -> None:
        target = self.root / "outside"
        target.mkdir()
        (target / "secret.py").write_text("outside", encoding="utf-8")
        symlink_file = self.repo / "baseline-capsule" / "linked.py"
        symlink_dir = self.repo / "baseline-capsule" / "linked-dir"
        symlink_file.symlink_to(target / "secret.py")
        symlink_dir.symlink_to(target, target_is_directory=True)

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertIn("baseline-capsule/linked.py", manifest["inventory"]["residueFiles"])
        self.assertIn("baseline-capsule/linked-dir", manifest["inventory"]["residueFiles"])
        self.assertNotIn("baseline-capsule/linked-dir/secret.py", manifest["inventory"]["filesystemLegacyFiles"])

    def test_tracked_symlink_is_not_accepted_as_legacy_file(self) -> None:
        tracked = self.repo / LEGACY_SOURCE_FILES[0]
        tracked.unlink()
        tracked.symlink_to(self.root / "outside-target")
        (self.root / "outside-target").write_text("outside", encoding="utf-8")

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertTrue(any(error["code"] == "LEGACY_FILESYSTEM_RESIDUE" for error in manifest["inventory"]["errors"]))

    def test_lstat_permission_error_is_fail_closed(self) -> None:
        bounded = self.repo / "baseline-capsule"
        original_lstat = Path.lstat

        for failure in (PermissionError("denied"), OSError("I/O failure")):
            with self.subTest(failure=type(failure).__name__):
                def lstat_with_error(path: Path):
                    if path == bounded:
                        raise failure
                    return original_lstat(path)

                with patch.object(Path, "lstat", lstat_with_error):
                    observation, errors = phase8_removal_census._filesystem_observation(self.repo)

                self.assertTrue(observation["legacyFiles"])
                self.assertTrue(any(error["code"] == "LEGACY_PATH_UNREADABLE" for error in errors))


if __name__ == "__main__":
    unittest.main()
