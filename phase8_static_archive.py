#!/usr/bin/env python3
"""Create or verify an immutable Phase 8 static archive without legacy readers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable


RESULT_CLASS = "HISTORICAL_RESULT"
CAPSULE_CLASS = "REFERENCED_CAPSULE"
MANIFEST_NAME = "manifest.json"
ARCHIVE_SCHEMA_VERSION = "phase8-static-archive-v1"
IDENTITY_FIELDS = ("st_size", "st_mode", "st_dev", "st_ino", "st_mtime_ns", "st_ctime_ns")


class ArchiveError(RuntimeError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digest_items(items: Iterable[dict[str, Any]]) -> str:
    lines = (
        f"{item['sourceClass']}\t{item['relativePath']}\t{item['size']}\t{item['sha256']}\t{item['originalMode']:04o}\n"
        for item in items
    )
    return _sha256("".join(lines).encode("utf-8"))


def _canonical_root(raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser().absolute()
    try:
        if path.is_symlink():
            raise ArchiveError(f"root path must not be a symlink: {path}")
        return path.resolve(strict=True)
    except OSError as exc:
        raise ArchiveError(f"root path is unavailable: {path}: {exc}") from exc


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_directory(path: Path, description: str) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ArchiveError(f"{description} is unavailable: {exc}") from exc
    if not stat.S_ISDIR(mode) or path.is_symlink():
        raise ArchiveError(f"{description} must be a non-symlink directory: {path}")


def _relative_regular_files(root: Path, description: str) -> list[Path]:
    _require_directory(root, description)
    files: list[Path] = []
    for directory, directories, names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        try:
            directory_mode = directory_path.lstat().st_mode
        except OSError as exc:
            raise ArchiveError(f"cannot stat {directory_path}: {exc}") from exc
        if not stat.S_ISDIR(directory_mode) or directory_path.is_symlink():
            raise ArchiveError(f"{description} contains a non-directory path: {directory_path}")
        for name in directories:
            child = directory_path / name
            try:
                child_mode = child.lstat().st_mode
            except OSError as exc:
                raise ArchiveError(f"cannot stat {child}: {exc}") from exc
            if not stat.S_ISDIR(child_mode) or child.is_symlink():
                raise ArchiveError(f"{description} contains a non-directory child: {child}")
        for name in names:
            child = directory_path / name
            try:
                child_mode = child.lstat().st_mode
            except OSError as exc:
                raise ArchiveError(f"cannot stat {child}: {exc}") from exc
            if not stat.S_ISREG(child_mode):
                raise ArchiveError(f"{description} contains a non-regular file: {child}")
            files.append(child)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _result_capsule_refs(results_root: Path) -> list[str]:
    refs: list[str] = []
    for path in _relative_regular_files(results_root, "historical result root"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArchiveError(f"cannot read historical result {path}: {exc}") from exc
        capsule_ref = value.get("capsuleRef") if isinstance(value, dict) else None
        if not isinstance(capsule_ref, str) or not capsule_ref.startswith("capsule:v1:"):
            raise ArchiveError(f"historical result has no capsuleRef: {path}")
        capsule_id = capsule_ref.removeprefix("capsule:v1:")
        if len(capsule_id) != 32 or any(character not in "0123456789abcdef" for character in capsule_id):
            raise ArchiveError(f"historical result has malformed capsuleRef: {path}")
        refs.append(capsule_id)
    if len(set(refs)) != len(refs):
        raise ArchiveError("historical results do not have distinct capsuleRef values")
    return sorted(refs)


def _snapshot(path: Path) -> tuple[int, int, int, int, int, int]:
    try:
        value = path.lstat()
    except OSError as exc:
        raise ArchiveError(f"cannot stat source path {path}: {exc}") from exc
    if not stat.S_ISREG(value.st_mode):
        raise ArchiveError(f"source path is not a regular file: {path}")
    return tuple(getattr(value, field) for field in IDENTITY_FIELDS)


def _copy_source(source: Path, destination: Path) -> tuple[int, str, int]:
    before = _snapshot(source)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    source_descriptor = os.open(source, source_flags)
    destination_descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    digest = hashlib.sha256()
    copied = 0
    try:
        with os.fdopen(source_descriptor, "rb") as input_handle, os.fdopen(destination_descriptor, "wb") as output_handle:
            input_before = tuple(getattr(os.fstat(input_handle.fileno()), field) for field in IDENTITY_FIELDS)
            if input_before != before:
                raise ArchiveError(f"source changed before copy: {source}")
            while chunk := input_handle.read(1024 * 1024):
                output_handle.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
            input_after = tuple(getattr(os.fstat(input_handle.fileno()), field) for field in IDENTITY_FIELDS)
            after = _snapshot(source)
            if input_after != before or after != before:
                raise ArchiveError(f"source changed during copy: {source}")
            output_handle.flush()
            os.fsync(output_handle.fileno())
    except BaseException:
        try:
            destination.unlink()
        except OSError:
            pass
        raise
    return copied, digest.hexdigest(), stat.S_IMODE(before[1])


def _stable_digest(source: Path, expected: tuple[int, int, int, int, int, int]) -> tuple[int, str]:
    descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    digest = hashlib.sha256()
    copied = 0
    with os.fdopen(descriptor, "rb") as handle:
        before = tuple(getattr(os.fstat(handle.fileno()), field) for field in IDENTITY_FIELDS)
        if before != expected:
            raise ArchiveError(f"source changed before archive validation: {source}")
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            copied += len(chunk)
        after = tuple(getattr(os.fstat(handle.fileno()), field) for field in IDENTITY_FIELDS)
    if after != expected or _snapshot(source) != expected:
        raise ArchiveError(f"source changed during archive validation: {source}")
    return copied, digest.hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _archive_item(source_class: str, source_root: Path, source: Path, archive_relative: Path) -> dict[str, Any]:
    relative = source.relative_to(source_root).as_posix()
    snapshot = _snapshot(source)
    return {
        "sourceClass": source_class,
        "sourcePath": str(source),
        "relativePath": archive_relative.as_posix(),
        "size": snapshot[0],
        "sha256": None,
        "originalMode": stat.S_IMODE(snapshot[1]),
        "snapshot": snapshot,
    }


def _source_items(results_root: Path, capsule_store_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    result_files = _relative_regular_files(results_root, "historical result root")
    refs = _result_capsule_refs(results_root)
    capsule_root = capsule_store_root / "capsules"
    _require_directory(capsule_root, "baseline capsule root")
    items = [
        _archive_item(RESULT_CLASS, results_root, path, Path("implementation-results") / path.relative_to(results_root))
        for path in result_files
    ]
    for capsule_id in refs:
        source_root = capsule_root / capsule_id
        _require_directory(source_root, f"referenced capsule {capsule_id}")
        for path in _relative_regular_files(source_root, f"referenced capsule {capsule_id}"):
            items.append(
                _archive_item(
                    CAPSULE_CLASS,
                    capsule_root,
                    path,
                    Path("baseline-capsules") / "capsules" / path.relative_to(capsule_root),
                )
            )
    return sorted(items, key=lambda item: item["relativePath"]), refs


def _source_shape(items: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    return [(item["sourceClass"], item["sourcePath"], item["relativePath"]) for item in items]


def _validate_staging_against_source(staging: Path, items: list[dict[str, Any]]) -> None:
    for item in items:
        source = Path(item["sourcePath"])
        snapshot = tuple(item["snapshot"])
        source_size, source_digest = _stable_digest(source, snapshot)
        destination = staging / item["relativePath"]
        try:
            observed = destination.lstat()
        except OSError as exc:
            raise ArchiveError(f"staging item is unavailable: {destination}: {exc}") from exc
        if not stat.S_ISREG(observed.st_mode):
            raise ArchiveError(f"staging item is not a regular file: {destination}")
        with destination.open("rb") as handle:
            staged_payload = handle.read()
        if (
            source_size != item["size"]
            or source_digest != item["sha256"]
            or len(staged_payload) != item["size"]
            or _sha256(staged_payload) != item["sha256"]
        ):
            raise ArchiveError(f"staging item differs from source: {source}")


def _manifest_content(items: list[dict[str, Any]], refs: list[str]) -> dict[str, Any]:
    archive_items = [
        {
            "sourceClass": item["sourceClass"],
            "relativePath": item["relativePath"],
            "size": item["size"],
            "sha256": item["sha256"],
            "originalMode": item["originalMode"],
        }
        for item in items
    ]
    result_items = [item for item in archive_items if item["sourceClass"] == RESULT_CLASS]
    capsule_items = [item for item in archive_items if item["sourceClass"] == CAPSULE_CLASS]
    content = {
        "schemaVersion": ARCHIVE_SCHEMA_VERSION,
        "disposition": "STATIC_ARCHIVE",
        "retentionDisposalAuthorized": False,
        "items": archive_items,
        "referencedCapsuleRefs": [f"capsule:v1:{capsule_id}" for capsule_id in refs],
        "counts": {
            "historicalResults": len(result_items),
            "referencedCapsules": len(refs),
            "files": len(archive_items),
            "bytes": sum(item["size"] for item in archive_items),
        },
        "aggregates": {
            "allItemsSha256": _digest_items(archive_items),
            "historicalResultsSha256": _digest_items(result_items),
            "referencedCapsuleFilesSha256": _digest_items(capsule_items),
            "referencedCapsuleRefsSha256": _sha256(
                "".join(f"capsule:v1:{capsule_id}\n" for capsule_id in refs).encode("utf-8")
            ),
        },
    }
    content["manifestSha256"] = _sha256(_canonical_json(content))
    return content


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    payload = _canonical_json(manifest) + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _safe_relative(value: object) -> Path:
    if not isinstance(value, str):
        raise ArchiveError("manifest relative path is invalid")
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts or "." in relative.parts:
        raise ArchiveError("manifest relative path escapes archive")
    return relative


def _verify_manifest(
    archive_root: Path,
    manifest: dict[str, Any],
    *,
    expected_archive_name: str | None = None,
) -> dict[str, Any]:
    if manifest.get("schemaVersion") != ARCHIVE_SCHEMA_VERSION:
        raise ArchiveError("archive manifest schema is invalid")
    if manifest.get("disposition") != "STATIC_ARCHIVE" or manifest.get("retentionDisposalAuthorized") is not False:
        raise ArchiveError("archive disposition is invalid")
    identity = dict(manifest)
    recorded_digest = identity.pop("manifestSha256", None)
    if not isinstance(recorded_digest, str) or _sha256(_canonical_json(identity)) != recorded_digest:
        raise ArchiveError("archive manifest identity differs")
    if (expected_archive_name or archive_root.name) != f"phase8-static-archive-v1-{recorded_digest}":
        raise ArchiveError("archive directory name does not bind manifest identity")
    try:
        root_mode = stat.S_IMODE(archive_root.lstat().st_mode)
    except OSError as exc:
        raise ArchiveError(f"cannot stat archive root: {exc}") from exc
    if root_mode != 0o500:
        raise ArchiveError("archive root mode is not 0500")
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ArchiveError("archive manifest items are invalid")
    expected_paths: set[Path] = {Path(MANIFEST_NAME)}
    expected_directories: set[Path] = {Path(".")}
    seen_paths: set[Path] = set()
    result_items: list[dict[str, Any]] = []
    capsule_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {
            "sourceClass", "relativePath", "size", "sha256", "originalMode"
        }:
            raise ArchiveError("archive manifest item fields are invalid")
        relative = _safe_relative(item["relativePath"])
        if relative in seen_paths:
            raise ArchiveError("archive manifest contains duplicate paths")
        seen_paths.add(relative)
        expected_paths.add(relative)
        if item["sourceClass"] not in {RESULT_CLASS, CAPSULE_CLASS}:
            raise ArchiveError("archive manifest source class is invalid")
        if item["sourceClass"] == RESULT_CLASS:
            if relative.parts[0] != "implementation-results":
                raise ArchiveError("historical result archive path is invalid")
            result_items.append(item)
        else:
            if len(relative.parts) < 4 or relative.parts[:2] != ("baseline-capsules", "capsules"):
                raise ArchiveError("referenced capsule archive path is invalid")
            capsule_items.append(item)
        for parent in relative.parents:
            expected_directories.add(parent)
        if not isinstance(item["size"], int) or item["size"] < 0:
            raise ArchiveError("archive manifest size is invalid")
        if not isinstance(item["sha256"], str) or len(item["sha256"]) != 64:
            raise ArchiveError("archive manifest digest is invalid")
        if not isinstance(item["originalMode"], int) or not 0 <= item["originalMode"] <= 0o777:
            raise ArchiveError("archive manifest mode is invalid")
        path = archive_root / relative
        try:
            observed = path.lstat()
        except OSError as exc:
            raise ArchiveError(f"archive item is missing: {relative}: {exc}") from exc
        if not stat.S_ISREG(observed.st_mode) or stat.S_IMODE(observed.st_mode) != 0o400:
            raise ArchiveError(f"archive item mode/type is invalid: {relative}")
        with path.open("rb") as handle:
            payload = handle.read()
        if len(payload) != item["size"] or _sha256(payload) != item["sha256"]:
            raise ArchiveError(f"archive item bytes differ: {relative}")
    refs = manifest.get("referencedCapsuleRefs")
    if not isinstance(refs, list) or refs != sorted(set(refs)):
        raise ArchiveError("referenced capsule refs are invalid")
    capsule_ids: set[str] = set()
    for capsule_ref in refs:
        if not isinstance(capsule_ref, str) or not capsule_ref.startswith("capsule:v1:"):
            raise ArchiveError("referenced capsule ref is invalid")
        capsule_id = capsule_ref.removeprefix("capsule:v1:")
        if len(capsule_id) != 32 or any(character not in "0123456789abcdef" for character in capsule_id):
            raise ArchiveError("referenced capsule ref is malformed")
        capsule_ids.add(capsule_id)
    if any(Path(item["relativePath"]).parts[2] not in capsule_ids for item in capsule_items):
        raise ArchiveError("referenced capsule item has no matching ref")
    actual_paths: set[Path] = set()
    actual_directories: set[Path] = {Path(".")}
    for directory, directories, files in os.walk(archive_root, followlinks=False):
        directory_path = Path(directory)
        if directory_path != archive_root:
            mode = directory_path.lstat().st_mode
            if not stat.S_ISDIR(mode) or stat.S_IMODE(mode) != 0o500:
                raise ArchiveError(f"archive directory mode/type is invalid: {directory_path}")
            actual_directories.add(directory_path.relative_to(archive_root))
        for name in directories:
            child = directory_path / name
            if child.is_symlink():
                raise ArchiveError(f"archive contains symlink directory: {child}")
        for name in files:
            child = directory_path / name
            if child.is_symlink() or not stat.S_ISREG(child.lstat().st_mode):
                raise ArchiveError(f"archive contains non-regular file: {child}")
            actual_paths.add(child.relative_to(archive_root))
    if actual_paths != expected_paths:
        raise ArchiveError("archive contains unexpected or missing files")
    if actual_directories != expected_directories:
        raise ArchiveError("archive contains unexpected or missing directories")
    if _digest_items(items) != manifest["aggregates"].get("allItemsSha256"):
        raise ArchiveError("archive aggregate digest differs")
    if _digest_items(result_items) != manifest["aggregates"].get("historicalResultsSha256"):
        raise ArchiveError("historical result aggregate digest differs")
    if _digest_items(capsule_items) != manifest["aggregates"].get("referencedCapsuleFilesSha256"):
        raise ArchiveError("referenced capsule aggregate digest differs")
    if _sha256("".join(f"{capsule_ref}\n" for capsule_ref in refs).encode("utf-8")) != manifest["aggregates"].get("referencedCapsuleRefsSha256"):
        raise ArchiveError("referenced capsule ref digest differs")
    if manifest["counts"] != {
        "historicalResults": len(result_items),
        "referencedCapsules": len(refs),
        "files": len(items),
        "bytes": sum(item["size"] for item in items),
    }:
        raise ArchiveError("archive counts differ")
    return {
        "archivePath": str(archive_root),
        "manifestSha256": recorded_digest,
        "counts": manifest["counts"],
        "aggregates": manifest["aggregates"],
    }


def verify_archive(archive_path: str | Path) -> dict[str, Any]:
    archive_root = _canonical_root(archive_path)
    _require_directory(archive_root, "archive root")
    manifest_path = archive_root / MANIFEST_NAME
    try:
        if not stat.S_ISREG(manifest_path.lstat().st_mode) or stat.S_IMODE(manifest_path.lstat().st_mode) != 0o400:
            raise ArchiveError("archive manifest mode/type is invalid")
        raw_manifest = manifest_path.read_bytes()
        manifest = json.loads(raw_manifest.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveError(f"cannot read archive manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ArchiveError("archive manifest is not an object")
    if raw_manifest != _canonical_json(manifest) + b"\n":
        raise ArchiveError("archive manifest bytes are not canonical")
    return _verify_manifest(archive_root, manifest)


def _seal_tree(root: Path) -> None:
    directories: list[Path] = []
    for directory, _subdirectories, files in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        directories.append(directory_path)
        for name in files:
            path = directory_path / name
            os.chmod(path, 0o400)
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
    for directory in reversed(directories):
        os.chmod(directory, 0o500)
        _fsync_directory(directory)


def create_archive(
    results_root: str | Path,
    capsule_store_root: str | Path,
    archive_container: str | Path,
) -> dict[str, Any]:
    results = _canonical_root(results_root)
    capsule_store = _canonical_root(capsule_store_root)
    container = Path(archive_container).expanduser().absolute()
    active_roots = (results.parent, capsule_store.parent)
    if any(_is_inside(container, active_root) for active_root in active_roots):
        raise ArchiveError("archive container must be outside the active state root")
    items, refs = _source_items(results, capsule_store)
    if container.exists():
        _require_directory(container, "archive container")
        if stat.S_IMODE(container.lstat().st_mode) != 0o700:
            raise ArchiveError("archive container must have mode 0700")
    else:
        container.mkdir(mode=0o700, parents=True)
        _fsync_directory(container.parent)

    staging = container / f".staging-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        for item in items:
            source = Path(item["sourcePath"])
            destination = staging / item["relativePath"]
            copied, digest, mode = _copy_source(source, destination)
            if copied != item["size"] or mode != item["originalMode"]:
                raise ArchiveError(f"source identity differs during copy: {source}")
            item["sha256"] = digest
        current_items, current_refs = _source_items(results, capsule_store)
        if _source_shape(current_items) != _source_shape(items) or current_refs != refs:
            raise ArchiveError("source item set changed during archive staging")
        _validate_staging_against_source(staging, items)
        manifest = _manifest_content(items, refs)
        destination = container / f"phase8-static-archive-v1-{manifest['manifestSha256']}"
        if destination.exists():
            raise ArchiveError(f"archive destination already exists: {destination}")
        _write_manifest(staging / MANIFEST_NAME, manifest)
        _fsync_directory(staging)
        _seal_tree(staging)
        _verify_manifest(staging, manifest, expected_archive_name=destination.name)
        os.rename(staging, destination)
        _fsync_directory(container)
        result = verify_archive(destination)
        return result
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--results-root", required=True)
    create.add_argument("--capsule-store-root", required=True)
    create.add_argument("--archive-container", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--archive-path", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create_archive(args.results_root, args.capsule_store_root, args.archive_container)
        else:
            result = verify_archive(args.archive_path)
    except ArchiveError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
