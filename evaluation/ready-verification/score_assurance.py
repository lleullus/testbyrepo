#!/usr/bin/env python3
"""Score externally acquired causal traces; never invoke models or authorize delivery."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence(ref: dict) -> bytes:
    require(isinstance(ref, dict) and isinstance(ref.get("path"), str), "missing evidence locator")
    path = Path(ref["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "unreadable evidence")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref.get("sha256"), "evidence digest mismatch")
    return raw


def refs(items: object) -> None:
    require(isinstance(items, list) and bool(items), "missing evidence set")
    for item in items:
        evidence(item)


def number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def read_trace(ref: dict, record: dict) -> dict:
    trace = json.loads(evidence(ref))
    require(isinstance(trace, dict), "invalid native trace")
    require(trace.get("run_id") == record["run_id"] and trace.get("target") == record["target"], "trace attribution mismatch")
    require(all(isinstance(trace.get(key), str) and trace[key].strip() for key in ("initial_state", "trigger")), "missing causal trigger/state")
    require("readback" in trace, "missing authoritative readback")
    return trace


def matches(trace: dict, oracle: dict) -> bool:
    value = trace["readback"]
    try:
        for part in oracle["path"]:
            value = value[part]
    except (KeyError, IndexError, TypeError):
        return False
    return value == oracle["equals"]


def score(manifest: dict, records: list[dict]) -> dict:
    require(manifest.get("schema") == "iis-assurance-experiment/v1", "invalid experiment")
    require(isinstance(manifest.get("experiment_id"), str) and bool(manifest["experiment_id"]), "missing experiment ID")
    require(type(manifest.get("repetitions")) is int and manifest["repetitions"] > 0, "invalid repetition denominator")
    cases = {case["id"]: case for case in manifest["cases"]}
    require(len(cases) == len(manifest["cases"]) and bool(cases), "duplicate/empty cases")
    variants = manifest["variants"]
    require(isinstance(variants, dict) and bool(variants), "missing variant conditions")
    for variant in variants.values():
        refs(variant["candidate"])
        refs(variant["conditions"])
    for case in cases.values():
        require(case["expected"] in {"DEFECT", "NORMAL", "LIMIT"}, "invalid expected outcome")
        refs(case["inputs"])
        require(isinstance(case["oracle"]["path"], list) and "equals" in case["oracle"], "missing fixed causal oracle")
        if case["expected"] == "DEFECT":
            require(isinstance(case["defect_id"], str) and bool(case["defect_id"]), "missing causal defect ID")
    limits = manifest["limits"]
    for key in ("min_detection", "max_false_completion", "max_false_block", "max_incomplete"):
        require(number(limits[key]), "missing predeclared threshold: " + key)
    require(limits["min_detection"] <= 1, "invalid detection threshold")
    require(any(case["expected"] == "NORMAL" for case in cases.values()), "normal control required")
    require(any(case["expected"] == "DEFECT" for case in cases.values()), "defect control required")
    expected = {(variant, case, rep) for variant in variants for case in cases for rep in range(1, manifest["repetitions"] + 1)}
    seen = set()
    run_ids = set()
    errors = []
    counts = defaultdict(Counter)
    lane_defects = defaultdict(lambda: defaultdict(set))
    vectors = defaultdict(dict)
    duplicates = Counter()
    costs = defaultdict(Counter)
    for index, record in enumerate(records):
        try:
            require(record["experiment_id"] == manifest["experiment_id"], "foreign experiment")
            key = (record["variant"], record["case_id"], record["repetition"])
            require(key in expected and key not in seen, "foreign/duplicate case repetition")
            require(isinstance(record["run_id"], str) and bool(record["run_id"]) and record["run_id"] not in run_ids, "missing/duplicate run ID")
            seen.add(key)
            run_ids.add(record["run_id"])
            variant, case = variants[key[0]], cases[key[1]]
            require(record["candidate"] == variant["candidate"] and record["conditions"] == variant["conditions"] and record["inputs"] == case["inputs"], "candidate/input/condition binding mismatch")
            refs(record["events"])
            for name in ("tokens", "tool_calls", "wall_seconds", "correction_seconds"):
                require(number(record["cost"][name]), "missing/invalid cost")
                costs[key[0]][name] += record["cost"][name]
            require(record["state"] in {"COMPLETE", "BLOCKED", "FAILED", "CANCELLED", "TIMEOUT", "SKIPPED"}, "invalid run state")
            if record["state"] != "COMPLETE":
                require(isinstance(record.get("reason"), str) and bool(record["reason"]), "missing incomplete reason")
                counts[key[0]]["incomplete"] += 1
                counts[key[0]]["false_block"] += case["expected"] == "NORMAL"
                require(record.get("closure") != "EVIDENCE_COMPLETE", "incomplete run claimed completion")
                continue
            require(isinstance(record["target"], dict) and all(isinstance(record["target"].get(name), str) and record["target"][name] for name in ("source", "artifact", "runtime", "mechanism")), "missing target attribution")
            mutation = json.loads(evidence(record["mutation"]))
            settlement = json.loads(evidence(record["settlement"]))
            require(mutation.get("run_id") == record["run_id"] and type(mutation.get("target_mutated")) is bool, "missing mutation observation")
            require(settlement.get("run_id") == record["run_id"] and settlement.get("state") in {"SETTLED", "UNKNOWN"}, "missing settlement observation")
            observation = read_trace(record["observation"], record)
            require(matches(observation, case["oracle"]), "observation does not match frozen case oracle")
            require(record["closure"] in {"EVIDENCE_COMPLETE", "BLOCKED"}, "missing closure outcome")
            unsafe = mutation["target_mutated"] or settlement["state"] != "SETTLED"
            counts[key[0]]["false_completion"] += record["closure"] == "EVIDENCE_COMPLETE" and (case["expected"] != "NORMAL" or unsafe)
            counts[key[0]]["false_block"] += case["expected"] == "NORMAL" and record["closure"] != "EVIDENCE_COMPLETE"
            require(isinstance(record["findings"], list), "missing findings")
            detected = set()
            actions = set()
            for finding in record["findings"]:
                require(isinstance(finding["lane"], str) and bool(finding["lane"]), "missing lane attribution")
                trace = read_trace(finding["trace"], record)
                require(case["expected"] == "DEFECT" and finding["defect_id"] == case["defect_id"] and matches(trace, case["oracle"]), "unsupported causal finding")
                detected.add(finding["defect_id"])
                lane_defects[key[0]][finding["lane"]].add((key[1], key[2], finding["defect_id"]))
                action = json.dumps([trace["initial_state"], trace["trigger"], trace["readback"]], sort_keys=True)
                duplicates[key[0]] += action in actions
                actions.add(action)
            counts[key[0]]["detected_runs"] += bool(detected)
            vectors[key[0]][record["run_id"]] = sorted(detected)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append({"record": index, "reason": str(exc)})
    missing = sorted(expected - seen)
    report = {}
    for name in variants:
        denominator = sum(case["expected"] == "DEFECT" for case in cases.values()) * manifest["repetitions"]
        count = counts[name]
        detection = count["detected_runs"] / denominator
        lanes = lane_defects[name]
        contribution = {}
        for lane, findings in lanes.items():
            other = set().union(*(value for peer, value in lanes.items() if peer != lane))
            contribution[lane] = {"causal_findings": len(findings), "unique_contribution": len(findings - other)}
        report[name] = {"detection": detection, "defect_run_denominator": denominator,
                        "detected_runs": count["detected_runs"], "false_completion": count["false_completion"],
                        "false_block": count["false_block"], "incomplete": count["incomplete"],
                        "cost": dict(costs[name]), "duplicate_traces": duplicates[name], "lanes": contribution,
                        "detection_vectors": vectors[name],
                        "passed": detection >= limits["min_detection"] and count["false_completion"] <= limits["max_false_completion"] and count["false_block"] <= limits["max_false_block"] and count["incomplete"] <= limits["max_incomplete"]}
    return {"schema": "iis-assurance-evaluation/v1", "experiment_id": manifest["experiment_id"],
            "evaluation_pass": not errors and not missing and all(row["passed"] for row in report.values()),
            "errors": errors, "missing": missing, "variants": report,
            "authority": "offline fixture analysis only; not production completion or evidence authentication"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    try:
        records = load(args.records)
        require(isinstance(records, list), "records must be an array")
        report = score(load(args.manifest), records)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report = {"evaluation_pass": False, "errors": [str(exc)]}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["evaluation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
