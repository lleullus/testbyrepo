"""Web Comic Studio - Core Domain & Single Transactional Authority."""

from comic_new.composition import (
    CompositionError,
    CompositionRenderError,
    CompositionValidationError,
    RenderedArtifactBytes,
    SourceAssetError,
    TypographyError,
    normalize_state,
    render_canonical,
)
from comic_new.composition_service import (
    ArtifactNoLongerCurrentError,
    ArtifactReadbackError,
    CompositionService,
    CompositionServiceError,
    MaterializedArtifact,
)
from comic_new.generation import (
    CancelReceipt,
    EnqueueReceipt,
    GenerationRunner,
    GenerationService,
    RunReceipt,
    StopReceipt,
)
from comic_new.store import (
    AuthorizationRevokedError,
    ConflictError,
    InvalidArtifactClosureError,
    InvalidJobStateError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RealizationIncompleteError,
    RunnerAlreadyActiveError,
    StaleRealizationError,
    StoreCorruptionError,
    TransactionalStore,
    TransactionalStoreError,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "TransactionalStore",
    "TransactionalStoreError",
    "ConflictError",
    "StoreCorruptionError",
    "ProjectAlreadyExistsError",
    "ProjectNotFoundError",
    "RealizationIncompleteError",
    "InvalidArtifactClosureError",
    "AuthorizationRevokedError",
    "StaleRealizationError",
    "InvalidJobStateError",
    "ValidationError",
    "RunnerAlreadyActiveError",
    "GenerationService",
    "GenerationRunner",
    "EnqueueReceipt",
    "CancelReceipt",
    "StopReceipt",
    "RunReceipt",
    "CompositionService",
    "MaterializedArtifact",
    "RenderedArtifactBytes",
    "CompositionError",
    "CompositionValidationError",
    "CompositionRenderError",
    "SourceAssetError",
    "TypographyError",
    "CompositionServiceError",
    "ArtifactReadbackError",
    "ArtifactNoLongerCurrentError",
    "normalize_state",
    "render_canonical",
]
