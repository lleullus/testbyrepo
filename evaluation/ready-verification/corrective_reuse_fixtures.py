"""Executable defect/control fixtures for IIS corrective reuse evaluation.

These fixtures exercise file durability, subprocess reproduction, scenario-state
reset, command settlement and evidence-applicability boundaries. They do not run
IIS agents or manufacture semantic verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Mapping


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


REPRODUCER_SOURCE = b'''from __future__ import annotations
import json
from pathlib import Path
import sys

target = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if target.get("cursor", 0) < target.get("retained_start", 0):
    print("CURSOR_OVERRUN")
    raise SystemExit(23)
print("STREAM_CONTINUES")
'''


def write_target(path: Path, *, defective: bool) -> None:
    value = {"cursor": 4 if defective else 12, "retained_start": 8}
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def write_ephemeral_reproducer(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "probe_reproducer.py"
    path.write_bytes(REPRODUCER_SOURCE)
    return path


def preserve_reproducer(content: bytes, destination: Path) -> tuple[Path, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination, sha256_file(destination)


def run_reproducer(script: Path, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(script), str(target)],
        text=True,
        capture_output=True,
        check=False,
    )


def promote_regression(reproducer: Path, project_tests: Path) -> tuple[Path, str]:
    promoted = project_tests / "test_cursor_overrun_regression.py"
    promoted.parent.mkdir(parents=True, exist_ok=True)
    promoted.write_bytes(reproducer.read_bytes())
    return promoted, sha256_file(promoted)


@dataclass(frozen=True)
class ExecutionIdentity:
    command_contract: str
    build_id: str
    config_id: str
    runtime_id: str


@dataclass
class ExecutionWorkspace:
    identity: ExecutionIdentity
    scenario_state: Path

    def write_state(self, value: str) -> None:
        self.scenario_state.parent.mkdir(parents=True, exist_ok=True)
        self.scenario_state.write_text(value, encoding="utf-8")

    def read_state(self) -> str:
        return self.scenario_state.read_text(encoding="utf-8")

    def reset_state(self, expected_initial: str) -> None:
        self.write_state(expected_initial)


def reusable_execution_method(previous: ExecutionIdentity, current: ExecutionIdentity) -> bool:
    return (
        previous.command_contract == current.command_contract
        and previous.build_id == current.build_id
        and previous.config_id == current.config_id
        and previous.runtime_id == current.runtime_id
    )


class InvocationCommandHarness:
    """A tiny non-idempotent command surface with attributable settlement."""

    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path
        self.state_path.write_text("0\n", encoding="utf-8")

    def _read(self) -> int:
        return int(self.state_path.read_text(encoding="utf-8").strip())

    def run(self, arguments: Iterable[str], *, lose_response_after_apply: bool = False) -> tuple[str, int | None]:
        args = tuple(arguments)
        if args != ("--apply",):
            return "USAGE_ERROR_NO_EFFECT", self._read()
        applied = self._read() + 1
        self.state_path.write_text(f"{applied}\n", encoding="utf-8")
        if lose_response_after_apply:
            return "RESPONSE_LOST", None
        return "APPLIED", applied

    def authoritative_readback(self) -> int:
        return self._read()


@dataclass(frozen=True)
class MethodPremise:
    owner: str
    interface: str
    persistence_policy: str
    authoritative_readback: str
    effect_strategy: str
    safety_condition: str


def method_change_kind(reviewed: MethodPremise, candidate: MethodPremise) -> str:
    return "SAME_REVIEWED_METHOD" if reviewed == candidate else "MATERIAL_METHOD_CHANGE"


@dataclass(frozen=True)
class EvidenceApplicability:
    obligation: str
    original_target: str
    original_invocation: str
    dependencies: frozenset[str]
    mechanism_id: str
    runtime_config_id: str
    time_sensitive: bool = False


def evidence_action(
    record: EvidenceApplicability,
    *,
    current_target: str,
    changed_dependencies: Iterable[str],
    mechanism_id: str,
    runtime_config_id: str,
    current_state_observed: bool,
    dependency_span_bounded: bool,
) -> str:
    if not dependency_span_bounded:
        return "BROADEN_FRESH_ACQUISITION"
    if record.mechanism_id != mechanism_id or record.runtime_config_id != runtime_config_id:
        return "FRESH_OBSERVATION"
    if record.dependencies.intersection(changed_dependencies):
        return "FRESH_OBSERVATION"
    if record.time_sensitive and not current_state_observed:
        return "FRESH_OBSERVATION"
    if not record.original_target or not record.original_invocation or not current_target:
        return "EVIDENCE_LIMIT"
    return "RETAIN_WITH_ORIGINAL_ATTRIBUTION"


def write_review_artifact(path: Path, payload: Mapping[str, object]) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, sha256_file(path)


def review_handoff_is_readable(path: Path, expected_sha256: str) -> bool:
    return path.is_file() and sha256_file(path) == expected_sha256


def loaded_contract_matches(
    *, repository_identity: str, installed_identity: str, invocation_identity: str
) -> bool:
    return bool(repository_identity) and repository_identity == installed_identity == invocation_identity


@dataclass(frozen=True)
class SiblingPath:
    name: str
    causal_owner: str
    parser: str
    material: bool


def direct_same_assumption_siblings(
    origin: SiblingPath, candidates: Iterable[SiblingPath]
) -> tuple[str, ...]:
    return tuple(
        item.name
        for item in candidates
        if item.name != origin.name
        and item.material
        and item.causal_owner == origin.causal_owner
        and item.parser == origin.parser
    )
