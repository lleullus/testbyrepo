#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = (
    ([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT),
    ([sys.executable, "-B", "implementation-lead/run_tests.py"], ROOT),
    ([sys.executable, "-B", "verification-lead/run_tests.py"], ROOT),
)


def main() -> int:
    for argv, cwd in SUITES:
        print(f"+ ({cwd}) {' '.join(argv)}", flush=True)
        subprocess.run(argv, cwd=cwd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
