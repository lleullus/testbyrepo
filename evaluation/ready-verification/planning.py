#!/usr/bin/env python3
"""Capture explicit planning turns and audit a fixed cohort; never approve a turn automatically."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import uuid

from run_agent import invoke, load_events, summarize

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "planning-cases.json"
_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

APP = '''import json, os, sys, tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
root = Path(__file__).resolve().parent
command = sys.argv[1] if len(sys.argv) > 1 else "status"
state = json.loads((root / "state.json").read_text())
registry = json.loads((root / "registry.json").read_text())
if command == "status":
    result = state
elif command == "capabilities":
    result = registry
elif command == "artifact":
    result = json.loads((root / "release.json").read_text())
elif command == "external":
    try:
        with urlopen(json.loads((root / "external.json").read_text())["url"], timeout=5) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        result = {"available": False, "http_status": error.code}
    except URLError as error:
        result = {"available": False, "transport_error": str(error.reason)}
elif command == "publish" and "publish" in registry["commands"]:
    if state.get("document") != "alpha" or state.get("publication") not in {"draft", "published"}:
        raise SystemExit("invalid publication state")
    if state["publication"] == "draft":
        state["publication"] = "published"
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=root, delete=False) as output:
                temporary = Path(output.name)
                json.dump(state, output)
            os.replace(temporary, root / "state.json")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    result = state
else:
    raise SystemExit("unavailable command")
print(json.dumps(result, sort_keys=True))
'''

POLICY = """- The document identity is alpha; the local document owner may publish it.
- Publication changes draft to published and survives a process restart.
- Repeating publication leaves the same published result; it does not create a second document.
- Existing legacy status remains stable; internal storage and implementation choices are not product policy.
- Ordinary publication is the local CLI publish operation; existing status/default-status and truthful capabilities discovery remain available. This public boundary is deliberate; storage and internal command routing are not fixed.
- Successful initial or repeated publication returns exit zero and the same current state meaning as ordinary status. JSON spacing and key order are not policy. Non-publication values, including opaque source_version, remain unchanged.
- A definite failure returns nonzero and an identifiable error without manufacturing a document or claiming success. Missing, corrupt or different identity is not silently reset to alpha draft.
- Interrupted persistence may leave the complete prior draft or complete published result, never a partial/corrupt product state. Lost response is resolved by current status before retry; no repair/reset capability is promised.
- Immediate publication calls may overlap and converge on published while preserving other values. Overlapping status may read complete draft or published; status begun after successful publication reads published. Power-loss guarantees and unrelated external state writers are outside this contract.
- No UI, account provisioning, network publication, or unrelated future candidate is required.
"""


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def put(root: Path, relative: str, content: str) -> Path:
    root.mkdir(mode=0o700, exist_ok=True)
    path = root / relative
    current = root
    for part in Path(relative).parts[:-1]:
        current /= part
        current.mkdir(mode=0o700, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def snapshot(project: Path) -> dict[str, str]:
    return {str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(project.rglob("*"))
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts}


def protected(files: dict[str, str]) -> dict[str, str]:
    return {path: digest for path, digest in files.items() if not path.startswith("docs/planning/")}


def behavior(policy: str = POLICY, *, scope: str = "alpha publication and legacy preservation") -> str:
    return f"# Publication behavior\n\nStatus: approved\nOwner: evaluation product owner\nScope: {scope}\n\n" + policy


def spec(outcome: str, boundary: str, trigger: str, readback: str, *, surface: str = "Existing | ordinary local CLI", condition: str = "None", status: str = "approved") -> str:
    return f"""# Alpha publication

Status: {status}
Owner: evaluation product owner
Source-Increment: None

## Problem

The local owner needs the approved alpha result without losing legacy behavior.

## Desired Outcome

- {outcome}

## Requirements

- {outcome}
- Preserve the adopted alpha publication and legacy behavior.

## Non-Goals

- UI and unrelated future candidate work
- Mutating the separately owned external authority

## Implementation Constraints

Internal implementation choices remain delivery-owned.

## Verification Expectations

- Outcome: {outcome}
  Acceptance boundary: {boundary}
  Trigger or inspection target: {trigger}
  Expected observable result: {outcome}
  Authoritative readback: {readback}
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: {surface}
  External condition: {condition}

## Behavior Authorities

- docs/planning/behavior/contexts/publication.md | Scope: alpha publication and legacy preservation

## UI / UX

Not applicable

## Open Questions

None
"""


def ticket(project: Path, number: int, ac: str, scope: str, non_goals: str) -> str:
    return f"""# TICKET-{number:03d}: Alpha publication

Status: draft
Parent-Spec: ../SPEC.md
Project-Root: {project}
Worker:
UI: no

## Goal

{ac}

## Acceptance Criteria

- {ac}

## Scope

{scope}

## Non-Goals

- {non_goals}

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1
  Behavior authority ordinals: 1
  Initial state: Alpha is draft and legacy status is stable.
  Trigger or inspection target: Publish alpha, restart the process, repeat publication and inspect current status and legacy behavior.
  Acceptance boundary: ordinary CLI publication and authoritative persisted status after process restart
  Expected observable result: {ac}
  Authoritative readback: Actual ordinary CLI status from the current persisted document; acknowledgements and source constants are not delivery proof.
  Decision boundary: Current readback determines publication, persistence and preservation.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | ordinary publication and persisted status readback
  External condition: None

## Behavior Authorities

- docs/planning/behavior/contexts/publication.md | Scope: alpha publication and legacy preservation

## References

- ../SPEC.md
"""


def _require_current_source() -> None:
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != _SOURCE_SHA256:
        raise ValueError("planning source changed after import; use a fresh process")


def prepare(case_id: str, arena: Path, variant: str, repetition: int, *, external_url: str | None = None) -> Path:
    _require_current_source()
    case = next((row for row in json.loads(ORACLE.read_text())["cases"] if row["case_id"] == case_id), None)
    if case is None:
        raise ValueError("unknown planning case")
    if repetition < 1 or not variant:
        raise ValueError("variant and positive repetition are required")
    root = arena.resolve() / uuid.uuid4().hex
    root.mkdir(parents=True, mode=0o700)
    project = root / "product"
    project.mkdir(mode=0o700)
    put(project, "app.py", APP)
    state = {"document": "alpha", "publication": "draft", "legacy": "stable", "source_version": 1}
    registry = {"commands": ["status", "capabilities"]}
    write_json(project / "state.json", state)
    write_json(project / "registry.json", registry)
    initial_fact = f"Historical investigation navigation only. app.py status read alpha=draft and legacy=stable. registry.json had no publish command. State anchor SHA-256: {hashlib.sha256((project / 'state.json').read_bytes()).hexdigest()}. Registry anchor SHA-256: {hashlib.sha256((project / 'registry.json').read_bytes()).hexdigest()}. Facts are not product policy. Re-establish only load-bearing facts at their proper currentness boundary."
    put(project, "investigation.txt", initial_fact + "\n")
    family, state_name = case["family"], case["state"]
    outcome = "The owner can publish alpha durably, repeated publication keeps the same result, and legacy status remains stable."
    boundary = "ordinary CLI publication and authoritative persisted status after process restart"
    trigger = "Publish alpha through the ordinary product entrypoint, restart the process, then inspect status and legacy behavior."
    readback = "Actual ordinary CLI status from the current persisted document; acknowledgements and source constants are not delivery proof."
    surface = "Ticket Scope creates | ordinary publication and persisted status readback"
    condition = "None"
    policy = POLICY
    behavior_scope = "alpha publication and legacy preservation"
    extra = ""
    if family == "current-evidence" and state_name == "changed":
        state["source_version"] = 2
        state["publication"] = "published"
        write_json(project / "state.json", state)
    if family == "absence-and-search-universe" and state_name == "expanded":
        registry["commands"].append("publish")
        write_json(project / "registry.json", registry)
        extra = "If current product capability already satisfies the request, report that fact and the exact remaining non-planning action rather than inventing a construction Increment. Do not execute publication in this planning episode."
    if family in {"approved-behavior-reuse", "behavior-impact-not-code-size"}:
        registry["commands"].append("publish")
        write_json(project / "registry.json", registry)
    if family == "approved-behavior-reuse":
        behavior_scope = "alpha publication, ordinary CLI status export and legacy preservation"
        policy += """- The local document owner exports alpha through the ordinary local CLI export operation. Successful export returns exit zero and one JSON object on standard output, with the same complete current document meaning as ordinary status, including identity, publication, legacy and opaque metadata. Canonical means semantic JSON content; whitespace and key order are not policy.
- Export is a read-only point-in-time snapshot. It does not create or manage an output file, another document, synchronization or a new persisted lifecycle, and never changes identity or any persisted value. Earlier exported content does not update afterward.
- Export overlapping publication may observe either complete draft or complete published state, never a mixture; export begun after successful publication observes published. Without a state change, repeated exports have the same semantic content. A retry obtains a current snapshot, not guaranteed reproduction of an interrupted earlier snapshot.
- Missing, corrupt, different-identity or invalid-publication state yields nonzero and an identifiable error, never manufactured alpha defaults or successful snapshot output. Partial or interrupted output is not a successful export; exact diagnostics beyond identifiable failure are not policy.
- Truthful capabilities discovery includes export once delivered. Existing publication, explicit/default status, failure/recovery, persistence, repetition, overlap and non-publication-value preservation retain the rules above. Internal storage, synchronization and routing are not selected; power loss and unrelated external writers remain outside scope.
"""
        outcome = "The local owner can export the current alpha status as a canonical JSON snapshot while preserving existing publication and legacy behavior."
        boundary = "ordinary CLI export stdout JSON snapshot and unchanged ordinary publication/status behavior"
        trigger = "Export current alpha through the ordinary local CLI export operation; compare its stdout snapshot with current persisted status and inspect preserved publication behavior."
        readback = "Actual stdout JSON object from ordinary CLI export compared with the complete current persisted document meaning from ordinary status; existing approved behavior is preserved."
        surface = "Ticket Scope creates | ordinary CLI export stdout snapshot"
    if family == "approved-behavior-reuse" and state_name == "authority-conflict":
        policy = policy.replace("the local document owner may publish it", "only a distinct release operator may publish it")
        extra = "The current request explicitly reserves publication to the local document owner; the older authority must not silently override that current product choice."
    if family == "behavior-impact-not-code-size":
        if state_name == "local-delta":
            extra = "The changed observable rule is only: a status query for an unknown document returns an explicit not-found result; alpha publication and all existing lifecycle rules are preserved."
            outcome = "An unknown document status returns an explicit not-found result while existing alpha publication and legacy behavior remain unchanged."
            boundary = "ordinary unknown-document status and preserved alpha/legacy behavior"
            trigger = "Query an unknown document through ordinary status; then inspect unchanged alpha status and existing publication behavior."
            readback = "The ordinary unknown-document result is explicitly not-found; alpha publication and legacy status retain their approved meaning."
            surface = "Ticket Scope creates | unknown-document status result"
        else:
            extra = "A proposed small change adds delayed publication confirmation. Owner revocation and cancellation must win over late success; retries share the same operation identity, and competing owners cannot both acquire publication ownership. These are fixed product rules, not internal lock or queue prescriptions."
            extra += " Only the currently authorized document owner may acquire, cancel or revoke publication ownership. A competing acquisition reports conflict without replacing the incumbent. Completed publication is not reversed; cancellation/revocation effective before completion permanently prevents that operation's publication. A concurrent race may choose either winner but never report both publication and cancellation as successful. A new attempt after cancellation, revocation or definitive failure uses a new identity; retries retain the original identity, owner and current outcome, and a mismatched identity/owner/document combination is rejected. Lost response alone is unresolved, not failure or cancellation. Restart preserves attributable recovery; no automatic expiry or timeout cancellation is required. Readback distinguishes pending, published, cancelled, revoked and failed operations from the document's current published state."
            outcome = "Delayed publication respects current ownership and cancellation; retries do not duplicate publication and late success cannot revive cancellation."
            boundary = "delayed publication confirmation under current ownership, retry and cancellation"
            trigger = "Request publication, retry after a lost response, revoke or cancel before delayed completion, and inspect the current attributable publication result."
            readback = "Current operation identity, owner and terminal publication state from the ordinary product readback, not the initial request acknowledgement."
            surface = "Ticket Scope creates | delayed publication and recovery readback"
    if family == "lifecycle-counterexamples":
        state["reservation"] = {"id": "res-alpha", "state": "held", "owner": "local"}
        write_json(project / "state.json", state)
        if state_name == "closed-policy":
            behavior_scope = "alpha publication and legacy preservation, and the existing res-alpha reservation lifecycle"
            extra = "The supplied approved reservation authority fully specifies the current local CLI lifecycle. Preserve both allowed confirmation/expiry race winners; neither a deterministic scheduler nor a new deadline policy is requested."
            policy += """- The reservation scope is the existing held reservation res-alpha, owned by local. Ordinary local CLI execution acts as the local operator; reservation identity is not a credential. Only when the current reservation owner is local may that operator confirm, cancel or explicitly expire it. No new account system, owner transfer, competing acquisition, reservation creation, availability state, renewal or reset capability is introduced.
- The ordinary local CLI operations are confirm res-alpha, cancel res-alpha and expire res-alpha. Existing status/default-status returns the complete alpha document including the reservation id, owner and current state. Unknown reservation identities, missing/corrupt reservation state, unsupported states and a non-local current owner are identifiable failures, not permission to create, repair or replace a reservation. Discovery truthfully advertises delivered operations.
- From held, confirmation selects confirmed, cancellation selects cancelled and explicit expiry selects expired. Expiry is an explicit authorized local action, not elapsed time: no deadline, timer, scheduler, automatic expiry or external clock is promised. A confirmation request may overlap other operations; starting it does not reserve success or priority.
- Confirmed, cancelled and expired are mutually exclusive durable terminal states. If different transitions overlap, either may win, never both; one completed transition prevents every different later transition. Thus confirmation/expiry may have either winner, and completed cancellation or expiry cannot be revived by late confirmation. No particular synchronization mechanism or interruption checkpoint is prescribed.
- Identity and authorization checks apply to every invocation. A successful initial transition, or a retry of that same action after its matching terminal outcome, returns exit zero and one JSON result carrying the unchanged reservation id, owner and current terminal state. Repeating an action cannot create another reservation or duplicate confirmation. A different action against a terminal state returns nonzero with an identifiable rejection and the actual terminal state; no second success is reported.
- Other definite failures return nonzero and an identifiable error without false success, manufactured state or mutation. Exact diagnostic wording, JSON spacing/key order and the particular nonzero exit code are not policy. Where no valid reservation can be read, do not invent a current identity or terminal result.
- Lost or interrupted response is uncertainty, not a state transition. Read current ordinary status before retry. A still-held result permits an authorized retry without priority over another transition; a terminal result determines the matching idempotent retry or conflicting rejection. There is no separate pending state, background scheduler or autonomous completion after the invoking process has stopped.
- Persistence interrupted during a transition leaves the complete prior held state or one complete committed terminal state, never partial/corrupt state. Identity, owner and the winning state survive process restart. Overlapping status may observe a complete prior or resulting state; a status call begun after an acknowledged transition must observe that terminal state. Power loss and unrelated external file writers are outside scope.
- Reservation operations never publish alpha or alter its identity, publication, legacy or opaque metadata. Existing publication remains independent: no confirmation prerequisite, automatic confirmation or shared terminal outcome. Publication and reservation transitions, including overlap, preserve one another's current fields; a later serialized update cannot lose the other operation's completed result. The existing publication failure/retry/restart/overlap guarantees remain unchanged.
- Acceptance exercises the ordinary local operations and complete current status readback, including repeat/conflicting actions, lost response, interruption, restart and permitted overlap results on independently arranged disposable instances. Private helpers, initial acknowledgements and source constants cannot replace that readback. Internal storage, routing and synchronization remain implementation-owned; no UI or external service is required.
"""
        else:
            extra = "The new reservation feature has held/confirmed/cancelled/expired states and delayed confirmation. The user has NOT decided the expiry-versus-confirmation rule or whether a late success may revive cancellation. These user-observable policies are not delegated to implementation. Identify the complete current decision frontier and stop for the user; do not adopt new authority or write a Spec/Ticket."
        outcome = "A reservation can be confirmed exactly once with attributable ownership, recovery and a coherent expiry/cancellation boundary."
        boundary = "existing reservation confirmation, recovery and current terminal state"
        trigger = "Confirm held reservation res-alpha, inspect retry after lost response, and exercise expiry/cancellation interleavings in the delivered product."
        readback = "Current reservation identity, ownership and terminal state from the ordinary product readback, including allowed and forbidden interleavings."
        surface = "Ticket Scope creates | confirmation and reservation recovery readback"
    artifact_case = family == "durable-product-boundary" and state_name == "canonical-deliverable"
    external_case = (family == "durable-product-boundary" and state_name == "external-outcome") or family in {"projection-external-effect", "projection-surface-currentness"}
    if artifact_case:
        write_json(project / "release.json", {"format_version": 1, "policy": "permissive"})
        outcome = "The canonical release.json artifact itself has integer format_version=2 and policy=strict."
        boundary = "canonical release artifact JSON fields"
        trigger = "Inspect release.json directly."
        readback = "The actual JSON object and exact fields in release.json; no unrelated runtime or external service is required."
        surface = "Existing | canonical release.json"
        policy = "- The requested product is the canonical release artifact with format_version=2 and policy=strict.\n- No external delivery or publication operation is promised.\n"
    if external_case:
        if not external_url:
            raise ValueError("external planning cases require one actual caller-owned loopback readback URL")
        write_json(project / "external.json", {"url": external_url})
        outcome = "The alpha request has an actual separately owned release effect with present=true and key=alpha, and current authoritative external readback confirms it."
        boundary = "ordinary request and separately owned external release effect"
        trigger = "Use the ordinary request path within approved delivery authority, then inspect app.py external and the declared readback URL. Planning inspection is read-only."
        readback = f"Actual HTTP readback at {external_url}; request acknowledgement alone is not the release effect."
        surface = "Ticket Scope creates | ordinary request integration and declared authoritative readback"
        condition = f"Separately owned local evaluation authority at {external_url}. Current reachability must be inspected; missing readback remains a required external condition, not Existing or successful delivery. Product mutation cannot create or replace that authority."
        policy = "- Request acceptance and actual external release effect are distinct.\n- Completion requires present=true and key=alpha from the separately owned authoritative readback.\n- Unavailable readback is not success, a product defect, or permission to replace the authority.\n"
        if family == "projection-surface-currentness":
            outcome = "The canonical integration contract preserves the actual alpha external readback and its current availability limits."
            boundary = "canonical integration contract and the exact declared upstream observation boundary"
            trigger = "Inspect app.py external read-only and the canonical integration contract."
            surface = ("Existing | ordinary external readback command and directly observed upstream"
                       if state_name == "observed" else "Not yet established: required upstream availability remains unresolved")
            extra = "Do not adopt a Spec or ready a Ticket if this exact outcome-local acceptance surface remains unresolved; return the upstream planning gap without converting it to Existing."
    adopted = family not in {"current-evidence", "absence-and-search-universe", "durable-product-boundary"}
    if adopted:
        put(project, "docs/planning/behavior/contexts/publication.md", behavior(policy, scope=behavior_scope))
        put(project, "docs/planning/behavior/INDEX.md", f"# Behavior\n\n## Bounded Contexts\n\n- [Publication](contexts/publication.md): {behavior_scope}\n")
    if adopted:
        put(project, "investigation.txt", "Historical fixture navigation only: inspect current state.json and registry.json at the exact anchors. No recorded observation grants product policy or approval.\n")
    if not external_case and not artifact_case:
        extra += " Existing alpha identity and legacy values are preserved. Other metadata is opaque unless the requested delta explicitly concerns it. No unpublication, extra document, new account system or unrelated future behavior is requested.\nFixed existing publication meaning:\n" + POLICY
    contract = f"User-confirmed fixture product meaning:\nOutcome: {outcome}\nAcceptance boundary: {boundary}\nTrigger or inspection target: {trigger}\nExpected observable result: {outcome}\nAuthoritative readback: {readback}\nDisposition: Independent\nIndependent verification required: yes\nAcceptance surface: {surface}\nExternal condition: {condition}\n{extra}\nInternal implementation choices are not fixed. No UI. Current planning owner: evaluation product owner.\n"
    put(project, "request.txt", contract)
    projection = family in {"projection-external-effect", "projection-surface-currentness", "ticket-set-integration"}
    if projection:
        baseline_spec = spec(outcome, boundary, trigger, readback, surface=surface, condition=condition)
        if family == "ticket-set-integration":
            put(project, "docs/planning/work/publication/SPEC.md", baseline_spec)
            if state_name == "owned-compatible":
                put(project, "docs/planning/work/publication/tickets/TICKET-001.md",
                    ticket(project, 1, outcome, "Publication and affected legacy preservation form one owned product result.", "UI and unrelated future candidates"))
            else:
                put(project, "docs/planning/work/publication/tickets/TICKET-001.md",
                    ticket(project, 1, "Alpha becomes published durably.", "Only publication changes; this Ticket may affect legacy status.", "Legacy preservation is excluded from this Ticket"))
                put(project, "docs/planning/work/publication/tickets/TICKET-002.md",
                    ticket(project, 2, "Legacy remains stable after publication.", "Read-only observation only; no product change or integration ownership is authorized.", "Changing publication or restoring affected legacy behavior"))
        else:
            if state_name == "weakened-draft":
                draft = spec("The request helper returns accepted=true.", "private helper response", "Inspect the helper response.", "Internal accepted flag.", status="draft")
                put(project, "docs/planning/work/publication/SPEC.md", draft)
    before = snapshot(project)
    metadata = {"schema": "iis-planning-case/v1", "case_id": case_id, "run_id": root.name,
                "variant": variant, "repetition": repetition, "run_root": str(root), "project_root": str(project),
                "entry": case["entry"], "initial_snapshot": before, "turns": [],
                "fixture_source_sha256": _SOURCE_SHA256,
                "fixture_history_limit": "Preexisting approved authorities and projection inputs are explicitly authored fixture state, not evidence that a planning lifecycle ran. Fresh-authoring cases start without Scope, Spec or Tickets."}
    write_json(root / "metadata.json", metadata)
    return root / "metadata.json"


def initial_prompt(metadata: dict) -> str:
    root = metadata["project_root"]
    entry = metadata["entry"]
    common = f"""Project Root: {root}
This is one authorized disposable planning observation. Work DIRECT as Main; do not spawn subagents. Read canonical isolated skills/references/validators when needed, but do not inspect parent directories, other products, operating installations or hidden evaluation materials. Product source/state, investigation.txt, request.txt, external authority and existing history are read-only. Planning mutations are allowed only under this product's docs/planning with the owning leaf's real approval/validation rules. No delivery, publication command, network write or external side effect is authorized.
Read request.txt for the exact current user product meaning; inspect current product facts directly where load-bearing. investigation.txt is historical navigation, not product authority or current-state proof. {metadata['fixture_history_limit']}
"""
    if entry == "scope":
        return common + "Explicitly invoke skill://scope-shaper. Propose exactly the next durable construction Increment from current state, preserving real outcome boundaries and decisions reserved for Matt. Return the full proposal for actual user confirmation; do not write confirmed Scope artifacts or enter Matt before that separate response. If no construction is warranted, explain the current facts and stop."
    if entry == "matt":
        return common + "Explicitly invoke skill://ask-matt for this one next-increment-ready request. Perform actual Behavior analysis and current decision synthesis. Existing approved authority may be adopted only when applicable. Present every currently identifiable material user decision, or the complete integrated understanding and any changed authority for real approval, then stop. Do not assume approval or write Spec/Tickets before that separate user response."
    if entry == "spec":
        return common + "This is a projection-only observation, not a fresh Matt run: request.txt is the fixed user-confirmed fixture shared understanding, and its applicable approved Behavior authority is the supplied completed fixture planning input. Explicitly invoke skill://to-spec; Source Increment: None; work slug: publication. Review any supplied draft against that exact authority. Apply normal faithful-projection self-review, without a separate per-artifact approval gate. Then explicitly invoke To Tickets from the exact approved resulting Spec and stop at the reviewed Ready Set. If inputs contain a real unresolved product decision, return the exact gap instead of inventing an approval."
    return common + "This is a projection-only observation. Explicitly invoke skill://to-tickets from docs/planning/work/publication/SPEC.md. Review the complete draft Set, every applicable obligation including legacy preservation, and compatible mutation boundaries. Correct decomposition/serialization within approved meaning, or return a real upstream meaning gap. No separate per-artifact approval gate is requested. Stop at the complete validated Ready Ticket Set."


def run_turn(metadata_path: Path, message: str, *, agent_dir: Path, payload: Path, runtime_data: Path,
             model: str, thinking: str = "medium", timeout: int = 480) -> dict:
    _require_current_source()
    metadata_path = metadata_path.resolve(strict=True)
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("fixture_source_sha256") != _SOURCE_SHA256:
        raise ValueError("fixture preparation is not bound to this planning source")
    root, project = Path(metadata["run_root"]), Path(metadata["project_root"])
    if metadata_path != root / "metadata.json" or project != root / "product":
        raise ValueError("noncanonical planning case")
    turns = metadata["turns"]
    if turns:
        previous_native = summarize(load_events(Path(turns[-1]["raw_events"])))
        if not turns[-1]["clean_transport"] or not previous_native["model_completed"]:
            raise ValueError("cannot continue an unclean planning turn")
    before = snapshot(project)
    if turns and before != turns[-1]["post_snapshot"]:
        raise ValueError("planning input changed outside its recorded native turn")
    if not turns and before != metadata["initial_snapshot"]:
        raise ValueError("prepared input changed before invocation")
    output = root / f"turn-{len(turns) + 1}"
    observation = invoke(project_root=project, prompt=message, output_dir=output,
                         agent_dir=agent_dir, payload=payload, runtime_data=runtime_data,
                         model=model, thinking=thinking, timeout=timeout, session_dir=root / "sessions",
                         resume_session=Path(turns[-1]["session_file"]) if turns else None)
    after = snapshot(project)
    clean = observation["clean_transport"] and bool(observation.get("session_file"))
    record = {"turn": len(turns) + 1, "raw_events": observation["raw_events"],
              "raw_events_sha256": hashlib.sha256(Path(observation["raw_events"]).read_bytes()).hexdigest(),
              "terminal": str(output / "terminal.txt"), "terminal_sha256": hashlib.sha256((output / "terminal.txt").read_bytes()).hexdigest(),
              "prompt_sha256": observation["prompt_sha256"], "session_file": observation.get("session_file"),
              "resumed_from": observation.get("resumed_from"), "session_sha256": observation.get("session_sha256"),
              "actual_models": observation["actual_models"], "clean_transport": clean,
              "stop_reason": observation["stop_reason"], "error_message": observation["error_message"],
              "product_mutated": protected(before) != protected(after), "pre_snapshot": before, "post_snapshot": after,
              "elapsed_seconds": observation["elapsed_seconds"], "usage": observation["usage"],
              "tool_calls": len(observation["tool_calls"])}
    write_json(output / "record.json", record)
    for relative in after:
        if relative.startswith("docs/planning/"):
            put(output / "artifacts", relative, (project / relative).read_text())
    turns.append(record)
    write_json(metadata_path, metadata)
    return record


def report(cohort_path: Path, reviews_path: Path) -> dict:
    definition = json.loads(cohort_path.read_text())
    cohort = definition["runs"]
    required = {(case, variant, repetition) for case in definition["case_ids"]
                for variant in definition["variants"] for repetition in definition["repetitions"]}
    observed = [(row["case_id"], row["variant"], row["repetition"]) for row in cohort]
    if len(observed) != len(set(observed)) or set(observed) != required:
        raise ValueError("cohort must contain the exact declared case/profile/repetition denominator")
    reviews = json.loads(reviews_path.read_text())
    expected = {row["run_id"]: row for row in cohort}
    if len(expected) != len(cohort) or not expected:
        raise ValueError("cohort run IDs must be nonempty and unique")
    by_id = {row["run_id"]: row for row in reviews}
    errors = []
    if len(by_id) != len(reviews) or set(by_id) != set(expected):
        errors.append({"code": "inexact_review_denominator"})
    rows = []
    for run_id, coordinate in expected.items():
        path = Path(coordinate["metadata"])
        metadata = json.loads(path.read_text())
        turns = metadata["turns"]
        for field in ("run_id", "case_id", "variant", "repetition"):
            if metadata[field] != coordinate[field]:
                errors.append({"run_id": run_id, "code": "coordinate_mismatch", "field": field})
        review = by_id.get(run_id, {})
        if review.get("causal_evidence_sufficient") is not True or not review.get("reason"):
            errors.append({"run_id": run_id, "code": "insufficient_causal_evidence"})
        if not turns:
            errors.append({"run_id": run_id, "code": "missing_native_turns"})
        refs = review.get("evidence_refs", [])
        wanted = [{"path": row["raw_events"], "sha256": row["raw_events_sha256"]} for row in turns]
        if refs != wanted:
            errors.append({"run_id": run_id, "code": "inexact_turn_evidence"})
        previous = metadata["initial_snapshot"]
        for index, turn in enumerate(turns):
            if not turn["clean_transport"] or turn["product_mutated"] or turn["pre_snapshot"] != previous:
                errors.append({"run_id": run_id, "turn": index + 1, "code": "invalid_turn_boundary"})
            previous = turn["post_snapshot"]
            if index and turn["resumed_from"] != turns[index - 1]["session_file"]:
                errors.append({"run_id": run_id, "turn": index + 1, "code": "wrong_native_continuation"})
            for filename, digest in ((turn["raw_events"], turn["raw_events_sha256"]), (turn["terminal"], turn["terminal_sha256"])):
                if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != digest:
                    errors.append({"run_id": run_id, "turn": index + 1, "code": "raw_hash_mismatch"})
            native = summarize(load_events(Path(turn["raw_events"])))
            if not native["model_completed"]:
                errors.append({"run_id": run_id, "turn": index + 1, "code": "model_not_cleanly_terminated"})
            if (native["actual_models"] != [definition["model"]] or native["actual_models"] != turn["actual_models"]
                    or native["terminal_text"] != Path(turn["terminal"]).read_text()):
                errors.append({"run_id": run_id, "turn": index + 1, "code": "native_capture_mismatch"})
        if snapshot(Path(metadata["project_root"])) != previous:
            errors.append({"run_id": run_id, "code": "current_artifact_drift"})
        rows.append({key: coordinate[key] for key in ("run_id", "case_id", "variant", "repetition")} | {"turns": len(turns), "causal_evidence_sufficient": review.get("causal_evidence_sufficient") is True})
    return {"schema": "iis-planning-report/v1", "cohort_runs": len(cohort), "review_runs": len(reviews), "errors": errors,
            "causal_gate_pass": not errors, "cases": rows,
            "limit": "Checks capture/currentness/coverage and supplied reviews; Main owns semantic review and comparative adoption."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("--arena", required=True, type=Path)
    prepare_parser.add_argument("--variant", required=True)
    prepare_parser.add_argument("--repetition", type=int, default=1)
    prepare_parser.add_argument("--external-url")
    run = sub.add_parser("run")
    run.add_argument("--metadata", required=True, type=Path)
    run.add_argument("--message", type=Path)
    for flag in ("agent-dir", "payload", "runtime-data"):
        run.add_argument("--" + flag, required=True, type=Path)
    run.add_argument("--model", required=True)
    run.add_argument("--thinking", default="medium")
    run.add_argument("--timeout", type=int, default=480)
    aggregate = sub.add_parser("report")
    aggregate.add_argument("--cohort", required=True, type=Path)
    aggregate.add_argument("--reviews", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.case_id, args.arena, args.variant, args.repetition, external_url=args.external_url))
        return 0
    if args.command == "report":
        result = report(args.cohort, args.reviews)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["causal_gate_pass"] else 1
    metadata = json.loads(args.metadata.read_text())
    if metadata["turns"] and args.message is None:
        raise ValueError("continuation requires an explicit caller-authored message")
    message = args.message.read_text() if args.message else initial_prompt(metadata)
    result = run_turn(args.metadata, message, agent_dir=args.agent_dir, payload=args.payload,
                      runtime_data=args.runtime_data, model=args.model, thinking=args.thinking, timeout=args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["clean_transport"] and not result["product_mutated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
