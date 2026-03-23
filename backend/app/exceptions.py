"""Structured exception classes for Interview Simulator API.

These exceptions provide consistent error responses across the API with:
- Machine-readable error codes
- User-friendly messages
- HTTP status code mapping
- Optional additional context

Usage:
    from app.exceptions import ResourceNotFoundError, QuotaExceededError

    # Raise structured error
    raise ResourceNotFoundError("Interview", interview_id)

    # Raise with custom message
    raise QuotaExceededError(limit=5, used=5, plan="free")
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Machine-readable error codes for API responses."""

    # Authentication & Authorization
    AUTH_REQUIRED = "auth_required"
    AUTH_INVALID = "auth_invalid"
    AUTH_EXPIRED = "auth_expired"
    SUBSCRIPTION_REQUIRED = "subscription_required"
    PLAN_UPGRADE_REQUIRED = "plan_upgrade_required"

    # Quota & Usage
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"

    # Resource errors
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    VALIDATION_ERROR = "validation_error"
    INVALID_STATE = "invalid_state"

    # File & Upload errors
    FILE_TOO_LARGE = "file_too_large"
    INVALID_FILE_TYPE = "invalid_file_type"
    UPLOAD_FAILED = "upload_failed"

    # External service errors
    TRANSCRIPTION_FAILED = "transcription_failed"
    AI_SERVICE_UNAVAILABLE = "ai_service_unavailable"
    STORAGE_ERROR = "storage_error"

    # Interview-specific errors
    INTERVIEW_NOT_STARTED = "interview_not_started"
    INTERVIEW_ALREADY_COMPLETE = "interview_already_complete"
    NO_FEEDBACK_AVAILABLE = "no_feedback_available"

    # General errors
    INTERNAL_ERROR = "internal_error"
    BAD_REQUEST = "bad_request"


class AppError(Exception):
    """Base exception for application-level errors.

    Provides structured error responses with:
    - error_code: Machine-readable code for client handling
    - message: Human-readable error message
    - status_code: HTTP status code
    - details: Optional additional context

    Example usage:
        raise AppError(
            error_code=ErrorCode.QUOTA_EXCEEDED,
            message="Monthly interview limit reached",
            status_code=403,
            details={"limit": 5, "used": 5}
        )
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response format."""
        response = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


# Authentication Errors


class AuthRequiredError(AppError):
    """Raised when authentication is required but not provided."""

    def __init__(self, message: str | None = None):
        super().__init__(
            error_code=ErrorCode.AUTH_REQUIRED,
            message=message or "Authentication required",
            status_code=401,
        )


class AuthInvalidError(AppError):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str | None = None):
        super().__init__(
            error_code=ErrorCode.AUTH_INVALID,
            message=message or "Invalid credentials",
            status_code=401,
        )


class AuthExpiredError(AppError):
    """Raised when authentication token has expired."""

    def __init__(self, message: str | None = None):
        super().__init__(
            error_code=ErrorCode.AUTH_EXPIRED,
            message=message or "Authentication expired. Please log in again.",
            status_code=401,
        )


# Quota & Subscription Errors


class QuotaExceededError(AppError):
    """Raised when user exceeds their interview quota."""

    def __init__(
        self,
        limit: int,
        used: int,
        plan: str = "free",
        message: str | None = None,
    ):
        self.limit = limit
        self.used = used
        self.plan = plan
        super().__init__(
            error_code=ErrorCode.QUOTA_EXCEEDED,
            message=message
            or f"Interview limit reached. {plan.title()} plan: {limit} interviews/month. Upgrade to Pro for unlimited.",
            status_code=403,
            details={
                "limit": limit,
                "used": used,
                "remaining": max(0, limit - used),
                "plan": plan,
            },
        )


class PlanUpgradeRequiredError(AppError):
    """Raised when feature requires a higher subscription tier."""

    def __init__(
        self,
        feature: str,
        required_plan: str = "pro",
        current_plan: str = "free",
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.PLAN_UPGRADE_REQUIRED,
            message=message
            or f"{feature} requires {required_plan.title()} plan. Upgrade to access this feature.",
            status_code=403,
            details={
                "feature": feature,
                "required_plan": required_plan,
                "current_plan": current_plan,
                "upgrade_url": "/pricing",
            },
        )


class RateLimitedError(AppError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        retry_after: int | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.RATE_LIMITED,
            message=message or "Too many requests. Please wait before trying again.",
            status_code=429,
            details={"retry_after_seconds": retry_after} if retry_after else {},
        )


# Resource Errors


class ResourceNotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message or f"{resource_type} not found",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
            },
        )


class ResourceAlreadyExistsError(AppError):
    """Raised when trying to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str,
        identifier: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.ALREADY_EXISTS,
            message=message or f"{resource_type} already exists",
            status_code=409,
            details={
                "resource_type": resource_type,
                "identifier": identifier,
            },
        )


class ValidationError(AppError):
    """Raised when request validation fails."""

    def __init__(
        self,
        field: str | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message or f"Validation error{f' for {field}' if field else ''}",
            status_code=422,
            details=details or ({"field": field} if field else {}),
        )


class InvalidStateError(AppError):
    """Raised when operation is invalid for current resource state."""

    def __init__(
        self,
        resource_type: str,
        current_state: str,
        required_state: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.INVALID_STATE,
            message=message or f"{resource_type} is in invalid state: {current_state}",
            status_code=409,
            details={
                "resource_type": resource_type,
                "current_state": current_state,
                "required_state": required_state,
            },
        )


# File & Upload Errors


class FileTooLargeError(AppError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(
        self,
        max_size_mb: int,
        actual_size_mb: float | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.FILE_TOO_LARGE,
            message=message or f"File too large. Maximum size is {max_size_mb}MB.",
            status_code=413,
            details={
                "max_size_mb": max_size_mb,
                "actual_size_mb": actual_size_mb,
            },
        )


class InvalidFileTypeError(AppError):
    """Raised when uploaded file type is not allowed."""

    def __init__(
        self,
        file_type: str | None = None,
        allowed_types: list[str] | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.INVALID_FILE_TYPE,
            message=message or "Invalid file type",
            status_code=415,
            details={
                "file_type": file_type,
                "allowed_types": allowed_types or [],
            },
        )


class UploadFailedError(AppError):
    """Raised when file upload fails."""

    def __init__(
        self,
        reason: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.UPLOAD_FAILED,
            message=message or "File upload failed. Please try again.",
            status_code=500,
            details={"reason": reason} if reason else {},
        )


# External Service Errors


class TranscriptionError(AppError):
    """Raised when audio transcription fails."""

    def __init__(
        self,
        provider: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.TRANSCRIPTION_FAILED,
            message=message or "Failed to transcribe audio. Please try again.",
            status_code=502,
            details={"provider": provider} if provider else {},
        )


class AIServiceError(AppError):
    """Raised when AI feedback service is unavailable."""

    def __init__(
        self,
        service: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message=message or "AI feedback service temporarily unavailable.",
            status_code=503,
            details={
                "service": service,
            }
            if service
            else {},
        )


class StorageError(AppError):
    """Raised when storage operations fail."""

    def __init__(
        self,
        operation: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.STORAGE_ERROR,
            message=message or f"Storage {operation or 'operation'} failed",
            status_code=500,
            details={"operation": operation} if operation else {},
        )


# Interview-Specific Errors


class InterviewNotStartedError(AppError):
    """Raised when trying to access an interview that hasn't started."""

    def __init__(
        self,
        interview_id: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.INTERVIEW_NOT_STARTED,
            message=message or "Interview has not been started yet",
            status_code=409,
            details={"interview_id": str(interview_id)} if interview_id else {},
        )


class InterviewAlreadyCompleteError(AppError):
    """Raised when trying to modify a completed interview."""

    def __init__(
        self,
        interview_id: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.INTERVIEW_ALREADY_COMPLETE,
            message=message or "Interview is already complete and cannot be modified",
            status_code=409,
            details={"interview_id": str(interview_id)} if interview_id else {},
        )


class NoFeedbackAvailableError(AppError):
    """Raised when feedback is requested but not yet available."""

    def __init__(
        self,
        interview_id: str | None = None,
        message: str | None = None,
    ):
        super().__init__(
            error_code=ErrorCode.NO_FEEDBACK_AVAILABLE,
            message=message or "Feedback is not yet available for this interview",
            status_code=404,
            details={"interview_id": str(interview_id)} if interview_id else {},
        )


__all__ = [
    "ErrorCode",
    "AppError",
    # Auth errors
    "AuthRequiredError",
    "AuthInvalidError",
    "AuthExpiredError",
    # Quota errors
    "QuotaExceededError",
    "PlanUpgradeRequiredError",
    "RateLimitedError",
    # Resource errors
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ValidationError",
    "InvalidStateError",
    # File errors
    "FileTooLargeError",
    "InvalidFileTypeError",
    "UploadFailedError",
    # External service errors
    "TranscriptionError",
    "AIServiceError",
    "StorageError",
    # Interview errors
    "InterviewNotStartedError",
    "InterviewAlreadyCompleteError",
    "NoFeedbackAvailableError",
]
