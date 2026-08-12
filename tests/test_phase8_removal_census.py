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
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "phase8_removal_census.py"
SPEC = importlib.util.spec_from_file_location("phase8_removal_census", CENSUS)
assert SPEC and SPEC.loader
phase8_removal_census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase8_removal_census)


ROUTER_VERIFICATION_PATH = "/home/user01/project/iis-skills/verification-lead/SKILL.md"


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
        active_contracts = {
            "README.md": "IIS planning and implementation result.\n",
            "scope-shaper/SKILL.md": "Scope Shaper routes planning.\n",
            "matt/skills/to-tickets/SKILL.md": "Tickets preserve observable product flows.\n",
            "implementation-lead/SKILL.md": "Implementation Lead reports exact limitations.\n",
        }
        for relative, content in active_contracts.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for relative in phase8_removal_census.ACTIVE_VERIFICATION_FILES:
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        (self.repo / ".gitignore").write_text("__pycache__/\n*.py[cod]\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Removal census test",
                "-c",
                "user.email=removal@example.test",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=self.repo,
            check=True,
        )

        self.state = self.root / "state"
        self.results = self.state / "implementation-results"
        self.results.mkdir(parents=True)
        self.capsules = self.state / "baseline-capsules" / "capsules"
        self.capsule_id = "a" * 32
        (self.capsules / self.capsule_id / "root").mkdir(parents=True)
        (self.capsules / self.capsule_id / "root" / "source.txt").write_text(
            "retained", encoding="utf-8"
        )
        (self.capsules / ("b" * 32)).mkdir()
        self.result_payload = {
            "protocolVersion": "implementation-result-v3",
            "capsuleRef": f"capsule:v1:{self.capsule_id}",
        }
        (self.results / "complete.json").write_text(
            json.dumps(self.result_payload), encoding="utf-8"
        )

        self.installed = self.root / "installed-skills"
        router = self.installed / "iis-workflow/SKILL.md"
        router.parent.mkdir(parents=True)
        router.write_bytes(Path("/home/user01/.codex/skills/iis-workflow/SKILL.md").read_bytes())

        self.config = self.root / "opencode-config"
        self.config.mkdir()
        (self.config / "opencode.json").write_text(
            json.dumps({"$schema": "https://opencode.ai/config.json"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def argv(self) -> list[str]:
        return [
            sys.executable,
            str(CENSUS),
            "--repo-root",
            str(self.repo),
            "--state-root",
            str(self.state),
            "--installed-skill-root",
            str(self.installed),
            "--config-root",
            str(self.config),
        ]

    def census(self, argv: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv or self.argv(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_emits_complete_read_only_manifest(self) -> None:
        observed = (self.repo, self.state, self.installed, self.config)
        before = tuple(tree_identity(root) for root in observed)

        completed = self.census()

        after = tuple(tree_identity(root) for root in observed)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, after)
        manifest = json.loads(completed.stdout)
        self.assertEqual(manifest["schemaVersion"], "iis-removal-census-v2")
        self.assertEqual(manifest["roots"]["errors"], [])
        self.assertEqual(manifest["inventory"]["trackedRemovedMechanismFiles"], [])
        self.assertEqual(manifest["inventory"]["residueFiles"], [])
        self.assertTrue(
            all(item["isRegularFile"] for item in manifest["inventory"]["activeVerificationFiles"])
        )
        self.assertTrue(
            all(item["contentMatchesExpected"] for item in manifest["inventory"]["activeVerificationFiles"])
        )
        self.assertEqual(manifest["results"]["items"][0]["protocolVersion"], "implementation-result-v3")
        self.assertEqual(manifest["capsules"]["capsuleDirectoryCount"], 2)
        router = manifest["installedCallers"]["router"]
        self.assertTrue(router["hasVerificationRoute"])
        self.assertTrue(router["hasGoalLoopRoute"])
        self.assertTrue(router["hasGoalVerificationRoute"])
        self.assertTrue(router["routesByCompletionUnit"])
        self.assertTrue(router["requiresExactInputs"])
        self.assertTrue(router["keepsRecipeOptional"])
        self.assertTrue(router["rejectsNonIndependent"])
        self.assertTrue(router["forbidsFallback"])
        self.assertTrue(router["rejectsImplementationEvidence"])
        self.assertTrue(router["contentMatchesExpected"])
        skills = {item["name"]: item for item in manifest["installedCallers"]["skills"]}
        self.assertFalse(skills["implementation-lead"]["exists"])
        self.assertFalse(skills["verification-lead"]["exists"])
        self.assertFalse(skills["primary-verifier"]["exists"])
        self.assertEqual(manifest["legacyProcesses"]["matches"], [])
        self.assertEqual(manifest["legacyProcesses"]["observationErrors"], [])

    def test_optional_matching_implementation_installation_is_accepted(self) -> None:
        os.symlink(
            self.repo / "implementation-lead",
            self.installed / "implementation-lead",
            target_is_directory=True,
        )
        completed = self.census()
        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_removed_installed_skills_are_forbidden(self) -> None:
        removed = self.installed / "verification-lead"
        removed.mkdir()
        (removed / "SKILL.md").write_text("removed", encoding="utf-8")

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertTrue(
            any(error["code"] == "REMOVED_INSTALLED_SKILL" for error in manifest["installedCallers"]["errors"])
        )

    def test_wrong_optional_implementation_installation_is_fail_closed(self) -> None:
        installed = self.installed / "implementation-lead"
        installed.mkdir()
        (installed / "SKILL.md").write_text("stale copy", encoding="utf-8")

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertTrue(
            any(error["code"] == "INSTALLED_CALLER_MISMATCH" for error in manifest["installedCallers"]["errors"])
        )

    def test_router_removed_runtime_and_command_each_fail(self) -> None:
        router = self.installed / "iis-workflow/SKILL.md"
        baseline = router.read_text(encoding="utf-8")
        for residue in (
            "verification-runtime/iis-verify",
            "`iis-verify`",
        ):
            with self.subTest(residue=residue):
                router.write_text(baseline + residue, encoding="utf-8")
                completed = self.census()
                self.assertEqual(completed.returncode, 2, completed.stdout)
                router.write_text(baseline, encoding="utf-8")

    def test_foreign_or_missing_router_is_fail_closed(self) -> None:
        router = self.installed / "iis-workflow/SKILL.md"
        router.write_text("stale foreign router", encoding="utf-8")
        self.assertEqual(self.census().returncode, 2)
        router.unlink()
        self.assertEqual(self.census().returncode, 2)

    def test_contradictory_router_cannot_keep_positive_tokens_and_pass(self) -> None:
        router = self.installed / "iis-workflow/SKILL.md"
        router.write_text(
            router.read_text(encoding="utf-8")
            + "\nFor independent verification, select Implementation Lead and use its result as the AC verdict.\n",
            encoding="utf-8",
        )

        completed = self.census()

        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertFalse(manifest["installedCallers"]["router"]["contentMatchesExpected"])

    def test_renamed_installed_skill_cannot_expose_removed_runtime(self) -> None:
        renamed = self.installed / "renamed-checker/SKILL.md"
        renamed.parent.mkdir()
        renamed.write_text("Run verification-runtime/iis-verify", encoding="utf-8")
        completed = self.census()
        self.assertEqual(completed.returncode, 2, completed.stdout)
        manifest = json.loads(completed.stdout)
        self.assertTrue(
            any(error["code"] == "REMOVED_INSTALLED_SKILL" for error in manifest["installedCallers"]["errors"])
        )

    def test_active_config_and_contract_residue_are_fail_closed(self) -> None:
        for path, residue in (
            (self.config / "opencode.json", "iis-verify"),
            (self.repo / "README.md", "Primary Verifier"),
            (self.repo / "README.md", "verification-runtime"),
        ):
            with self.subTest(path=path):
                original = path.read_text(encoding="utf-8")
                path.write_text(original + residue, encoding="utf-8")
                completed = self.census()
                self.assertEqual(completed.returncode, 2, completed.stdout)
                path.write_text(original, encoding="utf-8")

    def test_readme_may_name_only_the_active_verification_leaf(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "verification-lead provides the active Verification Lead contract.\n",
            encoding="utf-8",
        )

        completed = self.census()

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_all_four_roots_are_required_by_cli(self) -> None:
        flag_indices = [
            self.argv().index(flag)
            for flag in ("--repo-root", "--state-root", "--installed-skill-root", "--config-root")
        ]
        for index in flag_indices:
            argv = self.argv()
            del argv[index : index + 2]
            with self.subTest(argv=argv):
                completed = self.census(argv)
                self.assertEqual(completed.returncode, 2)

    def test_missing_required_roots_fail_in_manifest(self) -> None:
        for flag in ("--repo-root", "--state-root", "--installed-skill-root", "--config-root"):
            argv = self.argv()
            argv[argv.index(flag) + 1] = str(self.root / f"missing-{flag[2:]}")
            with self.subTest(flag=flag):
                completed = self.census(argv)
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                manifest = json.loads(completed.stdout)
                self.assertTrue(manifest["roots"]["errors"])

    def test_unreadable_required_root_is_fail_closed(self) -> None:
        with patch.object(
            phase8_removal_census,
            "_required_directory",
            return_value=[{"code": "REQUIRED_ROOT_UNREADABLE", "message": "denied"}],
        ):
            manifest = phase8_removal_census.build_manifest(
                self.repo,
                self.state,
                self.installed,
                self.config,
            )
        self.assertTrue(phase8_removal_census._has_errors(manifest))

    def test_tracked_current_or_legacy_file_is_residue(self) -> None:
        for relative in (
            "iis_ephemeral_transport.py",
            "implementation-lead/tools/workflow-store/workflow_store.py",
        ):
            with self.subTest(relative=relative):
                path = self.repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("removed", encoding="utf-8")
                subprocess.run(["git", "add", relative], cwd=self.repo, check=True)
                completed = self.census()
                self.assertEqual(completed.returncode, 2, completed.stdout)
                path.unlink()
                subprocess.run(["git", "reset", "-q", "HEAD", "--", relative], cwd=self.repo, check=True)

    def test_exact_active_verification_leaf_files_are_not_removal_residue(self) -> None:
        subprocess.run(
            ["git", "add", *sorted(phase8_removal_census.ACTIVE_VERIFICATION_FILES)],
            cwd=self.repo,
            check=True,
        )

        completed = self.census()

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        manifest = json.loads(completed.stdout)
        self.assertEqual(manifest["inventory"]["trackedRemovedMechanismFiles"], [])
        self.assertEqual(manifest["inventory"]["residueFiles"], [])

    def test_each_active_verification_leaf_file_is_required(self) -> None:
        for relative in sorted(phase8_removal_census.ACTIVE_VERIFICATION_FILES):
            with self.subTest(relative=relative):
                path = self.repo / relative
                content = path.read_bytes()
                path.unlink()

                completed = self.census()

                self.assertEqual(completed.returncode, 2, completed.stdout)
                manifest = json.loads(completed.stdout)
                errors = manifest["inventory"]["errors"]
                self.assertTrue(
                    any(
                        error["code"] == "ACTIVE_VERIFICATION_FILE_MISSING"
                        and relative in error["message"]
                        for error in errors
                    )
                )
                path.write_bytes(content)

    def test_active_verification_leaf_symlinks_are_not_regular_files(self) -> None:
        target = self.root / "foreign-active-verification-file"
        target.write_text("foreign\n", encoding="utf-8")
        for relative in sorted(phase8_removal_census.ACTIVE_VERIFICATION_FILES):
            with self.subTest(relative=relative):
                path = self.repo / relative
                content = path.read_bytes()
                path.unlink()
                path.symlink_to(target)

                completed = self.census()

                self.assertEqual(completed.returncode, 2, completed.stdout)
                manifest = json.loads(completed.stdout)
                errors = manifest["inventory"]["errors"]
                self.assertTrue(
                    any(
                        error["code"] == "ACTIVE_VERIFICATION_FILE_NOT_REGULAR"
                        and relative in error["message"]
                        for error in errors
                    )
                )
                path.unlink()
                path.write_bytes(content)

    def test_each_active_verification_leaf_file_must_match_reviewed_content(self) -> None:
        for relative in sorted(phase8_removal_census.ACTIVE_VERIFICATION_FILES):
            with self.subTest(relative=relative):
                path = self.repo / relative
                content = path.read_bytes()
                path.write_text("trivial replacement\n", encoding="utf-8")

                completed = self.census()

                self.assertEqual(completed.returncode, 2, completed.stdout)
                manifest = json.loads(completed.stdout)
                errors = manifest["inventory"]["errors"]
                self.assertTrue(
                    any(
                        error["code"] == "ACTIVE_VERIFICATION_FILE_MISMATCH"
                        and relative in error["message"]
                        for error in errors
                    )
                )
                path.write_bytes(content)

    def test_other_verification_leaf_content_remains_residue(self) -> None:
        for relative, kind in (
            ("verification-lead/coverage_gate.py", "file"),
            ("verification-lead/tools/runtime.py", "file"),
            ("verification-lead/tests/pilot/extra.py", "file"),
            ("verification-lead/state", "directory"),
            ("verification-lead/tests/pilot/linked.py", "symlink"),
        ):
            with self.subTest(relative=relative, kind=kind):
                path = self.repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if kind == "file":
                    path.write_text("residue\n", encoding="utf-8")
                elif kind == "directory":
                    path.mkdir()
                else:
                    target = self.root / "foreign-verification-file"
                    target.write_text("foreign\n", encoding="utf-8")
                    path.symlink_to(target)
                completed = self.census()
                self.assertEqual(completed.returncode, 2, completed.stdout)
                if path.is_symlink() or path.is_file():
                    path.unlink()
                else:
                    path.rmdir()
                parent = path.parent
                while (
                    parent != self.repo
                    and parent.exists()
                    and parent.relative_to(self.repo).as_posix()
                    not in phase8_removal_census.ACTIVE_VERIFICATION_DIRECTORIES
                    and not any(parent.iterdir())
                ):
                    parent.rmdir()
                    parent = parent.parent

    def test_untracked_ignored_empty_and_symlink_residue_fail(self) -> None:
        cases = (
            ("verification-runtime/profile/package.json", "file"),
            ("verification-lead/__pycache__/coverage_gate.cpython-312.pyc", "file"),
            ("primary-verifier", "directory"),
            ("verification-runtime", "symlink"),
        )
        for relative, kind in cases:
            with self.subTest(relative=relative, kind=kind):
                path = self.repo / relative
                if kind == "file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("residue", encoding="utf-8")
                elif kind == "directory":
                    path.mkdir(parents=True)
                else:
                    target = self.root / "outside-runtime"
                    target.mkdir(exist_ok=True)
                    path.symlink_to(target, target_is_directory=True)
                completed = self.census()
                self.assertEqual(completed.returncode, 2, completed.stdout)
                if path.is_symlink() or path.is_file():
                    path.unlink()
                else:
                    path.rmdir()
                parent = path.parent
                while parent != self.repo and parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent

    def test_root_transport_bytecode_is_residue(self) -> None:
        cache = self.repo / "__pycache__"
        cache.mkdir()
        pyc = cache / "iis_ephemeral_transport.cpython-312.pyc"
        pyc.write_bytes(b"removed")
        completed = self.census()
        self.assertEqual(completed.returncode, 2, completed.stdout)

    def test_process_matching_covers_legacy_and_current_exact_names(self) -> None:
        for argv, expected in (
            (["python3", "/tmp/workflow_store.py"], "workflow_store.py"),
            (["/tmp/iis-verify", "--help"], "iis-verify"),
            (["python3", "/tmp/verification-runtime/control_entry.py"], "control_entry.py"),
            (["python3", "/tmp/verification-lead/coverage_gate.py"], "coverage_gate.py"),
            (
                ["python3", "/home/user01/project/iis-skills/iis_ephemeral_transport.py"],
                "iis_ephemeral_transport.py",
            ),
            (
                ["python3", "/home/user01/project/iis-skills/__pycache__/iis_ephemeral_transport.cpython-312.pyc"],
                "iis_ephemeral_transport.cpython-312.pyc",
            ),
        ):
            with self.subTest(argv=argv):
                self.assertEqual(phase8_removal_census._legacy_command(argv), expected)
        for argv in (
            ["python3", "-c", "iis-verify"],
            ["unrelated-command", "iis-verify"],
            ["python3", "/tmp/unrelated/control_entry.py"],
            ["python3", "/tmp/unrelated/coverage_gate.py"],
            ["python3", "/tmp/unrelated/iis_ephemeral_transport.py"],
            ["python3", "/tmp/unrelated/iis_ephemeral_transport.cpython-312.pyc"],
        ):
            self.assertIsNone(phase8_removal_census._legacy_command(argv))

        for argv, expected in (
            (["python3", "-u", "/tmp/workflow_store.py"], "workflow_store.py"),
            (["python3", "-X", "dev", "/tmp/verification-runtime/control_entry.py"], "control_entry.py"),
            (["python3", "--", "/tmp/verification-lead/coverage_gate.py"], "coverage_gate.py"),
        ):
            with self.subTest(argv=argv):
                self.assertEqual(phase8_removal_census._legacy_command(argv), expected)

    def test_process_match_or_unavailable_observation_fails(self) -> None:
        observations = (
            {
                "available": True,
                "matches": [{"pid": 1, "executable": "iis-verify", "argv": []}],
                "observationErrors": [],
            },
            {"available": False, "matches": [], "observationErrors": []},
            {
                "available": True,
                "matches": [],
                "observationErrors": [{"pid": 123, "error": "PermissionError"}],
            },
        )
        for observation in observations:
            with self.subTest(observation=observation), patch.object(
                phase8_removal_census,
                "_process_observation",
                return_value=observation,
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    code = phase8_removal_census.main(self.argv()[2:])
                self.assertEqual(code, 2)

    def test_unreadable_live_process_cmdline_is_observation_error(self) -> None:
        proc_root = Path("/proc")
        original_read_bytes = Path.read_bytes

        def read_bytes(path: Path) -> bytes:
            if path.parent.name.isdigit() and path.name == "cmdline":
                raise PermissionError("denied")
            return original_read_bytes(path)

        with patch.object(Path, "read_bytes", read_bytes):
            observation = phase8_removal_census._process_observation()

        self.assertTrue(observation["available"])
        self.assertTrue(observation["observationErrors"])
        self.assertTrue(
            all(item["error"] == "PermissionError" for item in observation["observationErrors"])
        )

    def test_unclassified_or_symlinked_active_config_entry_fails(self) -> None:
        tools = self.config / "tools"
        tools.mkdir()
        unsupported = tools / "verification.yaml"
        unsupported.write_text("iis-verify", encoding="utf-8")
        self.assertEqual(self.census().returncode, 2)
        unsupported.unlink()

        target = self.root / "foreign-tools"
        target.mkdir()
        (tools / "linked").symlink_to(target, target_is_directory=True)
        self.assertEqual(self.census().returncode, 2)

    def test_malformed_state_result_still_fails_without_writing(self) -> None:
        malformed = self.results / "malformed.json"
        malformed.write_bytes(b"{not json")
        observed = (self.repo, self.state, self.installed, self.config)
        before = tuple(tree_identity(root) for root in observed)
        completed = self.census()
        after = tuple(tree_identity(root) for root in observed)
        self.assertEqual(completed.returncode, 2, completed.stdout)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
