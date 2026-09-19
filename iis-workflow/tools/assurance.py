#!/usr/bin/env python3
"""Bind native evidence and calculate structural closure; never run agents or write Scope."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("iis_scope_validator", ROOT / "scope-shaper/tools/validate_scope.py")
assert SPEC is not None and SPEC.loader is not None
SCOPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCOPE)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(value: dict) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


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


def file_ref(path: Path) -> dict:
    need(path.is_absolute() and path.is_file() and not path.is_symlink(), "INVALID_FILE_REFERENCE")
    return {"path": str(path), "sha256": digest(path.read_bytes())}


def check_ref(ref: dict) -> None:
    need(isinstance(ref, dict) and text(ref.get("path")), "INVALID_FILE_REFERENCE")
    need(file_ref(Path(ref["path"])) == ref, "EVIDENCE_DRIFT:" + ref["path"])


def references(values: object, *, empty: bool = False) -> None:
    need(isinstance(values, list) and (empty or bool(values)), "MISSING_EVIDENCE")
    for ref in values:
        check_ref(ref)


def rows(value: object, label: str) -> dict[str, dict]:
    need(isinstance(value, list), "INVALID_LIST:" + label)
    result = {}
    for row in value:
        need(isinstance(row, dict) and text(row.get("id")), "INVALID_ID:" + label)
        need(row["id"] not in result, "DUPLICATE_ID:" + row["id"])
        result[row["id"]] = row
    return result


def load_baseline(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        block = raw
    else:
        section = SCOPE.sections(raw.decode()).get("Assurance Baseline", "")
        blocks = re.findall(r"^```iis-assurance\s*\n(.*?)^```\s*$", section, re.M | re.S)
        need(len(blocks) == 1, "BASELINE_BLOCK_REQUIRED")
        block = blocks[0].encode()
    value = json.loads(block)
    validate_baseline(value)
    return value, block


def validate_baseline(value: dict) -> dict:
    need(isinstance(value, dict) and value.get("schema") == "iis-assurance/v1", "INVALID_BASELINE")
    check_ref(value["scope"])
    scope = Path(value["scope"]["path"])
    authority = SCOPE.validate(scope)
    need(authority["status"] == "ready", "SCOPE_NOT_READY")
    acceptance = SCOPE.sections(scope.read_text(encoding="utf-8"))["Acceptance"]
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
        references(gate["mechanisms"])
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


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def source_identity(root: Path, base: str) -> dict:
    need(root.is_absolute() and root == root.resolve(), "INVALID_SOURCE_ROOT")
    need(git(root, "rev-parse", "--show-toplevel").decode().strip() == str(root), "SOURCE_ROOT_NOT_REPOSITORY")
    need(not git(root, "status", "--porcelain", "--untracked-files=all"), "TARGET_NOT_SEALED")
    result = git(root, "rev-parse", "HEAD").decode().strip()
    need(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base) is not None, "FULL_BASE_SHA_REQUIRED")
    need(git(root, "rev-parse", base + "^{commit}").decode().strip() == base, "INVALID_BASE_COMMIT")
    files = []
    for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, _, stage = header.split()
        need(mode in (b"100644", b"100755") and stage == b"0", "UNSUPPORTED_TARGET_ENTRY")
        path = root / os.fsdecode(name)
        ref = file_ref(path)
        files.append({**ref, "mode": stat.S_IMODE(path.stat().st_mode)})
    return {"root": str(root), "base": base, "result": result, "diff_sha256": digest(git(root, "diff", "--binary", base, result, "--")), "files": files}


def check_execution(execution: dict) -> None:
    need(isinstance(execution, dict) and text(execution.get("note")), "EXECUTION_IDENTITY_REQUIRED")
    for kind in ("artifacts", "runtime", "mechanisms"):
        references(execution[kind], empty=kind != "mechanisms")


def bind(baseline_path: Path, root: Path, base: str, execution: dict) -> dict:
    baseline, block = load_baseline(baseline_path)
    authority = validate_baseline(baseline)
    need(Path(authority["project_root"]).is_relative_to(root), "FOREIGN_PROJECT")
    check_execution(execution)
    return {"schema": "iis-assurance-binding/v1", "run_id": uuid.uuid4().hex,
            "baseline": {"path": str(baseline_path.resolve()), "sha256": digest(block)},
            "scope": baseline["scope"], "authorities": authority.get("product_authorities", []) + authority.get("transition_authorities", []),
            "source": source_identity(root, base), "execution": execution}


def current(baseline_path: Path, binding: dict) -> dict:
    need(binding.get("schema") == "iis-assurance-binding/v1" and text(binding.get("run_id")), "INVALID_BINDING")
    baseline, block = load_baseline(baseline_path)
    need(binding["baseline"] == {"path": str(baseline_path.resolve()), "sha256": digest(block)}, "BASELINE_DRIFT")
    authority = validate_baseline(baseline)
    need(baseline["scope"] == binding["scope"], "SCOPE_DRIFT")
    need(binding["authorities"] == authority.get("product_authorities", []) + authority.get("transition_authorities", []), "AUTHORITY_DRIFT")
    check_execution(binding["execution"])
    source = binding["source"]
    need(source_identity(Path(source["root"]), source["base"]) == source, "TARGET_DRIFT")
    return baseline


def run_gate(baseline_path: Path, binding: dict, gate_id: str, output: Path) -> dict:
    baseline = current(baseline_path, binding)
    gate = rows(baseline["gates"], "gates")[gate_id]
    output = output.resolve()
    need(not output.is_relative_to(Path(binding["source"]["root"])), "EVIDENCE_INSIDE_TARGET")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    env = {**os.environ, "IIS_ASSURANCE_RUN_ID": binding["run_id"], "IIS_ASSURANCE_GATE_ID": gate_id}
    invocation = "launch:" + uuid.uuid4().hex
    code = None
    failure = None
    stdout = stderr = b""
    try:
        process = subprocess.Popen(gate["argv"], cwd=gate["cwd"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        invocation = f"process:{process.pid}:{uuid.uuid4().hex}"
        try:
            stdout, stderr = process.communicate(timeout=gate["timeout"])
            code = process.returncode
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.wait()
            stdout, stderr = exc.output or b"", exc.stderr or b""
            process.stdout.close()
            process.stderr.close()
            failure = "TIMEOUT_EFFECT_SETTLEMENT_REQUIRED"
    except OSError as exc:
        failure = str(exc)
    (output / "stdout").write_bytes(stdout)
    (output / "stderr").write_bytes(stderr)
    refs = [file_ref(output / "stdout"), file_ref(output / "stderr")]
    jobs = None
    if gate["jobs"] and Path(gate["jobs_path"]).is_file():
        (output / "jobs.json").write_bytes(Path(gate["jobs_path"]).read_bytes())
        jobs = file_ref(output / "jobs.json")
        refs.append(jobs)
    record = {"schema": "iis-assurance-result/v1", "kind": "gate", "id": gate_id,
              "invocation": invocation, "binding": identity(binding), "completion": "BLOCKED" if failure else "COMPLETE",
              "evidence": refs, "effects": [], "capture": {"argv": gate["argv"], "cwd": gate["cwd"],
              "returncode": code, "stdout": refs[0], "stderr": refs[1], "jobs": jobs,
              "elapsed_seconds": time.monotonic() - started, "failure": failure}}
    try:
        current(baseline_path, binding)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        record["completion"] = "BLOCKED"
        record["capture"]["failure"] = str(exc)
    save(output / "result.json", record)
    return record


def check_gate(gate: dict, result: dict, binding: dict) -> None:
    capture = result["capture"]
    need(capture["argv"] == gate["argv"] and capture["cwd"] == gate["cwd"], "GATE_MECHANISM_MISMATCH")
    need(type(capture["returncode"]) is int and capture["returncode"] == 0 and capture["failure"] is None, "GATE_FAILED")
    need(type(capture["elapsed_seconds"]) in (int, float) and capture["elapsed_seconds"] >= 0, "MISSING_NATIVE_CAPTURE")
    for key in ("stdout", "stderr"):
        check_ref(capture[key])
        need(capture[key] in result["evidence"], "UNLINKED_NATIVE_CAPTURE")
    if gate["jobs"]:
        check_ref(capture["jobs"])
        need(capture["jobs"] in result["evidence"], "UNLINKED_JOB_EXPORT")
        jobs = read_json(Path(capture["jobs"]["path"]))
        need(jobs["run_id"] == binding["run_id"] and jobs["gate_id"] == gate["id"], "STALE_JOB_EXPORT")
        need(all(jobs["jobs"].get(name) == "SUCCESS" for name in gate["jobs"]), "REQUIRED_JOB_NOT_SUCCESSFUL")


def check_probe(lane: dict, result: dict) -> None:
    outcome = result["outcome"]
    need(outcome in {"COUNTEREXAMPLE_FOUND", "NO_COUNTEREXAMPLE_WITHIN_BUDGET", "UNOBSERVABLE"}, "INVALID_PROBE_OUTCOME")
    references(result["hypotheses"])
    actions = result["actions"]
    need(isinstance(actions, list) and len(actions) >= lane["min_actions"], "INSUFFICIENT_ACTIONS")
    attacked = set()
    for action in actions:
        need(action["surface"] in lane["surfaces"], "FOREIGN_ATTACK_SURFACE")
        attacked.add(action["surface"])
        need(all(text(action.get(key)) for key in ("hypothesis", "initial_state", "trigger", "readback")), "MISSING_ATTACK_TRACE")
        references(action["evidence"])
    need(attacked == set(lane["surfaces"]), "UNATTACKED_SURFACE")
    need(isinstance(result["findings"], list), "MISSING_FINDING_DISPOSITION")
    material_open = False
    for finding in result["findings"]:
        need(text(finding.get("anchor")), "MISSING_FINDING_ANCHOR")
        references(finding["evidence"])
        need(finding["materiality"] in {"MATERIAL", "OUT_OF_SCOPE", "UNKNOWN"}, "INVALID_MATERIALITY")
        need(finding["disposition"] in {"OPEN", "DISMISSED"}, "INVALID_FINDING_DISPOSITION")
        need(finding["materiality"] != "UNKNOWN", "UNKNOWN_FINDING_MATERIALITY")
        material_open |= finding["materiality"] == "MATERIAL" and finding["disposition"] == "OPEN"
    need((outcome == "COUNTEREXAMPLE_FOUND") == material_open, "FINDING_OUTCOME_MISMATCH")
    need(not material_open, "UNRESOLVED_COUNTEREXAMPLE")
    need(outcome != "UNOBSERVABLE", "PROBE_UNOBSERVABLE")


def close(baseline_path: Path, binding: dict, activity: dict, results: list[dict]) -> dict:
    reasons = []
    try:
        baseline = current(baseline_path, binding)
        need(activity["run_id"] == binding["run_id"], "FOREIGN_ACTIVITY")
        references(activity["evidence"])
        effects = rows(activity["effects"], "effects")
        for effect in effects.values():
            need(text(effect["owner"]) and effect["state"] == "SETTLED", "UNSETTLED_EFFECT")
            references(effect["evidence"])
        definitions = {"gate": rows(baseline["gates"], "gates"), "observation": rows(baseline["observations"], "observations"), "probe": rows(baseline["lanes"], "lanes")}
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
            need(result["schema"] == "iis-assurance-result/v1", "INVALID_RESULT")
            key = (result["kind"], result["id"])
            need(key not in seen, "DUPLICATE_RESULT")
            seen.add(key)
            need(key in started and result["invocation"] == started[key], "UNATTRIBUTABLE_RESULT")
            need(result["binding"] == identity(binding), "RESULT_BINDING_MISMATCH")
            references(result["evidence"])
            need(isinstance(result["effects"], list) and all(text(x) for x in result["effects"]) and set(result["effects"]).issubset(effects), "UNRECORDED_EFFECT")
            need(result["completion"] == "COMPLETE", "INCOMPLETE_RESULT")
            definition = definitions[key[0]][key[1]]
            if key[0] == "gate":
                check_gate(definition, result, binding)
            elif key[0] == "observation":
                need(all(result[field] == definition[field] for field in ("initial_state", "trigger", "readback", "predicate")), "OBSERVATION_BOUNDARY_MISMATCH")
                need(result["outcome"] == "SATISFIED", "OBSERVATION_NOT_SATISFIED")
            else:
                check_probe(definition, result)
        need(seen == set(started), "STARTED_RESULT_MISSING")
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        reasons.append(str(exc))
    return {"schema": "iis-assurance-closure/v1", "binding": identity(binding),
            "status": "BLOCKED" if reasons else "EVIDENCE_COMPLETE", "reasons": reasons}


def recording(ready: bytes, done: bytes) -> dict:
    need(ready.count(b"\nStatus: ready\n") == 1, "READY_STATUS_REQUIRED")
    need(done == ready.replace(b"\nStatus: ready\n", b"\nStatus: done\n", 1), "NOT_STATUS_ONLY")
    return {"ready_sha256": digest(ready), "done_sha256": digest(done), "status_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("baseline", type=Path)
    seal = commands.add_parser("bind")
    seal.add_argument("baseline", type=Path)
    seal.add_argument("--root", type=Path, required=True)
    seal.add_argument("--base", required=True)
    seal.add_argument("--execution", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    execution = commands.add_parser("bind-execution")
    execution.add_argument("binding", type=Path)
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
    try:
        if args.action == "validate":
            _, raw = load_baseline(args.baseline)
            result = {"status": "VALID", "baseline_sha256": digest(raw)}
        elif args.action == "bind":
            result = bind(args.baseline, args.root, args.base, read_json(args.execution))
            need(not args.output.resolve().is_relative_to(args.root), "EVIDENCE_INSIDE_TARGET")
            save(args.output, result)
        elif args.action == "bind-execution":
            old = read_json(args.binding)
            current(Path(old["baseline"]["path"]), old)
            new_execution = read_json(args.execution)
            check_execution(new_execution)
            result = {**old, "run_id": uuid.uuid4().hex, "execution": new_execution}
            need(not args.output.resolve().is_relative_to(Path(old["source"]["root"])), "EVIDENCE_INSIDE_TARGET")
            save(args.output, result)
        elif args.action == "run":
            result = run_gate(args.baseline, read_json(args.binding), args.gate_id, args.output)
        elif args.action == "close":
            result = close(args.baseline, read_json(args.binding), read_json(args.activity), [read_json(path) for path in args.results])
        else:
            result = recording(args.ready.read_bytes(), args.done.read_bytes())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get("status") == "BLOCKED" or result.get("completion") == "BLOCKED" else 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reasons": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
