"""Stateful Product Thesis work controlled by a trusted host."""
from __future__ import annotations

import json
from pathlib import Path
import uuid
import re

from iis_artifacts.publication import RevisionConflict, publish_ref, published_ref, recover_pending
from iis_artifacts.refs import validate_ref, validate_relative_path
from iis_artifacts.store import ArtifactStore

TERMINAL = {"CLOSED", "BUDGET_EXHAUSTED", "CANCELLED", "FAILED"}
MUTATION_BLOCKED = TERMINAL | {"CLOSING"}
FRONTIER_DISPOSITIONS = {"RESOLVED", "REUSED", "USER_CHOICE", "EVIDENCE_LIMIT", "OTHER_OWNER", "EXCLUDED_WITH_BASIS"}
PREMISE_DISPOSITIONS = {"RESOLVED", "USER_CHOICE", "EVIDENCE_LIMIT", "DEFERRED_NONBLOCKING", "OTHER_OWNER"}


class ThesisLifecycleError(RuntimeError):
    pass


def _schema(store: ArtifactStore) -> None:
    with store.connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS thesis_runs(
              run_id TEXT PRIMARY KEY,
              request_text TEXT NOT NULL,
              request_ref_json TEXT NOT NULL,
              originals_json TEXT NOT NULL,
              profile_json TEXT NOT NULL,
              phase TEXT NOT NULL,
              generation INTEGER NOT NULL,
              request_generation INTEGER NOT NULL,
              candidate_snapshot TEXT,
              candidate_path TEXT,
              expected_prior_json TEXT,
              budget_total INTEGER,
              budget_used INTEGER NOT NULL,
              created_sequence INTEGER NOT NULL,
              last_error TEXT
            );
            CREATE TABLE IF NOT EXISTS thesis_frontier(
              run_id TEXT NOT NULL,
              request_generation INTEGER NOT NULL,
              item_id TEXT NOT NULL,
              origin TEXT NOT NULL,
              question TEXT NOT NULL,
              material_change TEXT NOT NULL,
              decision_bearing INTEGER NOT NULL,
              disposition TEXT,
              basis TEXT,
              PRIMARY KEY(run_id, request_generation, item_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_premises(
              run_id TEXT NOT NULL,
              request_generation INTEGER NOT NULL,
              premise_id TEXT NOT NULL,
              statement TEXT NOT NULL,
              kind TEXT NOT NULL,
              depends_on TEXT NOT NULL,
              disposition TEXT,
              basis TEXT,
              PRIMARY KEY(run_id, request_generation, premise_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_reviews(
              invocation_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              request_generation INTEGER NOT NULL,
              candidate_generation INTEGER,
              phase TEXT NOT NULL,
              candidate_snapshot TEXT,
              candidate_path TEXT,
              status TEXT NOT NULL,
              inputs_json TEXT NOT NULL,
              result_ref_json TEXT,
              started_sequence INTEGER NOT NULL,
              completed_sequence INTEGER
            );
            CREATE TABLE IF NOT EXISTS thesis_findings(
              finding_key TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              request_generation INTEGER NOT NULL,
              reported_id TEXT NOT NULL,
              invocation_id TEXT NOT NULL,
              candidate_snapshot TEXT,
              anchor TEXT NOT NULL,
              scenario TEXT NOT NULL,
              apparent_success TEXT NOT NULL,
              broken_result TEXT NOT NULL,
              materiality TEXT NOT NULL,
              initial_disposition TEXT NOT NULL,
              UNIQUE(invocation_id, reported_id)
            );
            CREATE TABLE IF NOT EXISTS thesis_finding_dispositions(
              disposition_key TEXT PRIMARY KEY,
              finding_key TEXT NOT NULL,
              disposition TEXT NOT NULL,
              basis TEXT NOT NULL,
              sequence INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS thesis_closures(
              closure_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              request_generation INTEGER NOT NULL,
              candidate_generation INTEGER NOT NULL,
              candidate_snapshot TEXT NOT NULL,
              candidate_path TEXT NOT NULL,
              result TEXT NOT NULL,
              limitations TEXT NOT NULL,
              sequence INTEGER NOT NULL
            );
            """
        )
        required_columns = {
            "thesis_runs": {"request_ref_json", "request_generation", "budget_total", "budget_used"},
            "thesis_reviews": {"request_generation", "candidate_generation", "result_ref_json"},
            "thesis_findings": {"finding_key", "reported_id", "initial_disposition"},
        }
        for table, required in required_columns.items():
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            if not required.issubset(columns):
                raise ThesisLifecycleError("LEGACY_THESIS_STORE_REQUIRES_FRESH_RUNTIME")


def _run(store: ArtifactStore, run_id: str):
    _schema(store)
    with store.connect() as db:
        row = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        raise ThesisLifecycleError("unknown Thesis run")
    return row


def _request_ref(store: ArtifactStore, run_id: str, text: str, generation: int) -> dict[str, str]:
    snapshot = store.capture_mapping(
        {f"requests/{generation}/request.txt": text.encode("utf-8")},
        kind="request",
        origin="current-request",
        producer_run=run_id,
    )
    return {"snapshot": snapshot, "path": f"requests/{generation}/request.txt"}


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
    if budget is not None and (type(budget) is not int or budget <= 0):
        raise ThesisLifecycleError("review budget must be a positive integer")
    normalized = [validate_ref(item) for item in (originals or [])]
    for item in normalized:
        store.resolve(item)
    prior = None if expected_prior is None else validate_ref(expected_prior)
    if prior is not None:
        store.resolve(prior)
    run_id = "thesis-" + uuid.uuid4().hex
    request_ref = _request_ref(store, run_id, request_text, 0)
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_runs(run_id,request_text,request_ref_json,originals_json,profile_json,phase,generation,"
            "request_generation,candidate_snapshot,candidate_path,expected_prior_json,budget_total,budget_used,created_sequence,last_error) "
            "VALUES(?,?,?,?,?,'WORKING',0,0,NULL,NULL,?,?,0,?,NULL)",
            (
                run_id,
                request_text,
                json.dumps(request_ref),
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(profile or {}, ensure_ascii=False),
                None if prior is None else json.dumps(prior),
                budget,
                store.sequence_in(db, "thesis-run"),
            ),
        )
    return run_id


def inspect(store: ArtifactStore, run_id: str) -> dict:
    row = _run(store, run_id)
    req_gen = int(row["request_generation"])
    with store.connect() as db:
        frontier = [dict(item) for item in db.execute(
            "SELECT * FROM thesis_frontier WHERE run_id=? AND request_generation=? ORDER BY item_id",
            (run_id, req_gen),
        )]
        premises = [dict(item) for item in db.execute(
            "SELECT * FROM thesis_premises WHERE run_id=? AND request_generation=? ORDER BY premise_id",
            (run_id, req_gen),
        )]
        reviews = [dict(item) for item in db.execute(
            "SELECT * FROM thesis_reviews WHERE run_id=? ORDER BY started_sequence",
            (run_id,),
        )]
        findings = [dict(item) for item in db.execute(
            "SELECT * FROM thesis_findings WHERE run_id=? ORDER BY finding_key",
            (run_id,),
        )]
        dispositions = [dict(item) for item in db.execute(
            "SELECT d.* FROM thesis_finding_dispositions d JOIN thesis_findings f ON f.finding_key=d.finding_key "
            "WHERE f.run_id=? ORDER BY d.sequence",
            (run_id,),
        )]
        closures = [dict(item) for item in db.execute(
            "SELECT * FROM thesis_closures WHERE run_id=? ORDER BY sequence",
            (run_id,),
        )]
    return {
        "schema": "iis-thesis-work/v2",
        "run_id": run_id,
        "phase": row["phase"],
        "generation": int(row["generation"]),
        "request_generation": req_gen,
        "request": json.loads(row["request_ref_json"]),
        "budget": {"total": row["budget_total"], "used": int(row["budget_used"])},
        "candidate": None if row["candidate_snapshot"] is None else {
            "snapshot": row["candidate_snapshot"], "path": row["candidate_path"]
        },
        "frontier": frontier,
        "premises": premises,
        "reviews": reviews,
        "findings": findings,
        "finding_dispositions": dispositions,
        "closures": closures,
        "last_error": row["last_error"],
    }


def _require_mutable(row) -> None:
    if row["phase"] in MUTATION_BLOCKED:
        raise ThesisLifecycleError(f"Thesis run is not mutable in phase {row['phase']}")


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
    _require_mutable(row)
    if not all(isinstance(value, str) and value.strip() for value in (item_id, origin, question, material_change)):
        raise ThesisLifecycleError("frontier item fields must be nonempty")
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_frontier(run_id,request_generation,item_id,origin,question,material_change,decision_bearing) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(run_id,request_generation,item_id) DO UPDATE SET "
            "origin=excluded.origin,question=excluded.question,material_change=excluded.material_change,"
            "decision_bearing=excluded.decision_bearing,disposition=NULL,basis=NULL",
            (run_id, row["request_generation"], item_id, origin, question, material_change, int(decision_bearing)),
        )


def disposition_frontier(store: ArtifactStore, run_id: str, item_id: str, disposition: str, basis: str) -> None:
    row = _run(store, run_id)
    _require_mutable(row)
    if disposition not in FRONTIER_DISPOSITIONS or not basis.strip():
        raise ThesisLifecycleError("invalid frontier disposition or basis")
    with store.connect() as db:
        changed = db.execute(
            "UPDATE thesis_frontier SET disposition=?,basis=? WHERE run_id=? AND request_generation=? AND item_id=?",
            (disposition, basis, run_id, row["request_generation"], item_id),
        ).rowcount
    if changed != 1:
        raise ThesisLifecycleError("unknown frontier item")


def add_premise(store: ArtifactStore, run_id: str, *, premise_id: str, statement: str, kind: str, depends_on: str) -> None:
    row = _run(store, run_id)
    _require_mutable(row)
    if kind not in {"semantic", "binding_construction", "implementation_satisfaction"}:
        raise ThesisLifecycleError("invalid premise kind")
    if not all(isinstance(value, str) and value.strip() for value in (premise_id, statement, depends_on)):
        raise ThesisLifecycleError("premise fields must be nonempty")
    with store.connect() as db:
        db.execute(
            "INSERT INTO thesis_premises(run_id,request_generation,premise_id,statement,kind,depends_on) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(run_id,request_generation,premise_id) DO UPDATE SET statement=excluded.statement,"
            "kind=excluded.kind,depends_on=excluded.depends_on,disposition=NULL,basis=NULL",
            (run_id, row["request_generation"], premise_id, statement, kind, depends_on),
        )


def disposition_premise(store: ArtifactStore, run_id: str, premise_id: str, disposition: str, basis: str) -> None:
    row = _run(store, run_id)
    _require_mutable(row)
    if disposition not in PREMISE_DISPOSITIONS or not basis.strip():
        raise ThesisLifecycleError("invalid premise disposition or basis")
    with store.connect() as db:
        changed = db.execute(
            "UPDATE thesis_premises SET disposition=?,basis=? WHERE run_id=? AND request_generation=? AND premise_id=?",
            (disposition, basis, run_id, row["request_generation"], premise_id),
        ).rowcount
    if changed != 1:
        raise ThesisLifecycleError("unknown premise")


def _thesis_logical_path(value: str) -> str:
    logical = validate_relative_path(value)
    parts = logical.split("/")
    if (
        len(parts) != 5
        or parts[:3] != ["docs", "planning", "product-thesis"]
        or not parts[3]
        or re.fullmatch(r"THESIS-[0-9]{3,}\.md", parts[4]) is None
    ):
        raise ThesisLifecycleError("INVALID_THESIS_CANDIDATE_PATH")
    return logical


def submit_candidate_bytes(
    store: ArtifactStore,
    run_id: str,
    data: bytes,
    logical_path: str,
    *,
    expected_generation: int,
) -> dict[str, str]:
    row = _run(store, run_id)
    _require_mutable(row)
    if int(row["generation"]) != expected_generation:
        raise ThesisLifecycleError("GENERATION_CONFLICT")
    logical = _thesis_logical_path(logical_path)
    snapshot = store.capture_mapping(
        {logical: data},
        kind="candidate",
        origin="thesis-candidate",
        producer_run=run_id,
    )
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if current is None or int(current["generation"]) != expected_generation or current["phase"] in MUTATION_BLOCKED:
            db.execute("ROLLBACK")
            store.delete_snapshot(snapshot)
            raise ThesisLifecycleError("GENERATION_CONFLICT")
        db.execute(
            "UPDATE thesis_reviews SET status='STALE' WHERE run_id=? AND status='STARTED' AND phase='CANDIDATE_COUNTEREXAMPLE'",
            (run_id,),
        )
        db.execute(
            "UPDATE thesis_runs SET candidate_snapshot=?,candidate_path=?,generation=generation+1,"
            "phase='CANDIDATE_READY',last_error=NULL WHERE run_id=?",
            (snapshot, logical, run_id),
        )
        db.execute("COMMIT")
    return {"snapshot": snapshot, "path": logical}


def submit_candidate(
    store: ArtifactStore,
    run_id: str,
    candidate_file: Path,
    logical_path: str,
    *,
    expected_generation: int,
) -> dict[str, str]:
    return submit_candidate_bytes(
        store, run_id, Path(candidate_file).read_bytes(), logical_path, expected_generation=expected_generation
    )


def required_review_inputs(store: ArtifactStore, run_id: str, phase: str) -> list[dict[str, str]]:
    row = _run(store, run_id)
    values = [json.loads(row["request_ref_json"]), *json.loads(row["originals_json"])]
    if phase == "CANDIDATE_COUNTEREXAMPLE":
        if row["candidate_snapshot"] is None:
            raise ThesisLifecycleError("candidate review requires a fixed candidate")
        values.append({"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]})
    elif phase != "SOURCE_FRONTIER":
        raise ThesisLifecycleError("unsupported review phase")
    seen: set[tuple[str, str]] = set()
    result = []
    for item in values:
        normalized = validate_ref(item)
        key = (normalized["snapshot"], normalized["path"])
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def begin_review(store: ArtifactStore, run_id: str, phase: str, inputs: list[dict]) -> str:
    row = _run(store, run_id)
    _require_mutable(row)
    if phase not in {"SOURCE_FRONTIER", "CANDIDATE_COUNTEREXAMPLE"}:
        raise ThesisLifecycleError("unsupported review phase")
    normalized = [validate_ref(item) for item in inputs]
    for item in normalized:
        store.resolve(item)
    required = required_review_inputs(store, run_id, phase)
    supplied = {(item["snapshot"], item["path"]) for item in normalized}
    missing = [item for item in required if (item["snapshot"], item["path"]) not in supplied]
    if missing:
        raise ThesisLifecycleError("REVIEW_INPUT_MISMATCH")

    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if current is None or current["phase"] in MUTATION_BLOCKED:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("Thesis run cannot start review")
        total = current["budget_total"]
        used = int(current["budget_used"])
        if total is not None and used >= int(total):
            db.execute("UPDATE thesis_runs SET phase='BUDGET_EXHAUSTED' WHERE run_id=?", (run_id,))
            db.execute("COMMIT")
            raise ThesisLifecycleError("BUDGET_EXHAUSTED")
        invocation_id = "inv-" + uuid.uuid4().hex
        candidate_generation = int(current["generation"]) if phase == "CANDIDATE_COUNTEREXAMPLE" else None
        db.execute(
            "INSERT INTO thesis_reviews(invocation_id,run_id,request_generation,candidate_generation,phase,"
            "candidate_snapshot,candidate_path,status,inputs_json,result_ref_json,started_sequence,completed_sequence) "
            "VALUES(?,?,?,?,?,?,?,'STARTED',?,NULL,?,NULL)",
            (
                invocation_id,
                run_id,
                current["request_generation"],
                candidate_generation,
                phase,
                current["candidate_snapshot"] if phase == "CANDIDATE_COUNTEREXAMPLE" else None,
                current["candidate_path"] if phase == "CANDIDATE_COUNTEREXAMPLE" else None,
                json.dumps(normalized, ensure_ascii=False),
                store.sequence_in(db, "thesis-review-start"),
            ),
        )
        db.execute(
            "UPDATE thesis_runs SET phase='CHALLENGING',budget_used=budget_used+1 WHERE run_id=?",
            (run_id,),
        )
        db.execute("COMMIT")
    return invocation_id


def complete_review(
    store: ArtifactStore,
    invocation_id: str,
    *,
    result: dict,
    frontier: list[dict] | None = None,
    findings: list[dict] | None = None,
) -> list[str]:
    _schema(store)
    if not isinstance(result, dict) or not result:
        raise ThesisLifecycleError("review result must be a nonempty object")
    with store.connect() as db:
        review = db.execute("SELECT * FROM thesis_reviews WHERE invocation_id=?", (invocation_id,)).fetchone()
    if review is None or review["status"] != "STARTED":
        raise ThesisLifecycleError("review invocation is not active")

    result_snapshot = store.capture_mapping(
        {f"reviews/{invocation_id}/result.json": (json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")},
        kind="review-result",
        producer_run=review["run_id"],
        producer_invocation=invocation_id,
    )
    result_ref = {"snapshot": result_snapshot, "path": f"reviews/{invocation_id}/result.json"}
    created_findings: list[str] = []

    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        active = db.execute("SELECT * FROM thesis_reviews WHERE invocation_id=?", (invocation_id,)).fetchone()
        current = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (review["run_id"],)).fetchone()
        if active is None or active["status"] != "STARTED":
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("review invocation is not active")

        late = current is not None and current["phase"] == "CANCELLED"
        stale = (
            current is None
            or current["phase"] in {"FAILED", "CLOSED"}
            or int(active["request_generation"]) != int(current["request_generation"])
            or (
                active["phase"] == "CANDIDATE_COUNTEREXAMPLE"
                and (
                    int(active["candidate_generation"]) != int(current["generation"])
                    or active["candidate_snapshot"] != current["candidate_snapshot"]
                    or active["candidate_path"] != current["candidate_path"]
                )
            )
        )
        if late or stale:
            db.execute(
                "UPDATE thesis_reviews SET status=?,result_ref_json=?,completed_sequence=? WHERE invocation_id=?",
                (
                    "LATE" if late else "STALE",
                    json.dumps(result_ref),
                    store.sequence_in(db, "thesis-review-complete"),
                    invocation_id,
                ),
            )
            db.execute("COMMIT")
            return []

        if current["phase"] == "CLOSING":
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("review completion raced with lifecycle transition")

        for item in frontier or []:
            for key in ("item_id", "origin", "question", "material_change"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    db.execute("ROLLBACK")
                    raise ThesisLifecycleError("invalid frontier finding")
            db.execute(
                "INSERT INTO thesis_frontier(run_id,request_generation,item_id,origin,question,material_change,decision_bearing) "
                "VALUES(?,?,?,?,?,?,?) ON CONFLICT(run_id,request_generation,item_id) DO UPDATE SET "
                "origin=excluded.origin,question=excluded.question,material_change=excluded.material_change,"
                "decision_bearing=excluded.decision_bearing,disposition=NULL,basis=NULL",
                (
                    review["run_id"], review["request_generation"], item["item_id"], item["origin"],
                    item["question"], item["material_change"], int(bool(item.get("decision_bearing"))),
                ),
            )

        for item in findings or []:
            materiality = item.get("materiality")
            if materiality not in {"MATERIAL", "OUT_OF_SCOPE"}:
                db.execute("ROLLBACK")
                raise ThesisLifecycleError("invalid review finding materiality")
            for key in ("finding_id", "anchor", "scenario", "apparent_success", "broken_result"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    db.execute("ROLLBACK")
                    raise ThesisLifecycleError("finding fields must be nonempty")
            finding_key = "finding-" + uuid.uuid4().hex
            initial = "OPEN" if materiality == "MATERIAL" else "OUT_OF_SCOPE"
            try:
                db.execute(
                    "INSERT INTO thesis_findings(finding_key,run_id,request_generation,reported_id,invocation_id,"
                    "candidate_snapshot,anchor,scenario,apparent_success,broken_result,materiality,initial_disposition) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        finding_key, review["run_id"], review["request_generation"], item["finding_id"], invocation_id,
                        review["candidate_snapshot"], item["anchor"], item["scenario"], item["apparent_success"],
                        item["broken_result"], materiality, initial,
                    ),
                )
            except Exception as exc:
                db.execute("ROLLBACK")
                raise ThesisLifecycleError("DUPLICATE_FINDING_ID_WITHIN_INVOCATION") from exc
            created_findings.append(finding_key)

        db.execute(
            "UPDATE thesis_reviews SET status='COMPLETE',result_ref_json=?,completed_sequence=? WHERE invocation_id=?",
            (json.dumps(result_ref), store.sequence_in(db, "thesis-review-complete"), invocation_id),
        )
        db.execute("UPDATE thesis_runs SET phase='CLOSURE_CHECK' WHERE run_id=?", (review["run_id"],))
        db.execute("COMMIT")
    return created_findings

def _resolve_finding_key(store: ArtifactStore, run_id: str, identifier: str) -> str:
    with store.connect() as db:
        direct = db.execute(
            "SELECT finding_key FROM thesis_findings WHERE run_id=? AND finding_key=?",
            (run_id, identifier),
        ).fetchone()
        if direct is not None:
            return direct["finding_key"]
        rows = db.execute(
            "SELECT finding_key FROM thesis_findings WHERE run_id=? AND reported_id=?",
            (run_id, identifier),
        ).fetchall()
    if len(rows) != 1:
        raise ThesisLifecycleError("finding identifier is unknown or ambiguous")
    return rows[0]["finding_key"]


def disposition_finding(store: ArtifactStore, run_id: str, finding_id: str, disposition: str, basis: str) -> None:
    row = _run(store, run_id)
    _require_mutable(row)
    if disposition not in {"RESOLVED", "DISMISSED", "OUT_OF_SCOPE"} or not basis.strip():
        raise ThesisLifecycleError("invalid finding disposition")
    finding_key = _resolve_finding_key(store, run_id, finding_id)
    with store.connect() as db:
        finding = db.execute(
            "SELECT request_generation FROM thesis_findings WHERE finding_key=?",
            (finding_key,),
        ).fetchone()
        if finding is None or int(finding["request_generation"]) != int(row["request_generation"]):
            raise ThesisLifecycleError("cannot disposition a finding from another request generation")
        db.execute(
            "INSERT INTO thesis_finding_dispositions(disposition_key,finding_key,disposition,basis,sequence) "
            "VALUES(?,?,?,?,?)",
            ("disp-" + uuid.uuid4().hex, finding_key, disposition, basis, store.sequence_in(db, "thesis-finding-disposition")),
        )


def _finding_disposition(db, finding_key: str, initial: str) -> str:
    row = db.execute(
        "SELECT disposition FROM thesis_finding_dispositions WHERE finding_key=? ORDER BY sequence DESC LIMIT 1",
        (finding_key,),
    ).fetchone()
    return initial if row is None else row["disposition"]


def _evaluate_with_db(store: ArtifactStore, db, row) -> dict:
    phase = row["phase"]
    if phase == "CANCELLED":
        return {"result": "CANCELLED", "tasks": []}
    if phase == "FAILED":
        return {"result": "FAILED", "tasks": [{"item": "run", "reason": row["last_error"] or "FAILED"}]}
    if phase == "CLOSED":
        return {"result": "ALREADY_CLOSED", "tasks": []}
    req_gen = int(row["request_generation"])
    tasks: list[dict] = []
    waiting_user = False
    waiting_evidence = False
    if row["candidate_snapshot"] is None:
        tasks.append({"item": "candidate", "reason": "CANDIDATE_REQUIRED", "required_action": "Submit a fixed Thesis candidate."})

    started = db.execute(
        "SELECT invocation_id FROM thesis_reviews WHERE run_id=? AND request_generation=? AND status='STARTED'",
        (row["run_id"], req_gen),
    ).fetchall()
    for review in started:
        tasks.append({
            "item": review["invocation_id"],
            "reason": "REVIEW_RESULT_PENDING",
            "required_action": "Recover or terminally account for the started review before closure.",
        })

    source_review = db.execute(
        "SELECT 1 FROM thesis_reviews WHERE run_id=? AND request_generation=? AND phase='SOURCE_FRONTIER' "
        "AND status='COMPLETE' LIMIT 1",
        (row["run_id"], req_gen),
    ).fetchone()
    candidate_review = None
    if row["candidate_snapshot"] is not None:
        candidate_review = db.execute(
            "SELECT 1 FROM thesis_reviews WHERE run_id=? AND request_generation=? AND phase='CANDIDATE_COUNTEREXAMPLE' "
            "AND candidate_generation=? AND candidate_snapshot=? AND candidate_path=? AND status='COMPLETE' LIMIT 1",
            (row["run_id"], req_gen, row["generation"], row["candidate_snapshot"], row["candidate_path"]),
        ).fetchone()
    if source_review is None:
        tasks.append({"item": "review:source", "reason": "SOURCE_FRONTIER_REVIEW_REQUIRED"})
    if candidate_review is None:
        tasks.append({"item": "review:candidate", "reason": "CURRENT_CANDIDATE_CHALLENGE_REQUIRED"})

    frontier = db.execute(
        "SELECT * FROM thesis_frontier WHERE run_id=? AND request_generation=? ORDER BY item_id",
        (row["run_id"], req_gen),
    ).fetchall()
    premises = db.execute(
        "SELECT * FROM thesis_premises WHERE run_id=? AND request_generation=? ORDER BY premise_id",
        (row["run_id"], req_gen),
    ).fetchall()
    findings = db.execute(
        "SELECT * FROM thesis_findings WHERE run_id=? AND request_generation=? ORDER BY finding_key",
        (row["run_id"], req_gen),
    ).fetchall()
    if not frontier:
        tasks.append({"item": "frontier", "reason": "MATERIAL_FRONTIER_NOT_RECORDED"})
    for item in frontier:
        disposition = item["disposition"]
        if disposition is None:
            tasks.append({"item": item["item_id"], "reason": "FRONTIER_UNDISPOSITIONED"})
            continue
        if bool(item["decision_bearing"]) and not (item["basis"] or "").strip():
            tasks.append({"item": item["item_id"], "reason": "DECISION_DISCRIMINATOR_MISSING"})
        waiting_user |= disposition == "USER_CHOICE"
        waiting_evidence |= disposition == "EVIDENCE_LIMIT" and bool(item["decision_bearing"])
    for premise in premises:
        if premise["kind"] == "implementation_satisfaction":
            continue
        disposition = premise["disposition"]
        if disposition is None:
            tasks.append({"item": premise["premise_id"], "reason": "BLOCKING_PREMISE_UNRESOLVED"})
        else:
            waiting_user |= disposition == "USER_CHOICE"
            waiting_evidence |= disposition == "EVIDENCE_LIMIT"
    for finding in findings:
        disposition = _finding_disposition(db, finding["finding_key"], finding["initial_disposition"])
        if finding["materiality"] == "MATERIAL" and disposition not in {"RESOLVED", "DISMISSED"}:
            tasks.append({"item": finding["finding_key"], "reason": "MATERIAL_FINDING_UNRESOLVED"})

    if waiting_user:
        return {"result": "WAITING_USER", "tasks": tasks}
    if waiting_evidence:
        return {"result": "WAITING_EVIDENCE", "tasks": tasks}
    total = row["budget_total"]
    if tasks and total is not None and int(row["budget_used"]) >= int(total):
        return {"result": "BUDGET_EXHAUSTED", "tasks": tasks}
    if tasks:
        return {"result": "REWORK_REQUIRED", "tasks": tasks}
    return {"result": "ELIGIBLE", "tasks": []}


def evaluate_closure(store: ArtifactStore, run_id: str) -> dict:
    row = _run(store, run_id)
    with store.connect() as db:
        return _evaluate_with_db(store, db, row)


def _finalize_closure(
    store: ArtifactStore,
    row,
    *,
    limitations: str,
) -> dict:
    closure_id = "close-" + uuid.uuid4().hex
    candidate = {"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]}
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (row["run_id"],)).fetchone()
        if (
            current is None
            or current["phase"] != "CLOSING"
            or int(current["generation"]) != int(row["generation"])
            or int(current["request_generation"]) != int(row["request_generation"])
            or current["candidate_snapshot"] != row["candidate_snapshot"]
            or current["candidate_path"] != row["candidate_path"]
        ):
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("closure state changed before finalize")
        db.execute(
            "INSERT INTO thesis_closures(closure_id,run_id,request_generation,candidate_generation,"
            "candidate_snapshot,candidate_path,result,limitations,sequence) VALUES(?,?,?,?,?,?,'CALIBRATED',?,?)",
            (
                closure_id,
                row["run_id"],
                row["request_generation"],
                row["generation"],
                row["candidate_snapshot"],
                row["candidate_path"],
                limitations,
                store.sequence_in(db, "thesis-close"),
            ),
        )
        db.execute("UPDATE thesis_runs SET phase='CLOSED',last_error=NULL WHERE run_id=?", (row["run_id"],))
        db.execute("COMMIT")
    return {
        "schema": "iis-thesis-closure/v2",
        "closure_id": closure_id,
        "run_id": row["run_id"],
        "candidate": candidate,
        "result": "CALIBRATED",
        "limitations": limitations,
    }


def close_request(
    store: ArtifactStore,
    run_id: str,
    project_root: Path,
    *,
    limitations: str = "",
    expected_generation: int | None = None,
) -> dict:
    _schema(store)

    row = _run(store, run_id)
    if row["phase"] == "CLOSING":
        recover_pending(store, project_root)
        published = published_ref(store, row["candidate_path"])
        candidate = {"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]}
        if published == candidate:
            return _finalize_closure(store, row, limitations=limitations)
        with store.connect() as db:
            db.execute(
                "UPDATE thesis_runs SET phase='CLOSURE_CHECK',last_error=NULL WHERE run_id=? AND phase='CLOSING'",
                (run_id,),
            )

    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("unknown Thesis run")
        if row["phase"] in TERMINAL:
            db.execute("ROLLBACK")
            return _evaluate_with_db(store, db, row)
        if row["phase"] == "CLOSING":
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("closure is already in progress")
        if expected_generation is not None and int(row["generation"]) != expected_generation:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("GENERATION_CONFLICT")
        verdict = _evaluate_with_db(store, db, row)
        if verdict["result"] != "ELIGIBLE":
            next_phase = verdict["result"] if verdict["result"] in {
                "WAITING_USER", "WAITING_EVIDENCE", "BUDGET_EXHAUSTED"
            } else "WORKING"
            db.execute("UPDATE thesis_runs SET phase=? WHERE run_id=?", (next_phase, run_id))
            db.execute("COMMIT")
            return verdict
        candidate = {"snapshot": row["candidate_snapshot"], "path": row["candidate_path"]}
        prior = None if row["expected_prior_json"] is None else json.loads(row["expected_prior_json"])
        db.execute("UPDATE thesis_runs SET phase='CLOSING',last_error=NULL WHERE run_id=?", (run_id,))
        db.execute("COMMIT")

    try:
        publish_ref(store, candidate, project_root, candidate["path"], expected_prior=prior)
    except RevisionConflict as exc:
        with store.connect() as db:
            db.execute(
                "UPDATE thesis_runs SET phase='WORKING',last_error=? WHERE run_id=? AND phase='CLOSING'",
                (str(exc), run_id),
            )
        raise
    except BaseException as exc:
        # Leave CLOSING intact. A restart can recover any pending publication,
        # determine whether old/new bytes are live, then continue closure safely.
        with store.connect() as db:
            db.execute(
                "UPDATE thesis_runs SET last_error=? WHERE run_id=? AND phase='CLOSING'",
                (str(exc), run_id),
            )
        raise

    current = _run(store, run_id)
    return _finalize_closure(store, current, limitations=limitations)

def closed_for_ref(store: ArtifactStore, value: object) -> bool:
    item = validate_ref(value)
    _schema(store)
    with store.connect() as db:
        row = db.execute(
            "SELECT 1 FROM thesis_closures c JOIN thesis_runs r ON r.run_id=c.run_id "
            "WHERE c.candidate_snapshot=? AND c.candidate_path=? AND c.result='CALIBRATED' AND r.phase='CLOSED' LIMIT 1",
            (item["snapshot"], item["path"]),
        ).fetchone()
    return row is not None


def cancel(store: ArtifactStore, run_id: str) -> None:
    _schema(store)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("unknown Thesis run")
        if row["phase"] == "CLOSED":
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("closed Thesis history is immutable")
        if row["phase"] == "CLOSING":
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("cannot cancel while closure publication is in progress")
        db.execute("UPDATE thesis_runs SET phase='CANCELLED' WHERE run_id=?", (run_id,))
        db.execute("COMMIT")


def resume(
    store: ArtifactStore,
    run_id: str,
    request_text: str,
    *,
    budget_increment: int | None = None,
) -> None:
    row = _run(store, run_id)
    if row["phase"] not in {"WAITING_USER", "WAITING_EVIDENCE", "BUDGET_EXHAUSTED"}:
        raise ThesisLifecycleError("only a waiting or budget-exhausted Thesis run can resume")
    if not request_text.strip():
        raise ThesisLifecycleError("current resume request is required")
    if row["phase"] == "BUDGET_EXHAUSTED" and (budget_increment is None or budget_increment <= 0):
        raise ThesisLifecycleError("resuming exhausted work requires additional review budget")
    new_request_generation = int(row["request_generation"]) + 1
    new_ref = _request_ref(store, run_id, request_text, new_request_generation)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT * FROM thesis_runs WHERE run_id=?", (run_id,)).fetchone()
        if current is None or current["phase"] not in {"WAITING_USER", "WAITING_EVIDENCE", "BUDGET_EXHAUSTED"}:
            db.execute("ROLLBACK")
            raise ThesisLifecycleError("resume raced with another transition")
        budget_total = current["budget_total"]
        if budget_increment is not None:
            budget_total = (0 if budget_total is None else int(budget_total)) + int(budget_increment)
        db.execute("UPDATE thesis_reviews SET status='STALE' WHERE run_id=? AND status='STARTED'", (run_id,))
        db.execute(
            "UPDATE thesis_runs SET request_text=?,request_ref_json=?,request_generation=?,generation=generation+1,"
            "candidate_snapshot=NULL,candidate_path=NULL,phase='WORKING',budget_total=?,last_error=NULL WHERE run_id=?",
            (request_text, json.dumps(new_ref), new_request_generation, budget_total, run_id),
        )
        db.execute("COMMIT")
