#!/usr/bin/env python3
"""Create or validate one external planning workspace for a planning flow."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path
from typing import Sequence


DEFAULT_PLANNING_ROOT = Path("/tmp/opencode/planning")
WORK_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_ID_PATTERN = re.compile(r"^task-[a-f0-9]{32}$")


class WorkspaceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _lstat_directory(path: Path, code: str) -> os.stat_result:
    try:
        details = path.lstat()
    except OSError as exc:
        raise WorkspaceError(code, f"cannot inspect {path}: {exc}") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise WorkspaceError(code, f"must be a non-symlink directory: {path}")
    return details


def _validate_owned_directory(path: Path, code: str, *, writable: bool) -> None:
    details = _lstat_directory(path, code)
    if details.st_uid != os.geteuid():
        raise WorkspaceError(code, f"directory is not owned by the current user: {path}")
    if details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise WorkspaceError(code, f"directory has unsafe group/other write permission: {path}")
    if writable and not os.access(path, os.W_OK | os.X_OK):
        raise WorkspaceError(code, f"directory is not writable and searchable: {path}")


def _mkdir_exclusive(path: Path, code: str) -> None:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise WorkspaceError(code, f"refusing to adopt existing path: {path}") from exc
    except OSError as exc:
        raise WorkspaceError(code, f"cannot create {path}: {exc}") from exc
    _validate_owned_directory(path, code, writable=True)
    try:
        os.chmod(path, 0o700)
    except OSError as exc:
        raise WorkspaceError(code, f"cannot set owner-only permission on {path}: {exc}") from exc


def _ensure_default_root(root: Path) -> Path:
    if not root.is_absolute() or len(root.parts) < 3:
        raise WorkspaceError("INVALID_DEFAULT_ROOT", "default planning root identity is invalid")
    current = root.parent.parent
    _lstat_directory(current, "INVALID_DEFAULT_ROOT")
    if current.resolve(strict=True) != current:
        raise WorkspaceError("INVALID_DEFAULT_ROOT", "default planning root base must be canonical")
    for name in (root.parent.name, root.name):
        child = current / name
        if child.exists() or child.is_symlink():
            _validate_owned_directory(child, "UNSAFE_MANAGED_ANCESTOR", writable=True)
        else:
            _mkdir_exclusive(child, "UNSAFE_MANAGED_ANCESTOR")
        current = child
    canonical = root.resolve(strict=True)
    if canonical != root:
        raise WorkspaceError("UNSAFE_MANAGED_ANCESTOR", "default planning root is not canonical")
    return canonical


def _canonical_project_root(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise WorkspaceError("INVALID_PROJECT_ROOT", "project root must be absolute")
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise WorkspaceError("INVALID_PROJECT_ROOT", f"cannot resolve project root: {exc}") from exc
    if canonical != path or not canonical.is_dir():
        raise WorkspaceError("INVALID_PROJECT_ROOT", "project root must be one canonical directory")
    return canonical


def _future_project_root(raw: str) -> Path:
    if not raw or raw != os.path.normpath(raw):
        raise WorkspaceError(
            "INVALID_FUTURE_PROJECT_ROOT",
            "future project root must use one normalized absolute lexical path",
        )
    path = Path(raw)
    if not path.is_absolute():
        raise WorkspaceError("INVALID_FUTURE_PROJECT_ROOT", "future project root must be absolute")
    if path.exists() or path.is_symlink():
        raise WorkspaceError(
            "FUTURE_PROJECT_ROOT_EXISTS",
            "future project root already exists; use strict --project-root validation",
        )

    existing = path.parent
    while not existing.exists() and not existing.is_symlink():
        if existing == existing.parent:
            raise WorkspaceError("INVALID_FUTURE_PROJECT_ROOT", "future project root has no existing ancestor")
        existing = existing.parent
    details = _lstat_directory(existing, "UNSAFE_FUTURE_PROJECT_ANCESTOR")
    if stat.S_ISLNK(details.st_mode) or existing.resolve(strict=True) != existing:
        raise WorkspaceError(
            "UNSAFE_FUTURE_PROJECT_ANCESTOR",
            "future project root must have a canonical non-symlink existing ancestor",
        )
    if details.st_uid != os.geteuid() or details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise WorkspaceError(
            "UNSAFE_FUTURE_PROJECT_ANCESTOR",
            "future project root ancestor must be current-user-owned and not group/world writable",
        )
    if not os.access(existing, os.W_OK | os.X_OK):
        raise WorkspaceError(
            "UNSAFE_FUTURE_PROJECT_ANCESTOR",
            "future project root ancestor is not writable and searchable",
        )
    return path


def _validate_slug(slug: str) -> None:
    if not WORK_SLUG_PATTERN.fullmatch(slug):
        raise WorkspaceError("INVALID_WORK_SLUG", "work slug must be one lowercase kebab-case segment")


def _require_disjoint(workspace: Path, project_root: Path) -> None:
    if workspace == project_root or workspace.is_relative_to(project_root) or project_root.is_relative_to(workspace):
        raise WorkspaceError(
            "WORKSPACE_PROJECT_OVERLAP",
            "planning workspace and product project root must be disjoint directory trees",
        )


def _prepare_supplied(raw_workspace: str, project_root: Path) -> tuple[Path, bool]:
    supplied = Path(raw_workspace).expanduser()
    if not supplied.is_absolute():
        raise WorkspaceError("INVALID_WORKSPACE", "supplied planning workspace must be absolute")
    if supplied.exists() or supplied.is_symlink():
        _validate_owned_directory(supplied, "UNSAFE_WORKSPACE", writable=True)
        canonical = supplied.resolve(strict=True)
        if canonical != supplied:
            raise WorkspaceError("UNSAFE_WORKSPACE", "supplied planning workspace must be canonical")
        created = False
    else:
        parent = supplied.parent
        _validate_owned_directory(parent, "UNSAFE_WORKSPACE_PARENT", writable=True)
        canonical_parent = parent.resolve(strict=True)
        if canonical_parent != parent:
            raise WorkspaceError("UNSAFE_WORKSPACE_PARENT", "supplied workspace parent must be canonical")
        _require_disjoint(supplied, project_root)
        _mkdir_exclusive(supplied, "WORKSPACE_CREATE_FAILED")
        canonical = supplied.resolve(strict=True)
        created = True
    _require_disjoint(canonical, project_root)
    return canonical, created


def _validate_default_workspace_reuse(workspace: Path, work_slug: str) -> str | None:
    if not workspace.is_relative_to(DEFAULT_PLANNING_ROOT):
        return None
    relative = workspace.relative_to(DEFAULT_PLANNING_ROOT)
    if len(relative.parts) != 2:
        raise WorkspaceError(
            "INVALID_DEFAULT_WORKSPACE",
            "path below the default planning root is not an exact generated workspace",
        )
    task_id, generated_slug = relative.parts
    if not TASK_ID_PATTERN.fullmatch(task_id) or generated_slug != work_slug:
        raise WorkspaceError(
            "INVALID_DEFAULT_WORKSPACE",
            "generated workspace task identity or work slug does not match",
        )
    root = _ensure_default_root(DEFAULT_PLANNING_ROOT)
    task_directory = root / task_id
    _validate_owned_directory(task_directory, "UNSAFE_TASK_DIRECTORY", writable=True)
    _validate_owned_directory(workspace, "UNSAFE_WORKSPACE", writable=True)
    if stat.S_IMODE(task_directory.stat().st_mode) != 0o700:
        raise WorkspaceError("UNSAFE_TASK_DIRECTORY", "generated task directory mode must be 0700")
    if stat.S_IMODE(workspace.stat().st_mode) != 0o700:
        raise WorkspaceError("UNSAFE_WORKSPACE", "generated planning workspace mode must be 0700")
    if task_directory.resolve(strict=True) != task_directory or workspace.resolve(strict=True) != workspace:
        raise WorkspaceError("UNSAFE_WORKSPACE", "default workspace chain must retain canonical identity")
    if workspace.parent != task_directory:
        raise WorkspaceError("WORKSPACE_ESCAPE", "default workspace escaped its task directory")
    return task_id


def _prepare(project: Path, work_slug: str, workspace: str | None, *, future_root: bool) -> dict[str, object]:
    _validate_slug(work_slug)
    if workspace is not None:
        canonical, created = _prepare_supplied(workspace, project)
        task_id = _validate_default_workspace_reuse(canonical, work_slug)
        result: dict[str, object] = {
            "planningWorkspace": str(canonical),
            "workSlug": work_slug,
            "taskId": task_id,
            "defaultWorkspace": task_id is not None,
            "created": created,
        }
        if future_root:
            result.update({"projectRoot": None, "futureProjectRoot": str(project), "rootReady": False})
        else:
            result["projectRoot"] = str(project)
        return result

    root = _ensure_default_root(DEFAULT_PLANNING_ROOT)
    _require_disjoint(root, project)
    task_id = f"task-{uuid.uuid4().hex}"
    task_directory = root / task_id
    _mkdir_exclusive(task_directory, "TASK_DIRECTORY_COLLISION")
    workspace_path = task_directory / work_slug
    _mkdir_exclusive(workspace_path, "WORKSPACE_CREATE_FAILED")
    canonical = workspace_path.resolve(strict=True)
    if canonical.parent != task_directory.resolve(strict=True):
        raise WorkspaceError("WORKSPACE_ESCAPE", "work directory escaped the exclusive task directory")
    _require_disjoint(canonical, project)
    result = {
        "planningWorkspace": str(canonical),
        "workSlug": work_slug,
        "taskId": task_id,
        "defaultWorkspace": True,
        "created": True,
    }
    if future_root:
        result.update({"projectRoot": None, "futureProjectRoot": str(project), "rootReady": False})
    else:
        result["projectRoot"] = str(project)
    return result


def prepare(project_root: str, work_slug: str, workspace: str | None = None) -> dict[str, object]:
    return _prepare(_canonical_project_root(project_root), work_slug, workspace, future_root=False)


def prepare_future_root(future_project_root: str, work_slug: str, workspace: str | None = None) -> dict[str, object]:
    return _prepare(_future_project_root(future_project_root), work_slug, workspace, future_root=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepare", choices=["prepare"])
    roots = parser.add_mutually_exclusive_group(required=True)
    roots.add_argument("--project-root")
    roots.add_argument("--future-project-root")
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--workspace")
    args = parser.parse_args(argv)
    try:
        if args.future_project_root is not None:
            result = prepare_future_root(args.future_project_root, args.work_slug, args.workspace)
        else:
            result = prepare(args.project_root, args.work_slug, args.workspace)
    except WorkspaceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
