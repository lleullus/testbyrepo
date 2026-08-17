#!/usr/bin/env python3
"""Synchronize the canonical IIS Adaptive Planning skill into the live Codex install."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = ROOT / "iis-adaptive-planning"
INSTALLED_DIR = Path.home() / ".codex" / "skills" / "iis-adaptive-planning"

ALLOWED_TOP_LEVEL = {"SKILL.md", "agents", "references", "templates"}


def _canonical_files() -> tuple[Path, ...]:
    if not CANONICAL_DIR.is_dir() or CANONICAL_DIR.is_symlink():
        raise RuntimeError(f"invalid canonical Adaptive skill directory: {CANONICAL_DIR}")

    unexpected = {p.name for p in CANONICAL_DIR.iterdir()} - ALLOWED_TOP_LEVEL
    if unexpected:
        raise RuntimeError(f"unexpected Adaptive skill entries: {sorted(unexpected)}")

    files: list[Path] = []
    for path in CANONICAL_DIR.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"symlink is not allowed in Adaptive skill payload: {path}")
        if path.is_file():
            files.append(path.relative_to(CANONICAL_DIR))
    return tuple(sorted(files, key=lambda p: p.as_posix()))


def _installed_files() -> tuple[Path, ...]:
    if not INSTALLED_DIR.exists():
        return ()
    if not INSTALLED_DIR.is_dir() or INSTALLED_DIR.is_symlink():
        raise RuntimeError(f"invalid installed Adaptive skill directory: {INSTALLED_DIR}")

    files: list[Path] = []
    for path in INSTALLED_DIR.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"symlink is not allowed in installed Adaptive skill: {path}")
        if path.is_file():
            files.append(path.relative_to(INSTALLED_DIR))
    return tuple(sorted(files, key=lambda p: p.as_posix()))


def _same() -> bool:
    canonical = _canonical_files()
    if canonical != _installed_files():
        return False
    return all(
        (CANONICAL_DIR / relative).read_bytes()
        == (INSTALLED_DIR / relative).read_bytes()
        for relative in canonical
    )


def _atomic_copy(source: Path, target: Path) -> None:
    payload = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise RuntimeError(f"refusing to replace symlinked install target: {target}")

    fd, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _remove_stale_files(canonical: set[Path]) -> None:
    if not INSTALLED_DIR.exists():
        return

    for relative in _installed_files():
        if relative not in canonical:
            (INSTALLED_DIR / relative).unlink()

    directories = sorted(
        (p for p in INSTALLED_DIR.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass


def sync() -> None:
    canonical_files = _canonical_files()
    canonical_set = set(canonical_files)

    if INSTALLED_DIR.exists() and INSTALLED_DIR.is_symlink():
        raise RuntimeError(f"refusing to synchronize through symlink: {INSTALLED_DIR}")
    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)

    _remove_stale_files(canonical_set)
    for relative in canonical_files:
        _atomic_copy(CANONICAL_DIR / relative, INSTALLED_DIR / relative)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        if _same():
            print("SYNCED")
            return 0
        print("DRIFT")
        return 1

    sync()
    if not _same():
        raise RuntimeError("installed IIS Adaptive Planning skill does not match canonical source after sync")
    print(f"SYNCED: {INSTALLED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
