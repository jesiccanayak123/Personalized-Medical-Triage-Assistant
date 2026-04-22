"""Custom exceptions for Medical Triage Assistant."""

from typing import Optional, Any, Dict

from config.logging import logger


class AppException(Exception):
    """Base exception for all application errors."""
    
    DEFAULT_MESSAGE = "An error occurred"
    STATUS_CODE = 500

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message or self.DEFAULT_MESSAGE
        self.status_code = status_code or self.STATUS_CODE
        self.details = details or {}
        super().__init__(self.message)
        
        logger.warning(
            f"AppException: {self.__class__.__name__}",
            message=self.message,
            status_code=self.status_code,
            details=self.details,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "success": False,
            "error": {
                "type": self.__class__.__name__,
                "message": self.message,
                "details": self.details,
            }
        }


class AuthenticationError(AppException):
    """Authentication failed (401)."""
    
    DEFAULT_MESSAGE = "Authentication required"
    STATUS_CODE = 401


class AuthorizationError(AppException):
    """Authorization failed (403)."""
    
    DEFAULT_MESSAGE = "Access denied"
    STATUS_CODE = 403


class NotFoundError(AppException):
    """Resource not found (404)."""
    
    DEFAULT_MESSAGE = "Resource not found"
    STATUS_CODE = 404


class ValidationError(AppException):
    """Validation error (400)."""
    
    DEFAULT_MESSAGE = "Validation error"
    STATUS_CODE = 400


class ConflictError(AppException):
    """Resource conflict (409)."""
    
    DEFAULT_MESSAGE = "Resource conflict"
    STATUS_CODE = 409


class ServiceError(AppException):
    """Internal service error (500)."""
    
    DEFAULT_MESSAGE = "Internal service error"
    STATUS_CODE = 500


class RateLimitError(AppException):
    """Rate limit exceeded (429)."""
    
    DEFAULT_MESSAGE = "Rate limit exceeded"
    STATUS_CODE = 429


class ExternalServiceError(AppException):
    """External service error (502)."""
    
    DEFAULT_MESSAGE = "External service error"
    STATUS_CODE = 502

