"""Common downstream admission for hashless Scope v2 and closed Product Thesis refs."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

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


def admit_scope(store: ArtifactStore, scope: Path, *, role: str) -> dict:
    authority = SCOPE.validate(scope)
    if authority["status"] != "ready":
        raise AdmissionError("Scope must be ready for downstream admission")
    if role not in {"scope-plan", "scope-implement", "assurance"}:
        raise AdmissionError("unsupported downstream role")
    for source in authority.get("product_authorities", []):
        if not LIFECYCLE.closed_for_ref(store, source):
            raise AdmissionError("THESIS_CLOSURE_REQUIRED")
    root = Path(authority["project_root"])
    relative = scope.relative_to(root).as_posix()
    snapshot = store.capture_files(root, [scope], kind="source", origin=f"admission:{role}")
    return {
        "schema": "iis-admission/v1",
        "role": role,
        "scope": {"snapshot": snapshot, "path": relative},
        "product_authorities": authority.get("product_authorities", []),
        "transition_authorities": authority.get("transition_authorities", []),
        "status": "ELIGIBLE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", type=Path)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--role", required=True, choices=("scope-plan", "scope-implement", "assurance"))
    args = parser.parse_args()
    try:
        result = admit_scope(ArtifactStore(args.store, args.project_id), args.scope, role=args.role)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
