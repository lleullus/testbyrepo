#!/usr/bin/env python3
"""Prepare executor-owned protocol-5 IIS payloads and switch quiescent install paths."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import fcntl
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
SCHEMA = "iis-bundle/v5"
PROTOCOL = 5
NEW_FAMILY = "iis-skills"
INSTALL_SCHEMA = "iis-install/v5"
LEGACY_INSTALL_SCHEMAS = {"iis-install/v3", "iis-install/v4"}
PAYLOAD_ROOTS = (
    "iis-workflow", "product-thesis", "scope-shaper", "iis_artifacts", "iis-observatory", "repo-snapshot",
    "observatory/bin", "observatory/src",
    "companion-skills/scope-plan", "companion-skills/scope-implement",
    "companion-skills/production-heuristic-probing",
    "companion-skills/repository-investigation", "companion-skills/purpose-first-review",
    "iis_path_contract.py",
)
REQUIRED = (
    "iis-workflow/SKILL.md", "product-thesis/SKILL.md",
    "product-thesis/tools/lifecycle.py", "product-thesis/tools/thesis.py",
    "iis_artifacts/store.py", "iis_artifacts/admission.py",
    "iis-workflow/references/assurance.md", "iis-workflow/tools/assurance.py",
    "scope-shaper/SKILL.md", "scope-shaper/tools/validate_scope.py",
    "iis-observatory/SKILL.md", "repo-snapshot/SKILL.md",
    "observatory/bin/iis-observatory", "observatory/src/iis_observatory/__main__.py",
    "companion-skills/scope-plan/SKILL.md",
    "companion-skills/scope-plan/references/plan.md",
    "companion-skills/scope-implement/SKILL.md",
    "companion-skills/scope-implement/references/implement.md",
    "companion-skills/production-heuristic-probing/SKILL.md",
    "companion-skills/repository-investigation/SKILL.md",
    "companion-skills/purpose-first-review/SKILL.md",
    "iis_path_contract.py",
)
CANDIDATE_RETIRED = (
    "companion-skills/scope-verify", "companion-skills/scope-plan/references/review.md",
    "companion-skills/scope-plan/dispatch/reviewer.md",
    "iis-adaptive-planning", "matt", "delivery-runtime", "delivery-tools",
    "companion-skills/ready-ticket-plan", "companion-skills/ready-ticket-implement",
    "companion-skills/ready-ticket-verify", "companion-skills/ready-ticket-coverage",
    "companion-skills/ready-ticket-heuristic-probe", "companion-skills/scope-coverage",
)
TEXT_SUFFIXES = {".md", ".py", ".js", ".json", ".yaml", ".yml", ".sh", ".toml"}
RELEASE_ID = re.compile(r"^rel-[0-9a-f]{32}$")


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
        retired = source / relative
        if retired.is_symlink() or retired.is_file() or retired.is_dir() and any(retired.iterdir()):
            raise ValueError(f"retired payload is still present: {relative}")
    files: list[Path] = []
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
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=source, text=True, capture_output=True, check=False,
    )
    if result.returncode == 0:
        common = Path(result.stdout.strip())
        if common.name == ".git":
            origins.add(common.parent)
    return sorted(origins, key=lambda path: len(str(path)), reverse=True)


def rebase(content: bytes, origins: list[Path], destination: Path) -> bytes:
    for origin in origins:
        content = content.replace(str(origin).encode() + b"/", str(destination).encode() + b"/")
    return content


def release_path(store: Path, bundle_id: str) -> Path:
    if RELEASE_ID.fullmatch(bundle_id) is None:
        raise ValueError("release id must be an executor-allocated rel-<id>")
    destination = store / "releases" / bundle_id
    if destination.is_symlink():
        raise ValueError("release directory must not be a symlink")
    return destination


def record_path(store: Path, bundle_id: str) -> Path:
    if RELEASE_ID.fullmatch(bundle_id) is None:
        raise ValueError("invalid release id")
    return store / "records" / bundle_id


def _file_set(root: Path, *, ignore: set[str]) -> set[str]:
    result = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink in protected release: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if relative not in ignore:
                result.add(relative)
    return result


def check_release(store: Path, bundle_id: str) -> dict:
    release = release_path(store, bundle_id)
    record = record_path(store, bundle_id)
    manifest = read_json(release / "bundle.json")
    record_manifest = read_json(record / "bundle.json")
    if manifest != record_manifest:
        raise ValueError("release manifest changed")
    if (
        manifest.get("schema") != SCHEMA
        or manifest.get("protocol") != PROTOCOL
        or manifest.get("bundle_id") != bundle_id
        or manifest.get("family") != NEW_FAMILY
    ):
        raise ValueError("release identity, protocol, or family mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("incomplete release manifest")
    actual = _file_set(release, ignore={"bundle.json"})
    protected = _file_set(record / "payload", ignore=set())
    if actual != set(entries) or protected != set(entries):
        raise ValueError("release file set drift")
    for relative, expected in entries.items():
        if not isinstance(expected, dict) or set(expected) != {"mode"}:
            raise ValueError(f"invalid release manifest entry: {relative}")
        path = release / relative
        original = record / "payload" / relative
        if path.read_bytes() != original.read_bytes():
            raise ValueError(f"release file changed: {relative}")
        if stat.S_IMODE(path.stat().st_mode) != expected["mode"]:
            raise ValueError(f"release mode changed: {relative}")
    return manifest


def check_candidate_release(store: Path, bundle_id: str) -> dict:
    manifest = check_release(store, bundle_id)
    entries = set(manifest["files"])
    if not all(relative in entries for relative in REQUIRED):
        raise ValueError("incomplete IIS candidate manifest")
    if any(relative == retired or relative.startswith(retired + "/") for relative in entries for retired in CANDIDATE_RETIRED):
        raise ValueError("candidate release contains retired IIS payload")
    return manifest


def _legacy_release(store: Path, bundle_id: str) -> Path:
    release = store / "releases" / bundle_id
    if not release.is_dir() or release.is_symlink():
        raise ValueError("legacy current release is missing or unsafe")
    return release


def legacy_install_for_cutover(store: Path) -> dict:
    state = read_json(store / "installed.json")
    if state.get("schema") not in LEGACY_INSTALL_SCHEMAS:
        raise ValueError("unsupported installed-state schema")
    release = _legacy_release(store, state["bundle_id"])
    expected_pointer = {"kind": "symlink", "target": str(release)}
    if entry_identity(store / "current") != expected_pointer:
        raise ValueError("legacy installed current pointer drift")
    links = state.get("links")
    if not isinstance(links, dict) or not links:
        raise ValueError("legacy installed links are missing")
    for name, target in links.items():
        expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        if entry_identity(Path(name)) != expected:
            raise ValueError(f"legacy managed install entry drift: {name}")
    return {**state, "legacy": True}


def check_install(store: Path) -> dict:
    if (store / "pending.json").exists():
        raise ValueError("unfinished install transaction requires recovery")
    state = read_json(store / "installed.json")
    if state.get("schema") != INSTALL_SCHEMA or state.get("family") != NEW_FAMILY:
        raise ValueError("unsupported installed IIS contract")
    manifest = check_release(store, state["bundle_id"])
    expected_pointer = {"kind": "symlink", "target": str(release_path(store, state["bundle_id"]))}
    if entry_identity(store / "current") != expected_pointer:
        raise ValueError("installed current pointer drift")
    for name, target in state["links"].items():
        expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        if entry_identity(Path(name)) != expected:
            raise ValueError(f"managed install entry drift: {name}")
    return {**state, "family": manifest["family"]}


def inspect(store: Path, bundle_id: str | None = None) -> dict:
    store = store.resolve()
    with install_lock(store):
        if bundle_id is None:
            state = read_json(store / "installed.json")
            if state.get("schema") in LEGACY_INSTALL_SCHEMAS:
                legacy = legacy_install_for_cutover(store)
                return {
                    "bundle_id": legacy["bundle_id"],
                    "family": legacy["family"],
                    "protocol": "legacy",
                    "files": None,
                    "loaded_identity": "NOT_CHECKED",
                    "legacy_read_only": True,
                }
            installed = check_install(store)
            bundle_id = installed["bundle_id"]
            manifest = read_json(release_path(store, bundle_id) / "bundle.json")
        else:
            manifest = check_candidate_release(store, bundle_id)
        return {
            "bundle_id": manifest["bundle_id"],
            "family": manifest["family"],
            "protocol": manifest["protocol"],
            "files": len(manifest["files"]),
            "loaded_identity": "NOT_CHECKED",
        }


def prepare(source: Path, store: Path, origins: list[Path] | None = None) -> dict:
    source, store = source.resolve(strict=True), store.resolve()
    if store.is_relative_to(source):
        raise ValueError("release store must be outside source")
    files = payload_files(source)
    initial = {
        path.relative_to(source).as_posix(): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        for path in files
    }
    bundle_id = "rel-" + uuid.uuid4().hex
    with install_lock(store):
        destination = release_path(store, bundle_id)
        record = record_path(store, bundle_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        record.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".release-", dir=destination.parent))
        record_staging = Path(tempfile.mkdtemp(prefix=".record-", dir=record.parent))
        try:
            entries = {}
            original_roots = source_origins(source, origins)
            for path in files:
                relative = path.relative_to(source).as_posix()
                before, before_mode = initial[relative]
                if path.read_bytes() != before or stat.S_IMODE(path.stat().st_mode) != before_mode:
                    raise ValueError(f"source changed during capture: {relative}")
                content = rebase(before, original_roots, destination) if path.suffix in TEXT_SUFFIXES else before
                mode = before_mode & 0o555
                for root in (staging, record_staging / "payload"):
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    target.chmod(mode)
                entries[relative] = {"mode": mode}
            current_files = payload_files(source)
            if [item.relative_to(source).as_posix() for item in current_files] != list(initial):
                raise ValueError("source file set changed during capture")
            for path in current_files:
                relative = path.relative_to(source).as_posix()
                before, before_mode = initial[relative]
                if path.read_bytes() != before or stat.S_IMODE(path.stat().st_mode) != before_mode:
                    raise ValueError(f"source changed during capture: {relative}")
            manifest = {
                "schema": SCHEMA,
                "protocol": PROTOCOL,
                "family": NEW_FAMILY,
                "bundle_id": bundle_id,
                "source": str(source),
                "source_origins": [str(path) for path in original_roots],
                "files": entries,
            }
            atomic_json(staging / "bundle.json", manifest)
            atomic_json(record_staging / "bundle.json", manifest)
            (staging / "bundle.json").chmod(0o444)
            (record_staging / "bundle.json").chmod(0o400)
            os.replace(record_staging, record)
            os.replace(staging, destination)
            return check_candidate_release(store, bundle_id)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
            if record_staging.exists():
                shutil.rmtree(record_staging)


def entry_identity(path: Path) -> dict:
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "absent"}
    if path.is_file():
        return {
            "kind": "file",
            "mode": stat.S_IMODE(path.stat().st_mode),
            "content_b64": base64.b64encode(path.read_bytes()).decode("ascii"),
        }
    if path.is_dir():
        entries = []
        for child in sorted(path.rglob("*")):
            relative = child.relative_to(path).as_posix()
            if child.is_symlink():
                entries.append({"path": relative, "kind": "symlink", "target": os.readlink(child)})
            elif child.is_file():
                entries.append({
                    "path": relative,
                    "kind": "file",
                    "mode": stat.S_IMODE(child.stat().st_mode),
                    "content_b64": base64.b64encode(child.read_bytes()).decode("ascii"),
                })
            elif child.is_dir():
                entries.append({"path": relative, "kind": "directory", "mode": stat.S_IMODE(child.stat().st_mode)})
        return {"kind": "directory", "mode": stat.S_IMODE(path.stat().st_mode), "entries": entries}
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
    skills = sorted(
        Path(name).parent for name in manifest["files"]
        if name.endswith("/SKILL.md") and (
            len(Path(name).parts) == 2
            or Path(name).parts[0] == "companion-skills" and len(Path(name).parts) == 3
        )
    )
    links = {}
    for host, root in hosts.items():
        names = set()
        for skill in skills:
            if skill.name in names:
                raise ValueError(f"duplicate installed skill name: {skill.name}")
            names.add(skill.name)
            links[str(root / "skills" / skill.name)] = str(store / "current" / skill)
        if host not in {"omp", "codex"}:
            raise ValueError(f"unsupported install path adapter: {host}")
    return links


def restore_snapshot(store: Path, snapshot: dict) -> None:
    pointer = entry_identity(store / "current")
    pointer_targets = (snapshot["previous_current"], snapshot["target_current"])
    allowed_pointers = [
        {"kind": "symlink", "target": target} if target else {"kind": "absent"}
        for target in pointer_targets
    ]
    if pointer not in allowed_pointers:
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
        elif path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
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
        raise ValueError("explicit quiescent-host confirmation is required")
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
            raise ValueError("unfinished install transaction; recover it first")
        manifest = check_candidate_release(store, bundle_id)
        if (store / "installed.json").exists():
            schema = read_json(store / "installed.json").get("schema")
            old = legacy_install_for_cutover(store) if schema in LEGACY_INSTALL_SCHEMAS else check_install(store)
        else:
            old = None
        if old and not set(old["hosts"]).issubset(hosts):
            raise ValueError("shared current pointer requires all previously installed hosts in activation scope")
        if old and any(str(hosts[name]) != root for name, root in old["hosts"].items()):
            raise ValueError("host roots cannot move during activation")
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
        snapshot_dir = store / "snapshots" / ("install-" + uuid.uuid4().hex)
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
                raise ValueError(f"unmanaged install entry requires explicit --migrate: {name}")
            if before == after:
                continue
            item = {"path": name, "before": before, "after": after, "backup": str(snapshot_dir / str(index))}
            entries.append(item)
            originals.setdefault(name, item)
        snapshot_dir.mkdir(parents=True)
        previous_state = read_json(store / "installed.json") if old else None
        snapshot = {
            "entries": entries,
            "previous_current": previous_current,
            "previous_state": previous_state,
            "previous_family": old["family"] if old else None,
            "target_family": manifest["family"],
            "target_current": str(release_path(store, bundle_id)),
            "links_after": links,
            "snapshot": str(snapshot_dir / "snapshot.json"),
        }
        atomic_json(snapshot_dir / "snapshot.json", snapshot)
        atomic_json(store / "pending.json", snapshot)
        try:
            for item in entries:
                path = Path(item["path"])
                if entry_identity(path) != item["before"]:
                    raise ValueError(f"install entry changed after preflight: {path}")
                if item["before"]["kind"] != "absent":
                    item_backup = Path(item["backup"])
                    item_backup.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, item_backup)
                if item["after"]["kind"] == "symlink":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.symlink_to(item["after"]["target"], target_is_directory=True)
            set_pointer(store, str(release_path(store, bundle_id)))
            state = {
                "schema": INSTALL_SCHEMA,
                "bundle_id": bundle_id,
                "family": manifest["family"],
                "hosts": {name: str(root) for name, root in hosts.items()},
                "links": links,
                "originals": originals,
                "snapshot": snapshot["snapshot"],
                "loaded_identity": "NOT_CHECKED",
            }
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
        state = check_install(store)
        for name, target in state["links"].items():
            expected = {"kind": "symlink", "target": target} if target else {"kind": "absent"}
            if entry_identity(Path(name)) != expected:
                raise ValueError(f"refusing to remove changed install entry: {name}")
        snapshot = {
            "entries": list(state["originals"].values()),
            "previous_current": None,
            "previous_state": None,
            "snapshot": state["snapshot"],
            "target_current": str(release_path(store, state["bundle_id"])),
            "links_after": state["links"],
        }
        atomic_json(store / "pending.json", snapshot)
        restore_snapshot(store, snapshot)
        return {"removed": True, "releases_and_snapshots_preserved": True, "loaded_identity": "NOT_CHECKED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "inspect", "activate", "rollback", "remove"))
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
            result = {"bundle_id": manifest["bundle_id"], "family": manifest["family"], "files": len(manifest["files"]), "installed": False}
        elif args.action == "inspect":
            result = inspect(args.store, args.bundle)
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
