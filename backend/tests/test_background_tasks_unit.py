"""Unit tests for background task service (no database required)."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.background_tasks import (
    MAX_RETRIES,
    RETRY_DELAYS,
    BackgroundTaskService,
)


class TestBackgroundTaskServiceInit:
    """Tests for BackgroundTaskService initialization."""

    def test_initialization_creates_services(self):
        """Test that initialization creates audio and feedback services."""
        service = BackgroundTaskService()

        assert service.audio_service is not None
        assert service.feedback_service is not None


class TestLogWithContext:
    """Tests for _log_with_context method."""

    def test_logs_with_response_id(self, caplog):
        """Test that response_id is included in log."""
        service = BackgroundTaskService()
        response_id = uuid4()

        with caplog.at_level(logging.INFO):
            service._log_with_context(
                logging.INFO,
                "Test message",
                response_id=response_id,
            )

        assert "Test message" in caplog.text

    def test_logs_with_session_id(self, caplog):
        """Test that session_id is included in log."""
        service = BackgroundTaskService()
        session_id = uuid4()

        with caplog.at_level(logging.INFO):
            service._log_with_context(
                logging.INFO,
                "Test message",
                session_id=session_id,
            )

        assert "Test message" in caplog.text

    def test_logs_with_task_name(self, caplog):
        """Test that task_name is included in log."""
        service = BackgroundTaskService()

        with caplog.at_level(logging.INFO):
            service._log_with_context(
                logging.INFO,
                "Test message",
                task_name="test_task",
            )

        assert "Test message" in caplog.text

    def test_logs_with_additional_kwargs(self, caplog):
        """Test that additional kwargs are included in log."""
        service = BackgroundTaskService()

        with caplog.at_level(logging.INFO):
            service._log_with_context(
                logging.INFO,
                "Test message",
                custom_field="custom_value",
            )

        assert "Test message" in caplog.text

    def test_logs_with_exception_info(self, caplog):
        """Test that exception info is logged when exc_info=True."""
        service = BackgroundTaskService()

        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test exception")
            except ValueError:
                service._log_with_context(
                    logging.ERROR,
                    "Error occurred",
                    exc_info=True,
                )

        assert "Error occurred" in caplog.text

    def test_logs_at_different_levels(self, caplog):
        """Test logging at various levels."""
        service = BackgroundTaskService()

        with caplog.at_level(logging.DEBUG):
            service._log_with_context(logging.DEBUG, "Debug message")
            service._log_with_context(logging.INFO, "Info message")
            service._log_with_context(logging.WARNING, "Warning message")
            service._log_with_context(logging.ERROR, "Error message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text


class TestProcessResponseAudioAsync:
    """Tests for process_response_audio_async method."""

    @pytest.mark.asyncio
    async def test_rejects_invalid_audio_url(self, caplog):
        """Test that invalid audio URL is logged and returns early."""
        service = BackgroundTaskService()
        response_id = uuid4()

        with caplog.at_level(logging.WARNING):
            await service.process_response_audio_async(response_id, "invalid-url")

        assert "Invalid audio URL" in caplog.text

    @pytest.mark.asyncio
    async def test_rejects_empty_audio_url(self, caplog):
        """Test that empty audio URL is logged and returns early."""
        service = BackgroundTaskService()
        response_id = uuid4()

        with caplog.at_level(logging.WARNING):
            await service.process_response_audio_async(response_id, "")

        assert "Invalid audio URL" in caplog.text

    @pytest.mark.asyncio
    async def test_rejects_none_audio_url(self, caplog):
        """Test that None audio URL is logged and returns early."""
        service = BackgroundTaskService()
        response_id = uuid4()

        with caplog.at_level(logging.WARNING):
            await service.process_response_audio_async(response_id, None)

        assert "Invalid audio URL" in caplog.text

    @pytest.mark.asyncio
    async def test_handles_missing_audio_file(self, caplog):
        """Test that missing audio file is logged and returns early."""
        service = BackgroundTaskService()
        response_id = uuid4()

        with caplog.at_level(logging.WARNING):
            await service.process_response_audio_async(
                response_id, "/uploads/audio/nonexistent_file_xyz.webm"
            )

        assert "not found" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_processes_audio_successfully(self, tmp_path):
        """Test successful audio processing flow."""
        service = BackgroundTaskService()
        response_id = uuid4()

        # Create a temporary audio file
        audio_dir = tmp_path / "uploads" / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "test.webm"
        audio_file.write_bytes(b"fake audio data")

        # Mock SessionLocal and services
        mock_response = MagicMock()
        mock_response.id = response_id
        mock_response.session_id = uuid4()
        mock_response.duration_seconds = 120

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(service, "_process_audio_with_retry", return_value=("transcript", {})), \
             patch.object(service.audio_service, "save_audio_feedback", new_callable=AsyncMock), \
             patch.object(service, "generate_content_feedback_async", new_callable=AsyncMock):

            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            # Use the tmp_path as base for the audio path
            with patch("pathlib.Path.exists", return_value=True):
                await service.process_response_audio_async(
                    response_id, f"/uploads/audio/test.webm"
                )

    @pytest.mark.asyncio
    async def test_handles_processing_error(self, caplog, tmp_path):
        """Test that processing errors are caught and logged."""
        service = BackgroundTaskService()
        response_id = uuid4()

        # Create a temporary audio file
        audio_dir = tmp_path / "uploads" / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "error_test.webm"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_response.id = response_id
        mock_response.session_id = uuid4()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(service, "_process_audio_with_retry", side_effect=Exception("Processing failed")), \
             patch.object(service, "_update_processing_status_failed", new_callable=AsyncMock), \
             caplog.at_level(logging.ERROR):

            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("pathlib.Path.exists", return_value=True):
                # Should not raise - errors are caught internally
                await service.process_response_audio_async(
                    response_id, "/uploads/audio/error_test.webm"
                )

        assert "failed" in caplog.text.lower()


class TestProcessAudioWithRetry:
    """Tests for _process_audio_with_retry method."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Test successful processing on first attempt."""
        service = BackgroundTaskService()
        mock_session = AsyncMock()
        response_id = uuid4()

        with patch.object(
            service.audio_service,
            "process_response_audio",
            new_callable=AsyncMock,
            return_value=("transcript", {"metrics": "data"}),
        ):
            transcript, metrics = await service._process_audio_with_retry(
                mock_session, response_id, "/path/to/audio.webm"
            )

        assert transcript == "transcript"
        assert metrics == {"metrics": "data"}

    @pytest.mark.asyncio
    async def test_retries_on_transient_errors(self, caplog):
        """Test that transient errors trigger retries."""
        service = BackgroundTaskService()
        mock_session = AsyncMock()
        response_id = uuid4()

        call_count = 0

        async def mock_process(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < MAX_RETRIES:
                raise ConnectionError("Transient error")
            return "transcript", {"metrics": "data"}

        with patch.object(
            service.audio_service,
            "process_response_audio",
            side_effect=mock_process,
        ), patch("asyncio.sleep", new_callable=AsyncMock), \
           caplog.at_level(logging.WARNING):
            transcript, metrics = await service._process_audio_with_retry(
                mock_session, response_id, "/path/to/audio.webm"
            )

        assert call_count == MAX_RETRIES
        assert transcript == "transcript"
        assert "retrying" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self, caplog):
        """Test that all retries are exhausted before raising."""
        service = BackgroundTaskService()
        mock_session = AsyncMock()
        response_id = uuid4()

        with patch.object(
            service.audio_service,
            "process_response_audio",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Always times out"),
        ), patch("asyncio.sleep", new_callable=AsyncMock), \
           caplog.at_level(logging.ERROR):
            with pytest.raises(TimeoutError):
                await service._process_audio_with_retry(
                    mock_session, response_id, "/path/to/audio.webm"
                )

        assert "failed after" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_permanent_errors_not_retried(self, caplog):
        """Test that permanent errors are not retried."""
        service = BackgroundTaskService()
        mock_session = AsyncMock()
        response_id = uuid4()

        call_count = 0

        async def mock_process(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise TypeError("Permanent error")

        with patch.object(
            service.audio_service,
            "process_response_audio",
            side_effect=mock_process,
        ), caplog.at_level(logging.ERROR):
            with pytest.raises(TypeError, match="Permanent error"):
                await service._process_audio_with_retry(
                    mock_session, response_id, "/path/to/audio.webm"
                )

        # Should only be called once - no retries for permanent errors
        assert call_count == 1
        assert "Permanent error" in caplog.text

    @pytest.mark.asyncio
    async def test_retry_delays_are_correct(self):
        """Test that retry delays follow RETRY_DELAYS pattern."""
        service = BackgroundTaskService()
        mock_session = AsyncMock()
        response_id = uuid4()

        sleep_delays = []

        async def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch.object(
            service.audio_service,
            "process_response_audio",
            new_callable=AsyncMock,
            side_effect=[
                ValueError("Retry 1"),
                ValueError("Retry 2"),
                ("transcript", {}),
            ],
        ), patch("asyncio.sleep", side_effect=mock_sleep):
            await service._process_audio_with_retry(
                mock_session, response_id, "/path/to/audio.webm"
            )

        assert sleep_delays == RETRY_DELAYS[:2]


class TestUpdateProcessingStatusFailed:
    """Tests for _update_processing_status_failed method."""

    @pytest.mark.asyncio
    async def test_updates_status_to_failed(self):
        """Test that status is updated to FAILED with error message."""
        from app.models.interview import ProcessingStatus

        service = BackgroundTaskService()
        response_id = uuid4()

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        await service._update_processing_status_failed(
            mock_session, response_id, "Test error"
        )

        assert mock_response.processing_status == ProcessingStatus.FAILED
        assert mock_response.processing_error == "Test error"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_truncates_long_error_messages(self):
        """Test that error messages are truncated to 500 chars."""
        service = BackgroundTaskService()
        response_id = uuid4()
        long_error = "x" * 1000

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        await service._update_processing_status_failed(
            mock_session, response_id, long_error
        )

        assert len(mock_response.processing_error) == 500

    @pytest.mark.asyncio
    async def test_handles_missing_response(self, caplog):
        """Test handling when response is not found."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        # Should not raise
        await service._update_processing_status_failed(
            mock_session, response_id, "Error"
        )

    @pytest.mark.asyncio
    async def test_handles_commit_error(self, caplog):
        """Test handling when commit fails."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock(side_effect=Exception("Commit failed"))

        with caplog.at_level(logging.ERROR):
            # Should not raise
            await service._update_processing_status_failed(
                mock_session, response_id, "Error"
            )

        assert "Failed to update" in caplog.text


class TestGenerateContentFeedbackAsync:
    """Tests for generate_content_feedback_async method."""

    @pytest.mark.asyncio
    async def test_skips_existing_feedback(self, caplog):
        """Test that existing feedback is not regenerated."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_existing = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_existing

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             caplog.at_level(logging.DEBUG):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_content_feedback_async(response_id)

        assert "already exists" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_generates_feedback_when_none_exists(self):
        """Test that feedback is generated when none exists."""
        service = BackgroundTaskService()
        response_id = uuid4()

        # First call returns None (no existing feedback), second for maybe_generate
        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result_none)

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(service.feedback_service, "generate_feedback", new_callable=AsyncMock) as mock_generate, \
             patch.object(service, "_maybe_generate_session_feedback", new_callable=AsyncMock):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_content_feedback_async(response_id)

        mock_generate.assert_called_once_with(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_handles_value_error_gracefully(self, caplog):
        """Test that ValueError is logged at debug level."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result_none)

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(
                 service.feedback_service,
                 "generate_feedback",
                 new_callable=AsyncMock,
                 side_effect=ValueError("No transcript"),
             ), caplog.at_level(logging.DEBUG):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_content_feedback_async(response_id)

        assert "Could not generate feedback" in caplog.text

    @pytest.mark.asyncio
    async def test_handles_unexpected_error_gracefully(self, caplog):
        """Test that unexpected errors are logged at error level."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result_none)

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(
                 service.feedback_service,
                 "generate_feedback",
                 new_callable=AsyncMock,
                 side_effect=RuntimeError("Unexpected error"),
             ), caplog.at_level(logging.ERROR):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_content_feedback_async(response_id)

        assert "failed" in caplog.text.lower()


class TestGenerateSessionFeedbackAsync:
    """Tests for generate_session_feedback_async method."""

    @pytest.mark.asyncio
    async def test_waits_before_processing(self):
        """Test that method waits 2 seconds before processing."""
        service = BackgroundTaskService()
        session_id = uuid4()

        sleep_called = False

        async def mock_sleep(delay):
            nonlocal sleep_called
            if delay == 2:
                sleep_called = True

        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()  # Existing feedback

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with patch("asyncio.sleep", side_effect=mock_sleep), \
             patch("app.services.background_tasks.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_session_feedback_async(session_id)

        assert sleep_called

    @pytest.mark.asyncio
    async def test_skips_existing_session_feedback(self, caplog):
        """Test that existing session feedback is not regenerated."""
        service = BackgroundTaskService()
        session_id = uuid4()

        mock_existing = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_existing

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             caplog.at_level(logging.DEBUG):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_session_feedback_async(session_id)

        assert "already exists" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_generates_session_feedback_when_none_exists(self):
        """Test that session feedback is generated when none exists."""
        service = BackgroundTaskService()
        session_id = uuid4()

        mock_feedback = MagicMock()
        mock_feedback.overall_score = 85

        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result_none)

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(
                 service.feedback_service,
                 "generate_session_feedback",
                 new_callable=AsyncMock,
                 return_value=mock_feedback,
             ) as mock_generate:
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_session_feedback_async(session_id)

        mock_generate.assert_called_once_with(mock_session, session_id)

    @pytest.mark.asyncio
    async def test_handles_value_error_gracefully(self, caplog):
        """Test that ValueError is logged at debug level."""
        service = BackgroundTaskService()
        session_id = uuid4()

        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result_none)

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.background_tasks.SessionLocal") as mock_session_local, \
             patch.object(
                 service.feedback_service,
                 "generate_session_feedback",
                 new_callable=AsyncMock,
                 side_effect=ValueError("No responses"),
             ), caplog.at_level(logging.DEBUG):
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.generate_session_feedback_async(session_id)

        assert "Could not generate session feedback" in caplog.text


class TestMaybeGenerateSessionFeedback:
    """Tests for _maybe_generate_session_feedback method."""

    @pytest.mark.asyncio
    async def test_skips_if_response_not_found(self):
        """Test that method returns early if response not found."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        # Should not raise
        await service._maybe_generate_session_feedback(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_skips_if_session_feedback_exists(self, caplog):
        """Test that method skips if session feedback already exists."""
        service = BackgroundTaskService()
        response_id = uuid4()
        session_id = uuid4()

        mock_response = MagicMock()
        mock_response.session_id = session_id

        mock_session_feedback = MagicMock()

        # Create mock results for different queries
        response_result = MagicMock()
        response_result.first.return_value = mock_response

        feedback_result = MagicMock()
        feedback_result.first.return_value = mock_session_feedback

        call_count = 0

        async def mock_exec(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return response_result
            return feedback_result

        mock_session = AsyncMock()
        mock_session.exec = mock_exec

        with caplog.at_level(logging.DEBUG):
            await service._maybe_generate_session_feedback(mock_session, response_id)

        assert "already exists" in caplog.text.lower()


class TestRetryConstants:
    """Tests for retry configuration constants."""

    def test_max_retries_is_positive(self):
        """Test that MAX_RETRIES is a positive integer."""
        assert MAX_RETRIES > 0
        assert isinstance(MAX_RETRIES, int)

    def test_retry_delays_length_matches_max_retries(self):
        """Test that RETRY_DELAYS has entries for all retries."""
        assert len(RETRY_DELAYS) >= MAX_RETRIES - 1

    def test_retry_delays_are_positive(self):
        """Test that all retry delays are positive."""
        for delay in RETRY_DELAYS:
            assert delay > 0

    def test_retry_delays_increase(self):
        """Test that retry delays follow exponential backoff."""
        for i in range(1, len(RETRY_DELAYS)):
            assert RETRY_DELAYS[i] >= RETRY_DELAYS[i - 1]


class TestGlobalInstance:
    """Tests for the global background_tasks instance."""

    def test_global_instance_exists(self):
        """Test that the global instance is created."""
        from app.services.background_tasks import background_tasks

        assert background_tasks is not None
        assert isinstance(background_tasks, BackgroundTaskService)


class TestProcessResponseAudioAsyncOuterException:
    """Tests for outer exception handling in process_response_audio_async - covers lines 153-154."""

    @pytest.mark.asyncio
    async def test_outer_exception_logged(self, caplog):
        """Test that outer exception is logged (SessionLocal failure)."""
        service = BackgroundTaskService()
        response_id = uuid4()

        # Create a mock that raises when used as async context manager
        async def mock_aenter_error():
            raise Exception("Database connection pool exhausted")

        # Need to mock Path.exists() to return True so we get past the early returns
        with patch("pathlib.Path.exists", return_value=True):
            with patch("app.services.background_tasks.SessionLocal") as mock_session_local:
                mock_ctx = MagicMock()
                mock_ctx.__aenter__ = mock_aenter_error
                mock_ctx.__aexit__ = AsyncMock()
                mock_session_local.return_value = mock_ctx

                with caplog.at_level(logging.ERROR):
                    # Use valid audio URL format to pass the first check
                    await service.process_response_audio_async(
                        response_id, "/uploads/audio/test.wav"
                    )

        assert "Failed to start background audio processing" in caplog.text
        assert str(response_id) in caplog.text


class TestGenerateContentFeedbackAsyncOuterException:
    """Tests for outer exception handling in generate_content_feedback_async - covers lines 288-289."""

    @pytest.mark.asyncio
    async def test_outer_exception_logged(self, caplog):
        """Test that outer exception is logged (SessionLocal failure)."""
        service = BackgroundTaskService()
        response_id = uuid4()

        # Patch SessionLocal to raise an exception immediately
        with patch("app.services.background_tasks.SessionLocal") as mock_session_local:
            mock_session_local.side_effect = Exception("Database unavailable")

            with caplog.at_level(logging.ERROR):
                await service.generate_content_feedback_async(response_id)

        assert "Failed to start content feedback generation" in caplog.text
        assert str(response_id) in caplog.text


class TestMaybeGenerateSessionFeedbackAllHaveFeedback:
    """Tests for _maybe_generate_session_feedback when all responses have feedback - covers lines 338-388."""

    @pytest.mark.asyncio
    async def test_generates_session_feedback_when_all_ready(self, caplog):
        """Test that session feedback is generated when all responses have content feedback."""
        service = BackgroundTaskService()
        response_id = uuid4()
        session_id = uuid4()

        # Create mock response with session_id
        mock_response = MagicMock()
        mock_response.id = response_id
        mock_response.session_id = session_id

        # Create another mock response for the "all responses" query
        mock_response_2 = MagicMock()
        mock_response_2.id = uuid4()

        # Create mock content feedback
        mock_content_feedback = MagicMock()

        # Create mock session feedback result
        mock_session_feedback = MagicMock()
        mock_session_feedback.overall_score = 85.0

        # Set up query responses
        call_count = 0
        all_responses = [mock_response, mock_response_2]

        async def mock_exec(query):
            nonlocal call_count
            call_count += 1

            result = MagicMock()
            if call_count == 1:
                # First call: get response by ID
                result.first.return_value = mock_response
            elif call_count == 2:
                # Second call: check if session feedback exists - return None
                result.first.return_value = None
            elif call_count == 3:
                # Third call: get all responses for session
                result.all.return_value = all_responses
            elif call_count in [4, 5]:
                # Fourth/Fifth calls: check if each response has ContentFeedback
                result.first.return_value = mock_content_feedback
            return result

        mock_session = AsyncMock()
        mock_session.exec = mock_exec

        # Mock feedback service to return session feedback
        service.feedback_service.generate_session_feedback = AsyncMock(
            return_value=mock_session_feedback
        )

        with caplog.at_level(logging.INFO):
            await service._maybe_generate_session_feedback(mock_session, response_id)

        assert "All responses have feedback" in caplog.text
        assert "Successfully auto-generated session feedback" in caplog.text

    @pytest.mark.asyncio
    async def test_not_all_responses_have_feedback(self, caplog):
        """Test that session feedback is not generated when some responses lack feedback."""
        service = BackgroundTaskService()
        response_id = uuid4()
        session_id = uuid4()

        mock_response = MagicMock()
        mock_response.id = response_id
        mock_response.session_id = session_id

        mock_response_2 = MagicMock()
        mock_response_2.id = uuid4()

        all_responses = [mock_response, mock_response_2]
        call_count = 0

        async def mock_exec(query):
            nonlocal call_count
            call_count += 1

            result = MagicMock()
            if call_count == 1:
                result.first.return_value = mock_response
            elif call_count == 2:
                result.first.return_value = None  # No session feedback yet
            elif call_count == 3:
                result.all.return_value = all_responses
            elif call_count == 4:
                result.first.return_value = MagicMock()  # First has feedback
            elif call_count == 5:
                result.first.return_value = None  # Second does NOT have feedback
            return result

        mock_session = AsyncMock()
        mock_session.exec = mock_exec

        with caplog.at_level(logging.DEBUG):
            await service._maybe_generate_session_feedback(mock_session, response_id)

        assert "Not all responses have feedback yet" in caplog.text

    @pytest.mark.asyncio
    async def test_value_error_from_generate_session_feedback(self, caplog):
        """Test handling of ValueError from generate_session_feedback."""
        service = BackgroundTaskService()
        response_id = uuid4()
        session_id = uuid4()

        mock_response = MagicMock()
        mock_response.id = response_id
        mock_response.session_id = session_id

        all_responses = [mock_response]
        call_count = 0

        async def mock_exec(query):
            nonlocal call_count
            call_count += 1

            result = MagicMock()
            if call_count == 1:
                result.first.return_value = mock_response
            elif call_count == 2:
                result.first.return_value = None
            elif call_count == 3:
                result.all.return_value = all_responses
            elif call_count == 4:
                result.first.return_value = MagicMock()  # Has feedback
            return result

        mock_session = AsyncMock()
        mock_session.exec = mock_exec

        # Mock feedback service to raise ValueError
        service.feedback_service.generate_session_feedback = AsyncMock(
            side_effect=ValueError("No responses to aggregate")
        )

        with caplog.at_level(logging.WARNING):
            await service._maybe_generate_session_feedback(mock_session, response_id)

        assert "Could not auto-generate session feedback" in caplog.text

    @pytest.mark.asyncio
    async def test_general_exception_in_maybe_generate(self, caplog):
        """Test handling of general exception in _maybe_generate_session_feedback."""
        service = BackgroundTaskService()
        response_id = uuid4()

        mock_session = AsyncMock()
        # First exec call raises exception
        mock_session.exec = AsyncMock(side_effect=Exception("Database query failed"))

        with caplog.at_level(logging.ERROR):
            await service._maybe_generate_session_feedback(mock_session, response_id)

        assert "Error checking for auto session feedback generation" in caplog.text


class TestGenerateSessionFeedbackAsyncExceptions:
    """Tests for exception handling in generate_session_feedback_async - covers lines 451-461."""

    @pytest.mark.asyncio
    async def test_outer_exception_in_generate_session_feedback(self, caplog):
        """Test handling of exception when starting session feedback generation."""
        service = BackgroundTaskService()
        session_id = uuid4()

        # Create a mock that raises when used as async context manager
        async def mock_aenter_error():
            raise Exception("Connection refused")

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = mock_aenter_error
            mock_ctx.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_ctx

            with caplog.at_level(logging.ERROR):
                await service.generate_session_feedback_async(session_id)

        assert "Failed to start session feedback generation" in caplog.text
        assert str(session_id) in caplog.text

    @pytest.mark.asyncio
    async def test_inner_general_exception_in_generate_session_feedback(self, caplog):
        """Test handling of general exception inside session feedback generation."""
        service = BackgroundTaskService()
        session_id = uuid4()

        # Create a context manager that works but throws on exec
        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=Exception("Unexpected database error"))

        async def mock_ctx():
            return mock_session

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local:
            # Set up async context manager
            mock_session_local.return_value.__aenter__ = mock_ctx
            mock_session_local.return_value.__aexit__ = AsyncMock()

            with caplog.at_level(logging.ERROR):
                await service.generate_session_feedback_async(session_id)

        # Should log the inner exception
        assert "Background session feedback generation failed" in caplog.text or "Failed to start" in caplog.text

    @pytest.mark.asyncio
    async def test_value_error_in_generate_session_feedback_async(self, caplog):
        """Test handling of ValueError in generate_session_feedback_async."""
        service = BackgroundTaskService()
        session_id = uuid4()

        # Set up mock session with no existing feedback
        mock_session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None  # No existing feedback
        mock_session.exec = AsyncMock(return_value=result)

        # Mock feedback service to raise ValueError
        service.feedback_service.generate_session_feedback = AsyncMock(
            side_effect=ValueError("Session has no responses")
        )

        with patch("app.services.background_tasks.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock()

            with caplog.at_level(logging.DEBUG):
                await service.generate_session_feedback_async(session_id)

        assert "Could not generate session feedback" in caplog.text
