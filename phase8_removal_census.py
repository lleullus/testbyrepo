#!/usr/bin/env python3
"""Emit a read-only IIS removed-mechanism census as JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


LEGACY_SOURCE_PATHS = (
    "verification-lead/tools/verification-run",
    "implementation-lead/tools/implementation-result",
    "implementation-lead/tools/implementation-transaction",
    "implementation-lead/tools/workflow-store",
    "implementation-lead/tools/task-ownership-snapshot",
    "baseline-capsule",
)
CURRENT_VERIFICATION_PATHS = (
    "verification-lead",
    "primary-verifier",
    "iis_ephemeral_transport.py",
    "verification-runtime",
)
COUPLED_TEST_PATHS = (
    "implementation-lead/tests/implementation-result",
    "implementation-lead/tests/implementation-transaction",
    "implementation-lead/tests/pilot",
    "implementation-lead/tests/planning-workspace",
    "implementation-lead/tests/task-ownership",
    "implementation-lead/tests/workflow-store",
    "baseline-capsule/tests",
    "tests/test_iis_ephemeral_transport.py",
)
ACTIVE_VERIFICATION_FILES = frozenset(
    {
        "verification-lead/SKILL.md",
        "verification-lead/run_tests.py",
        "verification-lead/verdict_contract.py",
        "verification-lead/tests/test_contract.py",
        "verification-lead/tests/pilot/test_representative_pilots.py",
    }
)
ACTIVE_VERIFICATION_DIRECTORIES = frozenset(
    {
        "verification-lead",
        "verification-lead/tests",
        "verification-lead/tests/pilot",
    }
)
ACTIVE_VERIFICATION_SHA256 = {
    # Updated only with a reviewed canonical leaf change.
    "verification-lead/SKILL.md": "9ded06082faae2b46b935878df0af495492473f6e1fff9a462abe12dab7dd3fc",
    "verification-lead/run_tests.py": "8f0c1c288930dda0468d077bb61b6a046aad69b6531dc6cdb7f9d457cf8ea185",
    "verification-lead/verdict_contract.py": "0ec52acc6f27ca9167adbabeddfede4dfcc719e0fe480e124c43e3ff95dba9d7",
    "verification-lead/tests/test_contract.py": "50f888b5e1da9703aa3f4515d5ed9bbc2003fb2ae57c2c494e04c6ca0dad0fd5",
    "verification-lead/tests/pilot/test_representative_pilots.py": "02a122d5efbf0051d67f50b3d370f9dfa2c4f210516dd086d0e9be19a4d1c530",
}
ACTIVE_RALPH_SHA256 = {
    # Reviewed active Goal-fulfillment route, closure contract, and exact structural admission support.
    "ARCHITECTURE-CLOSURE.md": "86135fe01f5f7b9cbb50320df918b755c4afe6b83c3005e130748838612d1688",
    "iis-goal-loop/SKILL.md": "34b5f3ed7effee0e6f7daf1b47662eb7797cb4aa41ca92337012c3eecf7e87d2",
    "goal-verification-lead/SKILL.md": "02bba8db29057cefc65443ef50ffe1206fc0e0d27ac84d9cbad1ad3b10ddeaa6",
    "matt/skills/to-tickets/validate_ticket_set.py": "2a5eda27390c079bfb21200c71f96eec66f878c2bb9db1bc9696d8e37b8895ea",
}
LEGACY_EXECUTABLE_STEMS = (
    "verification_run",
    "implementation_result",
    "implementation_transaction",
    "workflow_store",
    "ownership_snapshot",
    "baseline_capsule",
)
LEGACY_EXECUTABLES = frozenset(f"{stem}.py" for stem in LEGACY_EXECUTABLE_STEMS)
LEGACY_PYC_PATTERN = re.compile(
    r"^(?:"
    + "|".join(LEGACY_EXECUTABLE_STEMS)
    + r")(?:\.cpython-\d+(?:\.\d+)*(?:\.opt-\d+)?)?\.pyc$"
)
CURRENT_UNIQUE_EXECUTABLES = frozenset({"iis-verify"})
CURRENT_UNIQUE_PYC_PATTERN = re.compile(
    r"^iis-verify(?:\.cpython-\d+(?:\.\d+)*(?:\.opt-\d+)?)?\.pyc$"
)
CURRENT_RUNTIME_EXECUTABLES = frozenset(
    {"control_entry.py", "model_relay.py", "outer_bootstrap.py", "verification_tools.py"}
)
CURRENT_RUNTIME_PYC_PATTERN = re.compile(
    r"^(?:control_entry|model_relay|outer_bootstrap|verification_tools)"
    r"(?:\.cpython-\d+(?:\.\d+)*(?:\.opt-\d+)?)?\.pyc$"
)
COVERAGE_GATE_PYC_PATTERN = re.compile(
    r"^coverage_gate(?:\.cpython-\d+(?:\.\d+)*(?:\.opt-\d+)?)?\.pyc$"
)
TRANSPORT_PYC_PATTERN = re.compile(
    r"^iis_ephemeral_transport(?:\.cpython-\d+(?:\.\d+)*(?:\.opt-\d+)?)?\.pyc$"
)
ACTIVE_REPO_FILES = (
    "README.md",
    "scope-shaper/SKILL.md",
    "matt/skills/to-tickets/SKILL.md",
    "implementation-lead/SKILL.md",
)
ACTIVE_REPO_TERM_ALLOWLIST = {
    "README.md": frozenset({"verification lead", "verification-lead"}),
    "implementation-lead/SKILL.md": frozenset({"verification lead"}),
}
REMOVED_ACTIVE_TERMS = (
    "verification lead",
    "primary verifier",
    "runtime runner",
    "verification-lead",
    "primary-verifier",
    "iis-verify",
    "verification-runtime",
    "iis_ephemeral_transport",
    "route-navigation",
    "coverage_gate",
    "publish_route_navigation",
)
ROUTER_RELATIVE_PATH = Path("iis-workflow/SKILL.md")
ROUTER_IMPLEMENTATION_PATH = "/home/user01/project/iis-skills/implementation-lead/SKILL.md"
ROUTER_VERIFICATION_PATH = "/home/user01/project/iis-skills/verification-lead/SKILL.md"
ROUTER_GOAL_LOOP_PATH = "/home/user01/project/iis-skills/iis-goal-loop/SKILL.md"
ROUTER_GOAL_VERIFICATION_PATH = "/home/user01/project/iis-skills/goal-verification-lead/SKILL.md"
ROUTER_SHA256 = "85f3d7aed5399bf869595adc0bd08d2d58a82a71fc0c9da2ff384cff7a1088b9"
CONFIG_SUFFIXES = frozenset({".json", ".jsonc", ".md", ".ts", ".js"})
CONFIG_EXCLUDED_DIRECTORIES = frozenset({"node_modules", ".audit", ".git"})
ACTIVE_CONFIG_ROOT_FILES = frozenset(
    {"opencode.json", "opencode.jsonc", "AGENTS.md", "package.json"}
)
ACTIVE_CONFIG_DIRECTORIES = frozenset(
    {"agent", "agents", "command", "commands", "plugin", "plugins", "tools", "instructions", "skill", "skills"}
)
INERT_CONFIG_SUFFIXES = (".disabled",)
TRANSPORT_SOURCE_PATH = Path("/home/user01/project/iis-skills/iis_ephemeral_transport.py")
TRANSPORT_CACHE_ROOT = TRANSPORT_SOURCE_PATH.parent / "__pycache__"
LEGACY_SKILL_TERMS = (
    "baseline-capsule",
    "implementation-result",
    "implementation-transaction",
    "task-ownership",
    "workflow-store",
    "verification-run",
    "verification-result-v1",
    "ownership_snapshot",
    "executable_identity",
    "PROCESS executor",
)
CAPSULE_REF_PATTERN = re.compile(r"^capsule:v1:([a-f0-9]{32})$")
PYTHON_INTERPRETER_PATTERN = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")


def _error(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _canonical_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve(strict=False)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digest_lines(lines: Iterable[str]) -> str:
    return _sha256("".join(lines).encode("utf-8"))


def _read_result_items(result_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not result_root.exists():
        return [], [_error("RESULT_ROOT_MISSING", f"result root does not exist: {result_root}")]
    if not result_root.is_dir():
        return [], [_error("RESULT_ROOT_NOT_DIRECTORY", f"result root is not a directory: {result_root}")]

    paths: list[Path] = []

    def record_walk_error(exc: OSError) -> None:
        errors.append(_error("RESULT_ROOT_UNREADABLE", f"cannot enumerate result root: {exc}"))

    for directory, _subdirectories, files in os.walk(result_root, followlinks=False, onerror=record_walk_error):
        root = Path(directory)
        paths.extend(root / filename for filename in files)

    items: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda path: path.relative_to(result_root).as_posix()):
        try:
            mode = path.lstat().st_mode
            relative_path = path.relative_to(result_root).as_posix()
            if not stat.S_ISREG(mode):
                items.append(
                    {
                        "relativePath": relative_path,
                        "size": None,
                        "sha256": None,
                        "protocolVersion": None,
                        "capsuleRef": None,
                        "error": _error("RESULT_NOT_REGULAR_FILE", "result entry is not a regular file"),
                    }
                )
                continue
            payload = path.read_bytes()
        except OSError as exc:
            items.append(
                {
                    "relativePath": path.relative_to(result_root).as_posix(),
                    "size": None,
                    "sha256": None,
                    "protocolVersion": None,
                    "capsuleRef": None,
                    "error": _error("RESULT_UNREADABLE", f"cannot read result: {exc}"),
                }
            )
            continue

        item: dict[str, Any] = {
            "relativePath": relative_path,
            "size": len(payload),
            "sha256": _sha256(payload),
            "protocolVersion": None,
            "capsuleRef": None,
        }
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            item["error"] = _error("RESULT_JSON_UNREADABLE", f"cannot decode result JSON: {exc}")
            items.append(item)
            continue
        if not isinstance(decoded, dict):
            item["error"] = _error("RESULT_JSON_NOT_OBJECT", "result JSON must be an object")
            items.append(item)
            continue

        protocol_version = decoded.get("protocolVersion")
        capsule_ref = decoded.get("capsuleRef")
        item["protocolVersion"] = protocol_version if isinstance(protocol_version, str) else None
        item["capsuleRef"] = capsule_ref if isinstance(capsule_ref, str) else None
        field_errors: list[str] = []
        if not isinstance(protocol_version, str):
            field_errors.append("protocolVersion")
        if not isinstance(capsule_ref, str):
            field_errors.append("capsuleRef")
        if field_errors:
            item["error"] = _error(
                "RESULT_FIELDS_MISSING", f"result does not contain string fields: {', '.join(field_errors)}"
            )
        items.append(item)
    return items, errors


def _file_digest_list(items: list[dict[str, Any]], result_root: Path) -> str | None:
    if any(item["sha256"] is None for item in items):
        return None
    # This is the same sha256sum-compatible list shape used by the preparation evidence.
    return _digest_lines(
        f"{item['sha256']}  {result_root / item['relativePath']}\n" for item in items
    )


def _directory_bytes(root: Path) -> tuple[int | None, list[dict[str, str]]]:
    if not root.exists():
        return None, [_error("CAPSULE_ROOT_MISSING", f"capsule root does not exist: {root}")]
    if not root.is_dir():
        return None, [_error("CAPSULE_ROOT_NOT_DIRECTORY", f"capsule root is not a directory: {root}")]
    errors: list[dict[str, str]] = []
    paths: list[Path] = []

    def record_walk_error(exc: OSError) -> None:
        errors.append(_error("CAPSULE_ROOT_UNREADABLE", f"cannot enumerate capsule root: {exc}"))

    for directory, _subdirectories, files in os.walk(root, followlinks=False, onerror=record_walk_error):
        directory_path = Path(directory)
        paths.extend(directory_path / filename for filename in files)

    total = 0
    for path in paths:
        try:
            if stat.S_ISREG(path.lstat().st_mode):
                total += path.lstat().st_size
        except OSError as exc:
            errors.append(_error("CAPSULE_ENTRY_UNREADABLE", f"cannot stat {path}: {exc}"))
    return total, errors


def _capsule_observation(state_root: Path, result_items: list[dict[str, Any]]) -> dict[str, Any]:
    store_root = state_root / "baseline-capsules"
    capsules_root = store_root / "capsules"
    store_bytes, errors = _directory_bytes(store_root)
    capsule_bytes, capsule_errors = _directory_bytes(capsules_root)
    errors.extend(capsule_errors)

    directory_count: int | None = None
    try:
        capsules_is_directory = stat.S_ISDIR(capsules_root.lstat().st_mode)
    except OSError:
        capsules_is_directory = False
    if capsules_is_directory:
        try:
            directory_count = sum(1 for entry in os.scandir(capsules_root) if entry.is_dir(follow_symlinks=False))
        except OSError as exc:
            errors.append(_error("CAPSULE_ROOT_UNREADABLE", f"cannot count capsule directories: {exc}"))

    refs = sorted({item["capsuleRef"] for item in result_items if isinstance(item["capsuleRef"], str)})
    referenced: list[dict[str, Any]] = []
    for capsule_ref in refs:
        match = CAPSULE_REF_PATTERN.fullmatch(capsule_ref)
        if match is None:
            referenced.append(
                {
                    "capsuleRef": capsule_ref,
                    "exists": False,
                    "error": _error("CAPSULE_REF_MALFORMED", "capsuleRef does not have the capsule:v1 token form"),
                }
            )
            continue
        capsule_path = capsules_root / match.group(1)
        try:
            exists = stat.S_ISDIR(capsule_path.lstat().st_mode)
        except OSError:
            exists = False
        entry: dict[str, Any] = {"capsuleRef": capsule_ref, "exists": exists}
        if not exists:
            entry["error"] = _error("REFERENCED_CAPSULE_MISSING", "referenced capsule directory is absent")
        referenced.append(entry)

    return {
        "storeRoot": str(store_root),
        "capsulesRoot": str(capsules_root),
        "capsuleDirectoryCount": directory_count,
        "storeBytes": store_bytes,
        "capsuleBytes": capsule_bytes,
        "referenced": referenced,
        "referenceListSha256": _digest_lines(f"{capsule_ref}\n" for capsule_ref in refs),
        "errors": errors,
    }


def _git_output(repo_root: Path, arguments: list[str]) -> tuple[bytes | None, dict[str, str] | None]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return None, _error("GIT_EXECUTABLE_UNAVAILABLE", f"cannot execute git: {exc}")
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        return None, _error("GIT_COMMAND_FAILED", f"git {' '.join(arguments)} failed: {message}")
    return completed.stdout, None


def _tracked_inventory(repo_root: Path) -> dict[str, Any]:
    revision_raw, revision_error = _git_output(repo_root, ["rev-parse", "HEAD"])
    source_raw, source_error = _git_output(
        repo_root,
        ["ls-files", "-z", "--", *LEGACY_SOURCE_PATHS, *CURRENT_VERIFICATION_PATHS],
    )
    test_raw, test_error = _git_output(repo_root, ["ls-files", "-z", "--", *COUPLED_TEST_PATHS])
    errors = [error for error in (revision_error, source_error, test_error) if error is not None]

    active_verification_files: list[dict[str, Any]] = []
    for relative in sorted(ACTIVE_VERIFICATION_FILES):
        path = repo_root / relative
        entry: dict[str, Any] = {"path": relative}
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            entry.update({"exists": False, "isRegularFile": False})
            error = _error(
                "ACTIVE_VERIFICATION_FILE_MISSING",
                f"active verification file is missing: {relative}",
            )
            entry["error"] = error
            errors.append(error)
        except OSError as exc:
            entry.update({"exists": None, "isRegularFile": False})
            error = _error(
                "ACTIVE_VERIFICATION_FILE_UNREADABLE",
                f"cannot inspect active verification file {relative}: {exc}",
            )
            entry["error"] = error
            errors.append(error)
        else:
            is_regular = stat.S_ISREG(mode)
            entry.update({"exists": True, "isRegularFile": is_regular})
            if not is_regular:
                error = _error(
                    "ACTIVE_VERIFICATION_FILE_NOT_REGULAR",
                    f"active verification path is not a regular file: {relative}",
                )
                entry["error"] = error
                errors.append(error)
            else:
                try:
                    observed_sha256 = _sha256(path.read_bytes())
                except OSError as exc:
                    error = _error(
                        "ACTIVE_VERIFICATION_FILE_UNREADABLE",
                        f"cannot read active verification file {relative}: {exc}",
                    )
                    entry["error"] = error
                    errors.append(error)
                else:
                    expected_sha256 = ACTIVE_VERIFICATION_SHA256[relative]
                    entry.update(
                        {
                            "sha256": observed_sha256,
                            "expectedSha256": expected_sha256,
                            "contentMatchesExpected": observed_sha256 == expected_sha256,
                        }
                    )
                    if observed_sha256 != expected_sha256:
                        error = _error(
                            "ACTIVE_VERIFICATION_FILE_MISMATCH",
                            f"active verification file does not match reviewed content: {relative}",
                        )
                        entry["error"] = error
                        errors.append(error)
        active_verification_files.append(entry)

    active_ralph_files: list[dict[str, Any]] = []
    for relative, expected_sha256 in sorted(ACTIVE_RALPH_SHA256.items()):
        path = repo_root / relative
        entry = {"path": relative}
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            entry.update({"exists": False, "isRegularFile": False})
            error = _error("ACTIVE_RALPH_FILE_MISSING", f"active Ralph file is missing: {relative}")
            entry["error"] = error
            errors.append(error)
        except OSError as exc:
            entry.update({"exists": None, "isRegularFile": False})
            error = _error("ACTIVE_RALPH_FILE_UNREADABLE", f"cannot inspect active Ralph file {relative}: {exc}")
            entry["error"] = error
            errors.append(error)
        else:
            is_regular = stat.S_ISREG(mode)
            entry.update({"exists": True, "isRegularFile": is_regular})
            if not is_regular:
                error = _error("ACTIVE_RALPH_FILE_NOT_REGULAR", f"active Ralph path is not a regular file: {relative}")
                entry["error"] = error
                errors.append(error)
            else:
                try:
                    observed_sha256 = _sha256(path.read_bytes())
                except OSError as exc:
                    error = _error("ACTIVE_RALPH_FILE_UNREADABLE", f"cannot read active Ralph file {relative}: {exc}")
                    entry["error"] = error
                    errors.append(error)
                else:
                    entry.update(
                        {
                            "sha256": observed_sha256,
                            "expectedSha256": expected_sha256,
                            "contentMatchesExpected": observed_sha256 == expected_sha256,
                        }
                    )
                    if observed_sha256 != expected_sha256:
                        error = _error(
                            "ACTIVE_RALPH_FILE_MISMATCH",
                            f"active Ralph file does not match reviewed content: {relative}",
                        )
                        entry["error"] = error
                        errors.append(error)
        active_ralph_files.append(entry)

    revision = revision_raw.decode("ascii", errors="replace").strip() if revision_raw is not None else None
    source_files = (
        sorted(
            path
            for path in source_raw.decode("utf-8", errors="surrogateescape").split("\0")
            if path
            and path not in ACTIVE_VERIFICATION_FILES
            and (repo_root / path).exists()
            and stat.S_ISREG((repo_root / path).lstat().st_mode)
        )
        if source_raw is not None
        else []
    )
    test_files = (
        sorted(
            path
            for path in test_raw.decode("utf-8", errors="surrogateescape").split("\0")
            if path
            and path not in ACTIVE_VERIFICATION_FILES
            and (repo_root / path).exists()
            and stat.S_ISREG((repo_root / path).lstat().st_mode)
        )
        if test_raw is not None
        else []
    )
    tracked = set(source_files + test_files)
    filesystem, filesystem_errors = _filesystem_observation(repo_root)
    errors.extend(filesystem_errors)
    residue = sorted(path for path in filesystem["legacyFiles"] if path not in tracked)
    empty_directories = sorted(
        directory
        for directory in filesystem["legacyDirectories"]
        if not any(path.startswith(directory + "/") for path in filesystem["legacyFiles"])
    )
    if residue:
        errors.append(
            _error(
                "LEGACY_FILESYSTEM_RESIDUE",
                f"untracked or ignored legacy files remain on the filesystem: {', '.join(residue)}",
            )
        )
    if empty_directories:
        errors.append(
            _error(
                "LEGACY_FILESYSTEM_RESIDUE",
                f"empty legacy directories remain on the filesystem: {', '.join(empty_directories)}",
            )
        )
    tracked_removed = sorted(set(source_files + test_files))
    current_tracked = sorted(
        path
        for path in tracked_removed
        if any(path == root or path.startswith(root + "/") for root in CURRENT_VERIFICATION_PATHS)
        or path == "tests/test_iis_ephemeral_transport.py"
    )
    if tracked_removed:
        errors.append(
            _error(
                "TRACKED_REMOVED_MECHANISM_RESIDUE",
                f"tracked removed-mechanism files remain: {', '.join(tracked_removed)}",
            )
        )
    return {
        "repoRoot": str(repo_root),
        "revision": revision,
        "legacySourceFiles": source_files,
        "mechanismCoupledTestFiles": test_files,
        "trackedRemovedMechanismFiles": tracked_removed,
        "currentVerificationTrackedFiles": current_tracked,
        "activeVerificationFiles": active_verification_files,
        "activeRalphFiles": active_ralph_files,
        "filesystemLegacyFiles": filesystem["legacyFiles"],
        "filesystemLegacyDirectories": filesystem["legacyDirectories"],
        "residueFiles": residue,
        "emptyLegacyDirectories": empty_directories,
        "inventorySha256": _digest_lines(f"{path}\n" for path in [*source_files, *test_files]),
        "filesystemInventorySha256": filesystem["inventorySha256"],
        "errors": errors,
    }


def _filesystem_observation(repo_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Observe the bounded legacy paths on the actual filesystem without following symlinks."""
    errors: list[dict[str, str]] = []
    legacy_files: set[str] = set()
    legacy_directories: set[str] = set()
    bounded_roots = list(
        dict.fromkeys((*LEGACY_SOURCE_PATHS, *CURRENT_VERIFICATION_PATHS, *COUPLED_TEST_PATHS))
    )

    def record_walk_error(exc: OSError) -> None:
        errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot enumerate legacy path: {exc}"))

    for bounded in bounded_roots:
        path = repo_root / bounded
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot inspect legacy path {bounded}: {exc}"))
            continue
        if stat.S_ISLNK(mode):
            errors.append(_error("LEGACY_FILESYSTEM_RESIDUE", f"legacy path is a symlink: {bounded}"))
            continue
        if not stat.S_ISDIR(mode):
            legacy_files.add(bounded)
            continue
        for directory, subdirectories, filenames in os.walk(path, followlinks=False, onerror=record_walk_error):
            directory_path = Path(directory)
            relative_directory = directory_path.relative_to(repo_root).as_posix()
            if relative_directory not in ACTIVE_VERIFICATION_DIRECTORIES:
                legacy_directories.add(relative_directory)
            for subdirectory in subdirectories[:]:
                child = directory_path / subdirectory
                relative_child = child.relative_to(repo_root).as_posix()
                try:
                    child_mode = child.lstat().st_mode
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot inspect legacy path {relative_child}: {exc}"))
                    subdirectories.remove(subdirectory)
                    continue
                if stat.S_ISLNK(child_mode):
                    legacy_files.add(relative_child)
                    errors.append(_error("LEGACY_FILESYSTEM_RESIDUE", f"legacy path is a symlink: {relative_child}"))
                    subdirectories.remove(subdirectory)
            for filename in filenames:
                child = directory_path / filename
                relative_child = child.relative_to(repo_root).as_posix()
                try:
                    child_mode = child.lstat().st_mode
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot inspect legacy path {relative_child}: {exc}"))
                    continue
                if stat.S_ISLNK(child_mode):
                    legacy_files.add(relative_child)
                    errors.append(_error("LEGACY_FILESYSTEM_RESIDUE", f"legacy path is a symlink: {relative_child}"))
                elif relative_child not in ACTIVE_VERIFICATION_FILES:
                    legacy_files.add(relative_child)

    root_cache = repo_root / "__pycache__"
    try:
        with os.scandir(root_cache) as entries:
            for entry in entries:
                if TRANSPORT_PYC_PATTERN.fullmatch(entry.name):
                    relative = (Path("__pycache__") / entry.name).as_posix()
                    legacy_files.add(relative)
                    try:
                        if stat.S_ISLNK(entry.stat(follow_symlinks=False).st_mode):
                            errors.append(
                                _error("LEGACY_FILESYSTEM_RESIDUE", f"verification bytecode is a symlink: {relative}")
                            )
                    except OSError as exc:
                        errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot inspect {relative}: {exc}"))
    except FileNotFoundError:
        pass
    except OSError as exc:
        errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot enumerate root bytecode cache: {exc}"))

    files = sorted(legacy_files)
    directories = sorted(legacy_directories)
    return {
        "legacyFiles": files,
        "legacyDirectories": directories,
        "inventorySha256": _digest_lines(f"{path}\n" for path in [*files, *directories]),
    }, errors


def _legacy_command(argv: list[str]) -> str | None:
    if not argv:
        return None
    executable = Path(argv[0]).name
    if executable in LEGACY_EXECUTABLES or LEGACY_PYC_PATTERN.fullmatch(executable):
        return executable
    current = _current_verification_executable(argv[0])
    if current is not None:
        return current
    if PYTHON_INTERPRETER_PATTERN.fullmatch(executable) and len(argv) >= 2:
        script_argument = _python_script_argument(argv)
        if script_argument is None:
            return None
        script = Path(script_argument).name
        if script in LEGACY_EXECUTABLES or LEGACY_PYC_PATTERN.fullmatch(script):
            return script
        return _current_verification_executable(script_argument)
    return None


def _python_script_argument(argv: list[str]) -> str | None:
    index = 1
    while index < len(argv):
        argument = argv[index]
        if argument == "--":
            return argv[index + 1] if index + 1 < len(argv) else None
        if argument in {"-c", "-m"} or argument.startswith(("-c", "-m")):
            return None
        if argument in {"-W", "-X", "--check-hash-based-pycs"}:
            index += 2
            continue
        if argument.startswith(("-W", "-X", "--check-hash-based-pycs=")):
            index += 1
            continue
        if argument.startswith("-"):
            index += 1
            continue
        return argument
    return None


def _current_verification_executable(raw_path: str) -> str | None:
    path = Path(raw_path)
    name = path.name
    if name in CURRENT_UNIQUE_EXECUTABLES or CURRENT_UNIQUE_PYC_PATTERN.fullmatch(name):
        return name
    if "verification-runtime" in path.parts and (
        name in CURRENT_RUNTIME_EXECUTABLES or CURRENT_RUNTIME_PYC_PATTERN.fullmatch(name)
    ):
        return name
    if "verification-lead" in path.parts and (
        name == "coverage_gate.py" or COVERAGE_GATE_PYC_PATTERN.fullmatch(name)
    ):
        return name
    if name == "iis_ephemeral_transport.py" and path == TRANSPORT_SOURCE_PATH:
        return name
    if TRANSPORT_PYC_PATTERN.fullmatch(name) and path.parent == TRANSPORT_CACHE_ROOT:
        return name
    return None


def _process_observation() -> dict[str, Any]:
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return {"available": False, "matches": [], "observationErrors": []}

    excluded_pids = {os.getpid(), os.getppid()}
    matches: list[dict[str, Any]] = []
    observation_errors: list[dict[str, Any]] = []
    try:
        entries = list(proc_root.iterdir())
    except OSError as exc:
        return {
            "available": False,
            "matches": [],
            "observationErrors": [{"pid": None, "error": type(exc).__name__}],
        }
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) in excluded_pids:
            continue
        try:
            raw_argv = (entry / "cmdline").read_bytes()
        except (FileNotFoundError, ProcessLookupError):
            # A process that exited after enumeration cannot remain a hidden
            # removed-runtime invocation.
            continue
        except OSError as exc:
            observation_errors.append({"pid": int(entry.name), "error": type(exc).__name__})
            continue
        argv = [part.decode("utf-8", errors="surrogateescape") for part in raw_argv.split(b"\0") if part]
        executable = _legacy_command(argv)
        if executable is not None:
            matches.append({"pid": int(entry.name), "executable": executable, "argv": argv})
    return {
        "available": True,
        "matches": sorted(matches, key=lambda item: item["pid"]),
        "observationErrors": sorted(observation_errors, key=lambda item: item["pid"]),
    }


def _required_directory(root: Path, label: str) -> list[dict[str, str]]:
    try:
        mode = root.lstat().st_mode
    except FileNotFoundError:
        return [_error("REQUIRED_ROOT_MISSING", f"{label} does not exist: {root}")]
    except OSError as exc:
        return [_error("REQUIRED_ROOT_UNREADABLE", f"cannot inspect {label}: {exc}")]
    if not stat.S_ISDIR(mode):
        return [_error("REQUIRED_ROOT_NOT_DIRECTORY", f"{label} is not a directory: {root}")]
    try:
        with os.scandir(root) as entries:
            next(entries, None)
    except OSError as exc:
        return [_error("REQUIRED_ROOT_UNREADABLE", f"cannot enumerate {label}: {exc}")]
    return []


def _skill_entry(installed_skill_root: Path, name: str, repo_root: Path) -> dict[str, Any]:
    installed_dir = installed_skill_root / name
    skill_file = installed_dir / "SKILL.md"
    entry: dict[str, Any] = {"name": name}
    try:
        mode = installed_dir.lstat().st_mode
    except FileNotFoundError:
        entry.update({"exists": False, "isSymlink": False, "linkTarget": None})
        return entry
    except OSError as exc:
        entry.update({"exists": None, "error": _error("INSTALLED_CALLER_UNREADABLE", str(exc))})
        return entry
    entry["exists"] = True
    entry["isSymlink"] = stat.S_ISLNK(mode)
    try:
        entry["linkTarget"] = os.readlink(installed_dir) if entry["isSymlink"] else None
        entry["canonicalTarget"] = str(installed_dir.resolve(strict=True))
    except OSError as exc:
        entry["error"] = _error("INSTALLED_CALLER_UNREADABLE", str(exc))
        return entry
    expected_dir = repo_root / name
    entry["expectedTarget"] = str(expected_dir.resolve(strict=False))
    entry["targetMatchesExpected"] = entry["canonicalTarget"] == entry["expectedTarget"]
    try:
        payload = skill_file.read_bytes()
        expected_payload = (expected_dir / "SKILL.md").read_bytes()
    except OSError as exc:
        entry["error"] = _error("INSTALLED_CALLER_UNREADABLE", str(exc))
        return entry
    entry["skillMdSha256"] = _sha256(payload)
    entry["expectedSkillMdSha256"] = _sha256(expected_payload)
    entry["contentMatchesExpected"] = payload == expected_payload
    legacy_terms = sorted(term for term in LEGACY_SKILL_TERMS if term in payload.decode("utf-8", errors="replace"))
    entry["legacyTermsFound"] = legacy_terms
    return entry


def _installed_callers(installed_skill_root: Path, repo_root: Path) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    active_skill_files: list[dict[str, Any]] = []
    errors = _required_directory(installed_skill_root, "installed Codex skill root")
    for name in ("implementation-lead", "verification-lead", "primary-verifier"):
        entry = _skill_entry(installed_skill_root, name, repo_root)
        skills.append(entry)
        if "error" in entry:
            errors.append(entry["error"])
        if name in {"verification-lead", "primary-verifier"} and entry.get("exists"):
            errors.append(_error("REMOVED_INSTALLED_SKILL", f"removed installed skill remains: {name}"))
        if name == "implementation-lead" and entry.get("exists"):
            if not entry.get("targetMatchesExpected") or not entry.get("contentMatchesExpected"):
                errors.append(
                    _error("INSTALLED_CALLER_MISMATCH", "installed implementation-lead does not match repository")
                )
            elif entry.get("legacyTermsFound"):
                errors.append(
                    _error(
                        "INSTALLED_CALLER_MISMATCH",
                        "installed implementation-lead still references retired mechanism terms",
                    )
                )

    router_path = installed_skill_root / ROUTER_RELATIVE_PATH
    router: dict[str, Any] = {"path": str(router_path)}
    try:
        mode = router_path.lstat().st_mode
        if not stat.S_ISREG(mode):
            raise OSError("installed router is not a regular file")
        payload = router_path.read_bytes()
        text = payload.decode("utf-8")
        normalized = " ".join(text.split())
        router_sha256 = _sha256(payload)
        router.update(
            {
                "exists": True,
                "sha256": router_sha256,
                "expectedSha256": ROUTER_SHA256,
                "contentMatchesExpected": router_sha256 == ROUTER_SHA256,
            }
        )
        forbidden = sorted(
            term
            for term in (
                "verification-runtime/iis-verify",
                "`iis-verify`",
                "Primary Verifier",
            )
            if term in text
        )
        router["forbiddenTermsFound"] = forbidden
        router["hasImplementationRoute"] = ROUTER_IMPLEMENTATION_PATH in text
        router["hasVerificationRoute"] = ROUTER_VERIFICATION_PATH in text
        router["hasGoalLoopRoute"] = ROUTER_GOAL_LOOP_PATH in text
        router["hasGoalVerificationRoute"] = ROUTER_GOAL_VERIFICATION_PATH in text
        router["routesByCompletionUnit"] = all(
            term in normalized
            for term in (
                "Route By Requested Completion Unit",
                "Apply explicit leaf requests before broad IIS inference",
                "If the user requested planning only, do not enter Ralph",
                "Only fresh whole-Spec `GOAL VERIFIED`",
            )
        )
        router["requiresExactInputs"] = all(
            term in normalized
            for term in (
                "one exact ready local Markdown Ticket",
                "exact `Project-Root`",
            )
        )
        router["keepsRecipeOptional"] = all(
            term in normalized
            for term in (
                "Candidate Execution Recipe is optional",
                "non-authoritative",
            )
        )
        router["rejectsNonIndependent"] = all(
            term in normalized
            for term in (
                "`Operator-assisted`",
                "`Not independently verifiable`",
                "has no independent IIS verification route",
            )
        )
        router["forbidsFallback"] = all(
            term in normalized
            for term in (
                "Do not bypass that boundary through Implementation Lead",
                "another agent",
                "compatibility command",
                "implementation checks",
                "instead of selecting a fallback",
            )
        )
        router["rejectsImplementationEvidence"] = all(
            term in normalized
            for term in (
                "Do not require an Implementation Lead result",
                "independent authority",
                "direct evidence",
                "AC verdict",
            )
        )
        if (
            forbidden
            or not router["contentMatchesExpected"]
            or not router["hasImplementationRoute"]
            or not router["hasVerificationRoute"]
            or not router["hasGoalLoopRoute"]
            or not router["hasGoalVerificationRoute"]
            or not router["routesByCompletionUnit"]
            or not router["requiresExactInputs"]
            or not router["keepsRecipeOptional"]
            or not router["rejectsNonIndependent"]
            or not router["forbidsFallback"]
            or not router["rejectsImplementationEvidence"]
        ):
            errors.append(_error("INSTALLED_ROUTER_MISMATCH", "installed IIS router does not enforce cutover contract"))
    except (OSError, UnicodeDecodeError) as exc:
        router.update({"exists": False, "error": _error("INSTALLED_ROUTER_UNREADABLE", str(exc))})
        errors.append(router["error"])

    def walk_error(exc: OSError) -> None:
        errors.append(_error("INSTALLED_SKILL_UNREADABLE", f"cannot enumerate installed skills: {exc}"))

    for directory, subdirectories, filenames in os.walk(
        installed_skill_root,
        followlinks=False,
        onerror=walk_error,
    ):
        directory_path = Path(directory)
        for subdirectory in subdirectories[:]:
            child = directory_path / subdirectory
            try:
                child_mode = child.lstat().st_mode
            except OSError as exc:
                errors.append(_error("INSTALLED_SKILL_UNREADABLE", f"cannot inspect {child}: {exc}"))
                subdirectories.remove(subdirectory)
                continue
            if stat.S_ISLNK(child_mode):
                relative = child.relative_to(installed_skill_root).as_posix()
                try:
                    target = os.readlink(child)
                except OSError as exc:
                    errors.append(_error("INSTALLED_SKILL_UNREADABLE", f"cannot read link {relative}: {exc}"))
                    subdirectories.remove(subdirectory)
                    continue
                target_matches = sorted(term for term in REMOVED_ACTIVE_TERMS if term in target.lower())
                if target_matches:
                    errors.append(
                        _error(
                            "REMOVED_INSTALLED_SKILL",
                            f"installed skill link {relative} targets removed feature terms: {', '.join(target_matches)}",
                        )
                    )
                subdirectories.remove(subdirectory)
        if "SKILL.md" not in filenames:
            continue
        skill_path = directory_path / "SKILL.md"
        relative = skill_path.relative_to(installed_skill_root).as_posix()
        entry: dict[str, Any] = {"path": relative}
        try:
            mode = skill_path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise OSError("installed SKILL.md is not a regular file")
            payload = skill_path.read_bytes()
            text = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            entry["error"] = _error("INSTALLED_SKILL_UNREADABLE", f"cannot read {relative}: {exc}")
            errors.append(entry["error"])
            active_skill_files.append(entry)
            continue
        matches = sorted(term for term in REMOVED_ACTIVE_TERMS if term in text.lower())
        entry.update({"sha256": _sha256(payload), "removedTermsFound": matches})
        if matches and relative != ROUTER_RELATIVE_PATH.as_posix():
            errors.append(
                _error(
                    "REMOVED_INSTALLED_SKILL",
                    f"installed skill {relative} references removed feature terms: {', '.join(matches)}",
                )
            )
        active_skill_files.append(entry)
    return {
        "root": str(installed_skill_root),
        "skills": skills,
        "router": router,
        "activeSkillFiles": active_skill_files,
        "errors": errors,
    }


def _active_repo_contracts(repo_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for relative in ACTIVE_REPO_FILES:
        path = repo_root / relative
        entry: dict[str, Any] = {"path": relative}
        try:
            mode = path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise OSError("active contract is not a regular file")
            payload = path.read_bytes()
            text = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            entry["error"] = _error("ACTIVE_CONTRACT_UNREADABLE", f"cannot read {relative}: {exc}")
            errors.append(entry["error"])
            files.append(entry)
            continue
        allowed_terms = ACTIVE_REPO_TERM_ALLOWLIST.get(relative, frozenset())
        matches = sorted(
            term for term in REMOVED_ACTIVE_TERMS if term not in allowed_terms and term in text.lower()
        )
        entry.update({"sha256": _sha256(payload), "removedTermsFound": matches})
        if matches:
            errors.append(
                _error("ACTIVE_CONTRACT_RESIDUE", f"{relative} references removed active terms: {', '.join(matches)}")
            )
        files.append(entry)
    return {"files": files, "errors": errors}


def _active_config_observation(config_root: Path) -> dict[str, Any]:
    errors = _required_directory(config_root, "active OpenCode configuration root")
    files: list[dict[str, Any]] = []
    if errors:
        return {"root": str(config_root), "files": files, "errors": errors}

    def walk_error(exc: OSError) -> None:
        errors.append(_error("CONFIG_ROOT_UNREADABLE", f"cannot enumerate active config: {exc}"))

    bounded_paths: list[Path] = [config_root / name for name in sorted(ACTIVE_CONFIG_ROOT_FILES)]
    bounded_paths.extend(config_root / name for name in sorted(ACTIVE_CONFIG_DIRECTORIES))
    for bounded in bounded_paths:
        try:
            mode = bounded.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(_error("CONFIG_ENTRY_UNREADABLE", f"cannot inspect {bounded}: {exc}"))
            continue
        if stat.S_ISLNK(mode):
            relative = bounded.relative_to(config_root).as_posix()
            errors.append(_error("CONFIG_ENTRY_UNCLASSIFIED", f"active config path is a symlink: {relative}"))
            files.append({"path": relative, "type": "symlink"})
            continue
        if stat.S_ISREG(mode):
            candidates = [bounded]
        elif stat.S_ISDIR(mode):
            candidates = []
            for directory, subdirectories, filenames in os.walk(
                bounded,
                followlinks=False,
                onerror=walk_error,
            ):
                directory_path = Path(directory)
                for subdirectory in subdirectories[:]:
                    child = directory_path / subdirectory
                    try:
                        child_mode = child.lstat().st_mode
                    except OSError as exc:
                        errors.append(_error("CONFIG_ENTRY_UNREADABLE", f"cannot inspect {child}: {exc}"))
                        subdirectories.remove(subdirectory)
                        continue
                    if stat.S_ISLNK(child_mode):
                        relative = child.relative_to(config_root).as_posix()
                        errors.append(
                            _error("CONFIG_ENTRY_UNCLASSIFIED", f"active config directory is a symlink: {relative}")
                        )
                        files.append({"path": relative, "type": "symlink"})
                        subdirectories.remove(subdirectory)
                candidates.extend(directory_path / name for name in sorted(filenames))
        else:
            relative = bounded.relative_to(config_root).as_posix()
            errors.append(_error("CONFIG_ENTRY_UNCLASSIFIED", f"unsupported active config type: {relative}"))
            files.append({"path": relative, "type": "other"})
            continue

        for path in candidates:
            relative = path.relative_to(config_root).as_posix()
            entry: dict[str, Any] = {"path": relative}
            try:
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode):
                    raise OSError("active config file is a symlink")
                if not stat.S_ISREG(mode):
                    raise OSError("active config entry is not a regular file")
                if path.name.endswith(INERT_CONFIG_SUFFIXES):
                    entry.update({"type": "inert-disabled", "size": path.lstat().st_size})
                    files.append(entry)
                    continue
                if path.suffix.lower() not in CONFIG_SUFFIXES:
                    raise ValueError("unsupported active config extension")
                payload = path.read_bytes()
                text = payload.decode("utf-8")
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                entry["error"] = _error("CONFIG_ENTRY_UNCLASSIFIED", f"cannot classify {relative}: {exc}")
                errors.append(entry["error"])
                files.append(entry)
                continue
            matches = sorted(term for term in REMOVED_ACTIVE_TERMS if term in text.lower())
            entry.update({"type": "active-text", "sha256": _sha256(payload), "removedTermsFound": matches})
            if matches:
                errors.append(
                    _error("ACTIVE_CONFIG_RESIDUE", f"{relative} references removed active terms: {', '.join(matches)}")
                )
            files.append(entry)
    if not files:
        errors.append(_error("ACTIVE_CONFIG_UNOBSERVED", "no bounded active configuration files were observed"))
    return {"root": str(config_root), "files": files, "errors": errors}


def _has_errors(manifest: dict[str, Any]) -> bool:
    if (
        manifest["roots"]["errors"]
        or manifest["inventory"]["errors"]
        or manifest["results"]["errors"]
        or manifest["capsules"]["errors"]
        or manifest["activeContracts"]["errors"]
        or manifest["activeConfig"]["errors"]
    ):
        return True
    installed = manifest["installedCallers"]
    if installed["errors"]:
        return True
    if any("error" in item for item in manifest["results"]["items"]):
        return True
    if any("error" in item for item in manifest["capsules"]["referenced"]):
        return True
    processes = manifest.get("legacyProcesses")
    return (
        not isinstance(processes, dict)
        or processes.get("available") is not True
        or bool(processes.get("matches"))
        or bool(processes.get("observationErrors"))
    )


def build_manifest(
    repo_root: Path,
    state_root: Path,
    installed_skill_root: Path,
    config_root: Path,
) -> dict[str, Any]:
    result_root = state_root / "implementation-results"
    result_items, result_errors = _read_result_items(result_root)
    root_errors: list[dict[str, str]] = []
    for root, label in (
        (repo_root, "repository root"),
        (state_root, "state root"),
        (installed_skill_root, "installed Codex skill root"),
        (config_root, "active OpenCode configuration root"),
    ):
        root_errors.extend(_required_directory(root, label))
    return {
        "schemaVersion": "iis-removal-census-v2",
        "roots": {
            "repoRoot": str(repo_root),
            "stateRoot": str(state_root),
            "installedSkillRoot": str(installed_skill_root),
            "configRoot": str(config_root),
            "errors": root_errors,
        },
        "inventory": _tracked_inventory(repo_root),
        "results": {
            "root": str(result_root),
            "items": result_items,
            "fileDigestListSha256": _file_digest_list(result_items, result_root),
            "errors": result_errors,
        },
        "capsules": _capsule_observation(state_root, result_items),
        "activeContracts": _active_repo_contracts(repo_root),
        "activeConfig": _active_config_observation(config_root),
        "installedCallers": _installed_callers(installed_skill_root, repo_root),
        "legacyProcesses": _process_observation(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--installed-skill-root", required=True)
    parser.add_argument("--config-root", required=True)
    args = parser.parse_args(argv)

    manifest = build_manifest(
        _canonical_path(args.repo_root),
        _canonical_path(args.state_root),
        _canonical_path(args.installed_skill_root),
        _canonical_path(args.config_root),
    )
    print(json.dumps(manifest, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 2 if _has_errors(manifest) else 0


if __name__ == "__main__":
    raise SystemExit(main())
