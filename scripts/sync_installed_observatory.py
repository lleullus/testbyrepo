#!/usr/bin/env python3
"""Synchronize the canonical IIS Observatory skill into the live Codex install."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = ROOT / "iis-observatory"
INSTALLED_DIR = Path.home() / ".codex" / "skills" / "iis-observatory"
FILES = (Path("SKILL.md"), Path("agents/openai.yaml"))


def _same() -> bool:
    for relative in FILES:
        source = CANONICAL_DIR / relative
        target = INSTALLED_DIR / relative
        if not target.is_file() or source.read_bytes() != target.read_bytes():
            return False
    return True


def _atomic_copy(source: Path, target: Path) -> None:
    payload = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
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


def sync() -> None:
    for relative in FILES:
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
        raise RuntimeError("installed IIS Observatory skill does not match canonical source after sync")
    print(f"SYNCED: {INSTALLED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
