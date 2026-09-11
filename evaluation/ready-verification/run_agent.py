#!/usr/bin/env python3
"""Capture one real, isolated OMP invocation; never manufacture a verdict."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from typing import Any


def load_events(path: Path) -> list[dict[str, Any]]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def text_content(message: dict[str, Any]) -> str:
    content = message.get("content", [])
    if isinstance(content, str):
        return content
    return "\n".join(part.get("text", "") for part in content if part.get("type") == "text")


def terminal_lines(terminal: str) -> list[str]:
    """Ignore quoted examples and fenced/intermediate reports."""
    lines = []
    in_fence = False
    for raw in terminal.splitlines():
        if re.match(r"^\s*(?:```|~~~)", raw):
            in_fence = not in_fence
            lines.append("")
            continue
        if in_fence or raw.lstrip().startswith(">") or raw.startswith(("    ", "\t")):
            lines.append("")
            continue
        lines.append(raw.strip().replace("**", "").replace("`", ""))
    return lines


def canonical_field(terminal: str, heading: str, field: str, values: str) -> str | None:
    lines = terminal_lines(terminal)
    headings = [index for index, line in enumerate(lines)
                if re.fullmatch(r"(?:#{1,6}\s*)?" + re.escape(heading), line, re.IGNORECASE)]
    if len(headings) != 1:
        return None
    fields = [(index, match.group(1)) for index, line in enumerate(lines) if index > headings[0]
              and (match := re.fullmatch(r"(?:[-*+]\s+)?" + re.escape(field) + r"\s*:\s*(.*)", line, re.IGNORECASE))]
    if len(fields) != 1:
        return None
    index, value = fields[0]
    if not value and index + 1 < len(lines):
        value = lines[index + 1]
    match = re.fullmatch(r"(" + values + r")(?:\s+[—–-]\s+.*)?", value, re.IGNORECASE)
    return match.group(1) if match else None


def _verification_verdict(terminal: str) -> str | None:
    lines = terminal_lines(terminal)
    not_started = [line for line in lines if re.fullmatch(r"(?:#{1,6}\s*)?VERIFICATION NOT STARTED", line, re.IGNORECASE)]
    verdict = canonical_field(terminal, "READY TICKET VERIFICATION RESULT", "Verification Verdict", "VERIFIED|FAILED|INCONCLUSIVE")
    if not_started:
        return "VERIFICATION NOT STARTED" if len(not_started) == 1 and not any("READY TICKET VERIFICATION RESULT" in line.upper() for line in lines) else None
    return verdict.upper() if verdict else None


def boundary_results(events: list[dict[str, Any]], tool_name: str, action: str | None = None) -> list[dict[str, Any]]:
    """Return successful explicit Ready boundary-tool results; assistant narration is never evidence."""
    calls = {event.get("toolCallId"): event for event in events if event.get("type") == "tool_execution_start"}
    results = []
    for event in events:
        if event.get("type") != "tool_execution_end" or event.get("isError"):
            continue
        call = calls.get(event.get("toolCallId"), {})
        args = call.get("args", {})
        if call.get("toolName") != tool_name or (action is not None and args.get("action") != action):
            continue
        result = event.get("result", {})
        if not isinstance(result, dict):
            continue
        details = result.get("details")
        if not isinstance(details, dict):
            try:
                details = json.loads(text_content(result))
            except (TypeError, json.JSONDecodeError):
                continue
        if isinstance(details, dict):
            results.append({"args": args, "result": details, "tool_call_id": event.get("toolCallId")})
    return results

def host_ready_terminal_handles(events: list[dict[str, Any]]) -> list[str]:
    """Read handles only from host-produced task results/async delivery, never assistant narration."""
    calls = {event.get("toolCallId"): event for event in events if event.get("type") == "tool_execution_start"}
    sources: list[str] = []
    for event in events:
        if event.get("type") == "message_start":
            message = event.get("message", {})
            if message.get("role") == "custom" and message.get("customType") == "async-result" and message.get("attribution") == "agent":
                sources.append(str(message.get("content", "")))
        elif event.get("type") == "tool_execution_end" and not event.get("isError"):
            call = calls.get(event.get("toolCallId"), {})
            if call.get("toolName") == "task" and isinstance(event.get("result"), dict):
                sources.append(text_content(event["result"]))
    handles: list[str] = []
    for source in sources:
        handles.extend(re.findall(r"(?m)^Ready Verification Terminal: (ready-terminal-[0-9a-f-]+)$", source))
    return handles


def summarize(events: list[dict[str, Any]]) -> dict[str, Any]:
    messages = [event["message"] for event in events if event.get("type") == "message_end" and event.get("message", {}).get("role") == "assistant"]
    last = messages[-1] if messages else {}
    terminal = text_content(last) if last.get("stopReason") != "toolUse" and not any(
        part.get("type") == "toolCall" for part in last.get("content", []) if isinstance(part, dict)
    ) else ""
    agent_ended = any(event.get("type") == "agent_end" for event in events)
    model_completed = agent_ended and last.get("stopReason") == "stop" and bool(terminal.strip()) and not last.get("errorMessage")
    finalizations = boundary_results(events, "ready_finalize")
    finalization = finalizations[-1]["result"] if finalizations else None
    finalization_args = finalizations[-1]["args"] if finalizations else None
    delivered_handles = host_ready_terminal_handles(events)
    # Sequential re-verification supersedes earlier held handles; preserve raw delivery history.
    latest_handle = delivered_handles[-1] if delivered_handles else None
    host_terminal = latest_handle if latest_handle and delivered_handles.count(latest_handle) == 1 else None
    current_finalization = finalization if (host_terminal
        and finalization_args == {"terminal_handle": host_terminal}
        and finalization.get("verification_terminal") == host_terminal) else None
    parsed_text_verdict = _verification_verdict(terminal)
    finalizer_verdict = current_finalization.get("verification_verdict") if current_finalization else None
    parsed = finalizer_verdict if finalizer_verdict in {"VERIFIED", "FAILED", "INCONCLUSIVE"} else parsed_text_verdict
    preparation = canonical_field(terminal, "READY TICKET PLAN RESULT", "Completion", "COMPLETE|BLOCKED|PARTIAL")
    review = canonical_field(terminal, "READY TICKET PLAN RESULT", "Plan Review", r"/[^\n]+")
    implementation = canonical_field(terminal, "IMPLEMENT RESULT", "Completion", "COMPLETE|BLOCKED|PARTIAL")
    verifier_progression = current_finalization.get("verifier_ticket_progression") if current_finalization else None
    if verifier_progression is None:
        verifier_progression = canonical_field(terminal, "READY TICKET VERIFICATION RESULT", "Verifier Ticket Progression", "PENDING CALLER FINALIZATION|NOT APPLICABLE")
    verification_binding = current_finalization.get("verification_binding") if current_finalization else None
    verification_binding_sha256 = current_finalization.get("verification_binding_sha256") if current_finalization else None
    host_verdict_record = current_finalization.get("verification_verdict_record") if current_finalization else None
    host_verdict_record_sha256 = current_finalization.get("verification_verdict_record_sha256") if current_finalization else None
    verifier_model = current_finalization.get("verifier_model") if current_finalization else None
    calls = [event for event in events if event.get("type") == "tool_execution_start"]
    results = [event for event in events if event.get("type") == "tool_execution_end"]
    tool_errors = [event for event in results if event.get("isError") is True]
    usage = {key: sum(message.get("usage", {}).get(key, 0) for message in messages) for key in ("input", "output", "cacheRead", "cacheWrite", "totalTokens")}
    models = {f"{message.get('provider')}/{message.get('model')}" for message in messages}
    if isinstance(verifier_model, str):
        models.add(verifier_model.split(":", 1)[0])
    models = sorted(models)
    return {"terminal_text": terminal, "parsed_verdict": parsed if model_completed else None,
            "preparation_completion": preparation.upper() if model_completed and preparation else None,
            "plan_review_path": review if model_completed else None,
            "verifier_ticket_progression": verifier_progression.upper() if model_completed and isinstance(verifier_progression, str) else None,
            "host_verifier_terminal_handle": host_terminal if model_completed else None,
            "host_verifier_terminal_delivery_count": len(delivered_handles),
            "verifier_model": verifier_model if model_completed else None,
            "verification_binding_path": verification_binding if model_completed else None,
            "verification_binding_sha256": verification_binding_sha256.lower() if model_completed and isinstance(verification_binding_sha256, str) else None,
            "host_verdict_record_path": host_verdict_record if model_completed else None,
            "host_verdict_record_sha256": host_verdict_record_sha256.lower() if model_completed and isinstance(host_verdict_record_sha256, str) else None,
            "caller_finalization": finalization,
            "caller_finalization_args": finalization_args,
            "ticket_progression": current_finalization.get("ticket_progression") if current_finalization else None,
            "progression_basis": current_finalization.get("progression_basis") if current_finalization else None,
            "ticket_status_after": current_finalization.get("ticket_status_after") if current_finalization else None,
            "implementation_completion": implementation if model_completed else None,
            "tool_calls": calls, "tool_results": results, "tool_errors": tool_errors,
            "usage": usage, "actual_models": models,
            "agent_ended": agent_ended, "model_completed": bool(model_completed),
            "stop_reason": last.get("stopReason"), "error_message": last.get("errorMessage")}


def invoke(*, project_root: Path, prompt: str, output_dir: Path, agent_dir: Path,
           payload: Path, model: str, thinking: str = "medium",
           timeout: int = 600, session_dir: Path | None = None,
           resume_session: Path | None = None, wall_timeout_seconds: float | None = None,
           stage: str, boundary_callback=None) -> dict[str, Any]:
    project_root = project_root.resolve(strict=True)
    payload = payload.resolve(strict=True)
    agent_dir = agent_dir.resolve(strict=True)
    output_dir = output_dir.resolve()
    if output_dir.is_relative_to(project_root):
        raise ValueError("raw run evidence must be outside Project Root")
    if resume_session is not None and session_dir is None:
        raise ValueError("resuming requires one execution-owned session directory")
    if session_dir is not None:
        session_dir = session_dir.resolve()
        if session_dir.is_relative_to(project_root):
            raise ValueError("session evidence must be outside Project Root")
        if resume_session is None:
            session_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
        else:
            resume_session = resume_session.resolve(strict=True)
            if resume_session.parent != session_dir or not resume_session.is_file():
                raise ValueError("resume target must belong to the exact session directory")
            with resume_session.open(encoding="utf-8") as handle:
                header = json.loads(handle.readline())
                if header.get("type") == "title":
                    header = json.loads(handle.readline())
            if header.get("type") != "session" or Path(header.get("cwd", "")).resolve() != project_root:
                raise ValueError("resume target belongs to a different product")
    if wall_timeout_seconds is not None and wall_timeout_seconds <= 0:
        raise ValueError("wall timeout must be positive")
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    prompt_path = output_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    environment = dict(os.environ)
    environment.pop("OMP_PROFILE", None)
    bundle = json.loads((payload / "bundle.json").read_text(encoding="utf-8"))
    if bundle.get("schema") != "iis-bundle/v2" or bundle.get("protocol") != 2:
        raise ValueError("a complete current protocol-2 bundle is required")
    for key in ("IIS_READY_VALIDATOR_PATH", "IIS_READY_IIS_WORKFLOW_SKILL"):
        environment.pop(key, None)
    environment.update(PI_CODING_AGENT_DIR=str(agent_dir), PYTHONDONTWRITEBYTECODE="1")
    boundary_tools_required = stage in {"prepare", "implement", "verify", "adaptive"}
    if boundary_tools_required:
        environment["IIS_READY_VALIDATOR_PATH"] = str(payload / "matt/skills/to-tickets/validate_ticket.py")
    session_args = ["--no-session"] if session_dir is None else ["--session-dir", str(session_dir), "--no-title"]
    if resume_session is not None:
        session_args.extend(["--resume", str(resume_session)])
    extensions = ["--extension", str(payload / "delivery-tools/ready-ticket/omp.js")] if boundary_tools_required else []
    argv = ["omp", "--cwd", str(project_root), "--mode", "json", "--print", *session_args, "--no-rules",
            "--no-extensions", *extensions, "--model", model, "--thinking", thinking,
            "--max-time", f"{timeout}s", "--approval-mode", "yolo", prompt]
    started = time.monotonic()
    timed_out = False
    with (output_dir / "events.jsonl").open("w", encoding="utf-8") as stdout, (output_dir / "stderr.txt").open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(argv, cwd=project_root, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            allowance = timeout + 20 if wall_timeout_seconds is None else wall_timeout_seconds
            if boundary_callback is None:
                exit_code = process.wait(timeout=allowance)
            else:
                deadline = time.monotonic() + allowance
                while True:
                    boundary_callback(load_events(output_dir / "events.jsonl"))
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(argv, allowance)
                    try:
                        exit_code = process.wait(timeout=min(0.05, remaining))
                        boundary_callback(load_events(output_dir / "events.jsonl"))
                        break
                    except subprocess.TimeoutExpired:
                        continue
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
        except BaseException:
            # Callback/setup failures must not leave a live side-effect-capable actor.
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            raise
    result = summarize(load_events(output_dir / "events.jsonl"))
    result.update(schema="iis-agent-observation/v2", stage=stage, bundle_id=bundle["bundle_id"],
                  extension_requested=extensions, loaded_identity="REQUIRES_RAW_HOST_EVIDENCE",
                  model_requested=model, thinking=thinking,
                  project_root=str(project_root), payload=str(payload),
                  raw_events=str(output_dir / "events.jsonl"), prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                  elapsed_seconds=time.monotonic() - started, exit_code=exit_code, timed_out=timed_out)
    result["clean_transport"] = exit_code == 0 and not timed_out and result["model_completed"] and result["actual_models"] == [model]
    if not result["clean_transport"]:
        for field in ("implementation_completion", "preparation_completion", "plan_review_path", "parsed_verdict",
                      "verifier_ticket_progression", "host_verifier_terminal_handle", "verifier_model",
                      "verification_binding_path", "verification_binding_sha256", "host_verdict_record_path",
                      "host_verdict_record_sha256", "caller_finalization", "caller_finalization_args",
                      "ticket_progression", "progression_basis", "ticket_status_after"):
            result[field] = None
    if session_dir is not None:
        sessions = list(session_dir.glob("*.jsonl"))
        result["session_file"] = str(sessions[0]) if len(sessions) == 1 else None
        result["resumed_from"] = str(resume_session) if resume_session is not None else None
        if result["session_file"] is not None:
            result["session_sha256"] = hashlib.sha256(sessions[0].read_bytes()).hexdigest()
    (output_dir / "terminal.txt").write_text(result["terminal_text"], encoding="utf-8")
    (output_dir / "observation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=("plan", "prepare", "implement", "verify", "completion", "adaptive"))
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--agent-dir", required=True, type=Path)
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--thinking", default="medium")
    parser.add_argument("--timeout", default=600, type=int)
    parser.add_argument("--session-dir", type=Path)
    parser.add_argument("--resume-session", type=Path)
    args = parser.parse_args()
    result = invoke(project_root=args.project_root, prompt=args.prompt.read_text(encoding="utf-8"), output_dir=args.output,
                    agent_dir=args.agent_dir, payload=args.payload,
                    model=args.model, thinking=args.thinking, timeout=args.timeout,
                    session_dir=args.session_dir, resume_session=args.resume_session, stage=args.stage)
    print(json.dumps({key: result[key] for key in ("exit_code", "timed_out", "agent_ended", "clean_transport", "stop_reason", "error_message", "parsed_verdict", "preparation_completion", "implementation_completion", "actual_models", "elapsed_seconds", "raw_events")}, indent=2))
    return 0 if result["clean_transport"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
