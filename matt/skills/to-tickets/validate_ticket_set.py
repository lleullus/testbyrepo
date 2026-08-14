#!/usr/bin/env python3
"""Validate the complete ready Ticket set for one approved IIS Spec."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validate_ticket import (
    CORE_LABELS,
    SPEC_CORE_LABELS,
    STATUS_RE,
    TicketValidationError,
    _labeled_item,
    _section,
    _single_match,
    _top_level_items,
    validate,
)


class TicketSetValidationError(RuntimeError):
    pass


def validate_set(spec_path: str | Path, *, require_completable: bool = False) -> list[Path]:
    raw_spec = Path(spec_path).expanduser()
    if not raw_spec.is_absolute():
        raise TicketSetValidationError("Spec path must be absolute and canonical")
    try:
        spec = raw_spec.resolve(strict=True)
        spec_text = spec.read_text(encoding="utf-8")
    except OSError as exc:
        raise TicketSetValidationError(f"Spec is unreadable: {raw_spec}") from exc
    if raw_spec != spec or raw_spec.is_symlink() or not spec.is_file() or spec.name != "SPEC.md":
        raise TicketSetValidationError("Spec must be an absolute canonical raw SPEC.md file")
    if _single_match(STATUS_RE, spec_text, "Spec Status") != "approved":
        raise TicketSetValidationError("Spec must be approved")

    work = spec.parent
    if (
        work.parent.name != "work"
        or work.parent.parent.name != "planning"
        or work.parent.parent.parent.name != "docs"
    ):
        raise TicketSetValidationError("Spec must remain under Project-Root/docs/planning/work/<work-slug>")
    tickets_dir = work / "tickets"
    if not tickets_dir.is_dir() or tickets_dir.is_symlink():
        raise TicketSetValidationError("Spec has no canonical tickets directory")

    spec_outcomes = _top_level_items(
        _section(spec_text, "Verification Expectations"), "Verification Expectations"
    )
    if require_completable:
        for index, item in enumerate(spec_outcomes, 1):
            values = _labeled_item(item, SPEC_CORE_LABELS, f"Spec outcome {index}")
            if values["Disposition"] == "Not independently verifiable":
                raise TicketSetValidationError(
                    f"Complete Ready Ticket Set is not admitted: Spec outcome {index} has no approved completion evidence path"
                )

    tickets = sorted(tickets_dir.glob("TICKET-[0-9][0-9][0-9].md"))
    if not tickets:
        raise TicketSetValidationError("Spec has no implementation Tickets")

    covered_outcomes: set[int] = set()
    for ticket in tickets:
        try:
            validate(ticket)
        except TicketValidationError as exc:
            raise TicketSetValidationError(f"invalid Ticket {ticket.name}: {exc}") from exc
        text = ticket.read_text(encoding="utf-8")
        if _single_match(STATUS_RE, text, f"Ticket Status ({ticket.name})") != "ready":
            raise TicketSetValidationError(f"Ticket set is not ready: {ticket.name}")

        flow_items = _top_level_items(_section(text, "Verification"), "Verification")
        for index, item in enumerate(flow_items, 1):
            values = _labeled_item(item, CORE_LABELS, f"Verification flow {index}")
            covered_outcomes.add(int(values["Parent outcome ordinal"]))

    expected_outcomes = set(range(1, len(spec_outcomes) + 1))
    if covered_outcomes != expected_outcomes:
        missing = sorted(expected_outcomes - covered_outcomes)
        extra = sorted(covered_outcomes - expected_outcomes)
        raise TicketSetValidationError(
            f"Ticket set does not cover every Parent Spec outcome; missing={missing}, extra={extra}"
        )

    return tickets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-completable", action="store_true")
    parser.add_argument("spec")
    args = parser.parse_args(argv)
    try:
        tickets = validate_set(args.spec, require_completable=args.require_completable)
    except (TicketSetValidationError, TicketValidationError) as exc:
        print(f"INVALID SET: {exc}", file=sys.stderr)
        return 2
    print("VALID SET")
    for ticket in tickets:
        print(ticket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
