"""Tests for upload.py handler gaps - zero handler coverage.

These tests cover the handler logic in app/api/upload.py that lacks test coverage.
All tests use mocks to avoid database/filesystem dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import upload


def create_mock_user(user_id: str | None = None) -> MagicMock:
    """Create a mock user object."""
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


def create_mock_file(
    filename: str = "test.webm",
    content_type: str = "audio/webm",
    content: bytes = b"x" * 1024,
) -> MagicMock:
    """Create a mock UploadFile object."""
    file = MagicMock()
    file.filename = filename
    file.content_type = content_type
    file.read = AsyncMock(return_value=content)
    return file


class TestUploadAudioInvalidExtension:
    """Tests for upload_audio with invalid file extensions."""

    @pytest.mark.asyncio
    async def test_upload_audio_invalid_extension_raises_400(self):
        """Test that uploading a file with disallowed extension returns 400."""
        mock_file = create_mock_file(filename="test.exe", content_type="application/octet-stream")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=None,
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail.lower()


class TestUploadAudioMissingIdentifiers:
    """Tests for upload_audio when neither session_id nor preparation_id is provided."""

    @pytest.mark.asyncio
    async def test_upload_audio_missing_session_and_preparation_id_raises_400(self):
        """Test that missing both session_id and preparation_id returns 400."""
        mock_file = create_mock_file()
        mock_user = create_mock_user()
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=None,
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "session_id or preparation_id" in exc_info.value.detail.lower()


class TestUploadAudioSessionNotFound:
    """Tests for upload_audio when session_id points to non-existent session."""

    @pytest.mark.asyncio
    async def test_upload_audio_session_not_found_raises_404(self):
        """Test that non-existent session_id returns 404."""
        mock_file = create_mock_file()
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock the database to return no results
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=str(uuid4()),
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 404
        assert "session" in exc_info.value.detail.lower()


class TestUploadAudioPreparationNotFound:
    """Tests for upload_audio when preparation_id points to non-existent preparation."""

    @pytest.mark.asyncio
    async def test_upload_audio_preparation_not_found_raises_404(self):
        """Test that non-existent preparation_id returns 404."""
        mock_file = create_mock_file()
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock the database to return no results for preparation
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=None,
                question_id=None,
                preparation_id=str(uuid4()),
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 404
        assert "preparation" in exc_info.value.detail.lower()


class TestUploadAudioFileSize:
    """Tests for upload_audio file size validation."""

    @pytest.mark.asyncio
    async def test_upload_audio_file_too_large_raises_413(self):
        """Test that file exceeding 50MB returns 413."""
        # Create file content larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        mock_file = create_mock_file(content=large_content)
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_session = MagicMock()
        mock_session.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_session
        mock_db.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=str(uuid4()),
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_upload_audio_empty_file_raises_400(self):
        """Test that empty file returns 400."""
        mock_file = create_mock_file(content=b"")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_session = MagicMock()
        mock_session.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_session
        mock_db.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await upload.upload_audio(
                file=mock_file,
                session_id=str(uuid4()),
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()


class TestUploadAudioHappyPath:
    """Tests for upload_audio happy path scenarios."""

    @pytest.mark.asyncio
    @patch("app.api.upload.UPLOAD_DIR", autospec=True)
    async def test_upload_audio_with_session_id_happy_path(self, mock_upload_dir):
        """Test successful audio upload with session_id."""
        mock_file = create_mock_file()
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_session = MagicMock()
        mock_session.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_session
        mock_db.exec = AsyncMock(return_value=mock_result)

        # Mock Path operations
        mock_path = MagicMock()
        mock_path.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/audio/test.webm"
        )
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_path)
        mock_upload_dir.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/audio"
        )

        # Mock file write
        with patch("builtins.open", MagicMock()):
            result = await upload.upload_audio(
                file=mock_file,
                session_id=str(uuid4()),
                question_id=None,
                preparation_id=None,
                current_user=mock_user,
                db_session=mock_db,
            )

        assert result.audio_url.startswith("/uploads/audio/")
        assert result.filename.endswith(".webm")
        assert result.file_size_bytes == 1024

    @pytest.mark.asyncio
    @patch("app.api.upload.UPLOAD_DIR", autospec=True)
    async def test_upload_audio_with_preparation_id_happy_path(self, mock_upload_dir):
        """Test successful audio upload with preparation_id."""
        mock_file = create_mock_file()
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query for preparation
        mock_prep = MagicMock()
        mock_prep.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_prep
        mock_db.exec = AsyncMock(return_value=mock_result)

        # Mock Path operations
        mock_path = MagicMock()
        mock_path.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/audio/test.webm"
        )
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_path)
        mock_upload_dir.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/audio"
        )

        # Mock file write
        with patch("builtins.open", MagicMock()):
            result = await upload.upload_audio(
                file=mock_file,
                session_id=None,
                question_id=None,
                preparation_id=str(uuid4()),
                current_user=mock_user,
                db_session=mock_db,
            )

        assert result.audio_url.startswith("/uploads/audio/")
        assert result.filename.endswith(".webm")


class TestUploadVideoFeatureFlag:
    """Tests for upload_video feature flag."""

    @pytest.mark.asyncio
    async def test_upload_video_feature_flag_disabled_raises(self):
        """Test that video upload returns 404 when feature flag is disabled."""
        mock_file = create_mock_file(filename="test.mp4", content_type="video/mp4")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        with patch("app.feature_flags.settings") as mock_settings:
            mock_settings.video_features_enabled = False

            with pytest.raises(HTTPException) as exc_info:
                await upload.upload_video(
                    file=mock_file,
                    response_id=str(uuid4()),
                    current_user=mock_user,
                    db_session=mock_db,
                )

            assert exc_info.value.status_code == 404
            assert "video" in exc_info.value.detail.lower()


class TestUploadVideoValidation:
    """Tests for upload_video validation logic."""

    @pytest.mark.asyncio
    async def test_upload_video_invalid_extension_raises_400(self):
        """Test that video with invalid extension returns 400."""
        mock_file = create_mock_file(filename="test.avi", content_type="video/avi")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        with patch("app.feature_flags.settings") as mock_settings:
            mock_settings.video_features_enabled = True

            with pytest.raises(HTTPException) as exc_info:
                await upload.upload_video(
                    file=mock_file,
                    response_id=str(uuid4()),
                    current_user=mock_user,
                    db_session=mock_db,
                )

            assert exc_info.value.status_code == 400
            assert "not allowed" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_upload_video_response_not_found_raises_404(self):
        """Test that non-existent response returns 404."""
        mock_file = create_mock_file(filename="test.mp4", content_type="video/mp4")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock the database to return no results
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.exec = AsyncMock(return_value=mock_result)

        with patch("app.feature_flags.settings") as mock_settings:
            mock_settings.video_features_enabled = True

            with pytest.raises(HTTPException) as exc_info:
                await upload.upload_video(
                    file=mock_file,
                    response_id=str(uuid4()),
                    current_user=mock_user,
                    db_session=mock_db,
                )

            assert exc_info.value.status_code == 404
            assert "response" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_upload_video_empty_file_raises_400(self):
        """Test that empty video file returns 400."""
        mock_file = create_mock_file(filename="test.mp4", content_type="video/mp4", content=b"")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_response = MagicMock()
        mock_response.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_db.exec = AsyncMock(return_value=mock_result)

        with patch("app.feature_flags.settings") as mock_settings:
            mock_settings.video_features_enabled = True

            with pytest.raises(HTTPException) as exc_info:
                await upload.upload_video(
                    file=mock_file,
                    response_id=str(uuid4()),
                    current_user=mock_user,
                    db_session=mock_db,
                )

            assert exc_info.value.status_code == 400
            assert "empty" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_upload_video_too_large_raises_413(self):
        """Test that video exceeding 200MB returns 413."""
        large_content = b"x" * (201 * 1024 * 1024)
        mock_file = create_mock_file(
            filename="test.mp4", content_type="video/mp4", content=large_content
        )
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_response = MagicMock()
        mock_response.id = str(uuid4())
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_db.exec = AsyncMock(return_value=mock_result)

        with patch("app.feature_flags.settings") as mock_settings:
            mock_settings.video_features_enabled = True

            with pytest.raises(HTTPException) as exc_info:
                await upload.upload_video(
                    file=mock_file,
                    response_id=str(uuid4()),
                    current_user=mock_user,
                    db_session=mock_db,
                )

            assert exc_info.value.status_code == 413
            assert "too large" in exc_info.value.detail.lower()


class TestUploadVideoHappyPath:
    """Tests for upload_video happy path scenarios."""

    @pytest.mark.asyncio
    @patch("app.api.upload.VIDEO_UPLOAD_DIR", autospec=True)
    async def test_upload_video_happy_path_updates_response_video_url(self, mock_video_dir):
        """Test successful video upload updates response.video_url."""
        mock_file = create_mock_file(filename="test.mp4", content_type="video/mp4")
        mock_user = create_mock_user()
        mock_db = MagicMock()

        # Mock successful database query
        mock_response = MagicMock()
        mock_response.id = str(uuid4())
        mock_response.video_url = None
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response
        mock_db.exec = AsyncMock(return_value=mock_result)

        # Mock Path operations
        mock_path = MagicMock()
        mock_path.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/video/test.mp4"
        )
        mock_video_dir.__truediv__ = MagicMock(return_value=mock_path)
        mock_video_dir.resolve.return_value = MagicMock(
            __str__=lambda self: "/fake/uploads/video"
        )

        # Mock file write and db commit
        with patch("builtins.open", MagicMock()):
            with patch.object(mock_db, "commit", AsyncMock()):
                with patch("app.feature_flags.settings") as mock_settings:
                    mock_settings.video_features_enabled = True

                    result = await upload.upload_video(
                        file=mock_file,
                        response_id=str(uuid4()),
                        current_user=mock_user,
                        db_session=mock_db,
                    )

        assert result.video_url.startswith("/uploads/video/")
        assert result.filename.endswith(".mp4")
        assert result.file_size_bytes == 1024
