#!/usr/bin/env python3
"""Prepare fixed Product Thesis prompts and metadata; no agent runner or semantic grading."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import uuid

CASES = Path(__file__).with_name("cases.json")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_relative_path(raw: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\x00" in raw or "\\" in raw:
        raise ValueError("fixture path must be a non-empty POSIX relative path")
    parsed = PurePosixPath(raw)
    if parsed.is_absolute() or ".." in parsed.parts:
        raise ValueError("fixture path must stay below the project root")
    return Path(*parsed.parts)


def reject_symlink_chain(project: Path, relative: Path) -> None:
    current = project
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("fixture path may not traverse a symlink")


def materialize_fixture_files(project: Path, entries: list[dict]) -> list[dict]:
    metadata: list[dict] = []
    seen: set[str] = set()
    for entry in entries:
        relative = fixture_relative_path(entry["path"])
        key = relative.as_posix()
        if key in seen:
            raise ValueError(f"duplicate fixture path: {key}")
        seen.add(key)
        reject_symlink_chain(project, relative)
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        reject_symlink_chain(project, relative)
        target.write_text(entry["content"], encoding="utf-8")
        metadata.append({"path": key, "sha256": sha(target)})
    return metadata


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
    fixture_files = materialize_fixture_files(project, case.get("fixture_files", []))
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
        + "Read the supplied iis-workflow skill source and only the skills to which it routes. "
        + "Inspect evaluation-context.json, follow that routing contract, and return only the result it requires. "
        + "Do not infer a stage or output schema from the evaluator. Save the Thesis source when the supplied contract requires it; that write is authorized before request closure and is not downstream approval. "
        + ("Follow the user's exact downstream planning and stop authority; do not implement or verify a product. "
           if case.get("downstream_planning") else "Do not execute the downstream planning leaf or write other planning artifacts. ")
    )
    if fixture_files:
        prompt += "\nFixture source files (inspect the actual project files):\n" + "".join(
            f"- {item['path']}\n" for item in fixture_files
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
        "fixture_builder_sha256": sha(Path(__file__)),
        "fixture_files": fixture_files,
        "model": protocol["model"],
        "thinking": protocol["thinking"],
        "required_observations": case["required_observations"],
        "forbidden_observations": case["forbidden_observations"],
    }
    path = root / "metadata.json"
    write_json(path, metadata)
    return path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("--arena", required=True, type=Path)
    prepare_parser.add_argument("--variant", required=True)
    prepare_parser.add_argument("--repetition", required=True, type=int)
    args = parser.parse_args()
    print(prepare(args.case_id, args.arena, args.variant, args.repetition))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
