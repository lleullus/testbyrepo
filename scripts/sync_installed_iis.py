#!/usr/bin/env python3
"""Prepare immutable IIS payloads and explicitly switch quiescent host installs."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "iis-bundle/v2"
NEW_FAMILY = "ready-boundary-tools"
OLD_FAMILY = "ready-runtime-v2"
SUPPORTED_FAMILIES = {NEW_FAMILY, OLD_FAMILY}
PAYLOAD_ROOTS = (
    "iis-workflow", "iis-adaptive-planning", "matt/skills", "scope-shaper",
    "behavior-design-lead", "scope-investigation-runner", "repo-snapshot",
    "companion-skills", "planning-workspace", "iis_path_contract.py",
    "delivery-tools/ready-ticket",
)
REQUIRED = (
    "iis-workflow/SKILL.md", "matt/skills/to-tickets/validate_ticket.py",
    "companion-skills/ready-ticket-plan/SKILL.md",
    "companion-skills/ready-ticket-implement/SKILL.md",
    "companion-skills/ready-ticket-verify/SKILL.md",
    "delivery-tools/ready-ticket/index.js",
    "delivery-tools/ready-ticket/omp.js",
    "delivery-tools/ready-ticket/cli.js",
    "delivery-tools/ready-ticket/src/core.js",
    "delivery-tools/ready-ticket/src/verification-binding.js",
    "delivery-tools/ready-ticket/src/finalization.js",
)
CANDIDATE_RETIRED = (
    "companion-skills/ready-ticket-heuristic-probe",
    "delivery-runtime/ready-ticket-implement",
)
OLD_SIGNATURE = {
    "delivery-runtime/ready-ticket-implement/index.js",
    "delivery-runtime/ready-ticket-implement/src/core.js",
}
NEW_SIGNATURE = {
    "delivery-tools/ready-ticket/index.js",
    "delivery-tools/ready-ticket/omp.js",
    "delivery-tools/ready-ticket/src/core.js",
}
OLD_EXTENSION_NAME = "ready-ticket-implement-runtime"
NEW_EXTENSION_NAME = "ready-ticket-boundary-tools"
RETIREMENT_EVIDENCE_SCHEMA = "iis-ready-runtime-retirement-evidence/v1"
TEXT_SUFFIXES = {".md", ".py", ".js", ".json", ".yaml", ".yml", ".sh", ".toml"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


@contextmanager
def install_lock(store: Path):
    store.mkdir(parents=True, exist_ok=True)
    with (store / ".install.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def payload_files(source: Path) -> list[Path]:
    for relative in REQUIRED:
        path = source / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"incomplete candidate payload: {relative}")
    for relative in CANDIDATE_RETIRED:
        if (source / relative).exists() or (source / relative).is_symlink():
            raise ValueError(f"retired payload is still present: {relative}")
    files = []
    for root in PAYLOAD_ROOTS:
        target = source / root
        if not target.exists():
            raise ValueError(f"missing payload root: {root}")
        for path in ([target] if target.is_file() else target.rglob("*")):
            relative = path.relative_to(source)
            if any(part in {"__pycache__", ".pytest_cache", "tests", ".git", "node_modules"} for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError(f"symlink in source payload: {relative}")
            if path.is_file() and path.suffix != ".pyc":
                files.append(path)
    return sorted(files)


def source_origins(source: Path, explicit: list[Path] | None = None) -> list[Path]:
    origins = {source, *(path.resolve() for path in (explicit or []))}
    result = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            cwd=source, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        common = Path(result.stdout.strip())
        if common.name == ".git":
            origins.add(common.parent)
    return sorted(origins, key=lambda path: len(str(path)), reverse=True)


def rebase(content: bytes, origins: list[Path], destination: Path) -> bytes:
    # The replaceable model guide is deliberately external to every release.
    guides = {}
    for index, origin in enumerate(origins):
        guide = str(origin / "model-selection-guide.md").encode()
        token = f"__IIS_EXTERNAL_MODEL_GUIDE_{index}__".encode()
        if token in content:
            raise ValueError("reserved model-guide token in source")
        if guide in content:
            content = content.replace(guide, token)
            guides[token] = guide
    for origin in origins:
        content = content.replace(str(origin).encode() + b"/", str(destination).encode() + b"/")
    for token, guide in guides.items():
        content = content.replace(token, guide)
    return content


def release_path(store: Path, bundle_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", bundle_id):
        raise ValueError("bundle id must be an exact SHA-256")
    destination = store / "releases" / bundle_id
    if destination.is_symlink():
        raise ValueError("release directory must not be a symlink")
    return destination


def release_family(manifest: dict) -> str:
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("incomplete bundle manifest")
    files = set(entries)
    declared = manifest.get("family")
    if declared is not None and declared not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported bundle family: {declared}")
    has_old = OLD_SIGNATURE.issubset(files)
    has_new = NEW_SIGNATURE.issubset(files)
    if declared == OLD_FAMILY or declared is None and has_old and not has_new:
        if not has_old or has_new:
            raise ValueError("old runtime bundle family/signature mismatch")
        return OLD_FAMILY
    if declared == NEW_FAMILY or declared is None and has_new and not has_old:
        if not has_new or has_old:
            raise ValueError("boundary-tools bundle family/signature mismatch")
        return NEW_FAMILY
    raise ValueError("unsupported or ambiguous protocol-2 bundle family")


def check_release(store: Path, bundle_id: str) -> dict:
    """Validate one immutable release against its own manifest, including supported family identity."""
    release = release_path(store, bundle_id)
    manifest = read_json(release / "bundle.json")
    if manifest.get("schema") != SCHEMA or manifest.get("protocol") != 2 or manifest.get("bundle_id") != bundle_id:
        raise ValueError("bundle identity or protocol mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("incomplete bundle manifest")
    actual = set()
    for path in release.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink in immutable release: {path}")
        if path.is_file() and path.relative_to(release).as_posix() != "bundle.json":
            actual.add(path.relative_to(release).as_posix())
    if actual != set(entries):
        raise ValueError("bundle file set drift")
    for relative, expected in entries.items():
        path = release / relative
        if not path.resolve().is_relative_to(release.resolve()):
            raise ValueError("bundle path escapes release")
        if not isinstance(expected, dict) or "sha256" not in expected or "mode" not in expected:
            raise ValueError(f"invalid bundle manifest entry: {relative}")
        if sha(path.read_bytes()) != expected["sha256"] or stat.S_IMODE(path.stat().st_mode) != expected["mode"]:
            raise ValueError(f"bundle file drift: {relative}")
    family = release_family(manifest)
    return {**manifest, "family": family}


def check_candidate_release(store: Path, bundle_id: str) -> dict:
    manifest = check_release(store, bundle_id)
    entries = set(manifest["files"])
    if manifest["family"] != NEW_FAMILY:
        raise ValueError("candidate release must use ready-boundary-tools family")
    if not all(relative in entries for relative in REQUIRED):
        raise ValueError("incomplete boundary-tools candidate manifest")
    if any(relative == retired or relative.startswith(retired + "/") for relative in entries for retired in CANDIDATE_RETIRED):
        raise ValueError("candidate release contains retired payload")
    return manifest


def check_install(store: Path) -> dict:
    if (store / "pending.json").exists():
        raise ValueError("unfinished install transaction requires recovery")
    state = read_json(store / "installed.json")
    if state.get("schema") != "iis-install/v2":
        raise ValueError("unsupported installed-state schema")
    manifest = check_release(store, state["bundle_id"])
    expected_pointer = {"kind": "symlink", "target": str(release_path(store, state["bundle_id"]))}
    if entry_identity(store / "current") != expected_pointer:
        raise ValueError("installed current pointer drift")
    for name, target in state["links"].items():
        expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        if entry_identity(Path(name)) != expected:
            raise ValueError(f"managed install entry drift: {name}")
    return {**state, "family": manifest["family"]}


def prepare(source: Path, store: Path, origins: list[Path] | None = None) -> dict:
    source, store = source.resolve(strict=True), store.resolve()
    if store.is_relative_to(source):
        raise ValueError("bundle store must be outside source")
    files = payload_files(source)
    inputs = {path.relative_to(source).as_posix(): {"sha256": sha(path.read_bytes()),
              "mode": stat.S_IMODE(path.stat().st_mode)} for path in files}
    bundle_id = sha(json.dumps({"protocol": 2, "files": inputs}, sort_keys=True).encode())
    with install_lock(store):
        destination = release_path(store, bundle_id)
        if destination.exists():
            return check_candidate_release(store, bundle_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=destination.parent))
        try:
            entries = {}
            original_roots = source_origins(source, origins)
            for path in files:
                relative = path.relative_to(source).as_posix()
                content = path.read_bytes()
                if sha(content) != inputs[relative]["sha256"]:
                    raise ValueError(f"source changed during snapshot: {relative}")
                if path.suffix in TEXT_SUFFIXES:
                    content = rebase(content, original_roots, destination)
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                mode = inputs[relative]["mode"] & 0o555
                target.chmod(mode)
                entries[relative] = {"sha256": sha(content), "mode": mode}
            if payload_files(source) != files or any(sha(path.read_bytes()) != inputs[path.relative_to(source).as_posix()]["sha256"] for path in files):
                raise ValueError("source changed during snapshot")
            manifest = {"schema": SCHEMA, "protocol": 2, "family": NEW_FAMILY, "bundle_id": bundle_id,
                        "source": str(source), "source_origins": [str(path) for path in original_roots],
                        "files": entries, "input_files": inputs}
            atomic_json(staging / "bundle.json", manifest)
            (staging / "bundle.json").chmod(0o444)
            os.replace(staging, destination)
            return check_candidate_release(store, bundle_id)
        finally:
            if staging.exists():
                shutil.rmtree(staging)


def entry_identity(path: Path) -> dict:
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "absent"}
    if path.is_file():
        return {"kind": "file", "sha256": sha(path.read_bytes())}
    if path.is_dir():
        contents = {}
        for child in sorted(path.rglob("*")):
            relative = child.relative_to(path).as_posix()
            if child.is_symlink():
                contents[relative] = {"link": os.readlink(child)}
            elif child.is_file():
                contents[relative] = {"sha256": sha(child.read_bytes())}
            elif child.is_dir():
                contents[relative] = {"directory": True}
        return {"kind": "directory", "sha256": sha(json.dumps(contents, sort_keys=True).encode())}
    raise ValueError(f"unsupported install entry: {path}")


def canonical_directory(path: Path | None, label: str) -> Path:
    if path is None:
        raise ValueError(f"{label} is required")
    raw = Path(path)
    if not raw.is_absolute() or raw.is_symlink():
        raise ValueError(f"{label} must be an exact absolute directory")
    resolved = raw.resolve(strict=True)
    if resolved != raw or not resolved.is_dir():
        raise ValueError(f"{label} must be a canonical directory")
    return resolved


def canonical_evidence_file(path: Path | None, runtime_root: Path) -> tuple[Path | None, dict]:
    if path is None:
        return None, {"schema": RETIREMENT_EVIDENCE_SCHEMA, "runtime_root": str(runtime_root), "records": {}}
    raw = Path(path)
    if not raw.is_absolute() or raw.is_symlink():
        raise ValueError("retired Ready runtime evidence must be an exact absolute file")
    resolved = raw.resolve(strict=True)
    if resolved != raw or not resolved.is_file() or resolved.is_relative_to(runtime_root):
        raise ValueError("retired Ready runtime evidence must be a canonical file outside the retired runtime root")
    evidence = read_json(resolved)
    if (evidence.get("schema") != RETIREMENT_EVIDENCE_SCHEMA
            or evidence.get("runtime_root") != str(runtime_root)
            or not isinstance(evidence.get("records"), dict)):
        raise ValueError("invalid retired Ready runtime evidence")
    return resolved, evidence


def _runtime_record_owner(value: dict) -> str | None:
    return value.get("session_id") or value.get("parent_session_id") or value.get("owner")


def _terminal_runtime_record(value: dict, executions: dict[str, dict]) -> bool:
    kind = value.get("kind")
    if kind == "execution":
        return (value.get("phase") in {"COMPLETE", "BLOCKED"}
                and not value.get("active_operation") and not value.get("owned_service") and not value.get("uncertainty"))
    if kind == "assignment":
        return value.get("status") in {"terminal", "superseded"}
    if kind == "session":
        execution = executions.get(value.get("execution_id"))
        return bool(execution and _terminal_runtime_record(execution, executions))
    return False


def _retirement_evidence_disposition(relative: str, identity: dict, value: dict,
                                     evidence: dict) -> tuple[str, dict]:
    item = evidence.get("records", {}).get(relative)
    if not isinstance(item, dict):
        return "blocker", {"reason": "nonterminal runtime record has no independent settlement evidence"}
    owner = _runtime_record_owner(value)
    exact = (item.get("record_sha256") == identity["sha256"]
             and item.get("record_kind") == identity["kind"]
             and item.get("owner_session") == owner)
    if not exact:
        return "blocker", {"reason": "retirement evidence does not match exact record identity/owner"}
    live_work = item.get("live_work")
    live_service = item.get("live_service")
    effect = item.get("effect_disposition")
    if live_work != "absent" or live_service != "absent":
        return "blocker", {"reason": "retirement evidence reports live worker/process/service"}
    if effect not in {"none", "not_applied", "applied_settled"}:
        return "blocker", {"reason": "external effect settlement is unresolved"}
    if item.get("ownership_disposition") != "terminated_or_withdrawn":
        return "blocker", {"reason": "runtime ownership/assignment/reservation is not retired"}
    if not item.get("live_work_absence_evidence") or not item.get("readback_reference"):
        return "blocker", {"reason": "retirement evidence references are incomplete"}
    return "retired_stale_record", {
        "owner_session": owner,
        "live_work_absence_evidence": item["live_work_absence_evidence"],
        "effect_disposition": effect,
        "readback_reference": item["readback_reference"],
        "ownership_disposition": item["ownership_disposition"],
    }


def scan_retired_runtime(runtime_root: Path, evidence_path: Path | None = None) -> dict:
    """Read-only cutover scan. Explicit evidence is operator/host evidence, not installer inference."""
    root = canonical_directory(runtime_root, "retired Ready runtime root")
    evidence_file, evidence = canonical_evidence_file(evidence_path, root)
    identities: list[dict] = []
    values: dict[str, dict] = {}
    executions: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink in retired Ready runtime root: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        try:
            value = json.loads(data)
        except json.JSONDecodeError:
            value = {}
        kind = value.get("kind") if isinstance(value, dict) else None
        identity = {"path": relative, "sha256": sha(data), "kind": kind or "unknown"}
        identities.append(identity)
        values[relative] = value if isinstance(value, dict) else {}
        if kind == "execution" and value.get("execution_id"):
            executions[value["execution_id"]] = value
    records = []
    state_kinds = {"execution", "assignment", "session", "active_ticket"}
    for identity in identities:
        relative = identity["path"]
        value = values[relative]
        if value.get("kind") not in state_kinds:
            disposition, detail = "history_file", {}
        elif value.get("schema_version") == 2 and _terminal_runtime_record(value, executions):
            disposition, detail = "terminal_history", {}
        else:
            disposition, detail = _retirement_evidence_disposition(relative, identity, value, evidence)
        records.append({**identity, "disposition": disposition, **detail})
    blockers = [item for item in records if item["disposition"] == "blocker"]
    stale = [item for item in records if item["disposition"] == "retired_stale_record"]
    tree_digest = sha(json.dumps([{"path": item["path"], "sha256": item["sha256"]} for item in identities], sort_keys=True).encode())
    return {
        "schema": "iis-ready-runtime-retirement-scan/v1",
        "retired_runtime_root": str(root),
        "retired_runtime_tree_sha256": tree_digest,
        "evidence_path": str(evidence_file) if evidence_file else None,
        "evidence_sha256": sha(evidence_file.read_bytes()) if evidence_file else None,
        "records": records,
        "summary": {"records": len(records),
                    "history_files": sum(item["disposition"] == "history_file" for item in records),
                    "terminal_history": sum(item["disposition"] == "terminal_history" for item in records),
                    "retired_stale_record": len(stale), "blockers": len(blockers), "activation_allowed": not blockers},
    }


def archive_retired_runtime(runtime_root: Path, scan: dict, destination: Path) -> dict:
    root = canonical_directory(runtime_root, "retired Ready runtime root")
    fresh = scan_retired_runtime(root, Path(scan["evidence_path"]) if scan.get("evidence_path") else None)
    if (fresh["retired_runtime_tree_sha256"] != scan["retired_runtime_tree_sha256"]
            or fresh["records"] != scan["records"]):
        raise ValueError("retired Ready runtime changed after retirement preflight")
    if destination.exists():
        raise ValueError("retired Ready runtime archive destination already exists")
    shutil.copytree(root, destination)
    archived_files = []
    for path in sorted(destination.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink appeared in retired Ready runtime archive")
        if path.is_file():
            archived_files.append({"path": path.relative_to(destination).as_posix(), "sha256": sha(path.read_bytes())})
    archive_digest = sha(json.dumps(archived_files, sort_keys=True).encode())
    if archive_digest != scan["retired_runtime_tree_sha256"]:
        raise ValueError("retired Ready runtime archive does not match preflight bytes")
    return {"path": str(destination), "sha256": archive_digest, "records": len(archived_files)}


def set_pointer(store: Path, target: str | None) -> None:
    current = store / "current"
    if current.exists() and not current.is_symlink():
        raise ValueError("current must be an installer-owned symlink")
    if target is None:
        current.unlink(missing_ok=True)
        return
    temporary = store / (".current-" + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target)
        os.replace(temporary, current)
    finally:
        temporary.unlink(missing_ok=True)


def host_links(store: Path, manifest: dict, hosts: dict[str, Path]) -> dict[str, str | None]:
    skills = sorted(Path(name).parent for name in manifest["files"]
                    if name.endswith("/SKILL.md") and (
                        len(Path(name).parts) == 2
                        or Path(name).parts[0] == "companion-skills" and len(Path(name).parts) == 3
                        or Path(name).parts[:2] == ("matt", "skills") and len(Path(name).parts) == 4))
    links = {}
    for host, root in hosts.items():
        names = set()
        for skill in skills:
            if skill.name in names:
                raise ValueError(f"duplicate installed skill name: {skill.name}")
            names.add(skill.name)
            links[str(root / "skills" / skill.name)] = str(store / "current" / skill)
        links[str(root / "skills/ready-ticket-heuristic-probe")] = None
        if host == "omp":
            links[str(root / "extensions" / NEW_EXTENSION_NAME)] = str(store / "current/delivery-tools/ready-ticket")
            links[str(root / "extensions" / OLD_EXTENSION_NAME)] = None
        elif host != "codex":
            raise ValueError(f"unsupported install host: {host}")
    return links


def restore_snapshot(store: Path, snapshot: dict) -> None:
    # Check every entry before restoring any: never overwrite intervening user work.
    pointer = entry_identity(store / "current")
    pointer_targets = (snapshot["previous_current"], snapshot["target_current"])
    if pointer not in [{"kind": "symlink", "target": target} if target else {"kind": "absent"} for target in pointer_targets]:
        raise ValueError("current pointer changed outside the install transaction")
    touched = {item["path"] for item in snapshot["entries"]}
    for name, target in snapshot["links_after"].items():
        expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        if name not in touched and entry_identity(Path(name)) != expected:
            raise ValueError(f"install recovery conflicts with unchanged managed entry: {name}")
    for item in snapshot["entries"]:
        current = entry_identity(Path(item["path"]))
        allowed = [item["before"], item["after"], {"kind": "absent"}]
        if current not in allowed:
            raise ValueError(f"install recovery conflicts with current entry: {item['path']}")
        backup = Path(item["backup"])
        if item["before"]["kind"] != "absent" and current != item["before"] and entry_identity(backup) != item["before"]:
            raise ValueError(f"install recovery backup missing or changed: {backup}")
    for item in reversed(snapshot["entries"]):
        path, backup = Path(item["path"]), Path(item["backup"])
        if entry_identity(path) == item["before"]:
            continue
        if path.is_symlink():
            path.unlink()
        if item["before"]["kind"] != "absent":
            path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, path)
    set_pointer(store, snapshot["previous_current"])
    previous = snapshot["previous_state"]
    if previous is None:
        (store / "installed.json").unlink(missing_ok=True)
    else:
        atomic_json(store / "installed.json", previous)
    (store / "pending.json").unlink(missing_ok=True)


def activate(store: Path, bundle_id: str, hosts: dict[str, Path], *, quiescent: bool, migrate: bool = False,
             retired_ready_runtime_root: Path | None = None,
             retired_ready_runtime_evidence: Path | None = None) -> dict:
    if not quiescent:
        raise ValueError("explicit quiescent-host confirmation is required; cancellation receipt is not settlement")
    store = store.resolve()
    hosts = {name: root.resolve() for name, root in hosts.items()}
    for root in hosts.values():
        if root.is_relative_to(store) or store.is_relative_to(root):
            raise ValueError("host root and release store must be disjoint")
        for namespace in ("skills", "extensions"):
            if (root / namespace).is_symlink():
                raise ValueError(f"refusing install through symlinked host namespace: {root / namespace}")
    with install_lock(store):
        if (store / "pending.json").exists():
            raise ValueError("unfinished install transaction; use explicit rollback after containment")
        manifest = check_candidate_release(store, bundle_id)
        old = check_install(store) if (store / "installed.json").exists() else None
        if old and not set(old["hosts"]).issubset(hosts):
            raise ValueError("shared current pointer requires all previously installed hosts in activation scope")
        if old and any(str(hosts[name]) != root for name, root in old["hosts"].items()):
            raise ValueError("host roots cannot move during bundle activation; remove the old install explicitly")
        old_runtime_managed = bool(old and any(
            Path(name).name == OLD_EXTENSION_NAME and target
            for name, target in old["links"].items()
        ))
        retirement_scan = None
        retirement_root = None
        if old_runtime_managed:
            retirement_root = canonical_directory(retired_ready_runtime_root, "retired Ready runtime root")
            if retirement_root.is_relative_to(store) or any(
                    retirement_root.is_relative_to(root) or root.is_relative_to(retirement_root) for root in hosts.values()):
                raise ValueError("retired Ready runtime root must be disjoint from release store and host roots")
            retirement_scan = scan_retired_runtime(retirement_root, retired_ready_runtime_evidence)
            if not retirement_scan["summary"]["activation_allowed"]:
                raise ValueError("retired Ready runtime has live/unsettled/unattributed records")
        elif retired_ready_runtime_root is not None or retired_ready_runtime_evidence is not None:
            raise ValueError("retired Ready runtime inputs are only valid when the installed old runtime extension is managed")
        links = host_links(store, manifest, hosts)
        if old:
            for name in old["links"]:
                links.setdefault(name, None)
        previous_current = os.readlink(store / "current") if (store / "current").is_symlink() else None
        if (store / "current").exists() and previous_current is None:
            raise ValueError("unmanaged current entry")
        if old is None and previous_current is not None:
            raise ValueError("current pointer has no matching managed installation")
        entries = []
        snapshot_dir = store / "snapshots" / uuid.uuid4().hex
        originals = dict(old["originals"]) if old else {}
        for index, (name, target) in enumerate(links.items()):
            path = Path(name)
            before = entry_identity(path)
            after = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
            if old and name in old["links"]:
                expected = {"kind": "symlink", "target": old["links"][name]} if old["links"][name] else {"kind": "absent"}
                if before != expected:
                    raise ValueError(f"managed install entry drift: {name}")
            elif before["kind"] != "absent" and not migrate:
                raise ValueError(f"unmanaged install entry requires explicit --migrate and snapshot: {name}")
            if before == after:
                continue
            item = {"path": name, "before": before, "after": after, "backup": str(snapshot_dir / str(index))}
            entries.append(item)
            originals.setdefault(name, item)
        snapshot_dir.mkdir(parents=True)
        try:
            retirement_snapshot = None
            if retirement_scan is not None:
                archive = archive_retired_runtime(retirement_root, retirement_scan, snapshot_dir / "retired-ready-runtime")
                retirement_snapshot = {**retirement_scan, "archive": archive}
        except BaseException:
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            raise
        previous_state = read_json(store / "installed.json") if old else None
        snapshot = {"entries": entries, "previous_current": previous_current, "previous_state": previous_state,
                    "previous_family": old["family"] if old else None, "target_family": manifest["family"],
                    "target_current": str(release_path(store, bundle_id)), "links_after": links,
                    "retired_ready_runtime": retirement_snapshot,
                    "snapshot": str(snapshot_dir / "snapshot.json")}
        atomic_json(snapshot_dir / "snapshot.json", snapshot)
        atomic_json(store / "pending.json", snapshot)
        try:
            for item in entries:
                path = Path(item["path"])
                if entry_identity(path) != item["before"]:
                    raise ValueError(f"install entry changed after preflight: {path}")
                if item["before"]["kind"] != "absent":
                    os.replace(path, item["backup"])
                if item["after"]["kind"] == "symlink":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.symlink_to(item["after"]["target"], target_is_directory=True)
            set_pointer(store, str(release_path(store, bundle_id)))
            state = {"schema": "iis-install/v2", "bundle_id": bundle_id, "family": manifest["family"],
                     "hosts": {name: str(root) for name, root in hosts.items()},
                     "links": links, "originals": originals, "snapshot": snapshot["snapshot"],
                     "retired_ready_runtime": retirement_snapshot,
                     "loaded_identity": "NOT_CHECKED"}
            atomic_json(store / "installed.json", state)
            (store / "pending.json").unlink()
            return state
        except BaseException:
            restore_snapshot(store, snapshot)
            raise


def rollback(store: Path, *, quiescent: bool) -> dict:
    if not quiescent:
        raise ValueError("contain candidate work and effects before rollback")
    store = store.resolve()
    with install_lock(store):
        if (store / "pending.json").exists():
            snapshot = read_json(store / "pending.json")
        else:
            state = read_json(store / "installed.json")
            snapshot = read_json(Path(state["snapshot"]))
        restore_snapshot(store, snapshot)
        return {"restored": True, "loaded_identity": "NOT_CHECKED", "snapshot": snapshot["snapshot"]}


def remove(store: Path, *, quiescent: bool) -> dict:
    if not quiescent:
        raise ValueError("quiescent hosts are required before removing managed install entries")
    store = store.resolve()
    with install_lock(store):
        if (store / "pending.json").exists():
            raise ValueError("recover unfinished installation before removal")
        state = read_json(store / "installed.json")
        for name, target in state["links"].items():
            expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
            if entry_identity(Path(name)) != expected:
                raise ValueError(f"refusing to remove changed install entry: {name}")
        snapshot = {"entries": list(state["originals"].values()), "previous_current": None,
                    "previous_state": None, "snapshot": state["snapshot"],
                    "target_current": str(release_path(store, state["bundle_id"])), "links_after": state["links"]}
        atomic_json(store / "pending.json", snapshot)
        restore_snapshot(store, snapshot)
        return {"removed": True, "releases_and_snapshots_preserved": True, "loaded_identity": "NOT_CHECKED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "check", "activate", "rollback", "remove"))
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--origin", type=Path, action="append")
    parser.add_argument("--store", type=Path, default=Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "iis")
    parser.add_argument("--bundle")
    parser.add_argument("--host", choices=("omp", "codex"), action="append")
    parser.add_argument("--omp-root", type=Path, default=Path.home() / ".omp/agent")
    parser.add_argument("--codex-root", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--confirm-quiescent", action="store_true")
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--retired-ready-runtime-root", type=Path)
    parser.add_argument("--retired-ready-runtime-evidence", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            manifest = prepare(args.source, args.store, args.origin)
            result = {"bundle_id": manifest["bundle_id"], "family": manifest["family"],
                      "files": len(manifest["files"]), "installed": False}
        elif args.action == "check":
            with install_lock(args.store.resolve()):
                bundle_id = args.bundle or check_install(args.store.resolve())["bundle_id"]
                manifest = check_release(args.store.resolve(), bundle_id)
                result = {"bundle_id": manifest["bundle_id"], "family": manifest["family"],
                          "files": len(manifest["files"]), "loaded_identity": "NOT_CHECKED"}
        elif args.action == "activate":
            if not args.bundle:
                raise ValueError("activate requires --bundle")
            roots = {"omp": args.omp_root, "codex": args.codex_root}
            hosts = {name: roots[name] for name in (args.host or ["omp"])}
            result = activate(args.store, args.bundle, hosts, quiescent=args.confirm_quiescent, migrate=args.migrate,
                              retired_ready_runtime_root=args.retired_ready_runtime_root,
                              retired_ready_runtime_evidence=args.retired_ready_runtime_evidence)
        elif args.action == "rollback":
            result = rollback(args.store, quiescent=args.confirm_quiescent)
        else:
            result = remove(args.store, quiescent=args.confirm_quiescent)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
