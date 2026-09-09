#!/usr/bin/env python3
"""Expose decision-relevant raw tool evidence without adjudicating product meaning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex

from run_agent import load_events, summarize, text_content


def inspect(run_root: Path, stage: str) -> dict:
    metadata = json.loads((run_root / "metadata.json").read_text(encoding="utf-8"))
    summary = summarize(load_events(run_root / stage / "events.jsonl"))
    results = {event["toolCallId"]: event for event in summary["tool_results"]}
    evidence, first_trigger = [], None
    entry = Path(metadata["trigger_argv"][1])
    for ordinal, call in enumerate(summary["tool_calls"], 1):
        name = call["toolName"]
        if name not in {"bash", "ready_contract", "ready_finalize", "hub", "write"}:
            continue
        result = results.get(call["toolCallId"])
        if result is None:
            evidence.append({"tool_ordinal": ordinal, "tool": name, "args": call.get("args"), "completed": False})
            continue
        raw = text_content(result.get("result", {}))
        try:
            output = json.loads(raw)
        except json.JSONDecodeError:
            output = raw
        args = call.get("args", {})
        if name == "bash":
            try:
                command = shlex.split(args.get("command", ""))
            except ValueError:
                command = []
        else:
            command = []
        script_index = 1
        while script_index < len(command) and command[script_index] in ("-B", "-u", "-I"):
            script_index += 1
        script = Path(command[script_index]) if script_index < len(command) else None
        cwd = Path(args.get("cwd", metadata["project_root"]))
        resolved_script = (cwd / script).resolve() if script is not None else None
        actual_entry_invocation = bool(command and Path(command[0]).name in ("python", "python3", Path(metadata["trigger_argv"][0]).name)
                                       and resolved_script == entry.resolve() and not result.get("isError"))
        if actual_entry_invocation and first_trigger is None:
            first_trigger = ordinal
        evidence.append({"tool_ordinal": ordinal, "tool_call_id": call["toolCallId"], "tool": name, "args": args,
                         "completed": True, "is_error": result.get("isError", False), "output": output,
                         "ordinary_entrypoint_invoked": actual_entry_invocation})
    return {"case_id": metadata["case_id"], "run_id": metadata["run_id"], "stage": stage,
            "terminal_text": summary["terminal_text"], "parsed_verdict": summary["parsed_verdict"],
            "preparation_completion": summary["preparation_completion"], "actual_models": summary["actual_models"],
            "first_entrypoint_tool_ordinal": first_trigger, "raw_tool_evidence": evidence,
            "interpretation": "Command execution is evidence of a boundary attempt, not proof of its success or sufficiency."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("stage", choices=("plan", "prepare/planner", "prepare/heuristic", "prepare/reviewer", "prepare/lead", "implement", "verify"))
    args = parser.parse_args()
    print(json.dumps(inspect(args.run_root, args.stage), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
