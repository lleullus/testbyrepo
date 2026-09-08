#!/usr/bin/env python3
"""Capture a fixed implementation cohort; the caller owns services and verdicts."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess

from calibrate import product_snapshot, run_stage, write_json


def observe(argv: list[str], root: Path) -> dict:
    """Keep actual output, including failed or unavailable product observations."""
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=20)
        return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "timed_out": True,
                "stdout": (error.stdout or b"").decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout,
                "stderr": (error.stderr or b"").decode(errors="replace") if isinstance(error.stderr, bytes) else error.stderr}


def run_one(item: dict, protocol: dict) -> dict:
    metadata_path = Path(item["metadata"])
    if hashlib.sha256(metadata_path.read_bytes()).hexdigest() != item["metadata_sha256"]:
        raise ValueError("prepared implementation metadata changed")
    metadata = json.loads(metadata_path.read_text())
    environment = json.loads(Path(item["environment"]).read_text())
    root, run_root = Path(metadata["project_root"]), Path(metadata["run_root"])
    before = product_snapshot(root, [])
    if before != item["initial_snapshot"]:
        raise ValueError("prepared product changed before implementation")
    write_json(run_root / "before.json", before)
    runtime_data = run_root / "runtime-data"
    preparation = run_stage("prepare", metadata, agent_dir=Path(environment["agent_dir"]),
                            payload=Path(environment["payload"]), runtime_data=runtime_data,
                            model=protocol["model"], thinking=protocol["thinking"], timeout=protocol["timeout_seconds"])
    if preparation.get("parsed_completion") != "COMPLETE" or not preparation["clean_transport"]:
        result = {"metadata": str(metadata_path), "case_id": metadata["case_id"], "run_id": metadata["run_id"],
                  "profile": item["profile"], "parsed_completion": None, "clean_transport": False,
                  "preparation": preparation, "semantic_review": "REQUIRED"}
        write_json(run_root / "capture.json", result)
        return result
    metadata["plan_review_path"] = preparation["plan_review_path"]
    record = run_stage("implement", metadata, agent_dir=Path(environment["agent_dir"]),
                       payload=Path(environment["payload"]), runtime_data=runtime_data,
                       model=protocol["model"], thinking=protocol["thinking"], timeout=protocol["timeout_seconds"])
    after = product_snapshot(root, [])
    write_json(run_root / "after.json", after)
    if metadata.get("authority_state"):
        state_path = Path(metadata["authority_state"])
        write_json(run_root / "external-before-readback.json", json.loads(state_path.read_text()))
        requests = state_path.with_suffix(".requests.jsonl")
        if requests.exists():
            (run_root / "external-actor-requests.jsonl").write_bytes(requests.read_bytes())
    observer = metadata.get("observer_argv")
    commands = [("parent_readback", metadata["readback_argv"]), *[("parent_additional_trigger", argv) for argv in metadata.get("additional_trigger_argv", [])]]
    observations = [{"role": role, "attribution": "parent, not implementer self-check", **observe(argv, root)} for role, argv in commands]
    if observer:
        observations.append({"role": "parent_observer", "attribution": "parent, not implementer self-check", **observe(observer, root)})
    write_json(run_root / "product-observations.json", observations)
    write_json(run_root / "after-parent.json", product_snapshot(root, []))
    if metadata.get("authority_state"):
        write_json(run_root / "external-after-readback.json", json.loads(Path(metadata["authority_state"]).read_text()))
    executions = []
    for file in sorted(runtime_data.rglob("*.json")) if runtime_data.exists() else []:
        state = json.loads(file.read_text())
        if state.get("kind") == "execution" and state.get("project_root") == str(root):
            executions.append({"path": str(file), "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                               "execution_id": state.get("execution_id"), "phase": state.get("phase"),
                               "pause": state.get("pause"), "completion": state.get("completion")})
    result = {"metadata": str(metadata_path), "case_id": metadata["case_id"], "run_id": metadata["run_id"],
              "profile": item["profile"], "parsed_completion": record.get("parsed_completion"),
              "clean_transport": record["clean_transport"], "changed_paths": record["changed_paths"],
              "runtime_executions": executions, "record": str(run_root / "implement/record.json"),
              "product_observations": str(run_root / "product-observations.json"),
              "preparation": str(run_root / "prepare/record.json"),
              "parent_observation_snapshot": str(run_root / "after-parent.json"),
              "semantic_review": "REQUIRED"}
    write_json(run_root / "capture.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    items = protocol["runs"]
    if not items or len({item["metadata"] for item in items}) != len(items):
        raise ValueError("cohort must contain distinct prepared runs")
    if args.output.exists():
        raise ValueError("refusing to replace prior cohort results")
    for filename, expected in protocol["source_hashes"].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise ValueError(f"evaluation source changed: {filename}")
    for item in items:
        for filename, expected in item["profile_hashes"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
                raise ValueError(f"evaluation profile changed: {filename}")
    results = []
    with ThreadPoolExecutor(max_workers=protocol["concurrency"]) as pool:
        futures = {pool.submit(run_one, item, protocol): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"metadata": item["metadata"], "profile": item["profile"],
                          "capture_error": f"{type(error).__name__}: {error}", "semantic_review": "BLOCKED"}
            results.append(result)
            write_json(args.output, results)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if all(result.get("clean_transport") for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
