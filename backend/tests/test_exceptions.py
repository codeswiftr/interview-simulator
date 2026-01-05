"""Tests for structured exception classes.

Tests error codes, exception initialization, and response formatting.
"""

import pytest

from app.exceptions import (
    AIServiceError,
    AppError,
    AuthExpiredError,
    AuthInvalidError,
    AuthRequiredError,
    ErrorCode,
    FileTooLargeError,
    InterviewAlreadyCompleteError,
    InterviewNotStartedError,
    InvalidFileTypeError,
    InvalidStateError,
    NoFeedbackAvailableError,
    PlanUpgradeRequiredError,
    QuotaExceededError,
    RateLimitedError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    StorageError,
    TranscriptionError,
    UploadFailedError,
    ValidationError,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_auth_error_codes_exist(self):
        """Test authentication error codes exist."""
        assert ErrorCode.AUTH_REQUIRED.value == "auth_required"
        assert ErrorCode.AUTH_INVALID.value == "auth_invalid"
        assert ErrorCode.AUTH_EXPIRED.value == "auth_expired"

    def test_quota_error_codes_exist(self):
        """Test quota error codes exist."""
        assert ErrorCode.QUOTA_EXCEEDED.value == "quota_exceeded"
        assert ErrorCode.RATE_LIMITED.value == "rate_limited"
        assert ErrorCode.SUBSCRIPTION_REQUIRED.value == "subscription_required"

    def test_resource_error_codes_exist(self):
        """Test resource error codes exist."""
        assert ErrorCode.NOT_FOUND.value == "not_found"
        assert ErrorCode.ALREADY_EXISTS.value == "already_exists"
        assert ErrorCode.VALIDATION_ERROR.value == "validation_error"

    def test_file_error_codes_exist(self):
        """Test file error codes exist."""
        assert ErrorCode.FILE_TOO_LARGE.value == "file_too_large"
        assert ErrorCode.INVALID_FILE_TYPE.value == "invalid_file_type"
        assert ErrorCode.UPLOAD_FAILED.value == "upload_failed"


class TestAppError:
    """Tests for base AppError class."""

    def test_creates_with_required_fields(self):
        """Test creates exception with required fields."""
        error = AppError(
            error_code=ErrorCode.BAD_REQUEST,
            message="Something went wrong",
        )

        assert error.error_code == ErrorCode.BAD_REQUEST
        assert error.message == "Something went wrong"
        assert error.status_code == 400
        assert error.details == {}

    def test_creates_with_optional_fields(self):
        """Test creates exception with optional fields."""
        error = AppError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Server error",
            status_code=500,
            details={"trace_id": "abc123"},
        )

        assert error.status_code == 500
        assert error.details["trace_id"] == "abc123"

    def test_to_dict_format(self):
        """Test to_dict returns proper API format."""
        error = AppError(
            error_code=ErrorCode.BAD_REQUEST,
            message="Invalid request",
        )

        result = error.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "bad_request"
        assert result["error"]["message"] == "Invalid request"

    def test_to_dict_includes_details(self):
        """Test to_dict includes details when present."""
        error = AppError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Invalid field",
            details={"field": "email"},
        )

        result = error.to_dict()

        assert "details" in result["error"]
        assert result["error"]["details"]["field"] == "email"

    def test_inherits_from_exception(self):
        """Test can be raised as exception."""
        error = AppError(ErrorCode.BAD_REQUEST, "Test error")

        with pytest.raises(AppError) as exc_info:
            raise error

        assert exc_info.value.message == "Test error"


class TestAuthErrors:
    """Tests for authentication error classes."""

    def test_auth_required_defaults(self):
        """Test AuthRequiredError with defaults."""
        error = AuthRequiredError()
        assert error.error_code == ErrorCode.AUTH_REQUIRED
        assert error.status_code == 401
        assert "Authentication required" in error.message

    def test_auth_required_custom_message(self):
        """Test AuthRequiredError with custom message."""
        error = AuthRequiredError("Please log in first")
        assert error.message == "Please log in first"

    def test_auth_invalid_defaults(self):
        """Test AuthInvalidError with defaults."""
        error = AuthInvalidError()
        assert error.error_code == ErrorCode.AUTH_INVALID
        assert error.status_code == 401

    def test_auth_expired_defaults(self):
        """Test AuthExpiredError with defaults."""
        error = AuthExpiredError()
        assert error.error_code == ErrorCode.AUTH_EXPIRED
        assert "expired" in error.message.lower()


class TestQuotaErrors:
    """Tests for quota and subscription error classes."""

    def test_quota_exceeded_with_details(self):
        """Test QuotaExceededError includes limit details."""
        error = QuotaExceededError(limit=5, used=5, plan="free")

        assert error.error_code == ErrorCode.QUOTA_EXCEEDED
        assert error.status_code == 403
        assert error.details["limit"] == 5
        assert error.details["used"] == 5
        assert error.details["remaining"] == 0
        assert error.details["plan"] == "free"

    def test_quota_exceeded_calculates_remaining(self):
        """Test QuotaExceededError calculates remaining correctly."""
        error = QuotaExceededError(limit=10, used=7)
        assert error.details["remaining"] == 3

    def test_plan_upgrade_required(self):
        """Test PlanUpgradeRequiredError includes feature details."""
        error = PlanUpgradeRequiredError(
            feature="Unlimited interviews",
            required_plan="pro",
            current_plan="free",
        )

        assert error.error_code == ErrorCode.PLAN_UPGRADE_REQUIRED
        assert error.status_code == 403
        assert error.details["feature"] == "Unlimited interviews"
        assert error.details["required_plan"] == "pro"
        assert error.details["upgrade_url"] == "/pricing"

    def test_rate_limited_with_retry_after(self):
        """Test RateLimitedError includes retry_after."""
        error = RateLimitedError(retry_after=60)

        assert error.error_code == ErrorCode.RATE_LIMITED
        assert error.status_code == 429
        assert error.details["retry_after_seconds"] == 60

    def test_rate_limited_without_retry_after(self):
        """Test RateLimitedError works without retry_after."""
        error = RateLimitedError()
        assert error.details == {}


class TestResourceErrors:
    """Tests for resource error classes."""

    def test_resource_not_found_with_id(self):
        """Test ResourceNotFoundError includes resource details."""
        error = ResourceNotFoundError("Interview", "abc-123")

        assert error.error_code == ErrorCode.NOT_FOUND
        assert error.status_code == 404
        assert error.details["resource_type"] == "Interview"
        assert error.details["resource_id"] == "abc-123"

    def test_resource_not_found_without_id(self):
        """Test ResourceNotFoundError works without ID."""
        error = ResourceNotFoundError("User")
        assert error.details["resource_id"] is None

    def test_resource_already_exists(self):
        """Test ResourceAlreadyExistsError."""
        error = ResourceAlreadyExistsError("User", "email@example.com")

        assert error.error_code == ErrorCode.ALREADY_EXISTS
        assert error.status_code == 409
        assert error.details["identifier"] == "email@example.com"

    def test_validation_error_with_field(self):
        """Test ValidationError with field."""
        error = ValidationError(field="password")

        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.status_code == 422
        assert error.details["field"] == "password"

    def test_validation_error_with_details(self):
        """Test ValidationError with custom details."""
        error = ValidationError(
            message="Multiple validation errors",
            details={"errors": [{"field": "email", "msg": "invalid"}]},
        )
        assert "errors" in error.details

    def test_invalid_state_error(self):
        """Test InvalidStateError."""
        error = InvalidStateError(
            resource_type="Interview",
            current_state="completed",
            required_state="in_progress",
        )

        assert error.error_code == ErrorCode.INVALID_STATE
        assert error.status_code == 409
        assert error.details["current_state"] == "completed"
        assert error.details["required_state"] == "in_progress"


class TestFileErrors:
    """Tests for file and upload error classes."""

    def test_file_too_large(self):
        """Test FileTooLargeError."""
        error = FileTooLargeError(max_size_mb=25, actual_size_mb=30.5)

        assert error.error_code == ErrorCode.FILE_TOO_LARGE
        assert error.status_code == 413
        assert error.details["max_size_mb"] == 25
        assert error.details["actual_size_mb"] == 30.5

    def test_invalid_file_type(self):
        """Test InvalidFileTypeError."""
        error = InvalidFileTypeError(
            file_type="exe",
            allowed_types=["mp3", "wav", "webm"],
        )

        assert error.error_code == ErrorCode.INVALID_FILE_TYPE
        assert error.status_code == 415
        assert error.details["file_type"] == "exe"
        assert "mp3" in error.details["allowed_types"]

    def test_upload_failed(self):
        """Test UploadFailedError."""
        error = UploadFailedError(reason="Storage unavailable")

        assert error.error_code == ErrorCode.UPLOAD_FAILED
        assert error.status_code == 500
        assert error.details["reason"] == "Storage unavailable"


class TestExternalServiceErrors:
    """Tests for external service error classes."""

    def test_transcription_error(self):
        """Test TranscriptionError."""
        error = TranscriptionError(provider="whisper")

        assert error.error_code == ErrorCode.TRANSCRIPTION_FAILED
        assert error.status_code == 502
        assert error.details["provider"] == "whisper"

    def test_ai_service_error(self):
        """Test AIServiceError."""
        error = AIServiceError(service="claude")

        assert error.error_code == ErrorCode.AI_SERVICE_UNAVAILABLE
        assert error.status_code == 503
        assert error.details["service"] == "claude"

    def test_storage_error(self):
        """Test StorageError."""
        error = StorageError(operation="upload")

        assert error.error_code == ErrorCode.STORAGE_ERROR
        assert error.status_code == 500
        assert error.details["operation"] == "upload"


class TestInterviewErrors:
    """Tests for interview-specific error classes."""

    def test_interview_not_started(self):
        """Test InterviewNotStartedError."""
        error = InterviewNotStartedError(interview_id="abc-123")

        assert error.error_code == ErrorCode.INTERVIEW_NOT_STARTED
        assert error.status_code == 409
        assert error.details["interview_id"] == "abc-123"

    def test_interview_already_complete(self):
        """Test InterviewAlreadyCompleteError."""
        error = InterviewAlreadyCompleteError(interview_id="xyz-789")

        assert error.error_code == ErrorCode.INTERVIEW_ALREADY_COMPLETE
        assert error.status_code == 409
        assert "cannot be modified" in error.message

    def test_no_feedback_available(self):
        """Test NoFeedbackAvailableError."""
        error = NoFeedbackAvailableError(interview_id="test-id")

        assert error.error_code == ErrorCode.NO_FEEDBACK_AVAILABLE
        assert error.status_code == 404
        assert "not yet available" in error.message
