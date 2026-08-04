from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from durable_work import DurableWorkError, DurableWorkStore, TransitionDisposition
from implementation_verification import (
    Candidate,
    CriterionResult,
    Currentness,
    ImplementationStopped,
    Inspection,
    PublicResult,
    VerificationResult,
)


class _Execution(Protocol):
    def preflight_implementation(self, work: Path) -> ImplementationStopped | None: ...

    def preflight_verification(self, candidate: Candidate) -> VerificationCompletion | None: ...

    def implement(
        self,
        work: Path,
        worker: object,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> (
        Candidate
        | ImplementationStopped
        | ImplementationCompletion
        | ImplementationPending
        | ImplementationStoppedCompletion
    ): ...

    def verify(
        self,
        candidate: Candidate,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> Iterable[CriterionResult] | VerificationCompletion: ...

    def observe_currentness(self, result: PublicResult) -> Currentness: ...


@dataclass(frozen=True)
class VerificationCompletion:
    criterion_results: tuple[CriterionResult, ...]
    unresolved_observations: tuple[object, ...] = ()
    resolved_observation_identities: tuple[str, ...] = ()
    effect_safety_projections: tuple[object, ...] = ()
    publication_safe: bool = True


@dataclass(frozen=True)
class ImplementationCompletion:
    candidate: Candidate
    resolved_observation_identities: tuple[str, ...] = ()
    effect_safety_projections: tuple[object, ...] = ()


@dataclass(frozen=True)
class ImplementationPending:
    stopped: ImplementationStopped


@dataclass(frozen=True)
class ImplementationStoppedCompletion:
    stopped: ImplementationStopped
    resolved_observation_identities: tuple[str, ...] = ()
    effect_safety_projections: tuple[object, ...] = ()


def _worker_identity(worker: object) -> str:
    if isinstance(worker, str) and worker:
        return worker
    identity = getattr(worker, "durable_identity", None)
    if isinstance(identity, str) and identity:
        return identity
    raise ValueError("worker must expose one stable durable identity")


class DurableBackend:
    def __init__(self, store: DurableWorkStore, execution: _Execution) -> None:
        self._store = store
        self._execution = execution

    def _begin(
        self,
        work: Path,
        kind: str,
        semantic_input: object,
        *,
        exclude_completed_result_ref: str | None = None,
    ):
        while True:
            decision = self._store.begin(
                work,
                kind,
                semantic_input,
                f"progress:{uuid.uuid4().hex}",
                exclude_completed_result_ref=exclude_completed_result_ref,
            )
            if decision.disposition is not TransitionDisposition.BUSY:
                return decision
            while True:
                state = self._store.transition_state(decision.transition_identity)
                if state is None:
                    raise DurableWorkError("competing transition disappeared")
                if state["state"] != "ACTIVE":
                    break
                time.sleep(0.01)

    def implement(
        self,
        work: Path,
        worker: object,
    ) -> Candidate | ImplementationStopped:
        stopped = self._execution.preflight_implementation(work)
        if stopped is not None:
            return stopped
        semantic_input = {"worker": _worker_identity(worker)}
        excluded_result_ref = None
        while True:
            decision = self._begin(
                work,
                "IMPLEMENT",
                semantic_input,
                exclude_completed_result_ref=excluded_result_ref,
            )
            if decision.disposition is not TransitionDisposition.COMPLETED:
                break
            if not isinstance(decision.result, Candidate):
                raise DurableWorkError("completed implementation has no Candidate")
            try:
                currentness = self._execution.observe_currentness(decision.result)
            except DurableWorkError:
                currentness = Currentness.UNKNOWN
            if currentness is Currentness.CURRENT:
                return decision.result
            if decision.result.result_identity is None:
                raise DurableWorkError("completed Candidate has no durable identity")
            excluded_result_ref = decision.result.result_identity
        result = self._execution.implement(
            work,
            worker,
            decision.transition_identity,
            reenter=decision.disposition is TransitionDisposition.REENTER,
        )
        if isinstance(result, ImplementationPending):
            return result.stopped
        if isinstance(result, ImplementationStoppedCompletion):
            self._store.close_without_result(
                decision.transition_identity,
                private_safety={
                    "unresolvedObservations": [],
                    "resolvedObservationIdentities": list(
                        result.resolved_observation_identities
                    ),
                    "effectSafetyProjections": list(result.effect_safety_projections),
                },
            )
            return result.stopped
        if isinstance(result, ImplementationStopped):
            self._store.close_without_result(decision.transition_identity)
            return result
        if isinstance(result, ImplementationCompletion):
            candidate = result.candidate
            private_state = {
                "unresolvedObservations": [],
                "resolvedObservationIdentities": list(
                    result.resolved_observation_identities
                ),
                "effectSafetyProjections": list(result.effect_safety_projections),
            }
        else:
            candidate = result
            private_state = None
        published = self._store.publish(
            decision.transition_identity,
            candidate,
            private_state=private_state,
        )
        if not isinstance(published, Candidate):
            raise DurableWorkError("implementation published a non-Candidate result")
        return published

    def verify(self, candidate: Candidate) -> VerificationResult:
        if candidate.result_identity is None:
            raise ValueError("verify requires a durable Candidate")
        preflight = self._execution.preflight_verification(candidate)
        if preflight is not None and not preflight.publication_safe:
            return VerificationResult(candidate, preflight.criterion_results)
        durable_candidate = self._store.read_candidate(candidate.result_identity)
        if durable_candidate != candidate:
            raise ValueError("verify requires the exact durable Candidate")
        decision = self._begin(
            candidate.work,
            "VERIFY",
            {"candidate": candidate.result_identity},
        )
        if decision.disposition is TransitionDisposition.COMPLETED:
            if not isinstance(decision.result, VerificationResult):
                raise DurableWorkError("completed verification has no VerificationResult")
            return decision.result
        completion = preflight or self._execution.verify(
            candidate,
            decision.transition_identity,
            reenter=decision.disposition is TransitionDisposition.REENTER,
        )
        if isinstance(completion, VerificationCompletion):
            criterion_results = completion.criterion_results
            private_state = {
                "unresolvedObservations": list(completion.unresolved_observations),
                "resolvedObservationIdentities": list(
                    completion.resolved_observation_identities
                ),
                "effectSafetyProjections": list(completion.effect_safety_projections),
            }
        else:
            criterion_results = tuple(completion)
            private_state = {
                "unresolvedObservations": [],
                "resolvedObservationIdentities": [],
                "effectSafetyProjections": [],
            }
        result = VerificationResult(candidate, criterion_results)
        published = self._store.publish(
            decision.transition_identity,
            result,
            private_state=private_state,
        )
        if not isinstance(published, VerificationResult):
            raise DurableWorkError("verification published a non-verification result")
        return published

    def inspect(self, work: Path) -> Inspection:
        return self._store.inspect(work, self._execution.observe_currentness)
