"""Global utilities for Medical Triage Assistant."""

from global_utils.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ServiceError,
)
from global_utils.web_app import run_on_startup, run_on_shutdown

__all__ = [
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "ServiceError",
    "run_on_startup",
    "run_on_shutdown",
]

