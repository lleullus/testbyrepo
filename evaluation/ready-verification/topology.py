#!/usr/bin/env python3
"""Capture a fixed integrated-verifier cohort without adjudicating product meaning."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
from typing import Any

from calibrate import product_snapshot, run_stage


SCHEMA = "iis-verification-capture/v2"
_USAGE_KEYS = ("input", "output", "cacheRead", "cacheWrite", "totalTokens")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _checked_hashes(values: object, label: str) -> dict[str, str]:
    if not isinstance(values, dict) or not values:
        raise ValueError(f"{label} must be a non-empty path-to-SHA256 object")
    checked: dict[str, str] = {}
    for filename, expected in values.items():
        if not isinstance(filename, str) or not filename or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError(f"{label} contains an invalid path or SHA256")
        path = Path(filename).resolve(strict=True)
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"{label} identity changed: {filename}")
        checked[str(path)] = expected
    return checked


def _snapshot_protected(expected: dict[str, str]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for filename, original in expected.items():
        path = Path(filename)
        try:
            current = _sha256(path) if path.is_file() else None
            snapshot[filename] = {"expected_sha256": original, "sha256": current, "matches_expected": current == original}
        except OSError as error:
            snapshot[filename] = {"expected_sha256": original, "error": f"{type(error).__name__}: {error}", "matches_expected": False}
    return snapshot


def _validate_argv(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
        raise ValueError(f"{label} must be a non-empty argv array")
    return value


def _validate_item(item: object, source_hashes: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    if not isinstance(item, dict):
        raise ValueError("each protocol run must be an object")
    for key in ("metadata", "metadata_sha256", "environment", "profile", "initial_snapshot", "profile_hashes", "protected_hashes"):
        if key not in item:
            raise ValueError(f"protocol run is missing {key}")
    if not isinstance(item["profile"], str) or not item["profile"]:
        raise ValueError("profile must name the immutable payload, not select a lifecycle")
    metadata_path = Path(item["metadata"]).resolve(strict=True)
    if not metadata_path.is_file() or _sha256(metadata_path) != item["metadata_sha256"]:
        raise ValueError(f"prepared metadata changed: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    for key in ("case_id", "run_id", "run_root", "project_root", "ticket_path", "target_paths", "allowed_output_paths", "trigger_argv", "readback_argv"):
        if key not in metadata:
            raise ValueError(f"metadata is missing {key}")
    if not all(isinstance(metadata[key], str) and metadata[key] for key in ("case_id", "run_id", "run_root", "project_root", "ticket_path")):
        raise ValueError("metadata string identities must be non-empty")
    root = Path(metadata["project_root"]).resolve(strict=True)
    run_root = Path(metadata["run_root"]).resolve(strict=True)
    if not root.is_dir() or not root.is_relative_to(run_root) or run_root.is_relative_to(root):
        raise ValueError("Project Root must be an existing child of the external run root")
    if Path(metadata["ticket_path"]).resolve(strict=True).is_relative_to(root) is False:
        raise ValueError("Ticket must belong to Project Root")
    for key in ("target_paths", "allowed_output_paths"):
        if not isinstance(metadata[key], list) or not all(isinstance(value, str) and value for value in metadata[key]):
            raise ValueError(f"metadata {key} must be a path array")
        for value in metadata[key]:
            path = Path(value).resolve(strict=key == "target_paths")
            if key == "target_paths" and not path.is_relative_to(root):
                raise ValueError(f"metadata target is outside Project Root: {value}")
            if key == "allowed_output_paths" and (path == root or path.is_relative_to(root) or root.is_relative_to(path)):
                raise ValueError("allowed output must be an exact outside-root evidence path")
    _validate_argv(metadata["trigger_argv"], "metadata trigger_argv")
    _validate_argv(metadata["readback_argv"], "metadata readback_argv")
    for index, argv in enumerate(metadata.get("additional_trigger_argv", [])):
        _validate_argv(argv, f"metadata additional_trigger_argv[{index}]")
    if metadata.get("observer_argv") is not None:
        _validate_argv(metadata["observer_argv"], "metadata observer_argv")

    environment_path = Path(item["environment"]).resolve(strict=True)
    profile_hashes = _checked_hashes(item["profile_hashes"], "profile_hashes")
    if str(environment_path) not in profile_hashes:
        raise ValueError("environment file must be identity-bound in profile_hashes")
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if not isinstance(environment, dict) or not all(isinstance(environment.get(key), str) and environment[key] for key in ("agent_dir", "payload")):
        raise ValueError("environment must bind non-empty agent_dir and payload paths")
    Path(environment["agent_dir"]).resolve(strict=True)
    Path(environment["payload"]).resolve(strict=True)
    protected_hashes = _checked_hashes(item["protected_hashes"], "protected_hashes")
    if metadata.get("implementation_report_path"):
        report_path = Path(metadata["implementation_report_path"]).resolve(strict=True)
        if str(report_path) not in protected_hashes:
            raise ValueError("implementation_report_path must be identity-bound in protected_hashes")
    if not isinstance(item["initial_snapshot"], dict) or product_snapshot(root, []) != item["initial_snapshot"]:
        raise ValueError(f"prepared product identity changed: {metadata_path}")
    for filename in source_hashes:
        if _sha256(Path(filename)) != source_hashes[filename]:
            raise ValueError(f"evaluation source changed during preflight: {filename}")
    return metadata, environment, protected_hashes


def _capture_raw(source_value: object, destination: Path) -> dict[str, Any]:
    if source_value is None:
        return {"configured": False, "exists": False}
    if not isinstance(source_value, str) or not source_value:
        return {"configured": True, "exists": False, "error": "metadata path is not a non-empty string"}
    source = Path(source_value).resolve()
    try:
        if not source.is_file():
            return {"configured": True, "source": str(source), "exists": False}
        data = source.read_bytes()
        with destination.open("xb") as handle:
            handle.write(data)
        return {"configured": True, "source": str(source), "exists": True,
                "sha256": hashlib.sha256(data).hexdigest(), "byte_length": len(data), "capture": str(destination)}
    except OSError as error:
        return {"configured": True, "source": str(source), "exists": False,
                "error": f"{type(error).__name__}: {error}"}


def _runtime_states(runtime_data: Path) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    try:
        files = sorted(runtime_data.rglob("*.json")) if runtime_data.exists() else []
    except OSError as error:
        return [{"error": f"{type(error).__name__}: {error}"}]
    for path in files:
        entry: dict[str, Any] = {"path": str(path)}
        try:
            data = path.read_bytes()
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            value = json.loads(data)
            if isinstance(value, dict) and value.get("kind") == "execution":
                entry.update({key: value.get(key) for key in (
                    "execution_id", "purpose", "phase", "final_verdict", "completion",
                    "pause", "active_operation", "uncertain_effect", "project_root", "ticket_path")})
            else:
                entry["kind"] = value.get("kind") if isinstance(value, dict) else None
        except (OSError, json.JSONDecodeError) as error:
            entry["error"] = f"{type(error).__name__}: {error}"
        states.append(entry)
    return states


def _capture_boundary(label: str, metadata: dict[str, Any], protected: dict[str, str],
                      runtime_data: Path, capture_root: Path) -> dict[str, Any]:
    root = Path(metadata["project_root"])
    boundary: dict[str, Any] = {"label": label}
    try:
        boundary["product_snapshot"] = product_snapshot(root, [])
    except OSError as error:
        boundary["product_snapshot_error"] = f"{type(error).__name__}: {error}"
    boundary["protected"] = _snapshot_protected(protected)
    authority_path = metadata.get("authority_state_path", metadata.get("authority_state"))
    boundary["authority_state"] = _capture_raw(authority_path, capture_root / f"authority-state.{label}.raw")
    boundary["request_log"] = _capture_raw(metadata.get("request_log_path"), capture_root / f"request-log.{label}.raw")
    boundary["runtime_executions"] = _runtime_states(runtime_data)
    _write_new_json(capture_root / f"boundary.{label}.json", boundary)
    return boundary


def _observe(role: str, argv: list[str], root: Path) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=20)
        return {"role": role, "argv": argv, "exit_code": result.returncode, "timed_out": False,
                "stdout": result.stdout, "stderr": result.stderr, "elapsed_seconds": time.monotonic() - started}
    except subprocess.TimeoutExpired as error:
        return {"role": role, "argv": argv, "timed_out": True,
                "stdout": (error.stdout or b"").decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout,
                "stderr": (error.stderr or b"").decode(errors="replace") if isinstance(error.stderr, bytes) else error.stderr,
                "elapsed_seconds": time.monotonic() - started}
    except OSError as error:
        return {"role": role, "argv": argv, "timed_out": False,
                "execution_error": f"{type(error).__name__}: {error}", "elapsed_seconds": time.monotonic() - started}


def _parent_observations(metadata: dict[str, Any], capture_root: Path) -> list[dict[str, Any]]:
    root = Path(metadata["project_root"])
    commands: list[tuple[str, list[str]]] = [("readback", metadata["readback_argv"])]
    if metadata.get("observer_argv"):
        commands.append(("observer", metadata["observer_argv"]))
    observations = [_observe(role, argv, root) for role, argv in commands]
    _write_new_json(capture_root / "parent-observations.json", observations)
    return observations


def _remaining(deadline: float) -> tuple[int, float] | None:
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        return None
    return max(1, math.ceil(seconds)), seconds


def _stage_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {key: record.get(key) for key in (
        "stage", "parsed_verdict", "ticket_progression", "ticket_status_after", "clean_transport", "exit_code",
        "timed_out", "agent_ended", "stop_reason", "error_message", "elapsed_seconds", "usage",
        "tool_events", "target_mutated", "changed_paths", "all_changed_paths", "runtime_progression_paths",
        "raw_terminal_result", "raw_events")}


def _aggregate_stages(records: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, Any]]:
    usage = {key: sum(record.get("usage", {}).get(key, 0) for record in records) for key in _USAGE_KEYS}
    tools = {"starts": sum(record.get("tool_events", {}).get("starts", 0) for record in records),
             "ends": sum(record.get("tool_events", {}).get("ends", 0) for record in records),
             "errors": [{"stage": record.get("stage"), "event": error}
                        for record in records for error in record.get("tool_events", {}).get("errors", [])]}
    return usage, tools


def run_one(item: dict[str, Any], protocol: dict[str, Any], source_hashes: dict[str, str]) -> dict[str, Any]:
    metadata, environment, protected = _validate_item(item, source_hashes)
    run_root = Path(metadata["run_root"])
    capture_root = run_root / f"topology-{item['profile'].lower()}"
    capture_root.mkdir(mode=0o700, exist_ok=False)
    runtime_data = run_root / "runtime-data"
    started = time.monotonic()
    deadline = started + protocol["episode_timeout_seconds"]
    records: list[dict[str, Any]] = []
    stage_errors: list[dict[str, str]] = []
    stop = "NOT_STARTED"
    challenge: dict[str, Any] | None = None

    def invoke_stage(stage: str) -> dict[str, Any] | None:
        allowance = _remaining(deadline)
        if allowance is None:
            stage_errors.append({"stage": stage, "error": "episode timeout exhausted before invocation"})
            return None
        timeout, _wall_timeout = allowance
        try:
            record = run_stage(stage, metadata, agent_dir=Path(environment["agent_dir"]),
                               payload=Path(environment["payload"]), runtime_data=runtime_data,
                               model=protocol["model"], thinking=protocol["thinking"], timeout=timeout,
                               episode_deadline=deadline)
            records.append(record)
            return record
        except Exception as error:
            stage_errors.append({"stage": stage, "error": f"{type(error).__name__}: {error}"})
            return None

    verify = invoke_stage("verify")
    stop = ("VERIFY_CAPTURE_ERROR" if verify is None else
            "VERIFY_COMPLETE" if verify["clean_transport"] else "VERIFY_TRANSPORT_STOP")
    challenge_path = run_root / "challenge.json"
    if challenge_path.is_file():
        challenge = json.loads(challenge_path.read_text(encoding="utf-8"))

    after_actor = _capture_boundary("after-actor", metadata, protected, runtime_data, capture_root)
    observations = _parent_observations(metadata, capture_root)
    after_parent = _capture_boundary("after-parent-observation", metadata, protected, runtime_data, capture_root)
    usage, tool_events = _aggregate_stages(records)
    verify_records = [record for record in records if record["stage"] == "verify"]
    route = "INTEGRATED_VERIFY"
    result = {
        "schema": SCHEMA,
        "metadata": item["metadata"],
        "metadata_sha256": item["metadata_sha256"],
        "environment": item["environment"],
        "source_hashes_identity": hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest(),
        "profile_hashes": item["profile_hashes"],
        "initial_snapshot_identity": hashlib.sha256(json.dumps(item["initial_snapshot"], sort_keys=True).encode()).hexdigest(),
        "protected_hashes": item["protected_hashes"],
        "case_id": metadata["case_id"],
        "run_id": metadata["run_id"],
        "profile": item["profile"],
        "route": route,
        "model_tool_profile": {"model": protocol["model"], "thinking": protocol["thinking"]},
        "episode_timeout_seconds": protocol["episode_timeout_seconds"],
        "episode_stop": stop,
        "stage_count": len(records),
        "stages": [_stage_summary(record) for record in records],
        "stage_capture_errors": stage_errors,
        "parsed_verdict": verify_records[-1]["parsed_verdict"] if verify_records else None,
        "diagnostic_challenge": challenge,
        "usage": usage,
        "tool_events": tool_events,
        "model_elapsed_seconds": sum(record.get("elapsed_seconds", 0.0) for record in records),
        "episode_elapsed_seconds": time.monotonic() - started,
        "after_actor_boundary": str(capture_root / "boundary.after-actor.json"),
        "parent_observations": str(capture_root / "parent-observations.json"),
        "after_parent_observation_boundary": str(capture_root / "boundary.after-parent-observation.json"),
        "protected_matches_after_actor": all(value.get("matches_expected") for value in after_actor["protected"].values()),
        "protected_matches_after_parent_observation": all(value.get("matches_expected") for value in after_parent["protected"].values()),
        "parent_observation_count": len(observations),
        "parent_observation_policy": {"additional_trigger_argv_executed": False,
                                      "primary_readback_executed": True,
                                      "observer_executed": bool(metadata.get("observer_argv"))},
        "runtime_progression_paths": sorted({path for record in records for path in record.get("runtime_progression_paths", [])}),
        "unexpected_changed_paths": sorted({path for record in records for path in record.get("changed_paths", [])}),
        "semantic_review": "REQUIRED",
    }
    _write_new_json(capture_root / "capture.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="new final JSON array; per-settlement files use <output>.settlements/")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("refusing to replace prior cohort results")
    settlement_dir = args.output.with_name(args.output.name + ".settlements")
    if settlement_dir.exists():
        raise ValueError("refusing to replace prior settlement evidence")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if not isinstance(protocol, dict):
        raise ValueError("protocol must be a JSON object")
    for key in ("model", "thinking", "episode_timeout_seconds", "concurrency", "runs", "source_hashes"):
        if key not in protocol:
            raise ValueError(f"protocol is missing {key}")
    if not isinstance(protocol["model"], str) or not protocol["model"] or not isinstance(protocol["thinking"], str) or not protocol["thinking"]:
        raise ValueError("model and thinking must be non-empty strings")
    if not isinstance(protocol["episode_timeout_seconds"], int) or protocol["episode_timeout_seconds"] <= 0:
        raise ValueError("episode_timeout_seconds must be a positive integer")
    if not isinstance(protocol["concurrency"], int) or protocol["concurrency"] <= 0:
        raise ValueError("concurrency must be a positive integer")
    if not isinstance(protocol["runs"], list) or not protocol["runs"]:
        raise ValueError("runs must be a non-empty array")
    metadata_names = [item.get("metadata") if isinstance(item, dict) else None for item in protocol["runs"]]
    if any(not isinstance(name, str) or not name for name in metadata_names) or len(metadata_names) != len(set(metadata_names)):
        raise ValueError("runs must bind distinct metadata paths")
    source_hashes = _checked_hashes(protocol["source_hashes"], "source_hashes")
    validated = [_validate_item(item, source_hashes) for item in protocol["runs"]]
    roots = [str(Path(metadata["project_root"]).resolve()) for metadata, _environment, _protected in validated]
    if len(roots) != len(set(roots)):
        raise ValueError("runs must use distinct isolated Project Roots")

    settlement_dir.mkdir(parents=True, mode=0o700)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=protocol["concurrency"]) as pool:
        futures = {pool.submit(run_one, item, protocol, source_hashes): item for item in protocol["runs"]}
        for index, future in enumerate(as_completed(futures), start=1):
            item = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"schema": SCHEMA, "metadata": item["metadata"], "profile": item["profile"],
                          "capture_error": f"{type(error).__name__}: {error}", "semantic_review": "REQUIRED"}
            result["settlement_index"] = index
            results.append(result)
            safe_run = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(item["metadata"]).parent.name)
            settlement_path = settlement_dir / f"{index:04d}-{item['profile']}-{safe_run}.json"
            _write_new_json(settlement_path, result)
            print(json.dumps({"settled": index, "total": len(futures), "result": str(settlement_path)}, ensure_ascii=False), flush=True)
    _write_new_json(args.output, results)
    return 0 if all(result.get("parsed_verdict") is not None and not result.get("capture_error")
                    and not result.get("stage_capture_errors") for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
