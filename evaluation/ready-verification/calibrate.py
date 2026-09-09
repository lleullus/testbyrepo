#!/usr/bin/env python3
"""Prepare disposable cases and capture real DIRECT preparation and integrated verification.

Services are caller-owned: start service_argv before an invocation and stop it
when the case is closed. Oracle data is never placed in the product directory.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
import time
from typing import Any

import score_result
from run_agent import boundary_results, invoke, load_events, summarize

ROOT = Path(__file__).resolve().parent


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def product_snapshot(root: Path, allowed_outputs: list[str]) -> dict[str, str]:
    outputs = [Path(value).resolve() for value in allowed_outputs]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file() and ".git" not in path.relative_to(root).parts
            and "__pycache__" not in path.parts
            and not any(path == output or path.is_relative_to(output) for output in outputs)}


def digest(snapshot: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def prepare(case_id: str, arena: Path, port: int, kind: str = "verification") -> tuple[Path, dict[str, Any]]:
    from fixture_catalog import materialize
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    preparation_case = None
    if kind == "preparation":
        preparation_case = next(case for case in json.loads((ROOT / "planning-cases.json").read_text())["preparation_cases"] if case["case_id"] == case_id)
    run_root = arena.resolve() / uuid.uuid4().hex[:16]
    run_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    project_root, support_root = run_root / "product", run_root / "support"
    if kind == "implementation":
        from implementation_fixtures import materialize as materialize_implementation
        metadata = materialize_implementation(case_id, project_root, support_root, port=port)
    else:
        base_case = preparation_case["base_case"] if preparation_case else case_id
        case = next(case for case in manifest["cases"] if case["case_id"] == base_case)
        metadata = materialize(case, project_root, support_root, port=port)
    if preparation_case:
        plan = Path(metadata["ticket_path"]).parent.parent / "plans/PLAN-001.md"
        plan.parent.mkdir()
        plan.write_text("# Initial execution method\n\nThis is an unreviewed starting proposal, not admission.\n\n" + preparation_case["method"] + "\n")
        metadata["plan_navigation_paths"] = [str(plan)]
        if case_id == "prepare-evidence-reuse":
            evidence = run_root / "investigation.json"
            write_json(evidence, {"source_observations": [{"path": filename, "sha256": hashlib.sha256(Path(filename).read_bytes()).hexdigest(), "content": Path(filename).read_text()} for filename in metadata["target_paths"]],
                                  "limit": "Source inspection only, not a runtime observation or product verdict"})
            metadata["preparation_evidence_paths"] = [str(evidence)]
    metadata.update(case_id=case_id, run_id=run_root.name, run_root=str(run_root))
    for argv in (["git", "-c", "core.hooksPath=/dev/null", "init", "--quiet"],
                 ["git", "add", "--all"],
                 ["git", "-c", "user.name=Calibration", "-c", "user.email=calibration@localhost", "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Initial product state"]):
        subprocess.run(argv, cwd=project_root, check=True, capture_output=True)
    write_json(run_root / "metadata.json", metadata)
    return run_root, metadata


def stage_prompt(stage: str, metadata: dict[str, Any], run_root: Path) -> str:
    root = metadata["project_root"]
    common = (f"Project Root: {root}\n이 호출은 승인된 disposable 로컬 제품 작업이다. DIRECT로 수행하고 subagent를 만들지 않는다. "
              "운영 파일·다른 프로젝트·다른 세션·평가 정답을 읽거나 변경하지 않는다. 부모 디렉터리를 탐색하지 않는다. "
              "실제 도구 결과만 근거로 삼고 source 모양이나 내부 테스트로 실제 경계 결과를 대체하지 않는다. "
              "설치된 canonical skill과 그 reference/validator는 읽을 수 있다. 비밀키·외부 실계정은 사용하지 않는다. "
              "명시된 loopback 제품 서비스의 정상 호출만 허용되며 서비스 소스/관리 설정은 작업자 범위 밖이다.\n")
    target = (f"Ticket: {metadata['ticket_path']}\nCandidate Target Paths: {json.dumps(metadata['target_paths'])}\n"
              f"Declared Allowed Output Paths: {json.dumps(metadata['allowed_output_paths'])}\n")
    implementation_report: Path | None = None
    if metadata.get("implementation_report_path"):
        implementation_report = Path(metadata["implementation_report_path"])
    elif (run_root / "implement/terminal.txt").exists():
        implementation_report = run_root / "implement/terminal.txt"
    if stage == "verify" and implementation_report is not None:
        target += f"Implementation Report / Evidence: {implementation_report}\n구현 보고는 navigation일 뿐이며 완료·판정 근거가 아니다. 보고의 제한과 실제 현재 제품을 각각 확인한다.\n"
    if stage == "verify":
        if metadata.get("plan_review_path"):
            target += f"Optional method navigation (not product admission): {metadata['plan_review_path']}\n"
        return common + target + ("read로 skill://ready-ticket-verify 를 호출하고 이 Ticket의 통합 최종 검증을 수행하라. "
            "현재 authority와 stable target/scenario effect 경계를 직접 확인하고 ready_contract capture_verification으로 immutable binding을 만든 뒤 원계약의 모든 authored flow와 실제 실패 가능 frontier를 확인하라. "
            "발견한 반례는 verifier-owned current evidence와 finding disposition으로 닫아라. "
            "실제 실행은 일반 host-native 도구를 사용하고 settled nonzero 결과를 global lock으로 승격하지 않는다. "
            "원래 source/authority를 고쳐 합격시키지 말고 semantic terminal result를 먼저 닫은 뒤, 이 DIRECT 호출의 caller 단계에서 exact binding/SHA와 같은 verdict로 ready_finalize를 호출해 progression result를 별도로 보고하라.\n")
    if stage == "plan":
        return common + metadata["planning_prompt"] + ("\n이번 요청은 이 한 결과의 기획부터 approved Spec과 reviewed Ready Ticket Set까지다. "
            "read로 skill://ask-matt 를 호출하고 현재 권위를 확인하라. 제품 의미가 완전히 정해져 있으면 To Spec과 To Tickets까지 진행한다. "
            "별도 문서별 사용자 승인을 요구하지 않는다. 명시된 외부 미확인은 숨기지 않는다. "
            "추가 제품 결정이 정말 필요하면 정확히 무엇인지 보고하고, 구현·검증은 시작하지 않는다.\n")
    if stage == "implement":
        review = metadata.get("plan_review_path")
        if not review:
            raise ValueError("implementation requires actual current preparation handoff")
        target += f"Plan Review: {review}\n"
        return common + target + metadata["implementation_prompt"] + ("\nread로 skill://ready-ticket-implement 를 호출하여 이 exact Ticket만 구현하라. "
            "승인된 authority를 바꾸지 말고 실제 제품 진입점과 readback으로 self-check를 수행하라. "
            "loopback 서비스의 내부/설정은 수정하지 않는다. 정확한 구현 결과와 남은 한계를 보고하고 최종 검증은 시작하지 않는다.\n")
    raise ValueError(f"unknown stage: {stage}")


def current_review(metadata: dict[str, Any], review_path: Path, payload: Path) -> dict[str, Any]:
    """Ask the candidate's own current binding code; never synthesize admission."""
    tickets = metadata.get("ticket_paths", [metadata["ticket_path"]])
    script = """
import {pathToFileURL} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import fs from 'node:fs';
const [payload, root, reviewPath, ticketsJson] = process.argv.slice(1);
const {checkPlanAdmission} = await import(pathToFileURL(payload + '/delivery-tools/ready-ticket/src/core.js'));
const bundle = JSON.parse(fs.readFileSync(payload + '/bundle.json', 'utf8'));
const executeArgv = async (argv, options) => {
  try { const result = await promisify(execFile)(argv[0], argv.slice(1), {cwd:options.cwd, timeout:options.timeout});
    return {exitCode:0, interrupted:false, terminationState:'settled', ...result};
  } catch (error) { return {exitCode:error.code, interrupted:!!error.killed, terminationState:error.killed?'unknown':'settled', stdout:error.stdout, stderr:error.stderr}; }
};
const admissions = [];
for (const ticketPath of JSON.parse(ticketsJson)) {
  admissions.push(await checkPlanAdmission({ticketPath, projectRoot:root, planReviewPath:reviewPath, validatorPath:payload + '/matt/skills/to-tickets/validate_ticket.py', bundleIdentity:bundle.bundle_id, executeArgv}));
}
console.log(JSON.stringify(admissions));
"""
    result = subprocess.run(["node", "--input-type=module", "-e", script, str(payload.resolve()), metadata["project_root"], str(review_path), json.dumps(tickets)], capture_output=True, text=True, timeout=60)
    return {"current": result.returncode == 0, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "meaning": "current binding only; raw independent review remains required"}


def run_preparation(metadata: dict[str, Any], *, agent_dir: Path, payload: Path,
                    model: str, thinking: str, timeout: int) -> dict[str, Any]:
    root, run_root = Path(metadata["project_root"]), Path(metadata["run_root"])
    output = run_root / "prepare"
    output.mkdir(mode=0o700, exist_ok=False)
    review = output / "plan-review.json"
    tickets = metadata.get("ticket_paths", [metadata["ticket_path"]])
    before = product_snapshot(root, [])
    common = (f"Project Root: {root}\nTickets: {json.dumps(tickets)}\nPlan Review Output: {review}\n"
              f"현재 선택 모델은 {model}, thinking={thinking}; 이 역할은 DIRECT이며 subagent를 생성하지 않는다. "
              "read로 skill://ready-ticket-plan 및 그 세 reference를 읽는다. 제품/승인 authority/Ticket status는 수정하지 않는다. "
              "프로젝트와 명시된 evidence/reference 밖을 탐색하지 않는다. evaluator oracle/다른 run/운영 자격증명은 읽지 않는다. "
              "이번 호출의 역할만 수행하며 이후 독립 역할은 외부 caller가 별도 invocation으로 실행한다.\n")
    common += f"Existing method navigation: {json.dumps(metadata.get('plan_navigation_paths', []))}\nExisting investigation evidence: {json.dumps(metadata.get('preparation_evidence_paths', []))}\n"
    observations = []
    def role(name: str, instructions: str, resume: Path | None = None):
        result = invoke(project_root=root, prompt=common + instructions, output_dir=output / name,
                        agent_dir=agent_dir, payload=payload, model=model,
                        thinking=thinking, timeout=timeout, stage="prepare",
                        session_dir=output / "writer-sessions" if name in {"planner", "revision", "lead"} else None,
                        resume_session=resume)
        observations.append({"role": name, **result})
        return result
    planner = role("planner", "Planner로 현재 근거를 조사하고 필요한 project-local 실행계획을 작성한다. 계획 exact 경로와 근거를 반환한다. 자기 ADMIT/review JSON이나 lead 완료 terminal은 작성하지 않는다.")
    lead = None
    if planner["clean_transport"] and planner.get("session_file"):
        heuristic = role("heuristic", f"독립 Heuristic이다. 원계약에서 먼저 독립 pass 후 {output / 'planner/terminal.txt'}의 계획과 근거를 검토한다. 현실적 반례/미확인/기각 anchor를 반환한다. 계획·제품·review JSON은 수정하지 않으며 lead 완료 terminal을 내지 않는다.")
        if heuristic["clean_transport"]:
            revision = role("revision", f"동일 Planner로 {output / 'heuristic/terminal.txt'}와 raw evidence의 finding disposition만 수행한다. 실질 수정이 필요할 때만 영향 방법을 수정하거나 근거로 기각한다. 정상·무발견이면 계획 bytes를 그대로 유지하며 재설계/추가 승인/reviewer를 만들지 않는다. 독립 검토 판단은 만들지 않는다.", Path(planner["session_file"]))
            if revision["clean_transport"] and not review.exists():
                reviewed_snapshot = product_snapshot(root, [])
                review_before_lead = None
                reviewer = role("reviewer", f"작성자와 별도 독립 Plan Review다. 원계약 전체와 현재 계획을 직접 읽는다. Planner evidence: {output / 'revision/terminal.txt'}; Heuristic evidence: {output / 'heuristic/events.jsonl'}. 현재 bytes와 ready_contract inspect_authority를 사용하여 실제 판단의 iis-plan-review/v1 JSON을 {review}에 작성한다. review_origin.evidence_reference는 이 invocation의 {output / 'reviewer/events.jsonl'}이다. 계획/제품을 고쳐 허가하지 말고 정확한 ADMIT/REVISE/EVIDENCE_NEEDED와 근거를 반환한다. lead terminal은 내지 않는다.")
                if reviewer["clean_transport"] and review.is_file() and product_snapshot(root, []) == reviewed_snapshot:
                    review_before_lead = hashlib.sha256(review.read_bytes()).hexdigest()
                    lead = role("lead", f"원래 준비 lead의 handoff fan-in이다. 실제 별도 reviewer 결과 {review}, raw {output / 'reviewer/events.jsonl'}와 Heuristic/Planner evidence의 귀속·currentness·원래 requested Tickets 전체 ADMIT 분모만 대조한다. 두 번째 의미 검토/승인 단계가 아니다. 어느 계획/review/제품 파일도 수정하지 말고 READY TICKET PLAN RESULT terminal을 반환한다. 구현/최종 검증은 시작하지 않는다.", Path(revision["session_file"]))
    current = current_review(metadata, review, payload) if review.is_file() else {"current": False, "reason": "no actual review artifact"}
    after = product_snapshot(root, [])
    plan_paths = set()
    try:
        authored_review = json.loads(review.read_text())
        plan_paths = {str(Path(item["path"]).relative_to(root)) for item in authored_review.get("plans", [])}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    protected_changes = [path for path in changed if path not in plan_paths or "/plans/" not in path]
    completion = lead.get("preparation_completion") if lead else None
    clean = bool(lead) and all(item["clean_transport"] for item in observations)
    review_unchanged = bool(lead) and review.is_file() and review_before_lead == hashlib.sha256(review.read_bytes()).hexdigest() and product_snapshot(root, []) == reviewed_snapshot
    if completion == "COMPLETE" and (not clean or not current["current"] or protected_changes or not review_unchanged or lead.get("plan_review_path") != str(review)):
        completion = None
    result = {"case_id": metadata["case_id"], "run_id": metadata["run_id"], "stage": "prepare",
              "parsed_completion": completion, "plan_review_path": str(review) if review.is_file() else None,
              "clean_transport": clean, "current_review": current, "changed_paths": changed,
              "post_project_snapshot": after,
              "protected_changes": protected_changes, "roles": [{"role": item["role"], "raw_events": item["raw_events"], "clean_transport": item["clean_transport"]} for item in observations],
              "elapsed_seconds": sum(item["elapsed_seconds"] for item in observations),
              "raw_terminal_result": str(output / "lead/terminal.txt") if lead else None,
              "semantic_review": "REQUIRED; independent invocation and binding are not semantic scoring"}
    if metadata.get("setup_stages") == ["prepare"]:
        from completion import product_snapshot as completion_snapshot, snapshot_digest
        result["completion_input_digest"] = snapshot_digest(completion_snapshot(root))
    write_json(output / "record.json", result)
    return result


def apply_challenge(metadata: dict[str, Any], run_root: Path, events: list[dict[str, Any]]) -> dict[str, Any] | None:
    challenge = metadata.get("verification_challenge")
    if (not challenge or (run_root / "challenge.json").exists()
            or any(event.get("type") == "agent_end" for event in events)
            or boundary_results(events, "ready_finalize")):
        return None
    capture = next((entry["result"] for entry in boundary_results(events, "ready_contract", "capture_verification")
                    if entry["result"].get("binding_path") and entry["result"].get("binding_sha256")
                    and isinstance(entry["result"].get("binding"), dict)), None)
    if capture is None:
        return None
    paths = [Path(value).resolve() for value in challenge["paths"]]
    stable = {Path(value).resolve() for value in capture["binding"].get("stable_target_paths", [])}
    if not paths or any(path not in stable for path in paths):
        raise ValueError("challenge path is not part of the captured stable verification target")
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    for path in paths:
        content = path.read_text(encoding="utf-8")
        if challenge["before"] not in content:
            raise ValueError("challenge precondition changed")
    for path in paths:
        path.write_text(path.read_text(encoding="utf-8").replace(challenge["before"], challenge["after"]), encoding="utf-8")
    applied = {"applied": True, "boundary": "successful_capture_verification_result",
               "verification_binding": capture["binding_path"], "verification_binding_sha256": capture["binding_sha256"],
               "before": before, "after": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
               "attribution": "external evaluator, not actor mutation or actor evidence"}
    write_json(run_root / "challenge.json", applied)
    return applied


def run_stage(stage: str, metadata: dict[str, Any], *, agent_dir: Path, payload: Path,
              model: str, thinking: str, timeout: int,
              wall_timeout_seconds: float | None = None, episode_deadline: float | None = None) -> dict[str, Any]:
    run_root = Path(metadata["run_root"])
    if stage == "prepare":
        return run_preparation(metadata, agent_dir=agent_dir, payload=payload,
                               model=model, thinking=thinking, timeout=timeout)
    root = Path(metadata["project_root"])
    before = product_snapshot(root, metadata["allowed_output_paths"])
    ticket = Path(metadata["ticket_path"])
    ticket_before = ticket.read_text(encoding="utf-8") if ticket.exists() else None
    if episode_deadline is not None:
        wall_timeout_seconds = episode_deadline - time.monotonic()
        if wall_timeout_seconds <= 0:
            raise TimeoutError("episode timeout exhausted before invocation")
    observation = invoke(project_root=root, prompt=stage_prompt(stage, metadata, run_root), output_dir=run_root / stage,
                         agent_dir=agent_dir, payload=payload, model=model, thinking=thinking, timeout=timeout,
                         stage=stage, wall_timeout_seconds=wall_timeout_seconds,
                         boundary_callback=(lambda events: apply_challenge(metadata, run_root, events)) if stage == "verify" and metadata.get("verification_challenge") else None)
    after = product_snapshot(root, metadata["allowed_output_paths"])
    events = load_events(Path(observation["raw_events"]))
    finalizations = boundary_results(events, "ready_finalize") if stage == "verify" else []
    finalization = finalizations[-1]["result"] if finalizations else {}
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    finalizer_progression_paths: list[str] = []
    if stage == "verify" and ticket_before is not None and ticket.exists():
        ticket_after = ticket.read_text(encoding="utf-8")
        binding_matches = bool(observation.get("verification_binding_path")
                               and observation.get("verification_binding_sha256")
                               and finalization.get("verification_binding") == observation["verification_binding_path"]
                               and finalization.get("verification_binding_sha256") == observation["verification_binding_sha256"])
        if (ticket_after == re.sub(r"(?m)^Status: ready$", "Status: done", ticket_before)
                and observation.get("parsed_verdict") == "VERIFIED"
                and finalization.get("ticket_path") == str(ticket)
                and finalization.get("verification_verdict") == "VERIFIED"
                and finalization.get("ticket_progression") == "COMPLETED"
                and finalization.get("progression_basis") in {"WRITE_PERFORMED_THIS_CALL", "RECOVERED_CAPTURED_FINALIZER_RESULT"}
                and finalization.get("ticket_status_after") == "done"
                and binding_matches):
            finalizer_progression_paths.append(str(ticket.relative_to(root)))
    external_changes = []
    challenge_path = run_root / "challenge.json"
    if stage == "verify" and challenge_path.is_file():
        challenge = json.loads(challenge_path.read_text())
        for filename, expected in challenge.get("after", {}).items():
            path = Path(filename)
            relative = str(path.relative_to(root))
            if after.get(relative) == expected and before.get(relative) == challenge["before"].get(filename):
                external_changes.append(relative)
    unexpected_changed = [path for path in changed if path not in finalizer_progression_paths and path not in external_changes]
    record = {"case_id": metadata["case_id"], "run_id": metadata["run_id"], "stage": stage,
              "model_tool_profile": {"model": model, "thinking": thinking, "actual_models": observation["actual_models"]},
              "input_target_identity": digest(before), "raw_terminal_result": str(run_root / stage / "terminal.txt"),
              "raw_events": observation["raw_events"], "parsed_verdict": observation["parsed_verdict"],
              "verifier_ticket_progression": observation.get("verifier_ticket_progression"),
              "verification_binding_path": observation.get("verification_binding_path"),
              "verification_binding_sha256": observation.get("verification_binding_sha256"),
              "ticket_progression": observation["ticket_progression"],
              "progression_basis": observation.get("progression_basis"),
              "ticket_status_after": (re.search(r"(?m)^Status: (\w+)$", ticket.read_text()).group(1) if ticket.exists() and re.search(r"(?m)^Status: (\w+)$", ticket.read_text()) else None),
              "pre_project_root_digest": digest(before), "post_project_root_digest": digest(after),
              "target_mutated": bool(unexpected_changed) if stage == "verify" else False,
              "changed_paths": unexpected_changed, "all_changed_paths": changed,
              "finalizer_progression_paths": finalizer_progression_paths,
              "external_challenge_paths": external_changes,
              "challenge_applied": challenge_path.is_file() if metadata.get("verification_challenge") else None,
              "caller_finalization": finalization,
              "elapsed_seconds": observation["elapsed_seconds"],
              "exit_code": observation["exit_code"], "timed_out": observation["timed_out"], "agent_ended": observation["agent_ended"],
              "clean_transport": observation["clean_transport"], "stop_reason": observation["stop_reason"], "error_message": observation["error_message"],
              "usage": observation["usage"],
              "tool_events": {"starts": len(observation["tool_calls"]), "ends": len(observation["tool_results"]),
                              "errors": observation["tool_errors"]},
              "evidence_review": "PENDING_RAW_OBSERVATION_REVIEW"}
    if stage == "implement":
        record["parsed_completion"] = observation["implementation_completion"]
    write_json(run_root / stage / "record.json", record)
    return record



def run_cohort(args) -> int:
    metadata_paths = [Path(value).resolve(strict=True) for value in json.loads(args.cohort.read_text(encoding="utf-8"))]
    if not metadata_paths or len(metadata_paths) != len(set(metadata_paths)):
        raise ValueError("cohort must contain distinct prepared metadata paths")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    def run_one(metadata_path):
        argv = [sys.executable, "-B", str(Path(__file__).resolve()), "run", "verify", "--metadata", str(metadata_path),
                "--agent-dir", str(args.agent_dir), "--payload", str(args.payload),
                "--model", args.model, "--thinking", args.thinking, "--timeout", str(args.timeout)]
        result = subprocess.run(argv, capture_output=True, text=True)
        (metadata_path.parent / "invocation.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (metadata_path.parent / "invocation.stderr.txt").write_text(result.stderr, encoding="utf-8")
        return {"metadata": str(metadata_path), "exit_code": result.returncode,
                "verify_record": str(metadata_path.parent / "verify/record.json")}
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, metadata_path) for metadata_path in metadata_paths]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            write_json(args.output, results)
            print(json.dumps({"completed": len(results), "total": len(metadata_paths), **result}), flush=True)
    return 0 if all(result["exit_code"] == 0 for result in results) else 1

def _load_array(path: Path, name: str) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array")
    return value


def _run_pair(value: object) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    case_id, run_id = value.get("case_id"), value.get("run_id")
    if not isinstance(case_id, str) or not case_id or not isinstance(run_id, str) or not run_id:
        return None
    return case_id, run_id


def _pair_value(pair: tuple[str, str]) -> dict[str, str]:
    return {"case_id": pair[0], "run_id": pair[1]}


def _add_error(errors: list[dict[str, Any]], code: str, **details: object) -> None:
    errors.append({"code": code, **details})


def _verify_events_path(metadata: dict[str, Any]) -> Path | None:
    run_root = metadata.get("run_root")
    if not isinstance(run_root, str) or not run_root:
        return None
    return (Path(run_root) / "verify" / "events.jsonl").resolve()


def _validate_review_evidence(review: dict[str, Any], pair: tuple[str, str], expected_path: Path | None,
                              errors: list[dict[str, Any]]) -> None:
    refs = review.get("evidence_refs")
    if not isinstance(refs, list):
        _add_error(errors, "invalid_evidence_refs", **_pair_value(pair))
        return


    found_expected = False
    seen_paths: set[Path] = set()
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            _add_error(errors, "invalid_evidence_ref", **_pair_value(pair), index=index)
            continue
        path_value, expected_hash = ref.get("path"), ref.get("sha256")
        if not isinstance(path_value, str) or not path_value or not isinstance(expected_hash, str) or not expected_hash:
            _add_error(errors, "invalid_evidence_ref", **_pair_value(pair), index=index)
            continue
        try:
            evidence_path = Path(path_value).resolve()
        except (OSError, ValueError):
            _add_error(errors, "missing_evidence_ref", **_pair_value(pair), index=index, path=path_value)
            continue
        if evidence_path in seen_paths:
            _add_error(errors, "duplicate_evidence_ref", **_pair_value(pair), index=index, path=str(evidence_path))
        seen_paths.add(evidence_path)
        if expected_path is not None and evidence_path == expected_path:
            found_expected = True
        elif evidence_path.name == "events.jsonl" and evidence_path.parent.name == "verify":
            _add_error(errors, "foreign_verify_events_ref", **_pair_value(pair), index=index, path=str(evidence_path))
        try:
            actual_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        except OSError:
            _add_error(errors, "missing_evidence_ref", **_pair_value(pair), index=index, path=str(evidence_path))
            continue
        if expected_hash != actual_hash:
            _add_error(errors, "evidence_hash_mismatch", **_pair_value(pair), index=index, path=str(evidence_path))

    if not found_expected:
        _add_error(errors, "missing_verify_events_ref", **_pair_value(pair),
                   path=str(expected_path) if expected_path is not None else None)


def build_report(metadata_paths: list[Path], records: list[dict[str, Any]], reviews: list[dict[str, Any]],
                 manifest: dict[str, Any]) -> dict[str, Any]:
    """Combine label scoring with independent causal-review coverage without changing either input."""
    errors: list[dict[str, Any]] = []
    expected: dict[tuple[str, str], tuple[dict[str, Any], Path | None]] = {}
    expected_pairs: list[tuple[str, str]] = []
    for index, metadata_path in enumerate(metadata_paths):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _add_error(errors, "invalid_cohort_metadata", index=index, path=str(metadata_path))
            continue
        pair = _run_pair(metadata)
        if pair is None:
            _add_error(errors, "invalid_cohort_metadata", index=index, path=str(metadata_path))
            continue
        if pair in expected:
            _add_error(errors, "duplicate_cohort_run", **_pair_value(pair), path=str(metadata_path))
            continue
        expected[pair] = (metadata, _verify_events_path(metadata))
        expected_pairs.append(pair)
    if not expected_pairs:
        _add_error(errors, "empty_cohort")
    for pair in expected_pairs:
        expected_path = expected[pair][1]
        try:
            expected_exists = expected_path is not None and expected_path.is_file()
        except OSError:
            expected_exists = False
        if not expected_exists:
            _add_error(errors, "missing_verify_events", **_pair_value(pair),
                       path=str(expected_path) if expected_path is not None else None)
        elif not summarize(load_events(expected_path))["model_completed"]:
            _add_error(errors, "model_not_cleanly_terminated", **_pair_value(pair))
        if expected_exists:
            native = summarize(load_events(expected_path))
            supplied = [record for record in records if _run_pair(record) == pair]
            for record in supplied:
                if record.get("parsed_verdict") != native.get("parsed_verdict"):
                    _add_error(errors, "terminal_verdict_mismatch", **_pair_value(pair))
                if expected[pair][0].get("verification_challenge") and record.get("challenge_applied") is not True:
                    _add_error(errors, "required_challenge_not_applied", **_pair_value(pair))
                if record.get("stage") == "verify":
                    if (record.get("verification_binding_path") != native.get("verification_binding_path")
                            or record.get("verification_binding_sha256") != native.get("verification_binding_sha256")
                            or record.get("ticket_progression") != native.get("ticket_progression")
                            or record.get("progression_basis") != native.get("progression_basis")
                            or record.get("caller_finalization") != (native.get("caller_finalization") or {})):
                        _add_error(errors, "boundary_result_mismatch", **_pair_value(pair))
                if native.get("parsed_verdict") == "VERIFIED" and record.get("stage") == "verify":
                    caller = native.get("caller_finalization") or {}
                    if (native.get("verifier_ticket_progression") != "PENDING CALLER FINALIZATION"
                            or native.get("ticket_progression") != "COMPLETED"
                            or native.get("ticket_status_after") != "done"
                            or caller.get("verification_verdict") != "VERIFIED"
                            or caller.get("ticket_progression") != "COMPLETED"
                            or caller.get("progression_basis") not in {"WRITE_PERFORMED_THIS_CALL", "RECOVERED_CAPTURED_FINALIZER_RESULT"}
                            or caller.get("verification_binding") != native.get("verification_binding_path")
                            or caller.get("verification_binding_sha256") != native.get("verification_binding_sha256")):
                        _add_error(errors, "verified_progression_not_completed", **_pair_value(pair))

    result_pairs: list[tuple[str, str]] = []
    seen_results: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        pair = _run_pair(record)
        if pair is None:
            _add_error(errors, "invalid_result", index=index)
            continue
        result_pairs.append(pair)
        if pair not in expected:
            _add_error(errors, "external_result", **_pair_value(pair), index=index)
        elif pair in seen_results:
            _add_error(errors, "duplicate_result", **_pair_value(pair), index=index)
        else:
            seen_results.add(pair)
    for pair in expected_pairs:
        if pair not in seen_results:
            _add_error(errors, "missing_result", **_pair_value(pair))

    review_pairs: list[tuple[str, str]] = []
    seen_reviews: set[tuple[str, str]] = set()
    for index, review in enumerate(reviews):
        pair = _run_pair(review)
        if pair is None:
            _add_error(errors, "invalid_review", index=index)
            continue
        review_pairs.append(pair)
        if pair not in expected:
            _add_error(errors, "external_review", **_pair_value(pair), index=index)
            continue
        if pair in seen_reviews:
            _add_error(errors, "duplicate_review", **_pair_value(pair), index=index)
            continue
        seen_reviews.add(pair)
        if review.get("causal_evidence_sufficient") is not True:
            _add_error(errors, "insufficient_causal_evidence", **_pair_value(pair))
        reason = review.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            _add_error(errors, "invalid_review_reason", **_pair_value(pair))
        _validate_review_evidence(review, pair, expected[pair][1], errors)
    for pair in expected_pairs:
        if pair not in seen_reviews:
            _add_error(errors, "missing_review", **_pair_value(pair))

    label_score = score_result.score(manifest, records)
    return {
        "label_score": label_score,
        "candidate_accepted": bool(label_score["release_pass"] and not errors),
        "causal_review": {
            "coverage": {
                "expected_runs": [_pair_value(pair) for pair in expected_pairs],
                "result_runs": [_pair_value(pair) for pair in result_pairs],
                "review_runs": [_pair_value(pair) for pair in review_pairs],
            },
            "errors": errors,
        },
    }


def run_report(args) -> int:
    cohort_values = _load_array(args.cohort, "cohort")
    if not all(isinstance(value, str) and value for value in cohort_values):
        raise ValueError("cohort must contain metadata paths")
    metadata_paths = [Path(value).resolve() for value in cohort_values]
    records = _load_array(args.results, "results")
    reviews = _load_array(args.reviews, "reviews")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("results must contain JSON objects")
    if not all(isinstance(review, dict) for review in reviews):
        raise ValueError("reviews must contain JSON objects")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build_report(metadata_paths, records, reviews, manifest)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["candidate_accepted"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("prepare")
    setup.add_argument("case_id")
    setup.add_argument("--arena", required=True, type=Path)
    setup.add_argument("--port", required=True, type=int)
    run = commands.add_parser("run")
    run.add_argument("stage", choices=("plan", "prepare", "implement", "verify", "delivery"))
    setup.add_argument("--kind", choices=("verification", "implementation", "preparation"), default="verification")
    run.add_argument("--metadata", required=True, type=Path)
    run.add_argument("--agent-dir", required=True, type=Path)
    run.add_argument("--payload", required=True, type=Path)
    run.add_argument("--model", required=True)
    run.add_argument("--thinking", default="medium")
    run.add_argument("--timeout", type=int, default=600)
    batch = commands.add_parser("batch", help="Run one fixed cohort; services must already be supervised by the caller")
    batch.add_argument("--cohort", required=True, type=Path)
    batch.add_argument("--output", required=True, type=Path)
    batch.add_argument("--agent-dir", required=True, type=Path)
    batch.add_argument("--payload", required=True, type=Path)
    batch.add_argument("--model", required=True)
    batch.add_argument("--thinking", default="medium")
    batch.add_argument("--timeout", type=int, default=600)
    batch.add_argument("--workers", type=int, default=1)
    report = commands.add_parser("report", help="Read-only aggregation of label scores and causal-review coverage")
    report.add_argument("--cohort", required=True, type=Path)
    report.add_argument("--results", required=True, type=Path)
    report.add_argument("--reviews", required=True, type=Path)
    report.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "batch":
        return run_cohort(args)
    if args.command == "report":
        return run_report(args)
    if args.command == "prepare":
        root, metadata = prepare(args.case_id, args.arena, args.port, args.kind)
        print(json.dumps({"metadata": str(root / "metadata.json"), "service_argv": metadata["service_argv"]}, indent=2))
        return 0
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    records = []
    for stage in (("prepare", "implement", "verify") if args.stage == "delivery" else (args.stage,)):
        if stage == "verify" and metadata.get("reset_argv"):
            reset = subprocess.run(metadata["reset_argv"], cwd=metadata["project_root"], capture_output=True, text=True)
            write_json(Path(metadata["run_root"]) / f"reset-before-{stage}.json", {"argv": metadata["reset_argv"], "exit_code": reset.returncode, "stdout": reset.stdout, "stderr": reset.stderr})
            if reset.returncode:
                raise RuntimeError("fixture state reset failed; refusing to contaminate verification")
        record = run_stage(stage, metadata, agent_dir=args.agent_dir, payload=args.payload,
                           model=args.model, thinking=args.thinking, timeout=args.timeout)
        records.append(record)
        if stage == "prepare":
            if record.get("parsed_completion") != "COMPLETE":
                break
            metadata["plan_review_path"] = record["plan_review_path"]
            write_json(args.metadata, metadata)
        if stage == "implement" and record.get("parsed_completion") != "COMPLETE":
            break
        if not record["clean_transport"]:
            break
    print(json.dumps(records, indent=2))
    return 0 if all(record["clean_transport"] and (record.get("parsed_completion") == "COMPLETE" if record["stage"] in {"prepare", "implement"} else record.get("parsed_verdict") is not None if record["stage"] == "verify" else True) for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
