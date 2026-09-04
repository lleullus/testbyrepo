#!/usr/bin/env python3
"""Prepare one canonical project-local repository-investigation artifact path."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from iis_path_contract import (  # noqa: E402
    PathContractError,
    canonical_project_root,
    require_canonical_owned_directory,
    require_work_slug,
)


INVESTIGATION_FILE = re.compile(r"^INV-(\d{3})\.md$")


class InvestigationWorkspaceError(RuntimeError):
    pass


def _ensure_child(parent: Path, name: str) -> Path:
    child = parent / name
    if child.exists() or child.is_symlink():
        try:
            details = child.lstat()
        except OSError as exc:
            raise InvestigationWorkspaceError(f"cannot inspect {child}: {exc}") from exc
        if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
            raise InvestigationWorkspaceError(f"must be a non-symlink directory: {child}")
        if details.st_uid != os.geteuid():
            raise InvestigationWorkspaceError(f"directory is not owned by the current user: {child}")
        if details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise InvestigationWorkspaceError(
                f"directory has unsafe group/other write permission: {child}"
            )
    else:
        try:
            child.mkdir(mode=0o755)
            child.chmod(0o755)
        except OSError as exc:
            raise InvestigationWorkspaceError(f"cannot create investigation directory {child}: {exc}") from exc

    try:
        return require_canonical_owned_directory(child, writable=True)
    except PathContractError as exc:
        raise InvestigationWorkspaceError(str(exc)) from exc


def _next_revision(workspace: Path) -> str:
    ordinals: list[int] = []
    for path in workspace.iterdir():
        match = INVESTIGATION_FILE.fullmatch(path.name)
        if match is None:
            continue
        try:
            details = path.lstat()
        except OSError as exc:
            raise InvestigationWorkspaceError(f"cannot inspect {path}: {exc}") from exc
        if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
            raise InvestigationWorkspaceError(f"investigation revision must be a regular file: {path}")
        ordinals.append(int(match.group(1)))

    ordinal = max(ordinals, default=0) + 1
    if ordinal > 999:
        raise InvestigationWorkspaceError("investigation revision limit exceeded (INV-999)")
    return f"INV-{ordinal:03d}"


def prepare(project_root: str, investigation_slug: str) -> dict[str, str]:
    try:
        project = canonical_project_root(project_root, writable=True)
        require_work_slug(investigation_slug)
    except PathContractError as exc:
        raise InvestigationWorkspaceError(str(exc)) from exc

    # docs/ may be shared with product documentation. Never repair or loosen its
    # permissions as a side effect of repository investigation.
    docs = _ensure_child(project, "docs")
    investigation_root = _ensure_child(docs, "investigation")
    workspace = _ensure_child(investigation_root, investigation_slug)

    revision = _next_revision(workspace)
    artifact = workspace / f"{revision}.md"
    if artifact.exists() or artifact.is_symlink():
        raise InvestigationWorkspaceError(f"next investigation artifact already exists: {artifact}")

    return {
        "projectRoot": str(project),
        "investigationRoot": str(investigation_root),
        "investigationWorkspace": str(workspace),
        "investigationRevision": revision,
        "artifactPath": str(artifact),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--investigation-slug", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.project_root, args.investigation_slug)
    except (OSError, InvestigationWorkspaceError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
