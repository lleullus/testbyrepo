#!/usr/bin/env python3
"""Product Thesis work CLI. Review completion is recorded only by the trusted host API."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from iis_artifacts.store import ArtifactStore

SPEC_PATH = Path(__file__).with_name("lifecycle.py")
import importlib.util
SPEC = importlib.util.spec_from_file_location("iis_thesis_lifecycle_cli", SPEC_PATH)
assert SPEC is not None and SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LIFECYCLE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    commands = parser.add_subparsers(dest="action", required=True)

    begin = commands.add_parser("start")
    begin.add_argument("request")
    begin.add_argument("--budget", type=int)

    candidate = commands.add_parser("submit-candidate")
    candidate.add_argument("run")
    candidate.add_argument("file", type=Path)
    candidate.add_argument("--path", required=True)
    candidate.add_argument("--expected-generation", required=True, type=int)

    show = commands.add_parser("inspect")
    show.add_argument("run")

    close = commands.add_parser("close-request")
    close.add_argument("run")
    close.add_argument("--project-root", type=Path, required=True)

    resume = commands.add_parser("resume")
    resume.add_argument("run")
    resume.add_argument("--request", required=True)

    stop = commands.add_parser("cancel")
    stop.add_argument("run")

    drive = commands.add_parser("drive")
    drive.add_argument("run")

    args = parser.parse_args()
    store = ArtifactStore(args.store, args.project_id)
    try:
        if args.action == "start":
            result = {"run_id": LIFECYCLE.start(store, args.request, budget=args.budget)}
        elif args.action == "submit-candidate":
            result = LIFECYCLE.submit_candidate(
                store, args.run, args.file, args.path, expected_generation=args.expected_generation
            )
        elif args.action == "inspect":
            result = LIFECYCLE.inspect(store, args.run)
        elif args.action == "close-request":
            result = LIFECYCLE.close_request(store, args.run, args.project_root)
        elif args.action == "resume":
            LIFECYCLE.resume(store, args.run, args.request)
            result = LIFECYCLE.inspect(store, args.run)
        elif args.action == "cancel":
            LIFECYCLE.cancel(store, args.run)
            result = {"result": "CANCELLED"}
        else:
            state = LIFECYCLE.inspect(store, args.run)
            result = {
                "result": "HOST_INVOCATION_REQUIRED",
                "phase": state["phase"],
                "note": "The CLI cannot fabricate SOURCE_FRONTIER or CANDIDATE_COUNTEREXAMPLE completion; a trusted host must run and record them.",
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("result") == "REWORK_REQUIRED":
            return 20
        if result.get("result") in {"WAITING_USER", "WAITING_EVIDENCE", "CANCELLED", "HOST_INVOCATION_REQUIRED"}:
            return 10
        return 0
    except Exception as exc:
        print(json.dumps({"result": "FAILED", "reason": str(exc)}, ensure_ascii=False))
        return 30


if __name__ == "__main__":
    raise SystemExit(main())
