"""Small deterministic result helpers; this module does not execute verification."""

from __future__ import annotations

from collections.abc import Sequence


VERDICTS = frozenset({"PASS", "FAIL", "INCONCLUSIVE"})


def aggregate(ac_count: int, rows: Sequence[tuple[int, str]]) -> str:
    """Validate exact-once ordinal rows and derive the whole-Ticket result."""

    if ac_count < 1:
        raise ValueError("ac_count must be positive")
    if [ordinal for ordinal, _verdict in rows] != list(range(1, ac_count + 1)):
        raise ValueError("rows must contain every authored AC ordinal exactly once in order")
    verdicts = [verdict for _ordinal, verdict in rows]
    if any(verdict not in VERDICTS for verdict in verdicts):
        raise ValueError("invalid AC verdict")
    if "FAIL" in verdicts:
        return "FAILED"
    if all(verdict == "PASS" for verdict in verdicts):
        return "VERIFIED"
    return "INCONCLUSIVE"


def classify_boundary(*, admission_complete: bool, attempted: bool, contradiction: bool) -> str:
    """Expose the admission/runtime boundary without interpreting product semantics."""

    if not admission_complete:
        if attempted or contradiction:
            raise ValueError("an admission defect cannot have a product attempt or contradiction")
        return "VERIFICATION NOT STARTED"
    if not attempted:
        raise ValueError("a complete admission needs a fresh attempt before an AC verdict")
    return "FAIL" if contradiction else "INCONCLUSIVE"
