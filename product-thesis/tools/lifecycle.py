"""Stateful Product Thesis work and closure controlled by a trusted supervisor."""
from __future__ import annotations

import json
from pathlib import Path
import uuid

from iis_artifacts.publication import publish_ref
from iis_artifacts.refs import validate_ref, validate_relative_path
from iis_artifacts.store import ArtifactStore

TERMINAL = {"CLOSED", "BUDGET_EXHAUSTED", "CANCELLED", "FAILED"}
FRONTIER_DISPOSITIONS = {"RESOLVED", "REUSED", "USER_CHOICE", "EVIDENCE_LIMIT", "OTHER_OWNER", "EXCLUDED_WITH_BASIS"}
PREMISE_DISPOSITIONS = {"RESOLVED", "USER_CHOICE", "EVIDENCE_LIMIT", "DEFERRED_NONBLOCKING", "OTHER_OWNER"}
FINDING_DISPOSITIONS = {"OPEN", "RESOLVED", "DISMISSED", "OUT_OF_SCOPE"}


class ThesisLifecycleError(RuntimeError):
    pass


def _schema(store: ArtifactStore) -> None:
    with store.connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS thesis_runs(
              run_id TEXT PRIMARY KEY,
              request_text TEXT NOT NULL,
              originals_json TEXT NOT NULL,
              profile_json TEXT NOT NULL,
              phase TEXT NOT NULL,
              generation INTEGER NOT NULL,
              candidate_snapshot TEXT,
              candidate_path TEXT,
              expected_prior_json TEXT,
              budget INTEGER,
              created_sequence INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS thesis_frontier(
              run_id TEXT NOT NULL,
              item_id TEXT NOT NULL,
              origin TEXT NOT NULL,
              question TEXT NOT NULL,
              material_change TEXT NOT NULL,
              decision_bearing INTEGER NOT NULL,
              disposition TEXT,
              basis TEXT,
              PRIMARY KEY(run_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_premises(
              run_id TEXT NOT NULL,
              premise_id TEXT NOT NULL,
              statement TEXT NOT NULL,
              kind TEXT NOT NULL,
              depends_on TEXT NOT NULL,
              disposition TEXT,
              basis TEXT,
              PRIMARY KEY(run_id, premise_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_reviews(
              invocation_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              phase TEXT NOT NULL,
              candidate_snapshot TEXT,
              candidate_path TEXT,
              status TEXT NOT NULL,
              inputs_json TEXT NOT NULL,
              result_json TEXT,
              started_sequence INTEGER NOT NULL,
              completed_sequence INTEGER
            );
            CREATE TABLE IF NOT EXISTS thesis_findings(
              run_id TEXT NOT NULL,
              finding_id TEXT NOT NULL,
              invocation_id TEXT NOT NULL,
              candidate_snapshot TEXT,
              anchor TEXT NOT NULL,
              scenario TEXT NOT NULL,
              apparent_success TEXT NOT NULL,
              broken_result TEXT NOT NULL,
              materiality TEXT NOT NULL,
              disposition TEXT NOT NULL,
              basis TEXT,
              PRIMARY KEY(run_id, finding_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_closures(
              closure_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              candidate_snapshot TEXT NOT NULL,
              candidate_path TEXT NOT NULL,
              result TEXT NOT NULL,
              limitations TEXT NOT NULL,
              sequence INTEGER NOT NULL
            );
            """
        )


def start(
    store: ArtifactStore,
    request_text: str,
    *,
    originals: list[dict] | None = None,
    profile: dict | None = None,
    budget: int | None = None,
    expected_prior: dict | None = None,
) -> str:
    _schema(store)
    if not request_text.strip():
        raise ThesisLifecycleError("current request is required")
    normalized = [validate_ref(item) for item in (originals or [])]
    prior = None if expected_prior is None else validate_ref(expected_prior)
    run_id = "thesis-" + uuid.uuid4().hex
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_runs(run_id, request_text, originals_json, profile_json, phase, generation, "
            "candidate_snapshot, candidate_path, expected_prior_json, budget, created_sequence) "
            "VALUES(?, ?, ?, ?, 'WORKING', 0, NULL, NULL, ?, ?, ?)",
            (
                run_id,
                request_text,
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(profile or {}, ensure_ascii=False),
                None if prior is None else json.dumps(prior),
                budget,
                store.next_sequence(),
            ),
        )
    return run_id


def _run(store: ArtifactStore, run_id: str):
    _schema(store)
    with store.connect() as db:
        row = db.execute("SELECT * FROM thesis_runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        raise ThesisLifecycleError("unknown Thesis run")
    return row


def inspect(store: ArtifactStore, run_id: str) -> dict:
    row = _run(store, run_id)
    with store.connect() as db:
        frontier = [dict(item) for item in db.execute("SELECT * FROM thesis_frontier WHERE run_id=? ORDER BY item_id", (run_id,))]
        premises = [dict(item) for item in db.execute("SELECT * FROM thesis_premises WHERE run_id=? ORDER BY premise_id", (run_id,))]
        reviews = [dict(item) for item in db.execute("SELECT * FROM thesis_reviews WHERE run_id=? ORDER BY started_sequence", (run_id,))]
        findings = [dict(item) for item in db.execute("SELECT * FROM thesis_findings WHERE run_id=? ORDER BY finding_id", (run_id,))]
        closures = [dict(item) for item in db.execute("SELECT * FROM thesis_closures WHERE run_id=? ORDER BY sequence", (run_id,))]
    return {
        "schema": "iis-thesis-work/v1",
        "run_id": run_id,
        "phase": row["phase"],
        "generation": int(row["generation"]),
        "candidate": None if row["candidate_snapshot"] is None else {"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]},
        "frontier": frontier,
        "premises": premises,
        "reviews": reviews,
        "findings": findings,
        "closures": closures,
    }


def add_frontier(
    store: ArtifactStore,
    run_id: str,
    *,
    item_id: str,
    origin: str,
    question: str,
    material_change: str,
    decision_bearing: bool,
) -> None:
    row = _run(store, run_id)
    if row["phase"] in TERMINAL:
        raise ThesisLifecycleError("terminal Thesis run cannot accept frontier work")
    if not all(value.strip() for value in (item_id, origin, question, material_change)):
        raise ThesisLifecycleError("frontier item fields must be nonempty")
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_frontier(run_id,item_id,origin,question,material_change,decision_bearing) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(run_id,item_id) DO UPDATE SET origin=excluded.origin, "
            "question=excluded.question, material_change=excluded.material_change, decision_bearing=excluded.decision_bearing, "
            "disposition=NULL, basis=NULL",
            (run_id, item_id, origin, question, material_change, int(decision_bearing)),
        )


def disposition_frontier(store: ArtifactStore, run_id: str, item_id: str, disposition: str, basis: str) -> None:
    _run(store, run_id)
    if disposition not in FRONTIER_DISPOSITIONS or not basis.strip():
        raise ThesisLifecycleError("invalid frontier disposition or basis")
    with store.connect() as db:
        changed = db.execute(
            "UPDATE thesis_frontier SET disposition=?, basis=? WHERE run_id=? AND item_id=?",
            (disposition, basis, run_id, item_id),
        ).rowcount
    if changed != 1:
        raise ThesisLifecycleError("unknown frontier item")


def add_premise(store: ArtifactStore, run_id: str, *, premise_id: str, statement: str, kind: str, depends_on: str) -> None:
    _run(store, run_id)
    if kind not in {"semantic", "binding_construction", "implementation_satisfaction"}:
        raise ThesisLifecycleError("invalid premise kind")
    if not all(value.strip() for value in (premise_id, statement, depends_on)):
        raise ThesisLifecycleError("premise fields must be nonempty")
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_premises(run_id,premise_id,statement,kind,depends_on) VALUES(?,?,?,?,?) "
            "ON CONFLICT(run_id,premise_id) DO UPDATE SET statement=excluded.statement, kind=excluded.kind, "
            "depends_on=excluded.depends_on, disposition=NULL, basis=NULL",
            (run_id, premise_id, statement, kind, depends_on),
        )


def disposition_premise(store: ArtifactStore, run_id: str, premise_id: str, disposition: str, basis: str) -> None:
    _run(store, run_id)
    if disposition not in PREMISE_DISPOSITIONS or not basis.strip():
        raise ThesisLifecycleError("invalid premise disposition or basis")
    with store.connect() as db:
        changed = db.execute(
            "UPDATE thesis_premises SET disposition=?, basis=? WHERE run_id=? AND premise_id=?",
            (disposition, basis, run_id, premise_id),
        ).rowcount
    if changed != 1:
        raise ThesisLifecycleError("unknown premise")


def submit_candidate(
    store: ArtifactStore,
    run_id: str,
    candidate_file: Path,
    logical_path: str,
    *,
    expected_generation: int,
) -> dict:
    row = _run(store, run_id)
    if row["phase"] in TERMINAL:
        raise ThesisLifecycleError("terminal Thesis run cannot accept a candidate")
    if int(row["generation"]) != expected_generation:
        raise ThesisLifecycleError("GENERATION_CONFLICT")
    logical = validate_relative_path(logical_path)
    snapshot = store.capture_mapping(
        {logical: Path(candidate_file).read_bytes()},
        kind="candidate",
        origin=str(candidate_file),
        producer_run=run_id,
    )
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT generation FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if current is None or int(current["generation"]) != expected_generation:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("GENERATION_CONFLICT")
        db.execute(
            "UPDATE thesis_runs SET candidate_snapshot=?, candidate_path=?, generation=generation+1, phase='CANDIDATE_READY' "
            "WHERE run_id=?",
            (snapshot, logical, run_id),
        )
        db.execute("COMMIT")
    return {"snapshot": snapshot, "path": logical}


def begin_review(store: ArtifactStore, run_id: str, phase: str, inputs: list[dict]) -> str:
    """Trusted-host API. It is intentionally not exposed by the Thesis CLI."""
    row = _run(store, run_id)
    if phase not in {"SOURCE_FRONTIER", "CANDIDATE_COUNTEREXAMPLE"}:
        raise ThesisLifecycleError("unsupported review phase")
    candidate_snapshot = candidate_path = None
    if phase == "CANDIDATE_COUNTEREXAMPLE":
        if row["candidate_snapshot"] is None:
            raise ThesisLifecycleError("candidate review requires a fixed candidate")
        candidate_snapshot, candidate_path = row["candidate_snapshot"], row["candidate_path"]
    invocation_id = "inv-" + uuid.uuid4().hex
    normalized = [validate_ref(item) for item in inputs]
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_reviews(invocation_id,run_id,phase,candidate_snapshot,candidate_path,status,inputs_json,started_sequence) "
            "VALUES(?,?,?,?,?,'STARTED',?,?)",
            (
                invocation_id,
                run_id,
                phase,
                candidate_snapshot,
                candidate_path,
                json.dumps(normalized, ensure_ascii=False),
                store.next_sequence(),
            ),
        )
        db.execute("UPDATE thesis_runs SET phase='CHALLENGING' WHERE run_id=?", (run_id,))
    return invocation_id


def complete_review(
    store: ArtifactStore,
    invocation_id: str,
    *,
    result: dict,
    frontier: list[dict] | None = None,
    findings: list[dict] | None = None,
) -> None:
    """Trusted-host API used only after an actual invocation returns."""
    _schema(store)
    with store.connect() as db:
        review = db.execute("SELECT * FROM thesis_reviews WHERE invocation_id=?", (invocation_id,)).fetchone()
    if review is None or review["status"] != "STARTED":
        raise ThesisLifecycleError("review invocation is not an active host invocation")
    run_id = review["run_id"]
    for item in frontier or []:
        add_frontier(
            store,
            run_id,
            item_id=item["item_id"],
            origin=item["origin"],
            question=item["question"],
            material_change=item["material_change"],
            decision_bearing=bool(item.get("decision_bearing")),
        )
    with store.connect() as db:
        for item in findings or []:
            materiality = item.get("materiality")
            disposition = item.get("disposition", "OPEN")
            if materiality not in {"MATERIAL", "OUT_OF_SCOPE"} or disposition not in FINDING_DISPOSITIONS:
                raise ThesisLifecycleError("invalid review finding")
            for key in ("finding_id", "anchor", "scenario", "apparent_success", "broken_result"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ThesisLifecycleError("finding fields must be nonempty")
            db.execute(
                "INSERT INTO thesis_findings(run_id,finding_id,invocation_id,candidate_snapshot,anchor,scenario,"
                "apparent_success,broken_result,materiality,disposition,basis) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(run_id,finding_id) DO UPDATE SET invocation_id=excluded.invocation_id, "
                "candidate_snapshot=excluded.candidate_snapshot, anchor=excluded.anchor, scenario=excluded.scenario, "
                "apparent_success=excluded.apparent_success, broken_result=excluded.broken_result, "
                "materiality=excluded.materiality, disposition=excluded.disposition, basis=excluded.basis",
                (
                    run_id,
                    item["finding_id"],
                    invocation_id,
                    review["candidate_snapshot"],
                    item["anchor"],
                    item["scenario"],
                    item["apparent_success"],
                    item["broken_result"],
                    materiality,
                    disposition,
                    item.get("basis"),
                ),
            )
        db.execute(
            "UPDATE thesis_reviews SET status='COMPLETE', result_json=?, completed_sequence=? WHERE invocation_id=?",
            (json.dumps(result, ensure_ascii=False), store.next_sequence(), invocation_id),
        )
        db.execute("UPDATE thesis_runs SET phase='CLOSURE_CHECK' WHERE run_id=?", (run_id,))


def disposition_finding(store: ArtifactStore, run_id: str, finding_id: str, disposition: str, basis: str) -> None:
    _run(store, run_id)
    if disposition not in {"RESOLVED", "DISMISSED", "OUT_OF_SCOPE"} or not basis.strip():
        raise ThesisLifecycleError("invalid finding disposition")
    with store.connect() as db:
        changed = db.execute(
            "UPDATE thesis_findings SET disposition=?, basis=? WHERE run_id=? AND finding_id=?",
            (disposition, basis, run_id, finding_id),
        ).rowcount
    if changed != 1:
        raise ThesisLifecycleError("unknown finding")


def evaluate_closure(store: ArtifactStore, run_id: str) -> dict:
    row = _run(store, run_id)
    tasks: list[dict] = []
    waiting_user = False
    waiting_evidence = False
    if row["candidate_snapshot"] is None:
        tasks.append({"item": "candidate", "reason": "CANDIDATE_REQUIRED", "required_action": "Submit a fixed Thesis candidate."})
    with store.connect() as db:
        source_review = db.execute(
            "SELECT 1 FROM thesis_reviews WHERE run_id=? AND phase='SOURCE_FRONTIER' AND status='COMPLETE' LIMIT 1",
            (run_id,),
        ).fetchone()
        candidate_review = None
        if row["candidate_snapshot"] is not None:
            candidate_review = db.execute(
                "SELECT 1 FROM thesis_reviews WHERE run_id=? AND phase='CANDIDATE_COUNTEREXAMPLE' "
                "AND candidate_snapshot=? AND candidate_path=? AND status='COMPLETE' LIMIT 1",
                (run_id, row["candidate_snapshot"], row["candidate_path"]),
            ).fetchone()
        frontier = db.execute("SELECT * FROM thesis_frontier WHERE run_id=? ORDER BY item_id", (run_id,)).fetchall()
        premises = db.execute("SELECT * FROM thesis_premises WHERE run_id=? ORDER BY premise_id", (run_id,)).fetchall()
        findings = db.execute("SELECT * FROM thesis_findings WHERE run_id=? ORDER BY finding_id", (run_id,)).fetchall()
    if source_review is None:
        tasks.append({"item": "review:source", "reason": "SOURCE_FRONTIER_REVIEW_REQUIRED", "required_action": "Run the original-input omission review."})
    if candidate_review is None:
        tasks.append({"item": "review:candidate", "reason": "CURRENT_CANDIDATE_CHALLENGE_REQUIRED", "required_action": "Challenge the exact current candidate."})
    if not frontier:
        tasks.append({"item": "frontier", "reason": "MATERIAL_FRONTIER_NOT_RECORDED", "required_action": "Record the bounded semantic frontier from the original inputs."})
    for item in frontier:
        disposition = item["disposition"]
        if disposition is None:
            tasks.append({"item": item["item_id"], "reason": "FRONTIER_UNDISPOSITIONED", "required_action": "Resolve, reuse, route, exclude with basis, or preserve the exact blocking boundary."})
            continue
        if bool(item["decision_bearing"]) and not (item["basis"] or "").strip():
            tasks.append({"item": item["item_id"], "reason": "DECISION_DISCRIMINATOR_MISSING", "required_action": "Record the discriminator or exact stopping boundary."})
        if disposition == "USER_CHOICE":
            waiting_user = True
        if disposition == "EVIDENCE_LIMIT" and bool(item["decision_bearing"]):
            waiting_evidence = True
    for premise in premises:
        disposition = premise["disposition"]
        if premise["kind"] == "implementation_satisfaction":
            continue
        if disposition is None:
            tasks.append({"item": premise["premise_id"], "reason": "BLOCKING_PREMISE_UNRESOLVED", "required_action": "Resolve the premise or preserve the exact user/evidence boundary."})
        elif disposition == "USER_CHOICE":
            waiting_user = True
        elif disposition == "EVIDENCE_LIMIT":
            waiting_evidence = True
    for finding in findings:
        if finding["materiality"] == "MATERIAL" and finding["disposition"] not in {"RESOLVED", "DISMISSED"}:
            tasks.append({"item": finding["finding_id"], "reason": "MATERIAL_FINDING_UNRESOLVED", "required_action": "Revise the meaning or close the finding with grounded authority/evidence."})
    if waiting_user:
        return {"result": "WAITING_USER", "tasks": tasks}
    if waiting_evidence:
        return {"result": "WAITING_EVIDENCE", "tasks": tasks}
    if tasks:
        return {"result": "REWORK_REQUIRED", "tasks": tasks}
    return {"result": "ELIGIBLE", "tasks": []}


def close_request(store: ArtifactStore, run_id: str, project_root: Path, *, limitations: str = "") -> dict:
    row = _run(store, run_id)
    verdict = evaluate_closure(store, run_id)
    if verdict["result"] != "ELIGIBLE":
        phase = verdict["result"] if verdict["result"] in {"WAITING_USER", "WAITING_EVIDENCE"} else "WORKING"
        with store.connect() as db:
            db.execute("UPDATE thesis_runs SET phase=? WHERE run_id=?", (phase, run_id))
        return verdict
    candidate = {"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]}
    prior = None if row["expected_prior_json"] is None else json.loads(row["expected_prior_json"])
    publish_ref(store, candidate, project_root, row["candidate_path"], expected_prior=prior)
    closure_id = "close-" + uuid.uuid4().hex
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_closures(closure_id,run_id,candidate_snapshot,candidate_path,result,limitations,sequence) "
            "VALUES(?,?,?,?, 'CALIBRATED', ?, ?)",
            (closure_id, run_id, row["candidate_snapshot"], row["candidate_path"], limitations, store.next_sequence()),
        )
        db.execute("UPDATE thesis_runs SET phase='CLOSED' WHERE run_id=?", (run_id,))
    return {
        "schema": "iis-thesis-closure/v1",
        "closure_id": closure_id,
        "run_id": run_id,
        "candidate": candidate,
        "result": "CALIBRATED",
        "limitations": limitations,
    }


def closed_for_ref(store: ArtifactStore, value: object) -> bool:
    item = validate_ref(value)
    _schema(store)
    with store.connect() as db:
        row = db.execute(
            "SELECT 1 FROM thesis_closures WHERE candidate_snapshot=? AND candidate_path=? AND result='CALIBRATED' LIMIT 1",
            (item["snapshot"], item["path"]),
        ).fetchone()
    return row is not None


def resume(store: ArtifactStore, run_id: str, request_text: str) -> None:
    row = _run(store, run_id)
    if row["phase"] not in {"WAITING_USER", "WAITING_EVIDENCE", "BUDGET_EXHAUSTED"}:
        raise ThesisLifecycleError("only a waiting or budget-exhausted Thesis run can resume")
    if not request_text.strip():
        raise ThesisLifecycleError("current resume request is required")
    with store.connect() as db:
        db.execute(
            "UPDATE thesis_runs SET request_text=?, phase='WORKING' WHERE run_id=?",
            (request_text, run_id),
        )


def cancel(store: ArtifactStore, run_id: str) -> None:
    row = _run(store, run_id)
    if row["phase"] == "CLOSED":
        raise ThesisLifecycleError("closed Thesis history is immutable")
    with store.connect() as db:
        db.execute("UPDATE thesis_runs SET phase='CANCELLED' WHERE run_id=?", (run_id,))
