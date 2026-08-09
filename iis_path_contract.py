"""Shared canonical path rules for project-local IIS planning artifacts."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path


WORK_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PathContractError(RuntimeError):
    pass


def require_work_slug(value: str) -> None:
    if not WORK_SLUG_PATTERN.fullmatch(value):
        raise PathContractError("work slug must be one lowercase kebab-case segment")


def require_owned_directory(path: Path, *, writable: bool) -> None:
    try:
        details = path.lstat()
    except OSError as exc:
        raise PathContractError(f"cannot inspect {path}: {exc}") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise PathContractError(f"must be a non-symlink directory: {path}")
    if details.st_uid != os.geteuid():
        raise PathContractError(f"directory is not owned by the current user: {path}")
    if details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise PathContractError(f"directory has unsafe group/other write permission: {path}")
    if writable and not os.access(path, os.W_OK | os.X_OK):
        raise PathContractError(f"directory is not writable and searchable: {path}")


def require_canonical_owned_directory(path: Path, *, writable: bool) -> Path:
    require_owned_directory(path, writable=writable)
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise PathContractError(f"cannot resolve directory {path}: {exc}") from exc
    if canonical != path:
        raise PathContractError(f"directory path must be canonical: {path}")
    return canonical


def canonical_project_root(raw: str, *, writable: bool) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        raise PathContractError("project root must be absolute")
    return require_canonical_owned_directory(path, writable=writable)


def require_canonical_regular_file(path: Path) -> Path:
    if not path.is_absolute():
        raise PathContractError(f"file path must be absolute: {path}")
    try:
        details = path.lstat()
    except OSError as exc:
        raise PathContractError(f"cannot inspect {path}: {exc}") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise PathContractError(f"must be a non-symlink regular file: {path}")
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise PathContractError(f"cannot resolve file {path}: {exc}") from exc
    if canonical != path:
        raise PathContractError(f"file path must be canonical: {path}")
    if not os.access(path, os.R_OK):
        raise PathContractError(f"file is not readable: {path}")
    return canonical
