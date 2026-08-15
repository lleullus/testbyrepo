#!/usr/bin/env python3
"""Prepare the canonical project-local Scope Shaper artifact directories."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from iis_path_contract import (  # noqa: E402
    PathContractError,
    canonical_project_root,
    require_canonical_owned_directory,
    require_work_slug,
)


class ScopeWorkspaceError(RuntimeError):
    pass


def _safe_mode(path: Path) -> bool:
    mode = path.lstat().st_mode
    return not bool(mode & (stat.S_IWGRP | stat.S_IWOTH))


def _ensure_child(parent: Path, name: str, *, repair_owned_permissions: bool) -> Path:
    child = parent / name
    if child.exists() or child.is_symlink():
        try:
            details = child.lstat()
        except OSError as exc:
            raise ScopeWorkspaceError(f"cannot inspect {child}: {exc}") from exc
        if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
            raise ScopeWorkspaceError(f"must be a non-symlink directory: {child}")
        if details.st_uid != os.geteuid():
            raise ScopeWorkspaceError(f"directory is not owned by the current user: {child}")
        if not _safe_mode(child):
            if not repair_owned_permissions:
                raise ScopeWorkspaceError(f"directory has unsafe group/other write permission: {child}")
            try:
                child.chmod(0o755)
            except OSError as exc:
                raise ScopeWorkspaceError(f"cannot repair directory permissions for {child}: {exc}") from exc
    else:
        try:
            child.mkdir(mode=0o755)
            child.chmod(0o755)
        except OSError as exc:
            raise ScopeWorkspaceError(f"cannot create safe Scope directory {child}: {exc}") from exc

    try:
        return require_canonical_owned_directory(child, writable=True)
    except PathContractError as exc:
        raise ScopeWorkspaceError(str(exc)) from exc


def prepare(project_root: str, work_slug: str, *, repair_owned_permissions: bool = False) -> dict[str, str]:
    try:
        project = canonical_project_root(project_root, writable=True)
        require_work_slug(work_slug)
    except PathContractError as exc:
        raise ScopeWorkspaceError(str(exc)) from exc

    # docs/ and planning/ may be shared project directories. Never change their
    # permissions as a side effect of Scope-specific maintenance.
    docs = _ensure_child(project, "docs", repair_owned_permissions=False)
    planning = _ensure_child(docs, "planning", repair_owned_permissions=False)

    # Everything below scope-shaping/ is IIS Scope artifact space. An explicit
    # repair option may normalize only these owned directories.
    scope_root = _ensure_child(planning, "scope-shaping", repair_owned_permissions=repair_owned_permissions)
    work = _ensure_child(scope_root, work_slug, repair_owned_permissions=repair_owned_permissions)
    packages = _ensure_child(work, "work-packages", repair_owned_permissions=repair_owned_permissions)
    revisions = _ensure_child(work, "revisions", repair_owned_permissions=repair_owned_permissions)
    increments = _ensure_child(work, "increments", repair_owned_permissions=repair_owned_permissions)
    legacy_import = _ensure_child(work, "legacy-import", repair_owned_permissions=repair_owned_permissions)
    legacy_packages = _ensure_child(
        legacy_import,
        "work-packages",
        repair_owned_permissions=repair_owned_permissions,
    )
    return {
        "projectRoot": str(project),
        "scopeRoot": str(scope_root),
        "scopeWorkspace": str(work),
        "workPackages": str(packages),
        "revisions": str(revisions),
        "increments": str(increments),
        "legacyImport": str(legacy_import),
        "legacyWorkPackages": str(legacy_packages),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--repair-owned-permissions", action="store_true")
    args = parser.parse_args()
    try:
        result = prepare(
            args.project_root,
            args.work_slug,
            repair_owned_permissions=args.repair_owned_permissions,
        )
    except (OSError, ScopeWorkspaceError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
