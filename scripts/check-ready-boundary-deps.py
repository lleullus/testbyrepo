#!/usr/bin/env python3
"""Fail if a Ready boundary candidate payload depends on the retired Ready runtime surface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from sync_installed_iis import CANDIDATE_RETIRED, PAYLOAD_ROOTS, REQUIRED, TEXT_SUFFIXES

DENIED = {
    "ready_guard": re.compile(r"\bready_guard\b"),
    "ready_argv": re.compile(r"\bready_argv\b"),
    "runtime_data_env": re.compile(r"\bIIS_READY_RUNTIME_DATA\b"),
    "legacy_effect_phase": re.compile(r"\bEFFECT_UNCERTAIN\b"),
    "legacy_runtime_path": re.compile(r"delivery-runtime/ready-ticket-implement"),
    "legacy_extension_name": re.compile(r"ready-ticket-implement-runtime"),
}


def candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for relative in PAYLOAD_ROOTS:
        path = root / relative
        if path.is_symlink():
            raise ValueError(f"candidate payload root is a symlink: {relative}")
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_symlink():
                    raise ValueError(f"candidate payload contains symlink: {child.relative_to(root)}")
                if child.is_file():
                    files.append(child)
    return sorted(set(files))


def check(root: Path) -> dict:
    root = root.resolve(strict=True)
    for relative in REQUIRED:
        if not (root / relative).is_file():
            raise ValueError(f"missing required boundary payload: {relative}")
    for relative in CANDIDATE_RETIRED:
        if (root / relative).exists() or (root / relative).is_symlink():
            raise ValueError(f"retired Ready payload remains: {relative}")
    findings = []
    scanned = 0
    for path in candidate_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="strict")
        for name, pattern in DENIED.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                findings.append({"path": path.relative_to(root).as_posix(), "line": line, "denied": name})
    if findings:
        raise ValueError("retired Ready runtime dependency found: " + json.dumps(findings, ensure_ascii=False))
    return {"schema": "iis-ready-boundary-dependency-scan/v1", "root": str(root),
            "text_files_scanned": scanned, "findings": [], "status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), indent=2, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
