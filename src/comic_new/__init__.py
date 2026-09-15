"""Web Comic Studio - Core Domain & Single Transactional Authority."""

from comic_new.store import (
    AuthorizationRevokedError,
    ConflictError,
    InvalidArtifactClosureError,
    InvalidJobStateError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RealizationIncompleteError,
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
]
