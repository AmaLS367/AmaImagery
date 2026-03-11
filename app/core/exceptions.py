from __future__ import annotations

from typing import Any


class DomainException(Exception):
    """
    Base exception for domain errors.

    Provides structured error information with code, message, and optional details.
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class GenerationFailedException(DomainException):
    """
    Raised when image generation fails.

    Used when provider fails to generate an image or generation process encounters an error.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="generation_failed",
            message=message,
            details=details,
        )


class ProviderUnavailableException(DomainException):
    """
    Raised when a provider is unavailable or cannot be initialized.

    Used when provider registry cannot provide a requested provider or provider initialization fails.
    """

    def __init__(self, provider_name: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="provider_unavailable",
            message=f"Provider '{provider_name}' is unavailable",
            details={"provider": provider_name, **(details or {})},
        )


class RateLimitExceededException(DomainException):
    """
    Raised when rate limit is exceeded.

    Used when user or IP exceeds allowed request rate.
    """

    def __init__(self, retry_after: int | None = None, details: dict[str, Any] | None = None) -> None:
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(
            code="rate_limit_exceeded",
            message=message,
            details={"retry_after": retry_after, **(details or {})},
        )


class ValidationException(DomainException):
    """
    Raised when request validation fails.

    Used for business rule violations and invalid input data.
    """

    def __init__(self, message: str, field: str | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="validation_error",
            message=message,
            details={"field": field, **(details or {})},
        )


class AuthenticationException(DomainException):
    """
    Raised when authentication fails.

    Used for invalid credentials, expired tokens, or missing authentication.
    """

    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="authentication_failed",
            message=message,
            details=details,
        )


class ResourceNotFoundException(DomainException):
    """
    Raised when a requested resource is not found.

    Used for 404 errors when entity doesn't exist.
    """

    def __init__(
        self, resource_type: str, resource_id: str | None = None, details: dict[str, Any] | None = None
    ) -> None:
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            code="resource_not_found",
            message=message,
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})},
        )


class ConflictException(DomainException):
    """
    Raised when a resource conflict occurs.

    Used for 409 errors when resource already exists or state conflict.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="conflict",
            message=message,
            details=details,
        )


class TaskNotFoundException(DomainException):
    """
    Raised when a task is not found in the queue.

    Used when querying status of non-existent task.
    """

    def __init__(self, task_id: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="task_not_found",
            message=f"Task '{task_id}' not found",
            details={"task_id": task_id, **(details or {})},
        )


def map_exception_to_http(e: Exception) -> tuple[int, dict[str, Any]]:
    """
    Maps domain exceptions to HTTP status codes and response format.

    Returns tuple of (status_code, response_dict).
    Response format: {"error": {"code": "...", "message": "...", "details": {...}}}
    """
    if isinstance(e, DomainException):
        status_code = _get_status_code_for_domain_exception(e)
        return status_code, {
            "error": {
                "code": e.code,
                "message": e.message,
                "details": e.details,
            },
        }

    # Unknown exception - map to 500
    return 500, {
        "error": {
            "code": "internal_error",
            "message": "Internal server error",
            "details": {},
        },
    }


def _get_status_code_for_domain_exception(e: DomainException) -> int:
    """
    Maps domain exception codes to HTTP status codes.

    Returns appropriate HTTP status code based on exception type.
    """
    if isinstance(e, ValidationException):
        return 400
    if isinstance(e, AuthenticationException):
        return 401
    if isinstance(e, ResourceNotFoundException) or isinstance(e, TaskNotFoundException):
        return 404
    if isinstance(e, ConflictException):
        return 409
    if isinstance(e, RateLimitExceededException):
        return 429
    if isinstance(e, GenerationFailedException) or isinstance(e, ProviderUnavailableException):
        return 503

    # Default for unknown domain exceptions
    return 500
