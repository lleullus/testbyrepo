"""Trusted host adapter for actual Product Thesis review invocation records.

This module deliberately does not invoke a model by itself. A host adapter calls
`begin_review` immediately before dispatch and `complete_review` only after the
actual invocation has terminally returned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from iis_artifacts.store import ArtifactStore


@dataclass(frozen=True)
class HostReviewResult:
    invocation_id: str
    result: dict[str, Any]


def run_review(
    store: ArtifactStore,
    lifecycle: Any,
    run_id: str,
    phase: str,
    inputs: list[dict],
    invoke: Callable[[str, list[dict]], dict[str, Any]],
) -> HostReviewResult:
    invocation_id = lifecycle.begin_review(store, run_id, phase, inputs)
    result = invoke(phase, inputs)
    if not isinstance(result, dict):
        raise TypeError("host review invocation must return an object")
    lifecycle.complete_review(
        store,
        invocation_id,
        result=result.get("result", {}),
        frontier=result.get("frontier", []),
        findings=result.get("findings", []),
    )
    return HostReviewResult(invocation_id=invocation_id, result=result)
