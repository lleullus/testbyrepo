"""Defect/control models for failure-space completeness evaluation.

They prove the proposed discriminator separates nearby implementations; they do
not execute IIS roles or manufacture verifier evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class AdjacentTransition:
    defective: bool
    state: str = "A"

    def action_x(self) -> bool:
        self.state = "B"
        return True

    def next_operation(self) -> bool:
        return not (self.defective and self.state == "B")


@dataclass
class ThresholdStream:
    defective: bool
    threshold: int = 8
    produced: int = 0

    def produce_while_paused(self, size: int) -> str:
        self.produced += size
        return "producer-complete"

    def next_consumer_read_after_resume(self) -> str | None:
        return None if self.defective and self.produced > self.threshold else "next-output"


@dataclass
class SchedulerRecovery:
    defective: bool
    hidden: bool = False
    ready: bool = False

    def start_hidden(self) -> None:
        self.hidden = True

    def transport_pong(self) -> bool:
        return True

    def settle_parser(self) -> None:
        if not (self.defective and self.hidden):
            self.ready = True


@dataclass
class OwnerLiveness:
    defective: bool
    transport_alive: bool = True
    application_progress: bool = False

    def owner_is_usable(self) -> bool:
        return self.transport_alive if self.defective else self.transport_alive and self.application_progress


@dataclass
class TerminalLifecycle:
    defective: bool
    exited: bool = False
    ready: bool = False

    def observe_exit(self) -> None:
        self.exited = True
        self.ready = False

    def start_new(self) -> None:
        if not self.defective:
            self.exited = False
        self.ready = True

    def first_input(self) -> bool:
        return self.ready and not self.exited


@dataclass
class DelayedClose:
    defective: bool
    parent_alive: bool = True

    def release_before_callback(self) -> bool:
        if not self.defective:
            return False
        self.parent_alive = False
        return True

    def run_callback(self) -> str:
        if not self.parent_alive:
            return "use-after-free"
        self.parent_alive = False
        return "closed-once"


def semantic_preflight(
    thesis_obligations: Iterable[str], scope_acceptance: Iterable[str]
) -> tuple[str, tuple[str, ...]]:
    missing = tuple(sorted(set(thesis_obligations) - set(scope_acceptance)))
    return ("contract-gap", missing) if missing else ("ready", ())


def implementation_frontier(*, artifact_only: bool, runtime_clues: Iterable[str]) -> tuple[str, ...]:
    clues = tuple(runtime_clues)
    return () if artifact_only and not clues else clues


def evidence_disposition(*, required_runtime_available: bool, contradiction_observed: bool) -> str:
    if contradiction_observed:
        return "FAILED"
    return "VERIFIED" if required_runtime_available else "INCONCLUSIVE"
