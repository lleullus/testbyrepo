from __future__ import annotations

from pathlib import Path
from durable_backend import DurableBackend
from durable_work import DurableWorkStore
from effect_observation import EffectObservationModule
from implementation_execution import ImplementationExecution
from implementation_verification import ImplementationVerificationModule
from production_adapters import (
    LinuxEvidenceRunnerAdapter,
    LinuxSourceAdoptionAdapter,
    LinuxTerraWorkerAdapter,
    OpenCodeFreshVerifierAdapter,
    OpenCodeImplementationReviewAdapter,
    OpenCodeRunner,
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
    opencode_executable: str | Path,
    *,
    timeout_seconds: float = 300,
) -> ImplementationVerificationModule:
    root = Path(state_root).expanduser().resolve(strict=False)
    runner = OpenCodeRunner(opencode_executable, timeout_seconds=timeout_seconds)

    return _compose_module(
        root,
        OpenCodeImplementationReviewAdapter(runner),
        LinuxTerraWorkerAdapter(),
        LinuxSourceAdoptionAdapter(),
        OpenCodeFreshVerifierAdapter(runner),
        LinuxEvidenceRunnerAdapter(),
        effect_observer=None,
    )
