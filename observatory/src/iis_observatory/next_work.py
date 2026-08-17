from __future__ import annotations

from .model import Health, NextWork, NextWorkKind, ProjectState, Stage, natural_id_key


def evaluate_next_work(state: ProjectState) -> None:
    """Apply the IIS Current Planning State Check as a deterministic read model."""
    if state.planning_root is None:
        state.stage = Stage.UNKNOWN
        state.health = Health.NO_IIS
        state.next_work = NextWork(
            NextWorkKind.NONE, None, None, "none", "No docs/planning directory exists."
        )
        return

    if state.has_errors:
        first_error = next(issue for issue in state.issues if issue.severity == "error")
        state.stage = _best_effort_stage(state)
        state.health = Health.INCONSISTENT
        state.next_work = NextWork(
            NextWorkKind.CONSISTENCY_CHECK,
            None,
            first_error.path,
            "none",
            f"Planning artifacts are inconsistent: {first_error.code} {first_error.message}",
        )
        return

    tickets = sorted(state.tickets, key=lambda item: (natural_id_key(item.identifier), item.relative_path))
    blocked = [ticket for ticket in tickets if ticket.status == "blocked"]
    ready = [ticket for ticket in tickets if ticket.status == "ready"]
    drafts = [ticket for ticket in tickets if ticket.status == "draft"]
    other_remaining = [
        ticket for ticket in tickets if ticket.status not in {"done", "blocked", "ready", "draft"}
    ]

    if blocked:
        ticket = blocked[0]
        state.stage = Stage.DELIVERY
        state.health = Health.BLOCKED
        state.next_work = NextWork(
            NextWorkKind.TICKET_UNBLOCK,
            ticket.identifier,
            ticket.relative_path,
            "delivery outside IIS",
            "The current Increment contains a blocked non-done Ticket.",
        )
        return

    if ready:
        ticket = ready[0]
        state.stage = Stage.DELIVERY
        state.health = Health.READY
        state.next_work = NextWork(
            NextWorkKind.TICKET_IMPLEMENT,
            ticket.identifier,
            ticket.relative_path,
            "delivery outside IIS",
            "The current Increment contains a Ready non-done Ticket.",
        )
        return

    if drafts:
        ticket = drafts[0]
        state.stage = Stage.TICKETS
        state.health = Health.PLANNING
        state.next_work = NextWork(
            NextWorkKind.TICKET_REVIEW,
            ticket.identifier,
            ticket.relative_path,
            "To Tickets",
            "The current Ticket set contains a draft Ticket that is not yet Ready.",
        )
        return

    if other_remaining:
        ticket = other_remaining[0]
        state.stage = Stage.TICKETS
        state.health = Health.PLANNING
        state.next_work = NextWork(
            NextWorkKind.TICKET_REVIEW,
            ticket.identifier,
            ticket.relative_path,
            "To Tickets",
            f"The current Ticket has a non-terminal status: {ticket.status or 'missing'}.",
        )
        return

    if tickets and all(ticket.status == "done" for ticket in tickets):
        state.stage = Stage.COMPLETE
        state.health = Health.COMPLETE
        if state.next_candidate_work_packages:
            state.next_work = NextWork(
                NextWorkKind.SCOPE_SHAPER,
                None,
                state.current_scope.relative_path if state.current_scope else None,
                "Scope Shaper",
                "Current Increment delivery is complete. The current Scope has unshaped follow-up Work Package candidates.",
            )
        else:
            state.next_work = NextWork(
                NextWorkKind.NONE,
                None,
                None,
                "none established",
                "Current Increment delivery is complete and the current Scope has no authored Expansion candidate.",
            )
        return

    spec = state.current_spec
    if spec is not None:
        if spec.status == "approved":
            state.stage = Stage.TICKETS
            state.health = Health.PLANNING
            state.next_work = NextWork(
                NextWorkKind.TO_TICKETS,
                spec.identifier,
                spec.relative_path,
                "To Tickets",
                "The current Spec is approved but no Ticket set is present.",
            )
            return
        state.stage = Stage.PLANNING
        state.health = Health.PLANNING
        state.next_work = NextWork(
            NextWorkKind.TO_SPEC,
            spec.identifier,
            spec.relative_path,
            "To Spec",
            "A current Spec exists but is not approved.",
        )
        return

    if state.current_increment is not None:
        if state.current_increment.status == "superseded":
            state.stage = Stage.SHAPING
            state.health = Health.STALE
            state.next_work = NextWork(
                NextWorkKind.SCOPE_SHAPER,
                state.current_work_package.identifier if state.current_work_package else None,
                state.current_work_package.relative_path if state.current_work_package else None,
                "Scope Shaper",
                "Only a superseded Increment is available; a current next Increment is not established.",
            )
            return
        state.stage = Stage.PLANNING
        state.health = Health.PLANNING
        state.next_work = NextWork(
            NextWorkKind.ASK_MATT,
            state.current_increment.identifier,
            state.current_increment.relative_path,
            "Ask Matt",
            "The current Increment is admitted but no current Spec is present.",
        )
        return

    if state.current_work_slug:
        state.stage = Stage.PLANNING
        state.health = Health.PLANNING
        state.next_work = NextWork(
            NextWorkKind.ASK_MATT,
            state.current_work_slug,
            None,
            "Ask Matt",
            "A direct work area exists without a Source-Increment and has no current Spec.",
        )
        return

    if state.current_scope is not None or state.current_work_package is not None:
        state.stage = Stage.SHAPING
        state.health = Health.NEEDS_SCOPE
        target = state.current_work_package
        state.next_work = NextWork(
            NextWorkKind.SCOPE_SHAPER,
            target.identifier if target else None,
            target.relative_path if target else (state.current_scope.relative_path if state.current_scope else None),
            "Scope Shaper",
            "Scope artifacts exist but no current next Increment is admitted.",
        )
        return

    state.stage = Stage.SHAPING
    state.health = Health.NEEDS_SCOPE
    state.next_work = NextWork(
        NextWorkKind.SCOPE_SHAPER,
        None,
        None,
        "Scope Shaper",
        "A planning directory exists but no current planning unit is authored.",
    )


def _best_effort_stage(state: ProjectState) -> Stage:
    if state.tickets:
        return Stage.DELIVERY
    if state.current_spec is not None:
        return Stage.PLANNING
    if state.current_increment is not None:
        return Stage.PLANNING
    if state.current_scope is not None or state.current_work_package is not None:
        return Stage.SHAPING
    return Stage.UNKNOWN
