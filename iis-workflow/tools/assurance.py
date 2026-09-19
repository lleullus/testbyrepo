#!/usr/bin/env python3
"""Host-owned Assurance binding, execution attribution and structural closure."""
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
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from iis_artifacts.admission import require_admission, AdmissionError
from iis_artifacts.refs import validate_ref
from iis_artifacts.store import ArtifactStore, ArtifactStoreError

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


def _schema(store: ArtifactStore) -> None:
    with store.connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS assurance_bindings(
              binding_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL UNIQUE,
              admission_id TEXT NOT NULL,
              baseline_ref_json TEXT NOT NULL,
              scope_ref_json TEXT NOT NULL,
              source_snapshot TEXT NOT NULL,
              source_root TEXT NOT NULL,
              execution_root TEXT NOT NULL,
              binding_json TEXT NOT NULL,
              status TEXT NOT NULL,
              sequence INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assurance_invocations(
              invocation_id TEXT PRIMARY KEY,
              binding_id TEXT NOT NULL,
              kind TEXT NOT NULL,
              item_id TEXT NOT NULL,
              status TEXT NOT NULL,
              result_ref_json TEXT,
              started_sequence INTEGER NOT NULL,
              completed_sequence INTEGER,
              UNIQUE(binding_id, kind, item_id)
            );
            CREATE TABLE IF NOT EXISTS assurance_effects(
              binding_id TEXT NOT NULL,
              effect_id TEXT NOT NULL,
              owner TEXT NOT NULL,
              state TEXT NOT NULL,
              evidence_json TEXT NOT NULL,
              sequence INTEGER NOT NULL,
              PRIMARY KEY(binding_id, effect_id)
            );
            """
        )


def references(store: ArtifactStore, values: object, *, empty: bool = False, run_id: str | None = None, invocation_id: str | None = None) -> None:
    need(isinstance(values, list) and (empty or bool(values)), "MISSING_EVIDENCE")
    for item in values:
        ref = validate_ref(item)
        if run_id is None and invocation_id is None:
            store.resolve(ref)
        else:
            store.assert_producer(ref, run_id=run_id, invocation_id=invocation_id)


def rows(value: object, label: str) -> dict[str, dict]:
    need(isinstance(value, list), "INVALID_LIST:" + label)
    result = {}
    for row in value:
        need(isinstance(row, dict) and text(row.get("id")), "INVALID_ID:" + label)
        need(row["id"] not in result, "DUPLICATE_ID:" + row["id"])
        result[row["id"]] = row
    return result


def load_baseline(path: Path, store: ArtifactStore, *, trusted_uid: int | None = None) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        block = raw
    else:
        section = SCOPE.sections(raw.decode()).get("Assurance Baseline", "")
        blocks = re.findall(r"^\x60\x60\x60iis-assurance\s*\n(.*?)^\x60\x60\x60\s*$", section, re.M | re.S)
        need(len(blocks) == 1, "BASELINE_BLOCK_REQUIRED")
        block = blocks[0].encode()
    value = json.loads(block)
    validate_baseline(value, store, trusted_uid=trusted_uid)
    return value, block


def _stored_scope(store: ArtifactStore, value: dict, *, trusted_uid: int | None = None) -> dict:
    ref = validate_ref(value)
    return SCOPE.validate_bytes(store.read_bytes(ref), ref["path"], trusted_uid=trusted_uid)


def validate_baseline(value: dict, store: ArtifactStore, *, trusted_uid: int | None = None) -> dict:
    need(isinstance(value, dict) and value.get("schema") == "iis-assurance/v2", "INVALID_BASELINE")
    authority = _stored_scope(store, value["scope"], trusted_uid=trusted_uid)
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


def check_execution(store: ArtifactStore, execution: dict) -> None:
    need(isinstance(execution, dict) and text(execution.get("note")), "EXECUTION_IDENTITY_REQUIRED")
    for kind in ("artifacts", "runtime", "mechanisms"):
        references(store, execution[kind], empty=kind != "mechanisms")


def _canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _binding_record(store: ArtifactStore, binding_id: str) -> dict:
    _schema(store)
    with store.connect() as db:
        row = db.execute("SELECT * FROM assurance_bindings WHERE binding_id=?", (binding_id,)).fetchone()
    if row is None:
        raise ValueError("UNREGISTERED_BINDING")
    return dict(row)


def bind(
    baseline_path: Path,
    store: ArtifactStore,
    root: Path,
    execution: dict,
    *,
    execution_base: Path | None = None,
    trusted_request: str | None = None,
    project_owner_uid: int | None = None,
) -> dict:
    _schema(store)
    baseline, block = load_baseline(baseline_path, store, trusted_uid=project_owner_uid)
    authority = validate_baseline(baseline, store, trusted_uid=project_owner_uid)
    project_root = Path(authority["project_root"])
    need(project_root == Path(root).resolve(strict=True), "FOREIGN_PROJECT")
    admission = require_admission(
        store,
        baseline["scope"],
        role="assurance",
        current_request=trusted_request,
    )
    check_execution(store, execution)
    run_id = "run-" + uuid.uuid4().hex
    binding_id = "bind-" + uuid.uuid4().hex
    baseline_snapshot = store.capture_mapping({"baseline.json": block}, kind="source", origin=str(baseline_path), producer_run=run_id)
    source_snapshot = store.capture_tree(root, kind="source", origin=str(project_root), producer_run=run_id)
    execution_base = store.root / "executions" if execution_base is None else Path(execution_base)
    execution_base.mkdir(parents=True, exist_ok=True, mode=0o755)
    execution_root = execution_base / run_id / "source"
    execution_root.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    store.materialize_snapshot(source_snapshot, execution_root, read_only=True)
    binding = {
        "schema": "iis-assurance-binding/v3",
        "binding_id": binding_id,
        "run_id": run_id,
        "admission_id": admission["admission_id"],
        "baseline": {"snapshot": baseline_snapshot, "path": "baseline.json"},
        "scope": baseline["scope"],
        "authorities": authority.get("product_authorities", []) + authority.get("transition_authorities", []),
        "source": {"snapshot": source_snapshot, "root": str(project_root)},
        "execution_root": str(execution_root),
        "execution": execution,
        "project_owner_uid": project_owner_uid,
    }
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "INSERT INTO assurance_bindings(binding_id,run_id,admission_id,baseline_ref_json,scope_ref_json,source_snapshot,source_root,execution_root,binding_json,status,sequence) "
            "VALUES(?,?,?,?,?,?,?,?,?,'ACTIVE',?)",
            (
                binding_id, run_id, admission["admission_id"], json.dumps(binding["baseline"]), json.dumps(binding["scope"]),
                source_snapshot, str(project_root), str(execution_root), _canonical(binding), store.sequence_in(db, "assurance-binding"),
            ),
        )
        db.execute("COMMIT")
    return binding


def current(baseline_path: Path, store: ArtifactStore, binding: dict) -> dict:
    need(binding.get("schema") == "iis-assurance-binding/v3", "INVALID_BINDING")
    record = _binding_record(store, binding.get("binding_id", ""))
    need(record["status"] == "ACTIVE", "BINDING_NOT_ACTIVE")
    need(record["binding_json"] == _canonical(binding), "BINDING_RECORD_MISMATCH")
    baseline, block = load_baseline(
        baseline_path, store, trusted_uid=binding.get("project_owner_uid")
    )
    need(store.read_bytes(binding["baseline"]) == block, "BASELINE_DRIFT")
    authority = validate_baseline(baseline, store, trusted_uid=binding.get("project_owner_uid"))
    require_admission(store, baseline["scope"], role="assurance")
    need(baseline["scope"] == binding["scope"], "SCOPE_DRIFT")
    need(binding["authorities"] == authority.get("product_authorities", []) + authority.get("transition_authorities", []), "AUTHORITY_DRIFT")
    check_execution(store, binding["execution"])
    need(store.compare_tree(binding["source"]["snapshot"], Path(binding["source"]["root"])), "TARGET_DRIFT")
    return baseline


def _map_path(binding: dict, value: str) -> str:
    source_root = Path(binding["source"]["root"])
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        relative = path.relative_to(source_root)
    except ValueError:
        return value
    return str(Path(binding["execution_root"]) / relative)


def _begin_invocation(store: ArtifactStore, binding: dict, kind: str, item_id: str) -> str:
    _binding_record(store, binding["binding_id"])
    baseline = json.loads(store.read_bytes(binding["baseline"]))
    collection = {"gate": "gates", "observation": "observations", "probe": "lanes"}.get(kind)
    need(collection is not None and item_id in rows(baseline[collection], collection), "FOREIGN_STARTED_WORK")
    invocation_id = "inv-" + uuid.uuid4().hex
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute(
                "INSERT INTO assurance_invocations(invocation_id,binding_id,kind,item_id,status,result_ref_json,started_sequence,completed_sequence) "
                "VALUES(?,?,?,?, 'STARTED',NULL,?,NULL)",
                (invocation_id, binding["binding_id"], kind, item_id, store.sequence_in(db, "assurance-invocation-start")),
            )
        except Exception as exc:
            db.execute("ROLLBACK")
            raise ValueError("WORK_ALREADY_STARTED") from exc
        db.execute("COMMIT")
    return invocation_id


def begin_host_invocation(store: ArtifactStore, binding: dict, kind: str, item_id: str) -> str:
    if kind not in {"observation", "probe"}:
        raise ValueError("host invocation kind must be observation or probe")
    return _begin_invocation(store, binding, kind, item_id)


def capture_invocation_evidence(store: ArtifactStore, binding: dict, invocation_id: str, files: dict[str, bytes]) -> list[dict]:
    with store.connect() as db:
        row = db.execute("SELECT status FROM assurance_invocations WHERE invocation_id=? AND binding_id=?", (invocation_id, binding["binding_id"])).fetchone()
    need(row is not None and row["status"] == "STARTED", "EVIDENCE_INVOCATION_NOT_ACTIVE")
    snapshot = store.capture_mapping(files, kind="evidence", producer_run=binding["run_id"], producer_invocation=invocation_id)
    return [{"snapshot": snapshot, "path": path} for path in files]


def _complete_invocation(store: ArtifactStore, binding: dict, invocation_id: str, result: dict) -> dict:
    with store.connect() as db:
        row = db.execute("SELECT * FROM assurance_invocations WHERE invocation_id=? AND binding_id=?", (invocation_id, binding["binding_id"])).fetchone()
    if row is None or row["status"] != "STARTED":
        raise ValueError("INVOCATION_NOT_ACTIVE")
    need(result.get("binding") == binding["binding_id"], "RESULT_BINDING_MISMATCH")
    need(result.get("invocation") == invocation_id, "RESULT_INVOCATION_MISMATCH")
    need(result.get("kind") == row["kind"] and result.get("id") == row["item_id"], "RESULT_ITEM_MISMATCH")
    references(store, result.get("evidence"), run_id=binding["run_id"], invocation_id=invocation_id)
    result_snapshot = store.capture_mapping(
        {f"results/{invocation_id}.json": (_canonical(result) + "\n").encode("utf-8")},
        kind="assurance-result", producer_run=binding["run_id"], producer_invocation=invocation_id,
    )
    result_ref = {"snapshot": result_snapshot, "path": f"results/{invocation_id}.json"}
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        active = db.execute("SELECT status FROM assurance_invocations WHERE invocation_id=?", (invocation_id,)).fetchone()
        if active is None or active["status"] != "STARTED":
            db.execute("ROLLBACK")
            raise ValueError("INVOCATION_NOT_ACTIVE")
        db.execute(
            "UPDATE assurance_invocations SET status='COMPLETE',result_ref_json=?,completed_sequence=? WHERE invocation_id=?",
            (json.dumps(result_ref), store.sequence_in(db, "assurance-invocation-complete"), invocation_id),
        )
        db.execute("COMMIT")
    return result


def complete_host_invocation(store: ArtifactStore, binding: dict, invocation_id: str, result: dict) -> dict:
    with store.connect() as db:
        row = db.execute("SELECT kind FROM assurance_invocations WHERE invocation_id=? AND binding_id=?", (invocation_id, binding["binding_id"])).fetchone()
    need(row is not None and row["kind"] in {"observation", "probe"}, "NATIVE_GATE_CAPTURE_REQUIRED")
    return _complete_invocation(store, binding, invocation_id, result)


def effect_evidence(store: ArtifactStore, binding: dict, evidence: list[dict], *, settled: bool) -> None:
    references(store, evidence, empty=not settled, run_id=binding["run_id"])
    with store.connect() as db:
        for ref in evidence:
            producer = store.assert_producer(ref, run_id=binding["run_id"], kind="evidence")
            row = db.execute("SELECT status FROM assurance_invocations WHERE invocation_id=? AND binding_id=?", (producer["producer_invocation"], binding["binding_id"])).fetchone()
            need(row is not None, "EFFECT_EVIDENCE_INVOCATION_UNKNOWN")


def record_effect(store: ArtifactStore, binding: dict, effect_id: str, *, owner: str, state: str, evidence: list[dict]) -> None:
    need(text(effect_id) and text(owner), "INVALID_EFFECT")
    need(state in {"STARTED", "SETTLED", "UNKNOWN"}, "INVALID_EFFECT_STATE")
    effect_evidence(store, binding, evidence, settled=state == "SETTLED")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "INSERT INTO assurance_effects(binding_id,effect_id,owner,state,evidence_json,sequence) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(binding_id,effect_id) DO UPDATE SET owner=excluded.owner,state=excluded.state,evidence_json=excluded.evidence_json,sequence=excluded.sequence",
            (binding["binding_id"], effect_id, owner, state, json.dumps(evidence), store.sequence_in(db, "assurance-effect")),
        )
        db.execute("COMMIT")


def _native_runner(argv: list[str], cwd: str, env: dict[str, str], timeout: float) -> tuple[int | None, bytes, bytes, str | None]:
    code = None
    failure = None
    stdout = stderr = b""
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.wait()
            stdout, stderr = exc.output or b"", exc.stderr or b""
            failure = "TIMEOUT_EFFECT_SETTLEMENT_REQUIRED"
    except OSError as exc:
        failure = str(exc)
    return code, stdout, stderr, failure


def run_gate(
    baseline_path: Path,
    store: ArtifactStore,
    binding: dict,
    gate_id: str,
    output: Path,
    *,
    runner: Callable[[list[str], str, dict[str, str], float], tuple[int | None, bytes, bytes, str | None]] | None = None,
) -> dict:
    baseline = current(baseline_path, store, binding)
    gate = rows(baseline["gates"], "gates")[gate_id]
    output = output.resolve()
    need(not output.is_relative_to(Path(binding["source"]["root"])), "EVIDENCE_INSIDE_TARGET")
    output.mkdir(parents=True, exist_ok=False)
    original_argv = gate["argv"]
    executed_argv = [_map_path(binding, item) for item in original_argv]
    executed_cwd = _map_path(binding, gate["cwd"])
    jobs_path = None if gate["jobs_path"] is None else Path(_map_path(binding, gate["jobs_path"]))
    if jobs_path is not None and not jobs_path.is_absolute():
        jobs_path = Path(executed_cwd) / jobs_path
    if gate["jobs"] and jobs_path is not None:
        need(not jobs_path.exists() and not jobs_path.is_symlink(), "JOB_EXPORT_ALREADY_EXISTS")
    invocation = _begin_invocation(store, binding, "gate", gate_id)
    started = time.monotonic()
    env = {**os.environ, "IIS_ASSURANCE_RUN_ID": binding["run_id"], "IIS_ASSURANCE_GATE_ID": gate_id,
           "IIS_ASSURANCE_INVOCATION_ID": invocation, "IIS_ASSURANCE_JOBS_PATH": str(jobs_path) if jobs_path is not None else ""}
    runner = _native_runner if runner is None else runner
    try:
        code, stdout, stderr, failure = runner(executed_argv, executed_cwd, env, gate["timeout"])
    except Exception as exc:
        code, stdout, stderr, failure = None, b"", b"", f"GATE_RUNNER_FAILED:{exc}"
    (output / "stdout").write_bytes(stdout)
    (output / "stderr").write_bytes(stderr)
    evidence_map: dict[str, bytes] = {f"{gate_id}/stdout": stdout, f"{gate_id}/stderr": stderr}
    jobs_data = None
    if gate["jobs"] and jobs_path is not None and jobs_path.is_file():
        jobs_data = jobs_path.read_bytes()
        (output / "jobs.json").write_bytes(jobs_data)
        evidence_map[f"{gate_id}/jobs.json"] = jobs_data
    refs = capture_invocation_evidence(store, binding, invocation, evidence_map)
    by_path = {item["path"]: item for item in refs}
    stdout_ref = by_path[f"{gate_id}/stdout"]
    stderr_ref = by_path[f"{gate_id}/stderr"]
    jobs_ref = by_path.get(f"{gate_id}/jobs.json")
    result = {
        "schema": "iis-assurance-result/v3", "kind": "gate", "id": gate_id, "invocation": invocation,
        "binding": binding["binding_id"], "completion": "BLOCKED" if failure else "COMPLETE", "evidence": refs, "effects": [],
        "capture": {
            "argv": original_argv, "cwd": gate["cwd"], "executed_argv": executed_argv, "executed_cwd": executed_cwd,
            "returncode": code, "stdout": stdout_ref, "stderr": stderr_ref, "jobs": jobs_ref,
            "elapsed_seconds": time.monotonic() - started, "failure": failure,
        },
    }
    try:
        current(baseline_path, store, binding)
    except Exception as exc:
        result["completion"] = "BLOCKED"
        result["capture"]["failure"] = str(exc)
    _complete_invocation(store, binding, invocation, result)
    save(output / "result.json", result)
    return result


def check_gate(store: ArtifactStore, gate: dict, result: dict, binding: dict) -> None:
    capture = result["capture"]
    need(capture["argv"] == gate["argv"] and capture["cwd"] == gate["cwd"], "GATE_MECHANISM_MISMATCH")
    need(capture["executed_argv"] == [_map_path(binding, value) for value in gate["argv"]] and capture["executed_cwd"] == _map_path(binding, gate["cwd"]), "EXECUTED_MECHANISM_MISMATCH")
    need(type(capture["returncode"]) is int and capture["returncode"] == 0 and capture["failure"] is None, "GATE_FAILED")
    need(type(capture["elapsed_seconds"]) in (int, float) and capture["elapsed_seconds"] >= 0, "MISSING_NATIVE_CAPTURE")
    for key in ("stdout", "stderr"):
        store.assert_producer(capture[key], run_id=binding["run_id"], invocation_id=result["invocation"])
        need(capture[key] in result["evidence"], "UNLINKED_NATIVE_CAPTURE")
    if gate["jobs"]:
        need(capture["jobs"] is not None, "MISSING_JOB_EXPORT")
        store.assert_producer(capture["jobs"], run_id=binding["run_id"], invocation_id=result["invocation"])
        jobs = json.loads(store.read_bytes(capture["jobs"]))
        need(jobs["run_id"] == binding["run_id"] and jobs["gate_id"] == gate["id"], "STALE_JOB_EXPORT")
        need(jobs.get("invocation_id") == result["invocation"], "STALE_JOB_INVOCATION")
        need(all(jobs["jobs"].get(name) == "SUCCESS" for name in gate["jobs"]), "REQUIRED_JOB_NOT_SUCCESSFUL")


def check_probe(store: ArtifactStore, lane: dict, result: dict, binding: dict) -> None:
    outcome = result["outcome"]
    need(outcome in {"COUNTEREXAMPLE_FOUND", "NO_COUNTEREXAMPLE_WITHIN_BUDGET", "UNOBSERVABLE"}, "INVALID_PROBE_OUTCOME")
    references(store, result["hypotheses"], run_id=binding["run_id"], invocation_id=result["invocation"])
    actions = result["actions"]
    need(isinstance(actions, list) and len(actions) >= lane["min_actions"], "INSUFFICIENT_ACTIONS")
    attacked = set()
    for action in actions:
        need(action["surface"] in lane["surfaces"], "FOREIGN_ATTACK_SURFACE")
        attacked.add(action["surface"])
        need(all(text(action.get(key)) for key in ("hypothesis", "initial_state", "trigger", "readback")), "MISSING_ATTACK_TRACE")
        references(store, action["evidence"], run_id=binding["run_id"], invocation_id=result["invocation"])
    need(attacked == set(lane["surfaces"]), "UNATTACKED_SURFACE")
    need(isinstance(result["findings"], list), "MISSING_FINDING_DISPOSITION")
    material_open = False
    for finding in result["findings"]:
        need(text(finding.get("anchor")), "MISSING_FINDING_ANCHOR")
        references(store, finding["evidence"], run_id=binding["run_id"], invocation_id=result["invocation"])
        need(finding["materiality"] in {"MATERIAL", "OUT_OF_SCOPE", "UNKNOWN"}, "INVALID_MATERIALITY")
        need(finding["disposition"] in {"OPEN", "DISMISSED"}, "INVALID_FINDING_DISPOSITION")
        need(finding["materiality"] != "UNKNOWN", "UNKNOWN_FINDING_MATERIALITY")
        material_open |= finding["materiality"] == "MATERIAL" and finding["disposition"] == "OPEN"
    need((outcome == "COUNTEREXAMPLE_FOUND") == material_open, "FINDING_OUTCOME_MISMATCH")
    need(not material_open, "UNRESOLVED_COUNTEREXAMPLE")
    need(outcome != "UNOBSERVABLE", "PROBE_UNOBSERVABLE")


def _load_result(store: ArtifactStore, ref_json: str, binding: dict, invocation_id: str) -> dict:
    ref = json.loads(ref_json)
    store.assert_producer(ref, run_id=binding["run_id"], invocation_id=invocation_id, kind="assurance-result")
    return json.loads(store.read_bytes(ref))


def close(baseline_path: Path, store: ArtifactStore, binding: dict) -> dict:
    reasons: list[str] = []
    try:
        baseline = current(baseline_path, store, binding)
        definitions = {"gate": rows(baseline["gates"], "gates"), "observation": rows(baseline["observations"], "observations"), "probe": rows(baseline["lanes"], "lanes")}
        required = {(kind, name) for kind, items in definitions.items() for name, item in items.items() if kind != "probe" or item["required"]}
        with store.connect() as db:
            invocation_rows = db.execute("SELECT * FROM assurance_invocations WHERE binding_id=? ORDER BY started_sequence", (binding["binding_id"],)).fetchall()
            effect_rows = db.execute("SELECT * FROM assurance_effects WHERE binding_id=? ORDER BY sequence", (binding["binding_id"],)).fetchall()
        started = {(row["kind"], row["item_id"]) for row in invocation_rows}
        need(required.issubset(started), "REQUIRED_WORK_NOT_STARTED")
        for row in invocation_rows:
            key = (row["kind"], row["item_id"])
            need(key[0] in definitions and key[1] in definitions[key[0]], "FOREIGN_STARTED_WORK")
            need(row["status"] == "COMPLETE" and row["result_ref_json"], "STARTED_RESULT_MISSING")
            result = _load_result(store, row["result_ref_json"], binding, row["invocation_id"])
            need(result.get("schema") == "iis-assurance-result/v3", "INVALID_RESULT")
            need(result["kind"] == row["kind"] and result["id"] == row["item_id"], "RESULT_ITEM_MISMATCH")
            need(result["invocation"] == row["invocation_id"], "RESULT_INVOCATION_MISMATCH")
            need(result["binding"] == binding["binding_id"], "RESULT_BINDING_MISMATCH")
            references(store, result["evidence"], run_id=binding["run_id"], invocation_id=row["invocation_id"])
            need(result["completion"] == "COMPLETE", "INCOMPLETE_RESULT")
            definition = definitions[key[0]][key[1]]
            if key[0] == "gate":
                check_gate(store, definition, result, binding)
            elif key[0] == "observation":
                need(all(result[field] == definition[field] for field in ("initial_state", "trigger", "readback", "predicate")), "OBSERVATION_BOUNDARY_MISMATCH")
                need(result["outcome"] == "SATISFIED", "OBSERVATION_NOT_SATISFIED")
            else:
                check_probe(store, definition, result, binding)
        for effect in effect_rows:
            need(text(effect["owner"]) and effect["state"] == "SETTLED", "UNSETTLED_EFFECT")
            effect_evidence(store, binding, json.loads(effect["evidence_json"]), settled=True)
    except (ValueError, KeyError, TypeError, OSError, ArtifactStoreError, AdmissionError, subprocess.CalledProcessError) as exc:
        reasons.append(str(exc))
    return {"schema": "iis-assurance-closure/v3", "binding": binding.get("binding_id"), "status": "BLOCKED" if reasons else "EVIDENCE_COMPLETE", "reasons": reasons}


def recording(ready: bytes, done: bytes) -> dict:
    need(ready.count(b"\nStatus: ready\n") == 1, "READY_STATUS_REQUIRED")
    need(done == ready.replace(b"\nStatus: ready\n", b"\nStatus: done\n", 1), "NOT_STATUS_ONLY")
    return {"status_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--project-id")
    commands = parser.add_subparsers(dest="action", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("baseline", type=Path)
    record = commands.add_parser("recording")
    record.add_argument("ready", type=Path)
    record.add_argument("done", type=Path)
    for name in ("bind", "bind-execution", "run", "close"):
        commands.add_parser(name)
    args = parser.parse_args()
    try:
        if args.action in {"bind", "bind-execution", "run", "close"}:
            print(json.dumps({"status": "BLOCKED", "reasons": ["HOST_SUPERVISOR_REQUIRED"]}))
            return 20
        if args.action == "recording":
            result = recording(args.ready.read_bytes(), args.done.read_bytes())
        else:
            need(args.store is not None and args.project_id, "STORE_REQUIRED_FOR_STRUCTURE_VALIDATION")
            store = ArtifactStore(args.store, args.project_id)
            load_baseline(args.baseline, store)
            result = {"status": "VALID"}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reasons": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
