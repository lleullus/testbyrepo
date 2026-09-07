#!/usr/bin/env python3
"""Prepare and score bounded, real Outer Main completion observations.

The product fixtures and their historical reports are synthetic setup state.  A
`run` is a new, read-only OMP invocation over that state; only its captured raw
events and independently reviewed current boundary observations are evaluation
evidence.  Oracle labels stay in completion-cases.json outside every product.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
from typing import Any

from fixture_catalog import _put
from run_agent import invoke, load_events, summarize

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "completion-cases.json"


FIXTURE_NOTICE = """
EVALUATION FIXTURE NOTICE

This disposable tree is synthetic setup state. Ticket statuses, earlier owner
reports, Probe records, and implementation or verification reports in this tree
were seeded to define the starting state. They are not evidence that this
current evaluation invocation implemented or verified anything. Assess the
current Run Contract from the actual files, ordinary local CLI, canonical
artifact, and current attributable evidence that are inspectable now.
"""

APP = """
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state/current.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(command):
    state = load(STATE)
    if command == "legacy":
        result = {"input": "legacy", "value": state.get("legacy_value")}
    elif command == "operator":
        path = ROOT.parent / "support/operator-current.json"
        result = load(path) if path.is_file() else {"approved": False, "available": False}
        key = state.get("requested_action")
        result["product_self_check"] = "passed" if isinstance(key, str) and bool(key) else "failed"
    elif command == "external":
        path = ROOT.parent / "support/external-current.json"
        result = load(path) if path.is_file() else {"available": False, "delivery": "unobserved"}
    elif command == "artifact-check":
        path = ROOT / "release/canonical-result.json"
        result = load(path) if path.is_file() else {"present": False}
    else:
        result = state
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "status")
"""


BLUEPRINTS: dict[str, dict[str, Any]] = {
    "parent-obligation-owned": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "The current primary result is ready and preservation remains intact.",
        "state": {"primary_result": "ready", "preservation": "preserved"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [
            ("primary result is ready", "TICKET-001", ["state/current.json"]),
            ("preservation remains intact", "TICKET-001", ["state/current.json"]),
        ],
        "command": "status",
    },
    "parent-obligation-unowned": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "The current primary result is ready and preservation remains intact.",
        "state": {"primary_result": "ready"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [
            ("primary result is ready", "TICKET-001", ["state/current.json"]),
            ("preservation remains intact", None, []),
        ],
        "command": "status",
    },
    "later-change-preserved": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "The integrating change is delivered and the ordinary legacy entrypoint still returns stable-value.",
        "state": {"current_value": "revised-value", "legacy_value": "stable-value"},
        "tickets": [("TICKET-001", "done"), ("TICKET-002", "done")],
        "obligations": [("the current value is revised-value", "TICKET-001", ["state/current.json"]), ("legacy behavior remains stable after integration", "TICKET-002", ["state/current.json", "app.py"])],
        "command": "legacy",
        "ticket_commands": {"TICKET-001": "status", "TICKET-002": "legacy"},
        "history": "TICKET-001 previously accepted legacy value stable-value; TICKET-002 is the current integrating owner.",
    },
    "later-change-regressed": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "The integrating change is delivered and the ordinary legacy entrypoint still returns stable-value.",
        "state": {"current_value": "revised-value", "legacy_value": "regressed-value"},
        "tickets": [("TICKET-001", "done"), ("TICKET-002", "done")],
        "obligations": [("the current value is revised-value", "TICKET-001", ["state/current.json"]), ("legacy behavior remains stable after integration", "TICKET-002", ["state/current.json", "app.py"])],
        "command": "legacy",
        "ticket_commands": {"TICKET-001": "status", "TICKET-002": "legacy"},
        "history": "TICKET-001 previously accepted legacy value stable-value; TICKET-002 is the current integrating owner.",
    },
    "operator-proof-current": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The product self-check succeeds and preexisting authorized operator evidence has approved=true with an independently readable current result.",
        "state": {"requested_action": "alpha"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("current product self-check passes", "TICKET-001", ["app.py", "state/current.json"]), ("authorized operator approval for alpha", "TICKET-001", ["../support/operator-current.json"])],
        "command": "operator",
        "operator": {"approved": True, "key": "alpha", "authority": "preexisting local evaluation operator authority"},
    },
    "operator-proof-missing": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The product self-check succeeds and preexisting authorized operator evidence has approved=true with an independently readable current result.",
        "state": {"requested_action": "alpha"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("current product self-check passes", "TICKET-001", ["app.py", "state/current.json"]), ("authorized operator approval for alpha", "TICKET-001", ["../support/operator-current.json"])],
        "command": "operator",
    },
    "limited-canonical-scope": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The canonical release record is present, schema-valid, and declares format version 2.",
        "state": {"local_artifact_state": "available"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("canonical release record has format version 2", "TICKET-001", ["release/canonical-result.json", "evidence/limited-assessment.json"])],
        "command": "artifact-check",
        "artifact": {"format_version": 2, "channel": "local"},
        "limited": {"verdict": "PASS", "observed": "canonical release record format only", "evidence_limit": "No external delivery behavior was independently observed."},
    },
    "limited-external-overclaim": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The release is currently delivered through the external distribution surface and authoritative external readback confirms delivery.",
        "state": {"local_artifact_state": "available", "external_delivery": "unobserved"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("external distribution currently delivers the release", "TICKET-001", ["../support/external-current.json"])],
        "command": "external",
        "artifact": {"format_version": 2, "channel": "local"},
        "limited": {"verdict": "PASS", "observed": "canonical release record format only", "evidence_limit": "No external delivery behavior was independently observed."},
    },
    "artifact-canonical-correct": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The requested canonical artifact itself exists with format_version=2 and policy=strict.",
        "state": {"deliverable_kind": "canonical artifact"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("canonical artifact has the approved structure", "TICKET-001", ["release/canonical-result.json"])],
        "command": "artifact-check",
        "artifact": {"format_version": 2, "policy": "strict"},
    },
    "artifact-canonical-wrong": {
        "boundary": "BOUNDED_OUTCOME_SATISFIED",
        "predicate": "The requested canonical artifact itself exists with format_version=2 and policy=strict.",
        "state": {"deliverable_kind": "canonical artifact"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("canonical artifact has the approved structure", "TICKET-001", ["release/canonical-result.json"])],
        "command": "artifact-check",
        "artifact": {"format_version": 1, "policy": "permissive"},
    },
    "implementation-only-supported": {
        "boundary": "CURRENT_INCREMENT_IMPLEMENTED",
        "predicate": "Every current Ticket has an exact attributable implementation result with Completion: COMPLETE; verification is no and Ticket status remains ready.",
        "state": {"implemented_result": "available", "value": "revised-value"},
        "tickets": [("TICKET-001", "ready")],
        "obligations": [("implementation of revised-value is complete", "TICKET-001", ["evidence/implementation-result.json", "state/current.json"])],
        "command": "status",
        "implementation": {"Completion": "COMPLETE", "target": "app.py", "current_evidence": ["state/current.json"], "independent_verification_claimed": False},
    },
    "implementation-only-unsupported": {
        "boundary": "CURRENT_INCREMENT_IMPLEMENTED",
        "predicate": "Every current Ticket has an exact attributable implementation result with Completion: COMPLETE; verification is no and Ticket status remains ready.",
        "state": {"implemented_result": "available", "value": "revised-value"},
        "tickets": [("TICKET-001", "ready")],
        "obligations": [("implementation of revised-value is complete", "TICKET-001", ["evidence/implementation-result.json"])],
        "command": "status",
        "implementation": {"Completion": "COMPLETE", "target": "not recorded", "current_evidence": [], "independent_verification_claimed": False},
    },
    "probe-and-verification-current": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "Every current Ticket is done through an actual current verifier result; Probe completion is navigation only.",
        "product_outcome": "The ordinary current result returns value=revised-value.",
        "state": {"value": "revised-value"},
        "tickets": [("TICKET-001", "ready")],
        "obligations": [("ordinary current result returns value=revised-value", "TICKET-001", ["state/current.json"])],
        "command": "status",
        "setup_stages": ["probe", "verify"],
    },
    "probe-only-no-verification": {
        "boundary": "CURRENT_INCREMENT_DELIVERED",
        "predicate": "Every current Ticket is done through an actual current verifier result; Probe completion is navigation only.",
        "product_outcome": "The ordinary current result returns value=revised-value.",
        "state": {"value": "revised-value"},
        "tickets": [("TICKET-001", "ready")],
        "obligations": [("ordinary current result returns value=revised-value", "TICKET-001", ["state/current.json"])],
        "command": "status",
        "setup_stages": ["probe"],
    },
    "required-current-candidate-future": {
        "boundary": "NAMED_REQUIRED_ITEMS_DELIVERED",
        "predicate": "Required item core-result is currently delivered with value=ready; future-polish is Candidate and is not a completion obligation.",
        "state": {"core_result": "ready", "future_polish": "not implemented"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("required core-result is ready", "TICKET-001", ["state/current.json"])],
        "command": "status",
        "required": ["core-result"],
        "candidate": ["future-polish"],
    },
    "required-current-missing": {
        "boundary": "NAMED_REQUIRED_ITEMS_DELIVERED",
        "predicate": "Required item core-result is currently delivered with value=ready; future-polish is Candidate and is not a completion obligation.",
        "state": {"core_result": "missing", "future_polish": "available"},
        "tickets": [("TICKET-001", "done")],
        "obligations": [("required core-result is ready", "TICKET-001", ["state/current.json"])],
        "command": "status",
        "required": ["core-result"],
        "candidate": ["future-polish"],
    },
}


SUCCESS_HEADERS = {
    "IIS ADAPTIVE RUN COMPLETE",
    "IIS ADAPTIVE CURRENT INCREMENT IMPLEMENTED",
}
NONCOMPLETION_HEADERS = {
    "IIS ADAPTIVE RUN CONTRACT: USER INPUT REQUIRED",
    "IIS ADAPTIVE PLANNING PHASE COMPLETE",
    "IIS ADAPTIVE CURRENT INCREMENT DELIVERED",
    "IIS ADAPTIVE PLANNING: USER DECISION REQUIRED",
    "IIS ADAPTIVE COMPLETION EVIDENCE REQUIRED",
    "IIS ADAPTIVE RUN CONTRACT: AUTHORITY GAP",
    "IIS ADAPTIVE PLANNING: CONTRACT DRIFT",
    "IIS ADAPTIVE VERIFICATION TRIAGE",
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def load_array(path: Path, name: str) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array")
    return value


def load_oracle() -> dict[str, Any]:
    value = json.loads(ORACLE.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("cases"), list):
        raise ValueError("invalid completion case registry")
    return value


def _observation_contract(project: Path, command: str) -> dict[str, str]:
    artifact = command == "artifact-check"
    operator = command == "operator"
    return {
        "trigger": f"Inspect {project / 'release/canonical-result.json'} directly." if artifact else f"Run python3 {project / 'app.py'} {command}.",
        "boundary": "canonical release artifact" if artifact else "ordinary local CLI and its authoritative result",
        "readback": "The current canonical artifact's actual JSON fields." if artifact else "Actual JSON returned by the ordinary CLI; source constants are not runtime evidence.",
        "disposition": "Operator-assisted" if operator else "Independent",
        "independent": "no" if operator else "yes",
        "surface": "Operator-owned | preexisting approval outside product ownership" if operator else ("Existing | canonical release artifact" if artifact else "Existing | ordinary local CLI"),
        "condition": "Preexisting operator evidence outside product ownership is required; no new human action is authorized." if operator else "None",
    }


def _ticket_text(project: Path, ticket_id: str, status: str, predicate: str,
                 owned: list[dict[str, Any]], command: str) -> str:
    goals = "\n".join(f"- {row['obligation']}" for row in owned)
    criteria = "\n".join(f"- {row['obligation']}" for row in owned)
    contract = _observation_contract(project, command)
    verification = ""
    for ordinal, row in enumerate(owned, 1):
        verification += (
            "- Parent outcome ordinal: 1\n"
            f"  AC ordinals: {ordinal}\n"
            "  Behavior authority ordinals: 1\n"
            "  Initial state: The current product and declared evidence are available for inspection.\n"
            f"  Trigger or inspection target: {contract['trigger']}\n"
            f"  Acceptance boundary: {contract['boundary']}\n"
            f"  Expected observable result: {row['obligation']}\n"
            f"  Authoritative readback: {contract['readback']}\n"
            "  Decision boundary: Current readback establishes, contradicts, or leaves this obligation unresolved.\n"
            f"  Disposition: {contract['disposition']}\n"
            f"  Independent verification required: {contract['independent']}\n"
            f"  Acceptance surface: {contract['surface']}\n"
            f"  External condition: {contract['condition']}\n"
        )
    return f"""
# {ticket_id}: Current completion boundary work

Status: {status}
Parent-Spec: ../SPEC.md
Project-Root: {project}
Worker:
UI: no

## Goal

{goals}

## Acceptance Criteria

{criteria}

## Scope

Only the parent obligations listed above and their declared authoritative readback.

## Non-Goals

- Future candidate work
- External production mutation
- Parent obligations not listed in this Ticket

## Blockers

None

## Verification

{verification}
## Behavior Authorities

- docs/planning/behavior/contexts/completion-boundary.md | Scope: current product result and preservation

## References

- ../SPEC.md
- ../../current-run-contract.json

Completion context: {predicate}
"""


def materialize(case_id: str, project: Path, support: Path) -> dict[str, Any]:
    blueprint = BLUEPRINTS.get(case_id)
    if blueprint is None:
        raise ValueError(f"unknown completion case: {case_id}")
    if project == support or project.is_relative_to(support) or support.is_relative_to(project):
        raise ValueError("product and support roots must be separate sibling trees")
    if project.exists() and any(project.iterdir()):
        raise ValueError("refusing to overwrite an existing product")
    project.mkdir(parents=True, exist_ok=True, mode=0o700)
    support.mkdir(parents=True, exist_ok=True, mode=0o700)

    setup_stages = blueprint.get("setup_stages", [])
    history_limit = ("Product and approved authority are fixture setup. Probe/verifier evidence must come from actual recorded Ready invocations; no verdict or done state is seeded. The later Outer Main assessment does not itself perform delivery."
                     if setup_stages else "All Ticket/report/probe/verifier states are synthetic fixture setup history, not execution evidence from this evaluation run.")
    _put(project, "EVALUATION-FIXTURE-NOTICE.txt", history_limit if setup_stages else FIXTURE_NOTICE)
    app = _put(project, "app.py", APP)
    state = _put(project, "state/current.json", json.dumps(blueprint["state"], indent=2) + "\n")
    predicate = blueprint["predicate"]
    product_outcome = blueprint.get("product_outcome", predicate)
    boundary = blueprint["boundary"]
    required = blueprint.get("required", [])
    candidate = blueprint.get("candidate", [])
    implementation_enabled = boundary == "CURRENT_INCREMENT_IMPLEMENTED"
    command = blueprint["command"]
    obligations = [
        {
            "obligation": name,
            "owner_ticket": owner,
            "acceptance_owner": str(project / f"docs/planning/work/completion-boundary/tickets/{owner}.md") if owner else None,
            "current_evidence": [str(project / value) for value in evidence],
        }
        for name, owner, evidence in blueprint["obligations"]
    ]
    spec_outcomes = "\n".join(f"- {row['obligation']}" for row in obligations)
    observation_contract = _observation_contract(project, command)
    _put(project, "docs/planning/behavior/contexts/completion-boundary.md",
         "# Current product behavior\n\n" + spec_outcomes + "\n")

    mandate = _put(project, "docs/planning/ADAPTIVE-PLANNING-MANDATE.md", f"""
# Adaptive Planning Mandate

Desired Product Outcome: {predicate}
Decision Priorities: preserve current approved meaning; prefer actual attributable readback
Hard Constraints: local read-only final assessment; no new planning, product mutation, service, retry, or external action
Non-Goals: future candidate work and unrelated product expansion
Continuation Authority: {'BOUNDED_OUTCOME' if boundary != 'CURRENT_INCREMENT_DELIVERED' and boundary != 'CURRENT_INCREMENT_IMPLEMENTED' else 'CURRENT_INCREMENT'}
Return-to-User Boundary: missing authority, missing required evidence, or a material unresolved product decision
Applicability: this disposable current product
""")
    run_contract = {
        "Status": "CLOSED",
        "Goal Outcome": predicate,
        "Required Named Items": required or "None required",
        "Candidate Named Items": candidate or "None named",
        "Required Item Policy": "EXACT_REQUIRED_SET" if required else "NONE_REQUIRED",
        "Implementation": "yes" if implementation_enabled else "no",
        "Verification": "no" if implementation_enabled else "yes",
        "Run Completion Boundary": boundary,
        "Completion Predicate": predicate,
        "Authoritative Readback": "Inspect the ordinary local command, current state, canonical artifact, canonical Spec/Ticket ownership, and attributable evidence paths in this product.",
        "Run Contract Approval Gate": "not_required",
        "Source Authority": "Current evaluation mandate and canonical planning authority in this disposable product.",
    }
    contract = project / "docs/planning/work/current-run-contract.json"
    write_json(contract, run_contract)
    spec = _put(project, "docs/planning/work/completion-boundary/SPEC.md", f"""
# Current completion boundary

Status: approved
Owner: fixture planning owner
Source-Increment: None

## Problem

The user needs the specified current product result without losing applicable preserved behavior.

## Desired Outcome

{spec_outcomes}

## Requirements

- Produce the specified current product result.
- Preserve all applicable behavior adopted below.

## Non-Goals

- Future candidate work
- New product or external actions

## Implementation Constraints

Read-only completion assessment.

## Verification Expectations

- Outcome: {product_outcome}
  Acceptance boundary: {observation_contract['boundary']}
  Trigger or inspection target: {observation_contract['trigger']}
  Expected observable result: {product_outcome}
  Authoritative readback: {observation_contract['readback']}
  Disposition: {observation_contract['disposition']}
  Independent verification required: {observation_contract['independent']}
  Acceptance surface: {observation_contract['surface']}
  External condition: {observation_contract['condition']}

## Behavior Authorities

- docs/planning/behavior/contexts/completion-boundary.md | Scope: current product result and preservation

## UI / UX

Not applicable

## Open Questions

None
""")
    ticket_paths: list[str] = []
    owner_report_paths: list[str] = []
    for ticket_id, status in blueprint["tickets"]:
        owned = [row for row in obligations if row["owner_ticket"] == ticket_id]
        ticket = _put(
            project,
            f"docs/planning/work/completion-boundary/tickets/{ticket_id}.md",
            _ticket_text(project, ticket_id, "ready", predicate, owned, blueprint.get("ticket_commands", {}).get(ticket_id, command)),
        )
        ticket_paths.append(str(ticket))
        if setup_stages:
            continue
        evidence_lines = "\n".join(
            f"- {row['obligation']} | Claimed current readback: {', '.join(row['current_evidence']) or 'None'}"
            for row in owned
        )
        owner_report = _put(project, f"evidence/{ticket_id}-owner-result.txt", f"""
Synthetic fixture setup owner result
Ticket: {ticket}
Seeded disposition: accepted for only the listed Ticket boundaries
Owned acceptance obligations:
{evidence_lines}
Execution claim: no implementation or verifier execution is claimed for the current evaluation invocation.
Current use: inspect every claimed readback directly; this seeded report cannot establish changed, missing, or broader results by itself.
""")
        owner_report_paths.append(str(owner_report))

    # Validate the Ready Set before applying explicitly synthetic delivery history.
    # The set validator intentionally rejects already-done Tickets.
    subprocess.run(
        [sys.executable, "-B", str(ROOT.parents[1] / "matt/skills/to-tickets/validate_ticket_set.py"), str(spec)],
        check=True, capture_output=True, text=True,
    )
    for ticket_path, (_, status) in zip(ticket_paths, blueprint["tickets"], strict=True):
        if status != "ready":
            path = Path(ticket_path)
            path.write_text(path.read_text(encoding="utf-8").replace("Status: ready\n", f"Status: {status}\n", 1), encoding="utf-8")

    if not setup_stages:
        history = blueprint.get("history", "Seeded owner states establish fixture history only; inspect current product and evidence directly.")
        _put(project, "evidence/seeded-history.txt", f"Synthetic fixture setup history: {history}\nThis is not a record of actions performed by the current evaluation model invocation.\n")
    extra_readback_paths: list[str] = []
    if "operator" in blueprint:
        extra_readback_paths.append(str(support / "operator-current.json"))
        write_json(support / "operator-current.json", blueprint["operator"])
    if "artifact" in blueprint:
        extra_readback_paths.append(str(project / "release/canonical-result.json"))
        write_json(project / "release/canonical-result.json", blueprint["artifact"])
    if "limited" in blueprint:
        extra_readback_paths.append(str(project / "evidence/limited-assessment.json"))
        write_json(project / "evidence/limited-assessment.json", {**blueprint["limited"], "fixture_setup_history": True})
    if "implementation" in blueprint:
        extra_readback_paths.append(str(project / "evidence/implementation-result.json"))
        write_json(project / "evidence/implementation-result.json", {**blueprint["implementation"], "fixture_setup_history": True})

    trigger_argv = [sys.executable, str(app), command]
    readback_values = [str(app), str(state), str(contract), str(mandate), str(spec), *ticket_paths, *owner_report_paths, *extra_readback_paths]
    for obligation in obligations:
        readback_values.extend(obligation["current_evidence"])
    current_readback_paths = list(dict.fromkeys(readback_values))
    return {
        "project_root": str(project),
        "support_root": str(support),
        "ticket_paths": ticket_paths,
        "ticket_path": ticket_paths[0],
        "target_paths": [str(app), str(state)],
        "allowed_output_paths": [],
        "setup_stages": setup_stages,
        "trigger_argv": trigger_argv,
        "current_readback_paths": current_readback_paths,
        "service_argv": None,
        "service_port": None,
        "fixture_history_limit": history_limit,
    }


def prepare(case_id: str, arena: Path, variant: str, repetition: int) -> tuple[Path, dict[str, Any]]:
    oracle_cases = {case["case_id"] for case in load_oracle()["cases"]}
    if case_id not in oracle_cases or case_id not in BLUEPRINTS:
        raise ValueError(f"unknown completion case: {case_id}")
    if variant not in {"baseline", "candidate"}:
        raise ValueError("variant must be baseline or candidate")
    if isinstance(repetition, bool) or repetition < 1:
        raise ValueError("repetition must be a positive integer")
    run_id = uuid.uuid4().hex
    run_root = arena.resolve() / run_id
    run_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    metadata = materialize(case_id, run_root / "product", run_root / "support")
    metadata.update({
        "schema": "iis-completion-experiment-metadata/v1",
        "case_id": case_id,
        "run_id": run_id,
        "run_root": str(run_root),
        "variant": variant,
        "repetition": repetition,
    })
    project = Path(metadata["project_root"])
    if metadata["setup_stages"]:
        for argv in (["git", "-c", "core.hooksPath=/dev/null", "init", "--quiet"],
                     ["git", "add", "--all"],
                     ["git", "-c", "user.name=Calibration", "-c", "user.email=calibration@localhost", "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Initial product state"]):
            subprocess.run(argv, cwd=project, check=True, capture_output=True)
        for stage in metadata["setup_stages"]:
            metadata["current_readback_paths"].extend(str(run_root / stage / name) for name in ("terminal.txt", "record.json"))
        metadata["current_readback_paths"].append(str(run_root / "probe-binding.json"))
    expected = product_snapshot(project)
    metadata["setup_initial_product_digest"] = snapshot_digest(expected)
    if "verify" in metadata["setup_stages"]:
        ticket = Path(metadata["ticket_path"])
        expected[str(ticket.relative_to(run_root))] = hashlib.sha256(ticket.read_bytes().replace(b"Status: ready\n", b"Status: done\n", 1)).hexdigest()
    # A planned post-setup input is not a claim that setup already happened.
    metadata["initial_product_digest"] = snapshot_digest(expected)
    metadata_path = run_root / "metadata.json"
    write_json(metadata_path, metadata)
    return metadata_path, metadata


def product_snapshot(root: Path) -> dict[str, str]:
    # Both the product and its separately owned read-only authority are inputs.
    return {
        str(path.relative_to(root.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in (root, root.parent / "support")
        for path in sorted(directory.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and ".git" not in path.parts
    }


def snapshot_digest(snapshot: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def completion_prompt(metadata: dict[str, Any]) -> str:
    return (
        f"Project Root: {metadata['project_root']}\n"
        "IIS Adaptive Planning을 명시적으로 계속 호출한다. 이 호출은 이미 닫힌 현재 Mandate와 Run Contract에 대한 "
        "Outer Main의 읽기 전용 final completion assessment이다. read로 skill://iis-adaptive-planning 을 호출하고, "
        "그 현재 계약 및 terminal-report/run-contract reference를 적용하라. 새 기획, 구현, 검증, 서비스 생성, "
        "corrective retry, 제품·Ticket·evidence 수정, 외부 행위는 승인하지 않는다.\n"
        f"Current Mandate: {Path(metadata['project_root']) / 'docs/planning/ADAPTIVE-PLANNING-MANDATE.md'}\n"
        f"Current Run Contract: {Path(metadata['project_root']) / 'docs/planning/work/current-run-contract.json'}\n"
        f"Current canonical parent: {Path(metadata['project_root']) / 'docs/planning/work/completion-boundary/SPEC.md'}\n"
        f"Current canonical Tickets: {json.dumps(metadata['ticket_paths'], ensure_ascii=False)}\n"
        f"Ordinary read-only trigger argv: {json.dumps(metadata['trigger_argv'], ensure_ascii=False)}\n"
        f"Current readback paths: {json.dumps(metadata['current_readback_paths'], ensure_ascii=False)}\n"
        f"Fixture history boundary: {metadata['fixture_history_limit']}\n"
        "현재 inspectable local CLI, canonical artifact, operator evidence, acceptance ownership 및 실제 파일을 필요한 만큼 직접 관찰해 active predicate를 정확히 평가하라. "
        "선재 local operator approval은 현재 authority evidence일 수 있지만 새 사람 행위로 표현하지 않는다.\n"
        "현재 terminal-report 계약에서 이 assessment 결과에 정확히 대응하는 terminal을 사용하라. "
        "새 terminal을 만들거나 숨은 평가 정답·부모 디렉터리를 찾지 말고 STOP하라.\n"
    )


def _plain_line(line: str) -> str:
    value = line.strip().replace("**", "").replace("`", "")
    return re.sub(r"^#+\s*", "", value).strip()


def parse_completion(terminal: str, *, transport_valid: bool = True) -> bool | None:
    if not transport_valid:
        return None
    lines = {_plain_line(line) for line in terminal.splitlines() if _plain_line(line)}
    success = bool(lines & SUCCESS_HEADERS)
    incomplete = bool(lines & NONCOMPLETION_HEADERS) or bool(
        re.search(r"(?im)^\s*(?:[-*]\s*)?Whole-run (?:completion|predicate satisfied)\s*:\s*no\s*$", terminal.replace("**", "").replace("`", ""))
    )
    if success == incomplete:
        return None
    return success


def run(metadata_path: Path, *, agent_dir: Path, payload: Path, runtime_data: Path,
        model: str, thinking: str, timeout: int) -> dict[str, Any]:
    metadata_path = metadata_path.resolve(strict=True)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    run_root = Path(metadata["run_root"]).resolve(strict=True)
    if metadata_path != run_root / "metadata.json":
        raise ValueError("metadata must be the canonical run_root/metadata.json")
    project = Path(metadata["project_root"]).resolve(strict=True)
    for stage in metadata.get("setup_stages", []):
        try:
            setup = json.loads((run_root / stage / "record.json").read_text(encoding="utf-8"))
            observed = json.loads((run_root / stage / "observation.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValueError(f"actual {stage} setup capture is required") from error
        native_setup = summarize(load_events(run_root / stage / "events.jsonl"))
        if not native_setup["model_completed"]:
            raise ValueError(f"actual {stage} setup did not terminate cleanly")
        if setup.get("exit_code") != 0 or setup.get("agent_ended") is not True or setup.get("timed_out") is not False or setup.get("target_mutated") is not False:
            raise ValueError(f"actual {stage} setup did not terminate cleanly on its unchanged target")
        if not _model_matches(model, observed.get("actual_models")):
            raise ValueError(f"actual {stage} setup used a different model")
        if stage == "probe" and (observed.get("probe_completion") != "COMPLETE" or not (run_root / "probe-binding.json").is_file()):
            raise ValueError("actual COMPLETE probe and machine handoff are required")
        if stage == "verify" and setup.get("parsed_verdict") != "VERIFIED":
            raise ValueError("actual VERIFIED setup is required")
    before = product_snapshot(project)
    if snapshot_digest(before) != metadata.get("initial_product_digest"):
        raise ValueError("prepared product changed before the completion observation")
    observation = invoke(
        project_root=project,
        prompt=completion_prompt(metadata),
        output_dir=run_root / "completion",
        agent_dir=agent_dir,
        payload=payload,
        runtime_data=runtime_data,
        model=model,
        thinking=thinking,
        timeout=timeout,
    )
    after = product_snapshot(project)
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    transport_valid = observation["clean_transport"]
    parsed = parse_completion(observation["terminal_text"], transport_valid=transport_valid)
    events_path = Path(observation["raw_events"]).resolve()
    terminal_path = run_root / "completion/terminal.txt"
    record = {
        "schema": "iis-completion-observation/v1",
        "case_id": metadata["case_id"],
        "run_id": metadata["run_id"],
        "variant": metadata["variant"],
        "repetition": metadata["repetition"],
        "parsed_completion": parsed,
        "parse_status": "complete" if parsed is True else "incomplete" if parsed is False else "invalid",
        "raw_events": str(events_path),
        "raw_events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        "raw_terminal_result": str(terminal_path.resolve()),
        "terminal_sha256": hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        "model_requested": model,
        "actual_models": observation["actual_models"],
        "thinking": thinking,
        "exit_code": observation["exit_code"],
        "timed_out": observation["timed_out"],
        "agent_ended": observation["agent_ended"],
        "clean_transport": transport_valid,
        "stop_reason": observation["stop_reason"],
        "error_message": observation["error_message"],
        "target_mutated": bool(changed),
        "changed_paths": changed,
        "pre_project_root_digest": snapshot_digest(before),
        "post_project_root_digest": snapshot_digest(after),
        "elapsed_seconds": observation["elapsed_seconds"],
        "usage": observation["usage"],
        "fixture_history_limit": metadata["fixture_history_limit"],
        "causal_review": "PENDING_INDEPENDENT_MAIN_REVIEW",
    }
    write_json(run_root / "completion/record.json", record)
    return record


def _pair(value: object) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    case_id, run_id = value.get("case_id"), value.get("run_id")
    if not isinstance(case_id, str) or not case_id or not isinstance(run_id, str) or not run_id:
        return None
    return case_id, run_id


def _error(errors: list[dict[str, Any]], code: str, **details: object) -> None:
    errors.append({"code": code, **details})


def _model_matches(requested: object, actual: object) -> bool:
    if not isinstance(requested, str) or not requested or not isinstance(actual, list) or not actual:
        return False
    return all(
        isinstance(value, str) and (value == requested or ("/" not in requested and value.endswith("/" + requested)))
        for value in actual
    )


def _check_review(review: dict[str, Any], metadata: dict[str, Any], events_path: Path,
                  errors: list[dict[str, Any]]) -> None:
    pair = {"case_id": metadata["case_id"], "run_id": metadata["run_id"]}
    if review.get("causal_evidence_sufficient") is not True:
        _error(errors, "insufficient_causal_evidence", **pair)
    for field in ("reason", "boundary_review"):
        value = review.get(field)
        if not isinstance(value, str) or not value.strip():
            _error(errors, f"invalid_{field}", **pair)
    refs = review.get("evidence_refs")
    if not isinstance(refs, list) or len(refs) != 1 or not isinstance(refs[0], dict):
        _error(errors, "invalid_evidence_refs", **pair)
        return
    ref = refs[0]
    try:
        ref_path = Path(ref.get("path", "")).resolve()
    except (OSError, ValueError, TypeError):
        _error(errors, "invalid_evidence_ref", **pair)
        return
    if ref_path != events_path:
        _error(errors, "foreign_events_ref", path=str(ref_path), expected=str(events_path), **pair)
    try:
        digest = hashlib.sha256(ref_path.read_bytes()).hexdigest()
    except OSError:
        _error(errors, "missing_evidence_ref", path=str(ref_path), **pair)
        return
    if ref.get("sha256") != digest:
        _error(errors, "evidence_hash_mismatch", path=str(ref_path), **pair)


def build_report(metadata_paths: list[Path], records: list[dict[str, Any]],
                 reviews: list[dict[str, Any]], oracle: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    oracle_cases = {case["case_id"]: case for case in oracle["cases"]}
    expected: dict[tuple[str, str], tuple[dict[str, Any], Path]] = {}
    variants: set[str] = set()
    slices: dict[tuple[str, int], set[str]] = {}

    for index, metadata_path in enumerate(metadata_paths):
        try:
            path = metadata_path.resolve(strict=True)
            metadata = json.loads(path.read_text(encoding="utf-8"))
            pair = _pair(metadata)
            run_root = Path(metadata["run_root"]).resolve(strict=True)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            _error(errors, "invalid_cohort_metadata", index=index, path=str(metadata_path))
            continue
        if pair is None:
            _error(errors, "invalid_cohort_metadata", index=index, path=str(path))
            continue
        if path != run_root / "metadata.json" or metadata.get("run_id") != run_root.name:
            _error(errors, "noncanonical_cohort_metadata", index=index, path=str(path), case_id=pair[0], run_id=pair[1])
        try:
            canonical_run_id = uuid.UUID(pair[1]).hex == pair[1]
            project_root = Path(metadata["project_root"]).resolve(strict=True)
            support_root = Path(metadata["support_root"]).resolve(strict=True)
        except (OSError, ValueError, KeyError, TypeError):
            canonical_run_id = False
            project_root = support_root = run_root
        if not canonical_run_id or project_root != run_root / "product" or support_root != run_root / "support":
            _error(errors, "external_run_root", index=index, case_id=pair[0], run_id=pair[1])
        if metadata.get("schema") != "iis-completion-experiment-metadata/v1":
            _error(errors, "invalid_metadata_schema", index=index, case_id=pair[0], run_id=pair[1])
        if pair in expected:
            _error(errors, "duplicate_cohort_run", case_id=pair[0], run_id=pair[1])
            continue
        case_id, _ = pair
        if case_id not in oracle_cases:
            _error(errors, "external_cohort_case", case_id=case_id, run_id=pair[1])
        variant, repetition = metadata.get("variant"), metadata.get("repetition")
        if variant not in {"baseline", "candidate"} or isinstance(repetition, bool) or not isinstance(repetition, int) or repetition < 1:
            _error(errors, "invalid_cohort_coordinate", case_id=case_id, run_id=pair[1])
        else:
            variants.add(variant)
            bucket = slices.setdefault((variant, repetition), set())
            if case_id in bucket:
                _error(errors, "duplicate_case_in_slice", case_id=case_id, variant=variant, repetition=repetition)
            bucket.add(case_id)
        expected[pair] = (metadata, run_root / "completion/record.json")

    if not expected:
        _error(errors, "empty_cohort")
    if len(variants) > 1:
        _error(errors, "mixed_variant_cohort", variants=sorted(variants))
    required_ids = set(oracle_cases)
    for (variant, repetition), case_ids in sorted(slices.items()):
        missing = sorted(required_ids - case_ids)
        extra = sorted(case_ids - required_ids)
        if missing or extra:
            _error(errors, "inexact_case_denominator", variant=variant, repetition=repetition, missing=missing, extra=extra)
    required_repetitions = oracle.get("required_repetitions")
    if not isinstance(required_repetitions, list) or not required_repetitions or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in required_repetitions
    ) or len(required_repetitions) != len(set(required_repetitions)):
        _error(errors, "invalid_oracle_repetitions")
    elif len(variants) == 1:
        variant = next(iter(variants))
        observed_repetitions = {repetition for slice_variant, repetition in slices if slice_variant == variant}
        if observed_repetitions != set(required_repetitions):
            _error(errors, "inexact_repetition_denominator", variant=variant,
                   missing=sorted(set(required_repetitions) - observed_repetitions),
                   extra=sorted(observed_repetitions - set(required_repetitions)))

    result_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for index, record in enumerate(records):
        pair = _pair(record)
        if pair is None:
            _error(errors, "invalid_result", index=index)
            continue
        if pair not in expected:
            _error(errors, "external_result", case_id=pair[0], run_id=pair[1], index=index)
            continue
        if pair in result_by_pair:
            _error(errors, "duplicate_result", case_id=pair[0], run_id=pair[1], index=index)
            continue
        result_by_pair[pair] = record
        metadata, capture_path = expected[pair]
        try:
            captured = json.loads(capture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _error(errors, "missing_capture_record", case_id=pair[0], run_id=pair[1], path=str(capture_path))
            continue
        if captured != record:
            _error(errors, "capture_record_mismatch", case_id=pair[0], run_id=pair[1], path=str(capture_path))
        if record.get("variant") != metadata.get("variant") or record.get("repetition") != metadata.get("repetition"):
            _error(errors, "result_coordinate_mismatch", case_id=pair[0], run_id=pair[1])
        if record.get("pre_project_root_digest") != metadata.get("initial_product_digest"):
            _error(errors, "initial_product_mismatch", case_id=pair[0], run_id=pair[1])
        events_path = Path(metadata["run_root"]) / "completion/events.jsonl"
        terminal_path = Path(metadata["run_root"]) / "completion/terminal.txt"
        if record.get("raw_events") != str(events_path.resolve()) or record.get("raw_terminal_result") != str(terminal_path.resolve()):
            _error(errors, "raw_capture_path_mismatch", case_id=pair[0], run_id=pair[1])
        for path, hash_field, missing_code, mismatch_code in (
            (events_path, "raw_events_sha256", "missing_raw_events", "raw_events_hash_mismatch"),
            (terminal_path, "terminal_sha256", "missing_terminal", "terminal_hash_mismatch"),
        ):
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                _error(errors, missing_code, case_id=pair[0], run_id=pair[1], path=str(path))
                continue
            if record.get(hash_field) != digest:
                _error(errors, mismatch_code, case_id=pair[0], run_id=pair[1], path=str(path))
        try:
            terminal_text = terminal_path.read_text(encoding="utf-8")
        except OSError:
            terminal_text = ""
        try:
            native = summarize(load_events(events_path))
        except OSError:
            native = {}
        transport_valid = record.get("exit_code") == 0 and record.get("agent_ended") is True and record.get("timed_out") is False
        transport_valid = transport_valid and native.get("model_completed") is True
        if native.get("terminal_text") != terminal_text:
            _error(errors, "native_capture_mismatch", case_id=pair[0], run_id=pair[1])
        if record.get("parsed_completion") is not parse_completion(terminal_text, transport_valid=transport_valid):
            _error(errors, "parsed_terminal_mismatch", case_id=pair[0], run_id=pair[1])
        if record.get("parsed_completion") not in {True, False}:
            _error(errors, "invalid_completion", case_id=pair[0], run_id=pair[1])
        if not transport_valid:
            _error(errors, "model_not_cleanly_terminated", case_id=pair[0], run_id=pair[1])
        if record.get("target_mutated") is not False or record.get("pre_project_root_digest") != record.get("post_project_root_digest"):
            _error(errors, "target_changed", case_id=pair[0], run_id=pair[1])
        if not _model_matches(record.get("model_requested"), record.get("actual_models")):
            _error(errors, "model_mismatch", case_id=pair[0], run_id=pair[1])

    for pair in expected:
        if pair not in result_by_pair:
            _error(errors, "missing_result", case_id=pair[0], run_id=pair[1])

    review_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for index, review in enumerate(reviews):
        pair = _pair(review)
        if pair is None:
            _error(errors, "invalid_review", index=index)
            continue
        if pair not in expected:
            _error(errors, "external_review", case_id=pair[0], run_id=pair[1], index=index)
            continue
        if pair in review_by_pair:
            _error(errors, "duplicate_review", case_id=pair[0], run_id=pair[1], index=index)
            continue
        review_by_pair[pair] = review
        metadata = expected[pair][0]
        _check_review(review, metadata, Path(metadata["run_root"]) / "completion/events.jsonl", errors)
    for pair in expected:
        if pair not in review_by_pair:
            _error(errors, "missing_review", case_id=pair[0], run_id=pair[1])

    rows = []
    label_pass = bool(expected)
    for pair, (metadata, _) in expected.items():
        record = result_by_pair.get(pair)
        expected_completion = oracle_cases.get(pair[0], {}).get("expected_completion")
        actual = record.get("parsed_completion") if record else None
        matches = actual is expected_completion
        label_pass = label_pass and matches
        rows.append({
            "case_id": pair[0],
            "run_id": pair[1],
            "variant": metadata.get("variant"),
            "repetition": metadata.get("repetition"),
            "expected_completion": expected_completion,
            "parsed_completion": actual,
            "label_match": matches,
        })
    variant = next(iter(variants), None) if len(variants) == 1 else None
    candidate_accepted = variant == "candidate" and label_pass and not errors
    return {
        "schema": "iis-completion-experiment-report/v1",
        "variant": variant,
        "label_pass": label_pass,
        "candidate_accepted": candidate_accepted,
        "errors": errors,
        "coverage": {
            "oracle_cases": len(oracle_cases),
            "cohort_runs": len(expected),
            "result_runs": len(result_by_pair),
            "review_runs": len(review_by_pair),
            "slices": [{"variant": variant_name, "repetition": repetition, "cases": len(case_ids)} for (variant_name, repetition), case_ids in sorted(slices.items())],
        },
        "cases": rows,
        "baseline_note": "A baseline report is diagnostic and never sets candidate_accepted=true." if variant == "baseline" else None,
    }


def report(cohort: Path, results: Path, reviews: Path) -> dict[str, Any]:
    cohort_values = load_array(cohort, "cohort")
    if not all(isinstance(value, str) and value for value in cohort_values):
        raise ValueError("cohort must contain metadata path strings")
    metadata_paths = [Path(value) for value in cohort_values]
    records = load_array(results, "results")
    review_values = load_array(reviews, "reviews")
    if not all(isinstance(value, dict) for value in records):
        raise ValueError("results must contain JSON objects")
    if not all(isinstance(value, dict) for value in review_values):
        raise ValueError("reviews must contain JSON objects")
    return build_report(metadata_paths, records, review_values, load_oracle())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("prepare")
    setup.add_argument("case_id")
    setup.add_argument("--arena", required=True, type=Path)
    setup.add_argument("--variant", required=True, choices=("baseline", "candidate"))
    setup.add_argument("--repetition", required=True, type=int)
    execute = commands.add_parser("run")
    execute.add_argument("--metadata", required=True, type=Path)
    execute.add_argument("--agent-dir", required=True, type=Path)
    execute.add_argument("--payload", required=True, type=Path)
    execute.add_argument("--runtime-data", required=True, type=Path)
    execute.add_argument("--model", required=True)
    execute.add_argument("--thinking", default="medium")
    execute.add_argument("--timeout", default=480, type=int)
    aggregate = commands.add_parser("report")
    aggregate.add_argument("--cohort", required=True, type=Path)
    aggregate.add_argument("--results", required=True, type=Path)
    aggregate.add_argument("--reviews", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "prepare":
        metadata_path, metadata = prepare(args.case_id, args.arena, args.variant, args.repetition)
        print(json.dumps({"metadata": str(metadata_path), "service_argv": metadata["service_argv"], "service_port": metadata["service_port"]}, indent=2))
        return 0
    if args.command == "run":
        record = run(args.metadata, agent_dir=args.agent_dir, payload=args.payload, runtime_data=args.runtime_data,
                     model=args.model, thinking=args.thinking, timeout=args.timeout)
        print(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True))
        return 0 if record["clean_transport"] else 1
    aggregate_result = report(args.cohort, args.results, args.reviews)
    print(json.dumps(aggregate_result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if aggregate_result["candidate_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
