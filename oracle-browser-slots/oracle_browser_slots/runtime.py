"""Resolve and prove the Oracle Node runtime used by the slot wrapper."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Mapping, Sequence


ORACLE_PACKAGE_NAME = "@steipete/oracle"
FILE_SELECTION_PROTOCOL = "oracle-file-selection/v1"
SUPPORTED_ORACLE_VERSIONS = frozenset({"0.16.1"})


class OracleRuntimeError(Exception):
    """The installed Oracle runtime cannot be proven compatible."""


@dataclass(frozen=True)
class ResolvedOracleRuntime:
    node_path: Path
    node_version: str
    package_root: Path
    package_name: str
    package_version: str
    oracle_entry: Path
    oracle_entry_sha256: str
    selector_protocol: str = FILE_SELECTION_PROTOCOL

    @property
    def command_prefix(self) -> tuple[str, str]:
        return (str(self.node_path), str(self.oracle_entry))

    def identity_matches(self, payload: Mapping[str, Any]) -> bool:
        package = payload.get("package")
        entry_sha256 = payload.get("entry_sha256")
        return (
            payload.get("schema") == self.selector_protocol
            and isinstance(package, dict)
            and package.get("name") == self.package_name
            and package.get("version") == self.package_version
            and (entry_sha256 is None or entry_sha256 == self.oracle_entry_sha256)
        )


def resolve_oracle_runtime(
    *,
    product_root: Path | None = None,
    path: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ResolvedOracleRuntime:
    """Resolve product-relative Oracle first, otherwise the exact PATH executable."""

    search_path = path if path is not None else (environ or os.environ).get("PATH")
    node_candidate = shutil.which("node", path=search_path)
    if node_candidate is None:
        raise OracleRuntimeError("Node 실행 파일을 PATH에서 찾을 수 없습니다 (Node >= 24 필요).")
    node_path = _strict_file(node_candidate, "Node 실행 파일")
    node_version = _read_node_version(node_path, search_path)

    root = (product_root or Path(__file__).resolve().parents[2]).resolve()
    product_entry = root / "dist" / "bin" / "oracle-cli.js"
    if product_entry.exists():
        entry = _strict_file(product_entry, "제품 상대 Oracle CLI")
    else:
        path_candidate = shutil.which("oracle", path=search_path)
        if path_candidate is None:
            raise OracleRuntimeError(
                "제품 상대 dist/bin/oracle-cli.js와 PATH의 oracle 실행 파일을 찾을 수 없습니다."
            )
        entry = _strict_file(path_candidate, "PATH Oracle CLI")

    package_root = _owning_package_root(entry)
    package_json_path = package_root / "package.json"
    try:
        package = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleRuntimeError(f"Oracle package.json을 읽을 수 없습니다: {exc}") from exc
    if not isinstance(package, dict):
        raise OracleRuntimeError("Oracle package.json 최상위 값이 객체가 아닙니다.")

    package_name = package.get("name")
    package_version = package.get("version")
    if package_name != ORACLE_PACKAGE_NAME:
        raise OracleRuntimeError(
            f"Oracle CLI 소유 package 이름이 올바르지 않습니다: {package_name!r}"
        )
    if not isinstance(package_version, str) or package_version not in SUPPORTED_ORACLE_VERSIONS:
        raise OracleRuntimeError(
            f"지원하지 않는 Oracle release입니다: {package_version!r}; "
            f"지원 버전: {', '.join(sorted(SUPPORTED_ORACLE_VERSIONS))}"
        )
    declared_entry = _declared_oracle_entry(package_root, package)
    if declared_entry != entry:
        raise OracleRuntimeError(
            f"package.json bin.oracle과 선택된 CLI가 일치하지 않습니다: {declared_entry} != {entry}"
        )

    command_env = dict(environ or os.environ)
    if search_path is not None:
        command_env["PATH"] = search_path
    cli_version = _run_text(
        [str(node_path), str(entry), "--version"],
        env=command_env,
        description="Oracle CLI --version",
    ).strip()
    if cli_version != package_version:
        raise OracleRuntimeError(
            f"Oracle CLI 버전과 package.json 버전이 일치하지 않습니다: "
            f"{cli_version!r} != {package_version!r}"
        )

    capability_text = _run_text(
        [
            str(node_path),
            str(entry),
            "runtime",
            "file-selection",
            "--capability",
            "--json",
        ],
        env=command_env,
        description="Oracle file-selection capability",
    )
    try:
        capability = json.loads(capability_text)
    except json.JSONDecodeError as exc:
        raise OracleRuntimeError(
            f"Oracle file-selection capability 응답이 JSON이 아닙니다: {capability_text.strip()!r}"
        ) from exc

    resolved = ResolvedOracleRuntime(
        node_path=node_path,
        node_version=node_version,
        package_root=package_root,
        package_name=package_name,
        package_version=package_version,
        oracle_entry=entry,
        oracle_entry_sha256=_sha256(entry),
    )
    if not isinstance(capability, dict) or capability.get("ok") is not True:
        raise OracleRuntimeError("Oracle file-selection capability가 성공 응답을 반환하지 않았습니다.")
    if capability.get("capability") != "file-selection" or not resolved.identity_matches(capability):
        raise OracleRuntimeError(
            "Oracle file-selection capability의 protocol 또는 package identity가 일치하지 않습니다."
        )
    return resolved


def _strict_file(value: str | Path, description: str) -> Path:
    try:
        path = Path(value).resolve(strict=True)
    except OSError as exc:
        raise OracleRuntimeError(f"{description}을 해석할 수 없습니다: {exc}") from exc
    if not path.is_file():
        raise OracleRuntimeError(f"{description}이 일반 파일이 아닙니다: {path}")
    return path


def _read_node_version(node_path: Path, search_path: str | None) -> str:
    env = dict(os.environ)
    if search_path is not None:
        env["PATH"] = search_path
    value = _run_text([str(node_path), "--version"], env=env, description="Node --version").strip()
    match = re.fullmatch(r"v?(\d+)(?:\.\d+){1,2}(?:[-+].*)?", value)
    if match is None:
        raise OracleRuntimeError(f"Node 버전을 해석할 수 없습니다: {value!r}")
    if int(match.group(1)) < 24:
        raise OracleRuntimeError(f"지원되지 않는 Node 버전입니다: {value}; Node >= 24가 필요합니다.")
    return value


def _owning_package_root(entry: Path) -> Path:
    current = entry.parent
    filesystem_root = Path(current.anchor)
    while True:
        package_json = current / "package.json"
        if package_json.is_file():
            return current.resolve()
        if current == filesystem_root:
            break
        current = current.parent
    raise OracleRuntimeError(f"선택된 Oracle CLI의 owning package.json을 찾을 수 없습니다: {entry}")


def _declared_oracle_entry(package_root: Path, package: Mapping[str, Any]) -> Path:
    bin_value = package.get("bin")
    declared: object
    if isinstance(bin_value, dict):
        declared = bin_value.get("oracle")
    elif isinstance(bin_value, str):
        declared = bin_value
    else:
        declared = None
    if not isinstance(declared, str) or not declared:
        raise OracleRuntimeError("package.json에 bin.oracle 선언이 없습니다.")
    try:
        return (package_root / declared).resolve(strict=True)
    except OSError as exc:
        raise OracleRuntimeError(f"package.json bin.oracle을 해석할 수 없습니다: {exc}") from exc


def _run_text(command: Sequence[str], *, env: Mapping[str, str], description: str) -> str:
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
            env=dict(env),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise OracleRuntimeError(f"{description} 실행에 실패했습니다: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "응답 없음"
        raise OracleRuntimeError(
            f"{description}가 종료 코드 {completed.returncode}로 실패했습니다: {detail}"
        )
    return completed.stdout


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
