#!/usr/bin/env python3
"""Run the fixed local evidence for Phase 8's accepted supported range."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _error(check: str, code: str, message: str) -> dict[str, str]:
    return {"check": check, "code": code, "message": message}


def _git(repo_root: Path, arguments: list[str]) -> tuple[bytes | None, str | None]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return None, f"cannot execute git: {exc}"
    if completed.returncode:
        return None, completed.stderr.decode("utf-8", errors="replace").strip()
    return completed.stdout, None


def _worktree_identity(repo_root: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    head, head_error = _git(repo_root, ["rev-parse", "HEAD"])
    diff, diff_error = _git(repo_root, ["diff", "--binary", "--no-ext-diff", "HEAD"])
    untracked, untracked_error = _git(repo_root, ["ls-files", "--others", "--exclude-standard", "-z"])
    for code, message in (
        ("GIT_HEAD_UNAVAILABLE", head_error),
        ("GIT_DIFF_UNAVAILABLE", diff_error),
        ("GIT_UNTRACKED_UNAVAILABLE", untracked_error),
    ):
        if message is not None:
            errors.append(_error("worktreeIdentity", code, message))
    if errors:
        return None, errors

    files: list[dict[str, str]] = []
    for relative in sorted(value for value in untracked.decode("utf-8", errors="surrogateescape").split("\0") if value):
        path = repo_root / relative
        try:
            payload = path.read_bytes()
        except OSError as exc:
            errors.append(_error("worktreeIdentity", "UNTRACKED_FILE_UNREADABLE", f"cannot read {relative}: {exc}"))
            continue
        files.append({"path": relative, "sha256": _sha256(payload)})
    if errors:
        return None, errors
    canonical = json.dumps(files, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    identity_input = {
        "head": head.decode("ascii", errors="replace").strip(),
        "trackedDiffSha256": _sha256(diff),
        "untrackedFiles": files,
    }
    return {
        **identity_input,
        "untrackedFilesSha256": _sha256(canonical),
        "identitySha256": _sha256(
            json.dumps(identity_input, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ),
    }, []


def _run(name: str, command: list[str], cwd: Path) -> tuple[dict[str, Any], bytes]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return {
            "name": name,
            "command": command,
            "returncode": None,
            "stdoutSha256": None,
            "stderrSha256": None,
            "error": f"cannot execute command: {exc}",
        }, b""
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdoutSha256": _sha256(completed.stdout),
        "stderrSha256": _sha256(completed.stderr),
    }, completed.stdout


def _json_output(name: str, report: dict[str, Any], stdout: bytes) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    if report["returncode"] != 0:
        return None, _error(name, "COMMAND_FAILED", "fixed local command did not exit successfully")
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _error(name, "JSON_OUTPUT_INVALID", f"fixed local command did not emit one JSON value: {exc}")
    if not isinstance(value, dict):
        return None, _error(name, "JSON_OUTPUT_NOT_OBJECT", "fixed local command JSON output is not an object")
    return value, None


def _expect_exact(name: str, value: dict[str, Any], expected: dict[str, Any]) -> dict[str, str] | None:
    if value != expected:
        return _error(name, "JSON_OUTPUT_SEMANTICS_INVALID", "fixed local command JSON does not match accepted range")
    return None


def _empty_effect_set_and_unsupported_read(repo_root: Path) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    entrypoint_path = repo_root / "implementation-verification" / "production_entrypoint.py"
    adapters_path = repo_root / "implementation-verification" / "production_adapters.py"
    try:
        entrypoint = ast.parse(entrypoint_path.read_text(encoding="utf-8"), filename=str(entrypoint_path))
        adapters = ast.parse(adapters_path.read_text(encoding="utf-8"), filename=str(adapters_path))
    except (OSError, SyntaxError) as exc:
        return None, _error("productionScope", "SOURCE_UNREADABLE", f"cannot parse production scope source: {exc}")

    effect_empty = any(
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "ENABLED_PRODUCTION_EFFECT_ADAPTERS"
        and isinstance(node.value, ast.Tuple)
        and not node.value.elts
        for node in entrypoint.body
    )
    read_unsupported = False
    for node in adapters.body:
        if not isinstance(node, ast.ClassDef) or node.name != "LinuxEvidenceRunnerAdapter":
            continue
        for member in node.body:
            if not isinstance(member, ast.FunctionDef) or member.name != "__init__":
                continue
            for statement in ast.walk(member):
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Attribute)
                    and isinstance(statement.targets[0].value, ast.Name)
                    and statement.targets[0].value.id == "self"
                    and statement.targets[0].attr == "authenticated_read_enforced"
                    and isinstance(statement.value, ast.Constant)
                    and statement.value.value is False
                ):
                    read_unsupported = True
    if not effect_empty or not read_unsupported:
        return None, _error(
            "productionScope",
            "PRODUCTION_SCOPE_MISMATCH",
            "enabled Effect Adapter set or authenticated READ scope differs from the accepted range",
        )
    return {"enabledEffectAdapters": [], "authenticatedRead": "UNSUPPORTED"}, None


def _valid_census(value: dict[str, Any], head: str) -> dict[str, str] | None:
    try:
        installed = value["installedCallers"]
        inventory = value["inventory"]
        results = value["results"]
        capsules = value["capsules"]
        processes = value["legacyProcesses"]
        inventory_lists = (
            inventory["legacySourceFiles"],
            inventory["mechanismCoupledTestFiles"],
            inventory["filesystemLegacyFiles"],
            inventory["residueFiles"],
            inventory["emptyLegacyDirectories"],
        )
        inventory_valid = (
            isinstance(inventory, dict)
            and isinstance(inventory["errors"], list)
            and all(isinstance(item, list) for item in inventory_lists)
        )
        results_valid = (
            isinstance(results, dict)
            and isinstance(results["errors"], list)
            and isinstance(results["items"], list)
            and all(isinstance(item, dict) for item in results["items"])
        )
        capsules_valid = (
            isinstance(capsules, dict)
            and isinstance(capsules["errors"], list)
            and isinstance(capsules["referenced"], list)
            and all(isinstance(item, dict) for item in capsules["referenced"])
        )
        installed_valid = isinstance(installed, dict) and isinstance(installed["errors"], list)
        processes_valid = (
            isinstance(processes, dict)
            and isinstance(processes["available"], bool)
            and isinstance(processes["matches"], list)
            and all(isinstance(item, dict) for item in processes["matches"])
        )
        zero_inventory = (
            inventory["legacySourceFiles"] == []
            and inventory["mechanismCoupledTestFiles"] == []
            and inventory["filesystemLegacyFiles"] == []
            and inventory["residueFiles"] == []
            and inventory["emptyLegacyDirectories"] == []
        )
        valid = (
            value["schemaVersion"] == "phase8-removal-census-v1"
            and inventory["revision"] == head
            and inventory_valid
            and not inventory["errors"]
            and zero_inventory
            and results_valid
            and not results["errors"]
            and capsules_valid
            and not capsules["errors"]
            and installed_valid
            and not installed["errors"]
            and processes_valid
            and processes["available"] is True
            and processes["matches"] == []
            and all("error" not in item for item in results["items"])
            and all("error" not in item for item in capsules["referenced"])
        )
    except (KeyError, TypeError):
        valid = False
    if not valid:
        return _error("census", "CENSUS_SEMANTICS_INVALID", "read-only census is not healthy for this worktree")
    return None


def run_gate(repo_root: Path, state_root: Path, installed_skill_root: Path | None) -> tuple[dict[str, Any], int]:
    repo_root = repo_root.expanduser().resolve(strict=False)
    state_root = state_root.expanduser().resolve(strict=False)
    installed_skill_root = (
        installed_skill_root.expanduser().resolve(strict=False) if installed_skill_root is not None else None
    )
    errors: list[dict[str, str]] = []
    if installed_skill_root is None:
        errors.append(
            _error(
                "census",
                "INSTALLED_SKILL_ROOT_REQUIRED",
                "Phase 8 gate requires --installed-skill-root for installed caller proof",
            )
        )
    worktree, identity_errors = _worktree_identity(repo_root)
    errors.extend(identity_errors)
    commands: list[dict[str, Any]] = []
    production_root = repo_root / "implementation-verification"

    fixed_commands = (
        ("supportedRangeSmoke", [sys.executable, "production_supported_range_smoke.py"], production_root),
        ("mutationStopSmoke", [sys.executable, "production_smoke.py"], production_root),
        ("productionConformance", [sys.executable, "-m", "unittest", "-v", "tests.test_production_conformance"], production_root),
        (
            "legacyNegative",
            [
                sys.executable,
                "-m",
                "unittest",
                "-v",
                "tests.test_phase7_legacy_negative.Phase7LegacyNegativeTests.test_legacy_unavailable_production_fail_closed_flow",
            ],
            production_root,
        ),
    )
    outputs: dict[str, bytes] = {}
    for name, command, cwd in fixed_commands:
        report, stdout = _run(name, command, cwd)
        commands.append(report)
        outputs[name] = stdout
        if report["returncode"] != 0:
            errors.append(_error(name, "COMMAND_FAILED", "fixed local command did not exit successfully"))

    supported_range, error = _json_output("supportedRangeSmoke", commands[0], outputs["supportedRangeSmoke"])
    if error is not None:
        errors.append(error)
    elif (semantic_error := _expect_exact(
        "supportedRangeSmoke",
        supported_range,
        {
            "candidateImplementationChanges": 0,
            "canonicalSource": "implemented",
            "inspectionCurrentness": "CURRENT",
            "inspectionResult": "VerificationResult",
            "verificationStatus": "VERIFIED",
        },
    )) is not None:
        errors.append(semantic_error)

    mutation_stop, error = _json_output("mutationStopSmoke", commands[1], outputs["mutationStopSmoke"])
    if error is not None:
        errors.append(error)
    elif (semantic_error := _expect_exact(
        "mutationStopSmoke",
        mutation_stop,
        {
            "canonicalSource": "baseline",
            "reason": "conditional source adoption is unavailable",
            "status": "IMPLEMENTATION_STOPPED",
        },
    )) is not None:
        errors.append(semantic_error)

    scope, error = _empty_effect_set_and_unsupported_read(repo_root)
    if error is not None:
        errors.append(error)

    census_command = [
        sys.executable,
        "phase8_removal_census.py",
        "--repo-root",
        str(repo_root),
        "--state-root",
        str(state_root),
    ]
    census_command.extend(("--installed-skill-root", str(installed_skill_root)) if installed_skill_root is not None else ())
    census_report, census_stdout = _run("census", census_command, repo_root)
    commands.append(census_report)
    census, error = _json_output("census", census_report, census_stdout)
    if error is not None:
        errors.append(error)
    elif worktree is not None and (semantic_error := _valid_census(census, worktree["head"])) is not None:
        errors.append(semantic_error)

    accepted = not errors
    result = {
        "schemaVersion": "phase8-accepted-supported-range-gate-v1",
        "acceptedSupportedRangeStatus": "ACCEPTED_SUPPORTED_RANGE_VERIFIED" if accepted else "NOT_VERIFIED",
        "mutationCapableRuntimeStatus": "UNSUPPORTED_PRE_MUTATION_FAIL_CLOSED",
        "destructiveAuthorization": False,
        "pendingDestructivePrerequisites": [
            "DURABLE_DATA_DISPOSITION",
            "ACTIVE_CALLER_CUTOVER",
            "CONTINUOUS_LEGACY_WRITE_QUIESCENCE",
        ],
        "worktree": worktree,
        "productionScope": scope,
        "commands": commands,
        "census": (
            {
                "revision": census["inventory"]["revision"],
                "legacySourceFileCount": len(census["inventory"]["legacySourceFiles"]),
                "mechanismCoupledTestFileCount": len(census["inventory"]["mechanismCoupledTestFiles"]),
                "filesystemResidueFileCount": len(census["inventory"]["residueFiles"]),
                "emptyLegacyDirectoryCount": len(census["inventory"]["emptyLegacyDirectories"]),
                "historicalResultCount": len(census["results"]["items"]),
                "referencedCapsuleCount": len(census["capsules"]["referenced"]),
                "legacyProcessMatchCount": len(census["legacyProcesses"]["matches"]),
                "installedCallerErrorCount": len((census.get("installedCallers") or {}).get("errors") or []),
            }
            if census is not None and not error
            else None
        ),
        "errors": errors,
    }
    return result, 0 if accepted else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--installed-skill-root", required=True)
    args = parser.parse_args(argv)
    result, code = run_gate(
        Path(args.repo_root),
        Path(args.state_root),
        Path(args.installed_skill_root) if args.installed_skill_root else None,
    )
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
