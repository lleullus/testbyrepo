from __future__ import annotations

from pathlib import Path
from durable_backend import DurableBackend
from durable_work import DurableWorkStore
from effect_observation import EffectObservationModule
from implementation_execution import ImplementationExecution
from implementation_verification import ImplementationVerificationModule
from production_adapters import (
    LinuxEvidenceRunnerAdapter,
    LinuxFreshVerifierAdapter,
    LinuxImplementationReviewAdapter,
    LinuxSourceAdoptionAdapter,
    LinuxWorkerAdapter,
    ProcessImplementationCheck,
    ProcessImplementationReview,
    ProcessVerifier,
)
from verification_execution import ModuleExecution, VerificationExecution


ENABLED_PRODUCTION_EFFECT_ADAPTERS: tuple[str, ...] = ()


def _compose_module(
    root: Path,
    implementation_review_adapter,
    worker_adapter,
    adoption_adapter,
    fresh_verifier,
    runner,
    effect_observer: EffectObservationModule | None = None,
    implementation_effects=None,
) -> ImplementationVerificationModule:
    store = DurableWorkStore(root / "durable.sqlite3")
    implementation = ImplementationExecution(
        root,
        store,
        worker_adapter,
        adoption_adapter,
        implementation_review_adapter,
        implementation_effects,
        effect_observer,
    )
    verification = VerificationExecution(
        root,
        store,
        fresh_verifier,
        runner,
        implementation.observe_currentness,
        effect_observer,
    )
    execution = ModuleExecution(implementation, verification)
    return ImplementationVerificationModule(DurableBackend(store, execution))


def create_production_module(
    state_root: str | Path,
    verifier_argv: tuple[str, ...],
    implementation_review: ProcessImplementationReview,
    implementation_check: ProcessImplementationCheck,
) -> ImplementationVerificationModule:
    root = Path(state_root).expanduser().resolve(strict=False)
    if not isinstance(implementation_review, ProcessImplementationReview):
        raise TypeError("production implementation review must be ProcessImplementationReview")
    if not isinstance(implementation_check, ProcessImplementationCheck):
        raise TypeError("production implementation check must be ProcessImplementationCheck")

    return _compose_module(
        root,
        LinuxImplementationReviewAdapter(
            implementation_review,
            implementation_check,
            effect_adapter_enabled=bool(ENABLED_PRODUCTION_EFFECT_ADAPTERS),
        ),
        LinuxWorkerAdapter(),
        LinuxSourceAdoptionAdapter(),
        LinuxFreshVerifierAdapter(ProcessVerifier(verifier_argv)),
        LinuxEvidenceRunnerAdapter(),
        effect_observer=None,
    )
