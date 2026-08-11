#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = ("tests", "tests/pilot")


def main() -> int:
    for suite in SUITES:
        argv = [sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-v"]
        print(f"+ ({ROOT}) {' '.join(argv)}", flush=True)
        subprocess.run(argv, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
