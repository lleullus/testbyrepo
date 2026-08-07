#!/usr/bin/env python3
"""Prepare the canonical project-local IIS planning root."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Sequence


WORK_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KINDS = {"work": "work", "initiative": "initiatives"}


class WorkspaceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _owned_directory(path: Path, code: str, *, writable: bool) -> None:
    try:
        details = path.lstat()
    except OSError as exc:
        raise WorkspaceError(code, f"cannot inspect {path}: {exc}") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise WorkspaceError(code, f"must be a non-symlink directory: {path}")
    if details.st_uid != os.geteuid():
        raise WorkspaceError(code, f"directory is not owned by the current user: {path}")
    if details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise WorkspaceError(code, f"directory has unsafe group/other write permission: {path}")
    if writable and not os.access(path, os.W_OK | os.X_OK):
        raise WorkspaceError(code, f"directory is not writable and searchable: {path}")


def _canonical_project_root(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise WorkspaceError("INVALID_PROJECT_ROOT", "project root must be absolute")
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise WorkspaceError("INVALID_PROJECT_ROOT", f"cannot resolve project root: {exc}") from exc
    if canonical != path or not canonical.is_dir():
        raise WorkspaceError("INVALID_PROJECT_ROOT", "project root must be one existing canonical directory")
    _owned_directory(canonical, "INVALID_PROJECT_ROOT", writable=True)
    return canonical


def _ensure_child(parent: Path, name: str) -> Path:
    child = parent / name
    if child.exists() or child.is_symlink():
        _owned_directory(child, "UNSAFE_PLANNING_PATH", writable=True)
        if child.resolve(strict=True) != child:
            raise WorkspaceError("UNSAFE_PLANNING_PATH", f"path must remain canonical: {child}")
        return child
    try:
        child.mkdir(mode=0o755)
    except OSError as exc:
        raise WorkspaceError("PLANNING_ROOT_CREATE_FAILED", f"cannot create {child}: {exc}") from exc
    _owned_directory(child, "UNSAFE_PLANNING_PATH", writable=True)
    return child


def prepare(project_root: str, work_slug: str, kind: str = "work") -> dict[str, object]:
    if not WORK_SLUG_PATTERN.fullmatch(work_slug):
        raise WorkspaceError("INVALID_WORK_SLUG", "work slug must be one lowercase kebab-case segment")
    if kind not in KINDS:
        raise WorkspaceError("INVALID_PLANNING_KIND", "kind must be `work` or `initiative`")

    project = _canonical_project_root(project_root)
    docs = _ensure_child(project, "docs")
    planning = _ensure_child(docs, "planning")
    behavior = _ensure_child(planning, "behavior")
    container = _ensure_child(planning, KINDS[kind])
    artifact_workspace = _ensure_child(container, work_slug)

    return {
        "projectRoot": str(project),
        "planningRoot": str(planning),
        "behaviorRoot": str(behavior),
        "artifactWorkspace": str(artifact_workspace),
        "workSlug": work_slug,
        "kind": kind,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepare", choices=["prepare"])
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--kind", choices=sorted(KINDS), default="work")
    args = parser.parse_args(argv)
    try:
        result = prepare(args.project_root, args.work_slug, args.kind)
    except WorkspaceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
