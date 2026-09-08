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
PAYLOAD_ROOTS = (
    "iis-workflow", "iis-adaptive-planning", "matt/skills", "scope-shaper",
    "behavior-design-lead", "scope-investigation-runner", "repo-snapshot",
    "companion-skills", "planning-workspace", "iis_path_contract.py",
    "delivery-runtime/ready-ticket-implement",
)
REQUIRED = (
    "iis-workflow/SKILL.md", "matt/skills/to-tickets/validate_ticket.py",
    "companion-skills/ready-ticket-plan/SKILL.md",
    "companion-skills/ready-ticket-implement/SKILL.md",
    "companion-skills/ready-ticket-verify/SKILL.md",
    "delivery-runtime/ready-ticket-implement/index.js",
    "delivery-runtime/ready-ticket-implement/src/core.js",
    "delivery-runtime/ready-ticket-implement/src/plan-binding.js",
    "delivery-runtime/ready-ticket-implement/src/finalization.js",
)
RETIRED = ("companion-skills/ready-ticket-heuristic-probe",) + tuple(
    "delivery-runtime/ready-ticket-implement/src/" + name
    for name in ("observation-ledger.js", "inventory-policy.js", "retry-policy.js",
                 "probe-handoff.js", "service-supervisor.js")
)
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
    for relative in RETIRED:
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


def check_release(store: Path, bundle_id: str) -> dict:
    release = release_path(store, bundle_id)
    manifest = read_json(release / "bundle.json")
    if manifest.get("schema") != SCHEMA or manifest.get("protocol") != 2 or manifest.get("bundle_id") != bundle_id:
        raise ValueError("bundle identity or protocol mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not all(relative in entries for relative in REQUIRED):
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
        if sha(path.read_bytes()) != expected["sha256"] or stat.S_IMODE(path.stat().st_mode) != expected["mode"]:
            raise ValueError(f"bundle file drift: {relative}")
    return manifest


def check_install(store: Path) -> dict:
    if (store / "pending.json").exists():
        raise ValueError("unfinished install transaction requires recovery")
    state = read_json(store / "installed.json")
    if state.get("schema") != "iis-install/v2":
        raise ValueError("unsupported installed-state schema")
    check_release(store, state["bundle_id"])
    expected_pointer = {"kind": "symlink", "target": str(release_path(store, state["bundle_id"]))}
    if entry_identity(store / "current") != expected_pointer:
        raise ValueError("installed current pointer drift")
    for name, target in state["links"].items():
        expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        if entry_identity(Path(name)) != expected:
            raise ValueError(f"managed install entry drift: {name}")
    return state


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
            return check_release(store, bundle_id)
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
            manifest = {"schema": SCHEMA, "protocol": 2, "bundle_id": bundle_id,
                        "source": str(source), "source_origins": [str(path) for path in original_roots],
                        "files": entries, "input_files": inputs}
            atomic_json(staging / "bundle.json", manifest)
            (staging / "bundle.json").chmod(0o444)
            os.replace(staging, destination)
            return check_release(store, bundle_id)
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
            links[str(root / "extensions/ready-ticket-implement-runtime")] = str(store / "current/delivery-runtime/ready-ticket-implement")
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


def activate(store: Path, bundle_id: str, hosts: dict[str, Path], *, quiescent: bool, migrate: bool = False) -> dict:
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
        manifest = check_release(store, bundle_id)
        old = check_install(store) if (store / "installed.json").exists() else None
        if old and not set(old["hosts"]).issubset(hosts):
            raise ValueError("shared current pointer requires all previously installed hosts in activation scope")
        if old and any(str(hosts[name]) != root for name, root in old["hosts"].items()):
            raise ValueError("host roots cannot move during bundle activation; remove the old install explicitly")
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
        snapshot = {"entries": entries, "previous_current": previous_current, "previous_state": old,
                    "target_current": str(release_path(store, bundle_id)), "links_after": links,
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
            state = {"schema": "iis-install/v2", "bundle_id": bundle_id,
                     "hosts": {name: str(root) for name, root in hosts.items()},
                     "links": links, "originals": originals, "snapshot": snapshot["snapshot"],
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
        return {"removed": True, "release_and_runtime_data_preserved": True, "loaded_identity": "NOT_CHECKED"}


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
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            manifest = prepare(args.source, args.store, args.origin)
            result = {"bundle_id": manifest["bundle_id"], "files": len(manifest["files"]), "installed": False}
        elif args.action == "check":
            with install_lock(args.store.resolve()):
                bundle_id = args.bundle or check_install(args.store.resolve())["bundle_id"]
                manifest = check_release(args.store.resolve(), bundle_id)
                result = {"bundle_id": manifest["bundle_id"], "files": len(manifest["files"]), "loaded_identity": "NOT_CHECKED"}
        elif args.action == "activate":
            if not args.bundle:
                raise ValueError("activate requires --bundle")
            roots = {"omp": args.omp_root, "codex": args.codex_root}
            hosts = {name: roots[name] for name in (args.host or ["omp"])}
            result = activate(args.store, args.bundle, hosts, quiescent=args.confirm_quiescent, migrate=args.migrate)
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
