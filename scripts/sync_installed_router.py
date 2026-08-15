#!/usr/bin/env python3
"""Synchronize the canonical IIS router into the user's live Codex skill install."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "iis-workflow" / "SKILL.md"
INSTALLED = Path.home() / ".codex" / "skills" / "iis-workflow" / "SKILL.md"


def _same() -> bool:
    return INSTALLED.is_file() and CANONICAL.read_bytes() == INSTALLED.read_bytes()


def sync() -> None:
    payload = CANONICAL.read_bytes()
    INSTALLED.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=".SKILL.md.", dir=INSTALLED.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, INSTALLED)
    finally:
        if tmp.exists():
            tmp.unlink()


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
        raise RuntimeError("installed IIS router does not match canonical source after sync")
    print(f"SYNCED: {INSTALLED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
