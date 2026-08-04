from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Protocol


class CriterionOutcome(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNDETERMINED = "UNDETERMINED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNDETERMINED = "UNDETERMINED"


class Currentness(str, Enum):
    CURRENT = "CURRENT"
    NOT_CURRENT = "NOT_CURRENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Candidate:
    work: Path
    planning: object
    acceptance_criteria: tuple[object, ...]
    source: object
    implementation_changes: tuple[object, ...]
    preserved_changes: tuple[object, ...]
    result_identity: str | None = None

    @property
    def independent_verification_pending(self) -> bool:
        return True


@dataclass(frozen=True)
class ImplementationStopped:
    work: Path
    reason: str
    current_source: object


@dataclass(frozen=True)
class CriterionResult:
    criterion: object
    outcome: CriterionOutcome
    evidence: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        if self.outcome is not CriterionOutcome.UNDETERMINED and not self.evidence:
            raise ValueError("a conclusive criterion result requires independent evidence")


@dataclass(frozen=True, init=False)
class VerificationResult:
    candidate: Candidate
    criterion_results: tuple[CriterionResult, ...]
    status: VerificationStatus = field(init=False)
    result_identity: str | None = field(init=False)

    def __init__(
        self,
        candidate: Candidate,
        criterion_results: Iterable[CriterionResult],
        *,
        result_identity: str | None = None,
    ) -> None:
        results = tuple(criterion_results)
        if tuple(result.criterion for result in results) != candidate.acceptance_criteria:
            raise ValueError("verification must assess every exact acceptance criterion once")
        if any(result.outcome is CriterionOutcome.NOT_SATISFIED for result in results):
            status = VerificationStatus.NOT_SATISFIED
        elif any(result.outcome is CriterionOutcome.UNDETERMINED for result in results):
            status = VerificationStatus.UNDETERMINED
        else:
            status = VerificationStatus.VERIFIED
        object.__setattr__(self, "candidate", candidate)
        object.__setattr__(self, "criterion_results", results)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "result_identity", result_identity)


@dataclass(frozen=True)
class NoConclusiveResult:
    work: Path
    reason: str


PublicResult = Candidate | VerificationResult | NoConclusiveResult


@dataclass(frozen=True)
class Inspection:
    result: PublicResult
    currentness: Currentness


class _Backend(Protocol):
    def implement(self, work: Path, worker: object) -> Candidate | ImplementationStopped: ...

    def verify(self, candidate: Candidate) -> Iterable[CriterionResult]: ...

    def inspect(self, work: Path) -> Inspection: ...


def _canonical_work(work: str | Path) -> Path:
    path = Path(work).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("work must be an exact canonical ready Ticket file")
    return path


def _result_work(result: PublicResult) -> Path:
    if isinstance(result, VerificationResult):
        return result.candidate.work
    return result.work


class ImplementationVerificationModule:
    def __init__(self, backend: _Backend) -> None:
        self._backend = backend

    def implement(
        self,
        work: str | Path,
        worker: object,
    ) -> Candidate | ImplementationStopped:
        exact_work = _canonical_work(work)
        result = self._backend.implement(exact_work, worker)
        if result.work != exact_work:
            raise ValueError("implementation result differs from the requested work")
        return result

    def verify(self, candidate: Candidate) -> VerificationResult:
        return VerificationResult(candidate, self._backend.verify(candidate))

    def inspect(self, work: str | Path) -> Inspection:
        exact_work = _canonical_work(work)
        inspection = self._backend.inspect(exact_work)
        if _result_work(inspection.result) != exact_work:
            raise ValueError("inspection result differs from the requested work")
        return inspection
