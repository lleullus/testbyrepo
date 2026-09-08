#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "manifest.json"
VALID_VERDICTS = {"VERIFIED", "FAILED", "INCONCLUSIVE", "VERIFICATION NOT STARTED"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_verdict(value: object) -> str:
    raw = str(value or "").strip().upper()
    if raw in VALID_VERDICTS:
        return raw
    return "INVALID"


def _allowed_verdicts(case: dict[str, Any], expected: str) -> tuple[set[str], bool]:
    if "allowed_verdicts" not in case:
        return {expected}, expected in VALID_VERDICTS

    values = case["allowed_verdicts"]
    if not isinstance(values, list) or not values:
        return set(), False

    allowed: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            return set(), False
        verdict = normalize_verdict(value)
        if verdict not in VALID_VERDICTS:
            return set(), False
        allowed.add(verdict)
    return allowed, True


def _minimum_runs_per_case(manifest: dict[str, Any]) -> int | None:
    value = manifest.get("minimum_runs_per_case", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _run_id_key(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def score(manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    cases = {case["case_id"]: case for case in manifest["cases"]}
    by_case: dict[str, list[dict[str, Any]]] = {}
    unknown_records: list[str] = []
    run_ids: dict[str, object] = {}
    duplicate_run_ids: list[object] = []
    for record in records:
        case_id = str(record.get("case_id", ""))
        if case_id not in cases:
            unknown_records.append(case_id)
            continue
        by_case.setdefault(case_id, []).append(record)
        if "run_id" in record:
            run_id = record["run_id"]
            key = _run_id_key(run_id)
            if key in run_ids:
                duplicate_run_ids.append(run_id)
            else:
                run_ids[key] = run_id

    minimum_runs = _minimum_runs_per_case(manifest)
    false_verified = 0
    normal_false_rejection = 0
    malformed_terminal = 0
    target_mutation = 0
    unexpected_verdict_runs = 0
    invalid_allowed_verdict_cases: list[str] = []
    under_run_cases: list[str] = []
    rows: list[dict[str, Any]] = []
    confusion: Counter[str] = Counter()

    for case_id, case in cases.items():
        expected = normalize_verdict(case["expected"])
        allowed_verdicts, allowed_verdicts_valid = _allowed_verdicts(case, expected)
        if not allowed_verdicts_valid:
            invalid_allowed_verdict_cases.append(case_id)
        case_records = by_case.get(case_id, [])
        if minimum_runs is None or len(case_records) < minimum_runs:
            under_run_cases.append(case_id)
        actuals: list[str] = []
        false_verified_runs = 0
        normal_rejection_runs = 0
        mutation_runs = 0
        unexpected_runs = 0
        for record in case_records:
            actual = normalize_verdict(record.get("parsed_verdict")) if record.get("clean_transport") is not False else "INVALID"
            actuals.append(actual)
            confusion[f"{expected} -> {actual}"] += 1
            if actual not in allowed_verdicts:
                unexpected_verdict_runs += 1
                unexpected_runs += 1
            if actual == "VERIFIED" and actual not in allowed_verdicts:
                false_verified += 1
                false_verified_runs += 1
            if case.get("normal_twin") and expected == "VERIFIED" and actual != "VERIFIED":
                normal_false_rejection += 1
                normal_rejection_runs += 1
            if actual == "INVALID":
                malformed_terminal += 1
            if bool(record.get("target_mutated")):
                target_mutation += 1
                mutation_runs += 1
        rows.append(
            {
                "case_id": case_id,
                "family": case["family"],
                "variant": case["variant"],
                "runs": len(case_records),
                "expected": expected,
                "actual": actuals,
                "false_verified": false_verified_runs,
                "normal_false_rejection": normal_rejection_runs,
                "target_mutated": mutation_runs,
                "unexpected_verdict_runs": unexpected_runs,
            }
        )

    missing_cases = sorted(case_id for case_id in cases if not by_case.get(case_id))
    gate = manifest["release_gate"]
    release_pass = (
        false_verified <= int(gate["false_verified"])
        and normal_false_rejection <= int(gate["normal_false_rejection"])
        and malformed_terminal <= int(gate.get("malformed_terminal", 0))
        and target_mutation <= int(gate.get("target_mutation_runs", 0))
        and unexpected_verdict_runs <= int(gate.get("unexpected_verdict_runs", 0))
        and len(missing_cases) <= int(gate["missing_cases"])
        and not unknown_records
        and not duplicate_run_ids
        and not under_run_cases
        and not invalid_allowed_verdict_cases
    )
    return {
        "schema": "iis-ready-verification-score/v1",
        "release_pass": release_pass,
        "false_verified": false_verified,
        "normal_false_rejection": normal_false_rejection,
        "malformed_terminal": malformed_terminal,
        "target_mutation_runs": target_mutation,
        "unexpected_verdict_runs": unexpected_verdict_runs,
        "missing_cases": missing_cases,
        "unknown_record_case_ids": unknown_records,
        "duplicate_run_ids": duplicate_run_ids,
        "under_run_cases": under_run_cases,
        "invalid_allowed_verdict_cases": invalid_allowed_verdict_cases,
        "class_confusion": dict(sorted(confusion.items())),
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score externally produced Ready verification agent results.")
    parser.add_argument("results", type=Path, help="JSON array of agent-run records")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = load_json(args.manifest)
    records = load_json(args.results)
    if not isinstance(records, list):
        raise SystemExit("results must be a JSON array")
    report = score(manifest, records)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["release_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
