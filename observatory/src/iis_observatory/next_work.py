from __future__ import annotations

from .model import Health, NextWork, NextWorkKind, ProjectState, Stage


def evaluate_next_work(state: ProjectState) -> None:
    """Compute a read-only pointer for the unified Thesis → Scope → Plan path."""
    if state.planning_root is None:
        state.stage = Stage.UNKNOWN
        state.health = Health.NO_IIS
        state.next_work = NextWork(
            NextWorkKind.NONE,
            None,
            None,
            "none",
            "No docs/planning directory exists.",
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

    if state.direct_scope_mode:
        scope = state.current_scope
        if scope is None:
            state.stage = Stage.SHAPING
            state.health = Health.STALE
            state.next_work = NextWork(
                NextWorkKind.TRANSITION_REQUIRED,
                None,
                None,
                "transition required",
                "Only superseded direct Scope history is present; no current Scope is established.",
            )
            return
        if scope.status == "draft":
            state.stage = Stage.SHAPING
            state.health = Health.PLANNING
            state.next_work = NextWork(
                NextWorkKind.SCOPE_SHAPER,
                scope.work_slug,
                scope.relative_path,
                "Scope Shaper",
                "The current direct Scope is draft and still needs current product decisions before planning.",
            )
            return
        if scope.status == "ready":
            state.stage = Stage.PLANNING
            state.health = Health.PLANNING
            state.next_work = NextWork(
                NextWorkKind.NONE,
                scope.work_slug,
                scope.relative_path,
                "delivery state not established",
                "Ready alone does not distinguish unplanned, implemented or awaiting verification. Inspect current method/target/terminal evidence before choosing the next stage.",
            )
            return
        if scope.status == "done":
            state.stage = Stage.COMPLETE
            state.health = Health.COMPLETE
            if state.remaining_required_outcomes:
                state.stage = Stage.SHAPING
                state.health = Health.PLANNING
                state.next_work = NextWork(
                    NextWorkKind.SCOPE_SHAPER,
                    scope.work_slug,
                    scope.relative_path,
                    "Scope Shaper",
                    "The current Scope is done, but named outcome fulfillment is unassessed. Reconcile current completion evidence before selecting further construction.",
                )
            else:
                state.next_work = NextWork(
                    NextWorkKind.NONE,
                    None,
                    None,
                    "none established",
                    "Only this Scope is recorded done; the observed sources do not establish whole-request completion.",
                )
            return
        # superseded is retained as history, never resumed automatically.
        state.stage = Stage.SHAPING
        state.health = Health.STALE
        state.next_work = NextWork(
            NextWorkKind.TRANSITION_REQUIRED,
            scope.work_slug,
            scope.relative_path,
            "transition required",
            "The current direct Scope is superseded and must not be resumed automatically.",
        )
        return

    if state.legacy_history:
        if not state.transition_required:
            state.stage = Stage.UNKNOWN
            state.health = Health.STALE
            state.next_work = NextWork(NextWorkKind.NONE, None, None, "none established",
                                      "Only completed legacy history is observed; it requires no automatic migration or execution.")
            return
        state.stage = Stage.SHAPING
        state.health = Health.STALE
        target = state.transition_required[0] if state.transition_required else state.legacy_history[0]
        state.next_work = NextWork(
            NextWorkKind.TRANSITION_REQUIRED,
            target.identifier,
            target.relative_path,
            "transition required",
            "Legacy Scope/Increment/Spec/Ticket artifacts are read-only history; no automatic migration or Matt/Ticket pointer is issued.",
        )
        return

    state.stage = Stage.SHAPING
    state.health = Health.NEEDS_SCOPE
    state.next_work = NextWork(
        NextWorkKind.SCOPE_SHAPER,
        None,
        None,
        "Scope Shaper",
        "A planning directory exists but no current direct Scope is authored.",
    )


def _best_effort_stage(state: ProjectState) -> Stage:
    if state.direct_scope_mode or state.current_scope is not None:
        return Stage.SHAPING
    return Stage.UNKNOWN
