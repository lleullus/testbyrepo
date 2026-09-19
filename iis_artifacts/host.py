"""Trusted host API.

Strong enforcement lives in `iis_artifacts.supervisor.HostSupervisor`. This module
exports host-facing names only and intentionally exposes no helper that lets a
worker mark a review complete.
"""
from .supervisor import (
    HostBoundaryError,
    HostIntegrationUnavailable,
    HostSupervisor,
    SupervisorClient,
)

__all__ = [
    "HostBoundaryError",
    "HostIntegrationUnavailable",
    "HostSupervisor",
    "SupervisorClient",
]
