#!/usr/bin/env python3
"""Prepare and capture fixed Product Thesis model cases without auto-grading semantics."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
CASES = Path(__file__).with_name("cases.json")
RUN_AGENT = ROOT / "ready-verification/run_agent.py"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_by_id(case_id: str) -> dict:
    matches = [case for case in read_json(CASES)["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"unknown or duplicate case: {case_id}")
    return matches[0]


def prepare(case_id: str, arena: Path, variant: str, repetition: int) -> Path:
    cohort = read_json(CASES)
    protocol = cohort["protocol"]
    if variant not in protocol["variants"]:
        raise ValueError("variant is outside the frozen cohort")
    if repetition not in protocol["repetitions"]:
        raise ValueError("repetition is outside the frozen cohort")
    case = case_by_id(case_id)
    root = arena.resolve() / uuid.uuid4().hex
    project = root / "product"
    evidence = root / "evidence"
    project.mkdir(parents=True, mode=0o700)
    evidence.mkdir(mode=0o700)
    context = {
        "case_id": case_id,
        "fixture": case.get("fixture", "brief-only"),
        "current_product_evidence": "Use only the user prompt and this fixture. No implementation mechanism is product authority.",
        "approved_product_meaning": (
            "Current and applicable; reuse it without recalibration."
            if case.get("fixture") in {"approved-spec", "current-scope-thesis"}
            else "None"
        ),
        "planning_state": "One existing pointer; read-only inspection requested." if case.get("fixture") == "planning-state" else "No prior pointer required.",
    }
    write_json(project / "evaluation-context.json", context)
    prompt = (
        case["prompt"]
        + f"\n\nProject Root: {project}\n"
        + "Read the currently installed iis-workflow skill and only the skills to which that installed workflow routes. "
        + "Inspect evaluation-context.json, follow the installed routing contract, and return only the result that contract requires. "
        + "Do not infer a stage or output schema from the evaluator. Do not mutate files or execute the downstream planning leaf."
    )
    metadata = {
        "schema": "iis-product-thesis-case/v1",
        "case_id": case_id,
        "variant": variant,
        "repetition": repetition,
        "project_root": str(project),
        "evidence_root": str(evidence),
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "case_file": str(CASES),
        "case_file_sha256": sha(CASES),
        "runner_sha256": sha(Path(__file__)),
        "model": protocol["model"],
        "thinking": protocol["thinking"],
        "required_observations": case["required_observations"],
        "forbidden_observations": case["forbidden_observations"],
    }
    path = root / "metadata.json"
    write_json(path, metadata)
    return path


def load_runner():
    spec = importlib.util.spec_from_file_location("product_thesis_run_agent", RUN_AGENT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load shared isolated runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(metadata_path: Path, agent_dir: Path, payload: Path, output: Path, timeout: int) -> dict:
    metadata = read_json(metadata_path.resolve(strict=True))
    if metadata.get("schema") != "iis-product-thesis-case/v1":
        raise ValueError("unsupported metadata")
    if sha(CASES) != metadata["case_file_sha256"] or sha(Path(__file__)) != metadata["runner_sha256"]:
        raise ValueError("evaluation definition changed after preparation")
    if hashlib.sha256(metadata["prompt"].encode()).hexdigest() != metadata["prompt_sha256"]:
        raise ValueError("prepared prompt drift")
    runner = load_runner()
    result = runner.invoke(
        project_root=Path(metadata["project_root"]),
        prompt=metadata["prompt"],
        output_dir=output,
        agent_dir=agent_dir,
        payload=payload,
        model=metadata["model"],
        thinking=metadata["thinking"],
        timeout=timeout,
        stage="plan",
    )
    record = {
        "schema": "iis-product-thesis-observation/v1",
        "metadata": str(metadata_path.resolve()),
        "metadata_sha256": sha(metadata_path.resolve()),
        "case_id": metadata["case_id"],
        "variant": metadata["variant"],
        "repetition": metadata["repetition"],
        "required_observations": metadata["required_observations"],
        "forbidden_observations": metadata["forbidden_observations"],
        "automatic_semantic_acceptance": False,
        "raw_events": result["raw_events"],
        "terminal_text": result["terminal_text"],
        "clean_transport": result["clean_transport"],
        "actual_models": result["actual_models"],
    }
    write_json(output / "product-thesis-observation.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("--arena", required=True, type=Path)
    prepare_parser.add_argument("--variant", required=True)
    prepare_parser.add_argument("--repetition", required=True, type=int)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--metadata", required=True, type=Path)
    run_parser.add_argument("--agent-dir", required=True, type=Path)
    run_parser.add_argument("--payload", required=True, type=Path)
    run_parser.add_argument("--output", required=True, type=Path)
    run_parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.case_id, args.arena, args.variant, args.repetition))
        return 0
    record = run(args.metadata, args.agent_dir, args.payload, args.output, args.timeout)
    print(json.dumps({key: record[key] for key in ("case_id", "variant", "repetition", "clean_transport", "actual_models")}, ensure_ascii=False))
    return 0 if record["clean_transport"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
