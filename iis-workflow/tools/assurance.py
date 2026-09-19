#!/usr/bin/env python3
"""Bind native evidence and calculate structural closure using executor-owned fixed snapshots."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from iis_artifacts.refs import validate_ref
from iis_artifacts.store import ArtifactStore

SPEC = importlib.util.spec_from_file_location("iis_scope_validator", ROOT / "scope-shaper/tools/validate_scope.py")
assert SPEC is not None and SPEC.loader is not None
SCOPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCOPE)


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), "INVALID_OBJECT")
    return value


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def references(store: ArtifactStore, values: object, *, empty: bool = False) -> None:
    need(isinstance(values, list) and (empty or bool(values)), "MISSING_EVIDENCE")
    for item in values:
        store.resolve(validate_ref(item))


def rows(value: object, label: str) -> dict[str, dict]:
    need(isinstance(value, list), "INVALID_LIST:" + label)
    result = {}
    for row in value:
        need(isinstance(row, dict) and text(row.get("id")), "INVALID_ID:" + label)
        need(row["id"] not in result, "DUPLICATE_ID:" + row["id"])
        result[row["id"]] = row
    return result


def load_baseline(path: Path, store: ArtifactStore) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        block = raw
    else:
        section = SCOPE.sections(raw.decode()) .get("Assurance Baseline", "")
        blocks = re.findall(r"^```iis-assurance\s*\n(.*?)^```\s*$", section, re.M | re.S)
        need(len(blocks) == 1, "BASELINE_BLOCK_REQUIRED")
        block = blocks[0].encode()
    value = json.loads(block)
    validate_baseline(value, store)
    return value, block


def _stored_scope(store: ArtifactStore, value: dict) -> dict:
    ref = validate_ref(value)
    data = store.read_bytes(ref)
    return SCOPE.validate_bytes(data, ref["path"])


def validate_baseline(value: dict, store: ArtifactStore) -> dict:
    need(isinstance(value, dict) and value.get("schema") == "iis-assurance/v2", "INVALID_BASELINE")
    authority = _stored_scope(store, value["scope"])
    need(authority["status"] == "ready", "SCOPE_NOT_READY")
    acceptance = SCOPE.sections(store.read_bytes(value["scope"]).decode("utf-8"))["Acceptance"]
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", acceptance) if part.strip()]
    gates = rows(value["gates"], "gates")
    observations = rows(value["observations"], "observations")
    lanes = rows(value["lanes"], "lanes")
    surfaces = rows(value["surfaces"], "surfaces")
    need(bool(observations), "OBSERVATION_REQUIRED")
    all_ids = [*gates, *observations, *lanes]
    need(len(set(all_ids)) == len(all_ids), "DUPLICATE_RESULT_ID")
    obligations = value["obligations"]
    need(isinstance(obligations, list), "INVALID_OBLIGATIONS")
    anchors = []
    for row in obligations:
        need(isinstance(row, dict) and text(row.get("anchor")), "INVALID_ANCHOR")
        anchors.append(row["anchor"])
        evidence = row["evidence"]
        need(isinstance(evidence, list) and bool(evidence) and all(text(x) for x in evidence), "UNMAPPED_OBLIGATION")
        need(set(evidence).issubset(set(gates) | set(observations)), "FOREIGN_EVIDENCE_ID")
    need(len(anchors) == len(set(anchors)) and set(anchors) == set(paragraphs), "ACCEPTANCE_COVERAGE_MISMATCH")
    for gate in gates.values():
        need(isinstance(gate["argv"], list) and bool(gate["argv"]) and all(text(x) for x in gate["argv"]), "INVALID_ARGV")
        need(text(gate["cwd"]) and Path(gate["cwd"]).is_absolute(), "INVALID_CWD")
        need(type(gate["timeout"]) in (int, float) and 0 < gate["timeout"] <= 3600, "INVALID_TIMEOUT")
        references(store, gate["mechanisms"])
        need(isinstance(gate["jobs"], list) and all(text(x) for x in gate["jobs"]), "INVALID_JOBS")
        need(len(gate["jobs"]) == len(set(gate["jobs"])), "DUPLICATE_JOB")
        need((not gate["jobs"] and gate["jobs_path"] is None) or (bool(gate["jobs"]) and text(gate["jobs_path"]) and Path(gate["jobs_path"]).is_absolute()), "INVALID_JOB_EXPORT")
    for obs in observations.values():
        need(all(text(obs.get(key)) for key in ("initial_state", "trigger", "readback", "predicate")), "INVALID_OBSERVATION")
    assigned = set()
    for surface in surfaces.values():
        need(text(surface.get("boundary")), "INVALID_SURFACE")
    for lane in lanes.values():
        need(type(lane["required"]) is bool, "INVALID_REQUIRED")
        need(type(lane["min_actions"]) is int and lane["min_actions"] > 0, "INVALID_ACTION_BUDGET")
        need(text(lane["budget"]) and text(lane["safety"]), "MISSING_LANE_LIMITS")
        need(isinstance(lane["surfaces"], list) and bool(lane["surfaces"]) and all(text(x) for x in lane["surfaces"]), "INVALID_ASSIGNMENT")
        need(set(lane["surfaces"]).issubset(surfaces), "FOREIGN_SURFACE")
        if lane["required"]:
            assigned.update(lane["surfaces"])
    need(assigned == set(surfaces), "UNASSIGNED_SURFACE")
    need((bool(surfaces) and value["no_probe_reason"] is None) or (not surfaces and not lanes and text(value["no_probe_reason"])), "PROBE_POLICY_REQUIRED")
    return authority


def capture_source(store: ArtifactStore, root: Path, run_id: str) -> dict:
    root = Path(root).resolve(strict=True)
    need(root.is_absolute(), "INVALID_SOURCE_ROOT")
    snapshot = store.capture_tree(root, kind="source", origin=str(root), producer_run=run_id)
    return {"snapshot": snapshot, "root": str(root)}


def check_execution(store: ArtifactStore, execution: dict) -> None:
    need(isinstance(execution, dict) and text(execution.get("note")), "EXECUTION_IDENTITY_REQUIRED")
    for kind in ("artifacts", "runtime", "mechanisms"):
        references(store, execution[kind], empty=kind != "mechanisms")


def bind(baseline_path: Path, store: ArtifactStore, root: Path, execution: dict) -> dict:
    baseline, block = load_baseline(baseline_path, store)
    authority = validate_baseline(baseline, store)
    project_root = Path(authority["project_root"])
    need(project_root == Path(root).resolve(strict=True), "FOREIGN_PROJECT")
    check_execution(store, execution)
    run_id = "run-" + uuid.uuid4().hex
    baseline_snapshot = store.capture_mapping(
        {"baseline.json": block},
        kind="source",
        origin=str(baseline_path),
        producer_run=run_id,
    )
    source = capture_source(store, root, run_id)
    return {
        "schema": "iis-assurance-binding/v2",
        "binding_id": "bind-" + uuid.uuid4().hex,
        "run_id": run_id,
        "baseline": {"snapshot": baseline_snapshot, "path": "baseline.json"},
        "scope": baseline["scope"],
        "authorities": authority.get("product_authorities", []) + authority.get("transition_authorities", []),
        "source": source,
        "execution": execution,
    }


def current(baseline_path: Path, store: ArtifactStore, binding: dict) -> dict:
    need(binding.get("schema") == "iis-assurance-binding/v2" and text(binding.get("binding_id")) and text(binding.get("run_id")), "INVALID_BINDING")
    baseline, block = load_baseline(baseline_path, store)
    need(store.read_bytes(binding["baseline"]) == block, "BASELINE_DRIFT")
    authority = validate_baseline(baseline, store)
    need(baseline["scope"] == binding["scope"], "SCOPE_DRIFT")
    need(binding["authorities"] == authority.get("product_authorities", []) + authority.get("transition_authorities", []), "AUTHORITY_DRIFT")
    check_execution(store, binding["execution"])
    source = binding["source"]
    need(store.compare_tree(source["snapshot"], Path(source["root"])), "TARGET_DRIFT")
    return baseline


def run_gate(baseline_path: Path, store: ArtifactStore, binding: dict, gate_id: str, output: Path) -> dict:
    baseline = current(baseline_path, store, binding)
    gate = rows(baseline["gates"], "gates")[gate_id]
    output = output.resolve()
    need(not output.is_relative_to(Path(binding["source"]["root"])), "EVIDENCE_INSIDE_TARGET")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    env = {**os.environ, "IIS_ASSURANCE_RUN_ID": binding["run_id"], "IIS_ASSURANCE_GATE_ID": gate_id}
    invocation = "launch-" + uuid.uuid4().hex
    code = None
    failure = None
    stdout = stderr = b""
    try:
        process = subprocess.Popen(gate["argv"], cwd=gate["cwd"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        invocation = f"process-{process.pid}-" + uuid.uuid4().hex
        try:
            stdout, stderr = process.communicate(timeout=gate["timeout"])
            code = process.returncode
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.wait()
            stdout, stderr = exc.output or b"", exc.stderr or b""
            failure = "TIMEOUT_EFFECT_SETTLEMENT_REQUIRED"
    except OSError as exc:
        failure = str(exc)
    (output / "stdout").write_bytes(stdout)
    (output / "stderr").write_bytes(stderr)
    evidence_map: dict[str, bytes] = {f"{gate_id}/stdout": stdout, f"{gate_id}/stderr": stderr}
    jobs_data = None
    if gate["jobs"] and Path(gate["jobs_path"]).is_file():
        jobs_data = Path(gate["jobs_path"]).read_bytes()
        (output / "jobs.json").write_bytes(jobs_data)
        evidence_map[f"{gate_id}/jobs.json"] = jobs_data
    evidence_snapshot = store.capture_mapping(
        evidence_map,
        kind="evidence",
        origin=str(output),
        producer_run=binding["run_id"],
        producer_invocation=invocation,
    )
    stdout_ref = {"snapshot": evidence_snapshot, "path": f"{gate_id}/stdout"}
    stderr_ref = {"snapshot": evidence_snapshot, "path": f"{gate_id}/stderr"}
    jobs_ref = None if jobs_data is None else {"snapshot": evidence_snapshot, "path": f"{gate_id}/jobs.json"}
    refs = [stdout_ref, stderr_ref] + ([jobs_ref] if jobs_ref else [])
    record = {
        "schema": "iis-assurance-result/v2",
        "kind": "gate",
        "id": gate_id,
        "invocation": invocation,
        "binding": binding["binding_id"],
        "completion": "BLOCKED" if failure else "COMPLETE",
        "evidence": refs,
        "effects": [],
        "capture": {
            "argv": gate["argv"],
            "cwd": gate["cwd"],
            "returncode": code,
            "stdout": stdout_ref,
            "stderr": stderr_ref,
            "jobs": jobs_ref,
            "elapsed_seconds": time.monotonic() - started,
            "failure": failure,
        },
    }
    try:
        current(baseline_path, store, binding)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        record["completion"] = "BLOCKED"
        record["capture"]["failure"] = str(exc)
    save(output / "result.json", record)
    return record


def check_gate(store: ArtifactStore, gate: dict, result: dict, binding: dict) -> None:
    capture = result["capture"]
    need(capture["argv"] == gate["argv"] and capture["cwd"] == gate["cwd"], "GATE_MECHANISM_MISMATCH")
    need(type(capture["returncode"]) is int and capture["returncode"] == 0 and capture["failure"] is None, "GATE_FAILED")
    need(type(capture["elapsed_seconds"]) in (int, float) and capture["elapsed_seconds"] >= 0, "MISSING_NATIVE_CAPTURE")
    for key in ("stdout", "stderr"):
        store.resolve(capture[key])
        need(capture[key] in result["evidence"], "UNLINKED_NATIVE_CAPTURE")
    if gate["jobs"]:
        need(capture["jobs"] is not None, "MISSING_JOB_EXPORT")
        store.resolve(capture["jobs"])
        need(capture["jobs"] in result["evidence"], "UNLINKED_JOB_EXPORT")
        jobs = json.loads(store.read_bytes(capture["jobs"]))
        need(jobs["run_id"] == binding["run_id"] and jobs["gate_id"] == gate["id"], "STALE_JOB_EXPORT")
        need(all(jobs["jobs"].get(name) == "SUCCESS" for name in gate["jobs"]), "REQUIRED_JOB_NOT_SUCCESSFUL")


def check_probe(store: ArtifactStore, lane: dict, result: dict) -> None:
    outcome = result["outcome"]
    need(outcome in {"COUNTEREXAMPLE_FOUND", "NO_COUNTEREXAMPLE_WITHIN_BUDGET", "UNOBSERVABLE"}, "INVALID_PROBE_OUTCOME")
    references(store, result["hypotheses"])
    actions = result["actions"]
    need(isinstance(actions, list) and len(actions) >= lane["min_actions"], "INSUFFICIENT_ACTIONS")
    attacked = set()
    for action in actions:
        need(action["surface"] in lane["surfaces"], "FOREIGN_ATTACK_SURFACE")
        attacked.add(action["surface"])
        need(all(text(action.get(key)) for key in ("hypothesis", "initial_state", "trigger", "readback")), "MISSING_ATTACK_TRACE")
        references(store, action["evidence"])
    need(attacked == set(lane["surfaces"]), "UNATTACKED_SURFACE")
    need(isinstance(result["findings"], list), "MISSING_FINDING_DISPOSITION")
    material_open = False
    for finding in result["findings"]:
        need(text(finding.get("anchor")), "MISSING_FINDING_ANCHOR")
        references(store, finding["evidence"])
        need(finding["materiality"] in {"MATERIAL", "OUT_OF_SCOPE", "UNKNOWN"}, "INVALID_MATERIALITY")
        need(finding["disposition"] in {"OPEN", "DISMISSED"}, "INVALID_FINDING_DISPOSITION")
        need(finding["materiality"] != "UNKNOWN", "UNKNOWN_FINDING_MATERIALITY")
        material_open |= finding["materiality"] == "MATERIAL" and finding["disposition"] == "OPEN"
    need((outcome == "COUNTEREXAMPLE_FOUND") == material_open, "FINDING_OUTCOME_MISMATCH")
    need(not material_open, "UNRESOLVED_COUNTEREXAMPLE")
    need(outcome != "UNOBSERVABLE", "PROBE_UNOBSERVABLE")


def close(baseline_path: Path, store: ArtifactStore, binding: dict, activity: dict, results: list[dict]) -> dict:
    reasons = []
    try:
        baseline = current(baseline_path, store, binding)
        need(activity["run_id"] == binding["run_id"], "FOREIGN_ACTIVITY")
        references(store, activity["evidence"])
        effects = rows(activity["effects"], "effects")
        for effect in effects.values():
            need(text(effect["owner"]) and effect["state"] == "SETTLED", "UNSETTLED_EFFECT")
            references(store, effect["evidence"])
        definitions = {
            "gate": rows(baseline["gates"], "gates"),
            "observation": rows(baseline["observations"], "observations"),
            "probe": rows(baseline["lanes"], "lanes"),
        }
        started = {}
        invocations = set()
        need(isinstance(activity["started"], list), "INVALID_ACTIVITY")
        for item in activity["started"]:
            key = (item["kind"], item["id"])
            need(key[0] in definitions and key[1] in definitions[key[0]], "FOREIGN_STARTED_WORK")
            need(key not in started and text(item["invocation"]) and item["invocation"] not in invocations, "DUPLICATE_INVOCATION")
            started[key] = item["invocation"]
            invocations.add(item["invocation"])
        required = {(kind, name) for kind, items in definitions.items() for name, item in items.items() if kind != "probe" or item["required"]}
        need(required.issubset(started), "REQUIRED_WORK_NOT_STARTED")
        seen = set()
        for result in results:
            need(result["schema"] == "iis-assurance-result/v2", "INVALID_RESULT")
            key = (result["kind"], result["id"])
            need(key not in seen, "DUPLICATE_RESULT")
            seen.add(key)
            need(key in started and result["invocation"] == started[key], "UNATTRIBUTABLE_RESULT")
            need(result["binding"] == binding["binding_id"], "RESULT_BINDING_MISMATCH")
            references(store, result["evidence"])
            need(isinstance(result["effects"], list) and all(text(x) for x in result["effects"]) and set(result["effects"]).issubset(effects), "UNRECORDED_EFFECT")
            need(result["completion"] == "COMPLETE", "INCOMPLETE_RESULT")
            definition = definitions[key[0]][key[1]]
            if key[0] == "gate":
                check_gate(store, definition, result, binding)
            elif key[0] == "observation":
                need(all(result[field] == definition[field] for field in ("initial_state", "trigger", "readback", "predicate")), "OBSERVATION_BOUNDARY_MISMATCH")
                need(result["outcome"] == "SATISFIED", "OBSERVATION_NOT_SATISFIED")
            else:
                check_probe(store, definition, result)
        need(seen == set(started), "STARTED_RESULT_MISSING")
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        reasons.append(str(exc))
    return {
        "schema": "iis-assurance-closure/v2",
        "binding": binding.get("binding_id"),
        "status": "BLOCKED" if reasons else "EVIDENCE_COMPLETE",
        "reasons": reasons,
    }


def recording(ready: bytes, done: bytes) -> dict:
    need(ready.count(b"\nStatus: ready\n") == 1, "READY_STATUS_REQUIRED")
    need(done == ready.replace(b"\nStatus: ready\n", b"\nStatus: done\n", 1), "NOT_STATUS_ONLY")
    return {"status_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("baseline", type=Path)
    seal = commands.add_parser("bind")
    seal.add_argument("baseline", type=Path)
    seal.add_argument("--root", type=Path, required=True)
    seal.add_argument("--execution", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    execution = commands.add_parser("bind-execution")
    execution.add_argument("binding", type=Path)
    execution.add_argument("baseline", type=Path)
    execution.add_argument("execution", type=Path)
    execution.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("baseline", type=Path)
    run.add_argument("binding", type=Path)
    run.add_argument("gate_id")
    run.add_argument("--output", type=Path, required=True)
    closure = commands.add_parser("close")
    closure.add_argument("baseline", type=Path)
    closure.add_argument("binding", type=Path)
    closure.add_argument("--activity", type=Path, required=True)
    closure.add_argument("results", type=Path, nargs="+")
    record = commands.add_parser("recording")
    record.add_argument("ready", type=Path)
    record.add_argument("done", type=Path)
    args = parser.parse_args()
    store = ArtifactStore(args.store, args.project_id)
    try:
        if args.action == "validate":
            load_baseline(args.baseline, store)
            result = {"status": "VALID"}
        elif args.action == "bind":
            result = bind(args.baseline, store, args.root, read_json(args.execution))
            need(not args.output.resolve().is_relative_to(args.root.resolve()), "EVIDENCE_INSIDE_TARGET")
            save(args.output, result)
        elif args.action == "bind-execution":
            old = read_json(args.binding)
            current(args.baseline, store, old)
            new_execution = read_json(args.execution)
            check_execution(store, new_execution)
            result = {**old, "binding_id": "bind-" + uuid.uuid4().hex, "run_id": "run-" + uuid.uuid4().hex, "execution": new_execution}
            save(args.output, result)
        elif args.action == "run":
            result = run_gate(args.baseline, store, read_json(args.binding), args.gate_id, args.output)
        elif args.action == "close":
            result = close(args.baseline, store, read_json(args.binding), read_json(args.activity), [read_json(path) for path in args.results])
        else:
            result = recording(args.ready.read_bytes(), args.done.read_bytes())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get("status") == "BLOCKED" or result.get("completion") == "BLOCKED" else 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reasons": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
