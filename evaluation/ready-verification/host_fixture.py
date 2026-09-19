"""Synthetic trusted-host setup for ready-verification fixtures.

This module establishes fixture preconditions only. It does not invoke a model or
claim that the evaluated agent performed Product Thesis work.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from iis_artifacts.admission import admit_scope
from iis_artifacts.store import ArtifactStore

SPEC = importlib.util.spec_from_file_location(
    "ready_verification_thesis_lifecycle",
    ROOT / "product-thesis/tools/lifecycle.py",
)
assert SPEC is not None and SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LIFECYCLE)


def close_fixture_thesis(store: ArtifactStore, project: Path, thesis: Path) -> dict:
    logical = thesis.relative_to(project).as_posix()
    source_snapshot = store.capture_files(project, [thesis], kind="source", origin="ready-verification-original")
    original_ref = {"snapshot": source_snapshot, "path": logical}
    run = LIFECYCLE.start(
        store,
        "Synthetic ready-verification precondition: preserve the supplied adopted Thesis.",
        originals=[original_ref],
        profile={"fixture": True, "model": "not-invoked"},
    )
    LIFECYCLE.add_frontier(
        store,
        run,
        item_id="fixture-authority",
        origin="evaluation fixture",
        question="Is the supplied Thesis existing authority for this downstream case?",
        material_change="A different answer changes the tested role boundary.",
        decision_bearing=True,
    )
    LIFECYCLE.disposition_frontier(
        store,
        run,
        "fixture-authority",
        "RESOLVED",
        "The fixture explicitly supplies the adopted Thesis as a precondition; agent Thesis behavior is not the subject of this downstream case.",
    )
    source_review = LIFECYCLE.begin_review(store, run, "SOURCE_FRONTIER", LIFECYCLE.required_review_inputs(store, run, "SOURCE_FRONTIER"))
    LIFECYCLE.complete_review(store, source_review, result={"completion": "COMPLETE", "fixture": True, "model_invoked": False})
    candidate = LIFECYCLE.submit_candidate(store, run, thesis, logical, expected_generation=0)
    challenge = LIFECYCLE.begin_review(store, run, "CANDIDATE_COUNTEREXAMPLE", LIFECYCLE.required_review_inputs(store, run, "CANDIDATE_COUNTEREXAMPLE"))
    LIFECYCLE.complete_review(store, challenge, result={"completion": "COMPLETE", "fixture": True, "model_invoked": False}, findings=[])
    result = LIFECYCLE.close_request(
        store,
        run,
        project,
        limitations="Synthetic precondition closure only; no model behavior is claimed.",
        expected_generation=1,
    )
    if result.get("result") != "CALIBRATED":
        raise ValueError(f"fixture Thesis failed to close: {result}")
    return candidate


def source_block(source_ref: dict) -> str:
    return "```iis-sources\n" + json.dumps([source_ref], ensure_ascii=False, indent=2) + "\n```"


def admit_fixture_scope(store: ArtifactStore, scope: Path, role: str) -> dict:
    return admit_scope(store, scope, role=role)
