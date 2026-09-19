"""Common downstream admission over executor-owned fixed Scope bytes."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import uuid

from .publication import ensure_no_pending
from .refs import validate_ref
from .store import ArtifactStore

ROOT = Path(__file__).resolve().parents[1]
SCOPE_SPEC = importlib.util.spec_from_file_location("iis_scope_validator", ROOT / "scope-shaper/tools/validate_scope.py")
assert SCOPE_SPEC is not None and SCOPE_SPEC.loader is not None
SCOPE = importlib.util.module_from_spec(SCOPE_SPEC)
SCOPE_SPEC.loader.exec_module(SCOPE)

LIFECYCLE_SPEC = importlib.util.spec_from_file_location("iis_thesis_lifecycle", ROOT / "product-thesis/tools/lifecycle.py")
assert LIFECYCLE_SPEC is not None and LIFECYCLE_SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(LIFECYCLE_SPEC)
LIFECYCLE_SPEC.loader.exec_module(LIFECYCLE)


class AdmissionError(RuntimeError):
    pass


def _schema(store: ArtifactStore) -> None:
    with store.connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS admissions(
              admission_id TEXT PRIMARY KEY,
              role TEXT NOT NULL,
              scope_snapshot TEXT NOT NULL,
              scope_path TEXT NOT NULL,
              request_ref_json TEXT NOT NULL,
              product_authorities_json TEXT NOT NULL,
              transition_authorities_json TEXT NOT NULL,
              status TEXT NOT NULL,
              sequence INTEGER NOT NULL
            );
            """
        )


def _request_ref(store: ArtifactStore, admission_id: str, current_request: str) -> dict[str, str]:
    if not isinstance(current_request, str) or not current_request.strip():
        raise AdmissionError("CURRENT_REQUEST_REQUIRED")
    snapshot = store.capture_mapping(
        {"request.txt": current_request.encode("utf-8")},
        kind="request",
        origin=f"admission:{admission_id}",
        producer_run=admission_id,
    )
    return {"snapshot": snapshot, "path": "request.txt"}


def admit_fixed_scope(
    store: ArtifactStore,
    scope_ref: object,
    *,
    role: str,
    current_request: str,
    project_owner_uid: int | None = None,
) -> dict:
    _schema(store)
    ensure_no_pending(store)
    if role not in {"scope-plan", "scope-implement", "assurance"}:
        raise AdmissionError("unsupported downstream role")
    scope = validate_ref(scope_ref)
    data = store.read_bytes(scope)
    authority = SCOPE.validate_bytes(data, scope["path"], trusted_uid=project_owner_uid)
    if authority["status"] != "ready":
        raise AdmissionError("Scope must be ready for downstream admission")
    for source in authority.get("product_authorities", []):
        store.resolve(source)
        if not LIFECYCLE.closed_for_ref(store, source):
            raise AdmissionError("THESIS_CLOSURE_REQUIRED")
    for source in authority.get("transition_authorities", []):
        store.resolve(source)

    admission_id = "admit-" + uuid.uuid4().hex
    request_ref = _request_ref(store, admission_id, current_request)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "INSERT INTO admissions(admission_id,role,scope_snapshot,scope_path,request_ref_json,"
            "product_authorities_json,transition_authorities_json,status,sequence) VALUES(?,?,?,?,?,?,?,'ELIGIBLE',?)",
            (
                admission_id,
                role,
                scope["snapshot"],
                scope["path"],
                json.dumps(request_ref),
                json.dumps(authority.get("product_authorities", []), ensure_ascii=False),
                json.dumps(authority.get("transition_authorities", []), ensure_ascii=False),
                store.sequence_in(db, "admission"),
            ),
        )
        db.execute("COMMIT")
    return {
        "schema": "iis-admission/v2",
        "admission_id": admission_id,
        "role": role,
        "scope": scope,
        "request": request_ref,
        "product_authorities": authority.get("product_authorities", []),
        "transition_authorities": authority.get("transition_authorities", []),
        "status": "ELIGIBLE",
    }


def admit_scope(
    store: ArtifactStore,
    scope: Path,
    *,
    role: str,
    current_request: str = "Synthetic/test admission request.",
    project_owner_uid: int | None = None,
) -> dict:
    scope = Path(scope).resolve(strict=True)
    text = scope.read_text(encoding="utf-8")
    root = Path(SCOPE.metadata(text, "Project-Root")).expanduser().resolve(strict=True)
    try:
        logical = scope.relative_to(root).as_posix()
    except ValueError as exc:
        raise AdmissionError("Scope is outside Project-Root") from exc
    snapshot = store.capture_files(root, [scope], kind="source", origin=f"admission-capture:{role}")
    fixed = {"snapshot": snapshot, "path": logical}
    return admit_fixed_scope(
        store,
        fixed,
        role=role,
        current_request=current_request,
        project_owner_uid=project_owner_uid,
    )


def admission_record(store: ArtifactStore, admission_id: str) -> dict:
    _schema(store)
    with store.connect() as db:
        row = db.execute("SELECT * FROM admissions WHERE admission_id=?", (admission_id,)).fetchone()
    if row is None:
        raise AdmissionError("UNKNOWN_ADMISSION")
    return dict(row)


def require_admission(
    store: ArtifactStore,
    scope_ref: object,
    *,
    role: str,
    current_request: str | None = None,
) -> dict:
    scope = validate_ref(scope_ref)
    _schema(store)
    with store.connect() as db:
        row = db.execute(
            "SELECT * FROM admissions WHERE role=? AND scope_snapshot=? AND scope_path=? AND status='ELIGIBLE' "
            "ORDER BY sequence DESC LIMIT 1",
            (role, scope["snapshot"], scope["path"]),
        ).fetchone()
    if row is None:
        raise AdmissionError("HOST_ADMISSION_REQUIRED")
    result = dict(row)
    if current_request is not None:
        request_ref = json.loads(result["request_ref_json"])
        if store.read_bytes(request_ref).decode("utf-8") != current_request:
            raise AdmissionError("ADMISSION_CURRENT_REQUEST_MISMATCH")
    return result


def main() -> int:
    print(json.dumps({
        "status": "BLOCKED",
        "reason": "HOST_SUPERVISOR_REQUIRED",
        "detail": "Current downstream admission is issued only by the trusted supervisor; this module CLI cannot select a store or mint admission.",
    }, ensure_ascii=False))
    return 20


if __name__ == "__main__":
    raise SystemExit(main())
