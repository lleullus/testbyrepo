#!/usr/bin/env python3
"""Controlled local mock provider helper for testing comic-new generation engine.

Implements the ima2 CLI surface:
gen --stdin --mode direct --no-size-nudge --model ... --size ... --quality ... --timeout ... -o <staging_path> --json

Does NOT make external network or model provider calls.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock ima2 provider")
    subparsers = parser.add_subparsers(dest="subcommand")
    gen_parser = subparsers.add_parser("gen")

    gen_parser.add_argument("--stdin", action="store_true")
    gen_parser.add_argument("--mode", type=str, default="direct")
    gen_parser.add_argument("--no-size-nudge", action="store_true")
    gen_parser.add_argument("--model", type=str, default="nano-banana-pro")
    gen_parser.add_argument("--size", type=str, default="1024x1536")
    gen_parser.add_argument("--quality", type=str, default="high")
    gen_parser.add_argument("--timeout", type=int, default=60)
    gen_parser.add_argument("-o", "--out", type=str, required=True)
    gen_parser.add_argument("--json", action="store_true")

    # Mock behavior control flags
    gen_parser.add_argument("--mock-exit-code", type=int, default=0)
    gen_parser.add_argument("--mock-sleep", type=float, default=0.0)
    gen_parser.add_argument("--mock-spawn-descendant", action="store_true")
    gen_parser.add_argument("--mock-corrupt-png", action="store_true")
    gen_parser.add_argument("--mock-no-output", action="store_true")
    gen_parser.add_argument("--mock-gate-file", type=str, default=None)
    gen_parser.add_argument("--mock-record-stdin", type=str, default=None)

    args = parser.parse_args()

    if args.subcommand != "gen":
        sys.stderr.write(f"Unknown subcommand: {args.subcommand}\n")
        return 2

    # 1. Read stdin if requested
    stdin_data = ""
    if args.stdin:
        stdin_data = sys.stdin.read()

    if args.mock_record_stdin:
        Path(args.mock_record_stdin).write_text(stdin_data, encoding="utf-8")

    # 2. Spawn a descendant process if requested (to test process-tree termination)
    spawn_descendant = args.mock_spawn_descendant or (os.environ.get("MOCK_SPAWN_DESCENDANT") == "1")
    descendant_proc = None
    if spawn_descendant:
        descendant_proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(300)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # 3. Wait on gate file if requested
    gate_file = args.mock_gate_file or os.environ.get("MOCK_GATE_FILE")
    if gate_file:
        gate = Path(gate_file)
        while not gate.exists():
            time.sleep(0.05)

    # 4. Sleep if requested
    sleep_sec = args.mock_sleep or float(os.environ.get("MOCK_SLEEP", "0.0"))
    if sleep_sec > 0:
        time.sleep(sleep_sec)

    # 5. Handle mock failure modes
    exit_code = args.mock_exit_code or int(os.environ.get("MOCK_EXIT_CODE", "0"))
    if exit_code != 0:
        sys.stderr.write(f"Mock error exit code {exit_code}\n")
        return exit_code

    no_output = args.mock_no_output or (os.environ.get("MOCK_NO_OUTPUT") == "1")
    if no_output:
        return 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    corrupt_png = args.mock_corrupt_png or (os.environ.get("MOCK_CORRUPT_PNG") == "1")
    if corrupt_png:
        # Write invalid/truncated bytes
        out_path.write_bytes(b"\x89PNG\r\n\x1a\nTRUNCATED_CORRUPT_BYTES")
        return 0
    # 6. Generate valid PNG with requested size
    dims = (1024, 1536)
    if "x" in args.size:
        try:
            parts = args.size.split("x")
            dims = (int(parts[0]), int(parts[1]))
        except Exception:
            pass

    img = Image.new("RGB", dims, color=(40, 60, 80))
    img.save(str(out_path), format="PNG")

    if args.json:
        print(json.dumps({"request_id": f"req-mock-{os.getpid()}"}))

    return 0


if __name__ == "__main__":
    sys.exit(main())
