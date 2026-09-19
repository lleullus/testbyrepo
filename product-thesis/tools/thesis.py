#!/usr/bin/env python3
"""Worker-facing Product Thesis client for a trusted IIS supervisor."""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from iis_artifacts.supervisor import HostIntegrationUnavailable, SupervisorClient


def _client() -> SupervisorClient:
    raw = os.environ.get("IIS_SUPERVISOR_SOCKET")
    if not raw:
        raise HostIntegrationUnavailable("HOST_SUPERVISOR_REQUIRED")
    return SupervisorClient(Path(raw))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)

    commands.add_parser("start")

    candidate = commands.add_parser("submit-candidate")
    candidate.add_argument("run")
    candidate.add_argument("file", type=Path)
    candidate.add_argument("--path", required=True)
    candidate.add_argument("--expected-generation", required=True, type=int)

    show = commands.add_parser("inspect")
    show.add_argument("run")

    drive = commands.add_parser("drive")
    drive.add_argument("run")

    propose = commands.add_parser("propose")
    propose.add_argument("run")
    propose.add_argument("data", type=Path)

    close = commands.add_parser("close-request")
    close.add_argument("run")
    close.add_argument("--limitations", default="")

    stop = commands.add_parser("cancel")
    stop.add_argument("run")

    args = parser.parse_args()
    try:
        client = _client()
        if args.action == "start":
            payload = {"action": "start"}
        elif args.action == "submit-candidate":
            payload = {
                "action": "submit_candidate",
                "run_id": args.run,
                "content_b64": base64.b64encode(args.file.read_bytes()).decode("ascii"),
                "logical_path": args.path,
                "expected_generation": args.expected_generation,
            }
        elif args.action == "inspect":
            payload = {"action": "inspect", "run_id": args.run}
        elif args.action == "drive":
            payload = {"action": "drive", "run_id": args.run}
        elif args.action == "propose":
            payload = {
                "action": "propose",
                "run_id": args.run,
                "proposal": json.loads(args.data.read_text(encoding="utf-8")),
            }
        elif args.action == "close-request":
            payload = {"action": "close", "run_id": args.run, "limitations": args.limitations}
        else:
            payload = {"action": "cancel", "run_id": args.run}
        result = client.request(payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
