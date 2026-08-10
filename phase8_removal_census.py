#!/usr/bin/env python3
"""Emit a read-only Phase 8 legacy-removal preparation census as JSON."""

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
COUPLED_TEST_PATHS = (
    "verification-lead/tests",
    "implementation-lead/tests/implementation-result",
    "implementation-lead/tests/implementation-transaction",
    "implementation-lead/tests/pilot",
    "implementation-lead/tests/planning-workspace",
    "implementation-lead/tests/task-ownership",
    "implementation-lead/tests/workflow-store",
    "baseline-capsule/tests",
)
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
INSTALLED_SKILL_NAMES = (
    "implementation-lead",
    "primary-verifier",
    "verification-lead",
)
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
    source_raw, source_error = _git_output(repo_root, ["ls-files", "-z", "--", *LEGACY_SOURCE_PATHS])
    test_raw, test_error = _git_output(repo_root, ["ls-files", "-z", "--", *COUPLED_TEST_PATHS])
    errors = [error for error in (revision_error, source_error, test_error) if error is not None]

    revision = revision_raw.decode("ascii", errors="replace").strip() if revision_raw is not None else None
    source_files = (
        sorted(
            path
            for path in source_raw.decode("utf-8", errors="surrogateescape").split("\0")
            if path
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
    return {
        "repoRoot": str(repo_root),
        "revision": revision,
        "legacySourceFiles": source_files,
        "mechanismCoupledTestFiles": test_files,
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
    bounded_roots = list(dict.fromkeys((*LEGACY_SOURCE_PATHS, *COUPLED_TEST_PATHS)))

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
                legacy_files.add(relative_child)
                try:
                    child_mode = child.lstat().st_mode
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    errors.append(_error("LEGACY_PATH_UNREADABLE", f"cannot inspect legacy path {relative_child}: {exc}"))
                    continue
                if stat.S_ISLNK(child_mode):
                    errors.append(_error("LEGACY_FILESYSTEM_RESIDUE", f"legacy path is a symlink: {relative_child}"))

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
    # The bounded process census supports only an option-free Python script or
    # bytecode invocation. Interpreter options make the script position
    # ambiguous and are deliberately not matched.
    if PYTHON_INTERPRETER_PATTERN.fullmatch(executable) and len(argv) >= 2:
        script = Path(argv[1]).name
        if script in LEGACY_EXECUTABLES or LEGACY_PYC_PATTERN.fullmatch(script):
            return script
    return None


def _process_observation() -> dict[str, Any]:
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return {"available": False, "matches": []}

    excluded_pids = {os.getpid(), os.getppid()}
    matches: list[dict[str, Any]] = []
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return {"available": False, "matches": []}
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) in excluded_pids:
            continue
        try:
            raw_argv = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        argv = [part.decode("utf-8", errors="surrogateescape") for part in raw_argv.split(b"\0") if part]
        executable = _legacy_command(argv)
        if executable is not None:
            matches.append({"pid": int(entry.name), "executable": executable, "argv": argv})
    return {"available": True, "matches": sorted(matches, key=lambda item: item["pid"])}


def _installed_callers(installed_skill_root: Path | None, repo_root: Path) -> dict[str, Any] | None:
    if installed_skill_root is None:
        return None
    skills: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for name in INSTALLED_SKILL_NAMES:
        installed_dir = installed_skill_root / name
        skill_file = installed_dir / "SKILL.md"
        entry: dict[str, Any] = {"name": name}
        try:
            exists = skill_file.is_file()
            entry["exists"] = exists
            entry["isSymlink"] = installed_dir.is_symlink()
            entry["linkTarget"] = str(installed_dir.readlink()) if installed_dir.is_symlink() else None
            entry["canonicalTarget"] = str(installed_dir.resolve())
        except OSError as exc:
            errors.append(_error("INSTALLED_CALLER_MISMATCH", f"cannot resolve installed {name}: {exc}"))
            skills.append(entry)
            continue
        expected_target = str((repo_root / name).resolve(strict=False))
        entry["expectedTarget"] = expected_target
        entry["targetMatchesExpected"] = entry["canonicalTarget"] == expected_target
        try:
            payload = skill_file.read_bytes() if exists else b""
        except OSError as exc:
            errors.append(_error("INSTALLED_CALLER_MISMATCH", f"cannot read installed {name}/SKILL.md: {exc}"))
            payload = b""
        entry["skillMdSha256"] = _sha256(payload) if exists else None
        expected_skill = repo_root / name / "SKILL.md"
        try:
            expected_payload = expected_skill.read_bytes() if expected_skill.is_file() else b""
        except OSError as exc:
            errors.append(_error("INSTALLED_CALLER_MISMATCH", f"cannot read repository {name}/SKILL.md: {exc}"))
            expected_payload = b""
        entry["expectedSkillMdSha256"] = _sha256(expected_payload) if expected_payload else None
        entry["contentMatchesExpected"] = entry["skillMdSha256"] == entry["expectedSkillMdSha256"]
        legacy_terms = sorted(term for term in LEGACY_SKILL_TERMS if term in payload.decode("utf-8", errors="replace"))
        entry["legacyTermsFound"] = legacy_terms
        if not exists:
            errors.append(
                _error("INSTALLED_CALLER_MISMATCH", f"installed {name} SKILL.md is absent; cutover is incomplete")
            )
        elif not entry["targetMatchesExpected"]:
            errors.append(
                _error(
                    "INSTALLED_CALLER_MISMATCH",
                    f"installed {name} resolves to {entry['canonicalTarget']} instead of {expected_target}",
                )
            )
        elif not entry["contentMatchesExpected"]:
            errors.append(
                _error("INSTALLED_CALLER_MISMATCH", f"installed {name} SKILL.md content differs from the repository")
            )
        elif legacy_terms:
            errors.append(
                _error(
                    "INSTALLED_CALLER_MISMATCH",
                    f"installed {name} SKILL.md still references retired mechanism terms: {', '.join(legacy_terms)}",
                )
            )
        skills.append(entry)
    return {
        "root": str(installed_skill_root),
        "skills": skills,
        "errors": errors,
    }


def _has_errors(manifest: dict[str, Any]) -> bool:
    if manifest["inventory"]["errors"] or manifest["results"]["errors"] or manifest["capsules"]["errors"]:
        return True
    installed = manifest["installedCallers"]
    if installed is not None and installed["errors"]:
        return True
    if any("error" in item for item in manifest["results"]["items"]):
        return True
    if any("error" in item for item in manifest["capsules"]["referenced"]):
        return True
    processes = manifest.get("legacyProcesses")
    return not isinstance(processes, dict) or processes.get("available") is not True or bool(processes.get("matches"))


def build_manifest(
    repo_root: Path,
    state_root: Path,
    installed_skill_root: Path | None,
) -> dict[str, Any]:
    result_root = state_root / "implementation-results"
    result_items, result_errors = _read_result_items(result_root)
    return {
        "schemaVersion": "phase8-removal-census-v1",
        "inventory": _tracked_inventory(repo_root),
        "results": {
            "root": str(result_root),
            "items": result_items,
            "fileDigestListSha256": _file_digest_list(result_items, result_root),
            "errors": result_errors,
        },
        "capsules": _capsule_observation(state_root, result_items),
        "installedCallers": _installed_callers(installed_skill_root, repo_root),
        "legacyProcesses": _process_observation(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--installed-skill-root")
    args = parser.parse_args(argv)

    manifest = build_manifest(
        _canonical_path(args.repo_root),
        _canonical_path(args.state_root),
        _canonical_path(args.installed_skill_root) if args.installed_skill_root else None,
    )
    print(json.dumps(manifest, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 2 if _has_errors(manifest) else 0


if __name__ == "__main__":
    raise SystemExit(main())
