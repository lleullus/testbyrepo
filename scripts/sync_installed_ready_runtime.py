#!/usr/bin/env python3
"""Synchronize the Ready Ticket OMP runtime extension into the live OMP extension directory."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = ROOT / "delivery-runtime" / "ready-ticket-implement"
CANONICAL_SKILL_DIR = ROOT / "companion-skills" / "ready-ticket-implement"
CANONICAL_VERIFY_SKILL_DIR = ROOT / "companion-skills" / "ready-ticket-verify"
CANONICAL_PROBE_SKILL_DIR = ROOT / "companion-skills" / "ready-ticket-heuristic-probe"
INSTALLED_SKILL_DIR = Path(
    os.environ.get(
        "IIS_READY_SKILL_INSTALL_DIR",
        str(Path.home() / ".codex" / "skills" / "ready-ticket-implement"),
    )
).expanduser()
INSTALLED_VERIFY_SKILL_DIR = Path(
    os.environ.get(
        "IIS_READY_VERIFY_SKILL_INSTALL_DIR",
        str(Path.home() / ".codex" / "skills" / "ready-ticket-verify"),
    )
).expanduser()
INSTALLED_PROBE_SKILL_DIR = Path(
    os.environ.get(
        "IIS_READY_PROBE_SKILL_INSTALL_DIR",
        str(Path.home() / ".codex" / "skills" / "ready-ticket-heuristic-probe"),
    )
).expanduser()
INSTALLED_DIR = Path(
    os.environ.get(
        "IIS_READY_RUNTIME_INSTALL_DIR",
        str(Path.home() / ".omp" / "agent" / "extensions" / "ready-ticket-implement-runtime"),
    )
).expanduser()

TOP_LEVEL_FILES = {"index.js", "package.json", "README.md", "CLICK-PROVENANCE.md"}
SKILL_INSTALLS = (
    (
        CANONICAL_SKILL_DIR,
        INSTALLED_SKILL_DIR,
        (Path("SKILL.md"), Path("agents/openai.yaml"), Path("references/implement.md")),
    ),
    (
        CANONICAL_VERIFY_SKILL_DIR,
        INSTALLED_VERIFY_SKILL_DIR,
        (Path("SKILL.md"), Path("agents/openai.yaml"), Path("references/verify.md")),
    ),
    (
        CANONICAL_PROBE_SKILL_DIR,
        INSTALLED_PROBE_SKILL_DIR,
        (Path("SKILL.md"), Path("agents/openai.yaml"), Path("references/probe.md")),
    ),
)


def _skill_same() -> bool:
    for canonical_dir, installed_dir, files in SKILL_INSTALLS:
        for relative in files:
            canonical = canonical_dir / relative
            installed = installed_dir / relative
            if not canonical.is_file() or not installed.is_file():
                return False
            if canonical.read_bytes() != installed.read_bytes():
                return False
    return True


def _canonical_files() -> tuple[Path, ...]:
    if not CANONICAL_DIR.is_dir() or CANONICAL_DIR.is_symlink():
        raise RuntimeError(f"invalid canonical Ready runtime directory: {CANONICAL_DIR}")
    files = [Path(name) for name in sorted(TOP_LEVEL_FILES)]
    files.extend(sorted((path.relative_to(CANONICAL_DIR) for path in (CANONICAL_DIR / "src").glob("*.js")), key=lambda p: p.as_posix()))
    for relative in files:
        target = CANONICAL_DIR / relative
        if not target.is_file() or target.is_symlink():
            raise RuntimeError(f"invalid canonical Ready runtime file: {target}")
    return tuple(files)


def _installed_files() -> tuple[Path, ...]:
    if not INSTALLED_DIR.exists():
        return ()
    if not INSTALLED_DIR.is_dir() or INSTALLED_DIR.is_symlink():
        raise RuntimeError(f"invalid installed Ready runtime directory: {INSTALLED_DIR}")
    files = [path.relative_to(INSTALLED_DIR) for path in INSTALLED_DIR.rglob("*") if path.is_file()]
    if any((INSTALLED_DIR / relative).is_symlink() for relative in files):
        raise RuntimeError(f"symlinked file is not allowed in installed Ready runtime: {INSTALLED_DIR}")
    return tuple(sorted(files, key=lambda p: p.as_posix()))


def _same() -> bool:
    canonical = _canonical_files()
    if canonical != _installed_files():
        return False
    return all((CANONICAL_DIR / relative).read_bytes() == (INSTALLED_DIR / relative).read_bytes() for relative in canonical)


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise RuntimeError(f"refusing to replace symlinked install target: {target}")
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def sync() -> None:
    if not _skill_same():
        raise RuntimeError(
            f"installed Ready Skill does not match this runtime source: {INSTALLED_SKILL_DIR}"
        )
    canonical = _canonical_files()
    if INSTALLED_DIR.exists() and INSTALLED_DIR.is_symlink():
        raise RuntimeError(f"refusing to synchronize through symlink: {INSTALLED_DIR}")
    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)

    canonical_set = set(canonical)
    for relative in _installed_files():
        if relative not in canonical_set:
            (INSTALLED_DIR / relative).unlink()
    for directory in sorted((path for path in INSTALLED_DIR.rglob("*") if path.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass

    for relative in canonical:
        _atomic_copy(CANONICAL_DIR / relative, INSTALLED_DIR / relative)


def remove_install() -> None:
    if not INSTALLED_DIR.exists():
        return
    if not INSTALLED_DIR.is_dir() or INSTALLED_DIR.is_symlink():
        raise RuntimeError(f"refusing to remove non-directory Ready runtime install: {INSTALLED_DIR}")
    shutil.rmtree(INSTALLED_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        if _skill_same():
            print("READY")
            return 0
        print("SKILL_DRIFT")
        return 1
    if args.check:
        if _skill_same() and _same():
            print("SYNCED")
            return 0
        print("DRIFT")
        return 1
    if args.remove:
        remove_install()
        print(f"REMOVED: {INSTALLED_DIR}")
        return 0

    sync()
    if not _same():
        raise RuntimeError("installed Ready runtime does not match canonical source after sync")
    print(f"SYNCED: {INSTALLED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
