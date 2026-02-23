"""Comprehensive unit tests for app/api/upload.py.

Pure unit tests — no database or filesystem required.
All DB interactions, file I/O, and external dependencies are mocked.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from fastapi import HTTPException

from app.api.upload import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_VIDEO_FILE_SIZE,
    VIDEO_ALLOWED_EXTENSIONS,
    AudioUploadResponse,
    upload_audio,
    upload_video,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_upload_file(filename: str, content: bytes = b"audio-data") -> MagicMock:
    """Build a minimal UploadFile mock."""
    uf = MagicMock()
    uf.filename = filename
    uf.read = AsyncMock(return_value=content)
    return uf


def _make_session(first_return=None) -> AsyncMock:
    """Build an AsyncSession mock whose exec().first() returns *first_return*."""
    result = MagicMock()
    result.first.return_value = first_return

    session = AsyncMock()
    session.exec = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    return session


def _make_user(user_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    return user


def _make_interview_session(user_id: uuid.UUID | None = None) -> MagicMock:
    session_obj = MagicMock()
    session_obj.id = uuid.uuid4()
    session_obj.user_id = user_id or uuid.uuid4()
    return session_obj


def _make_preparation(user_id: uuid.UUID | None = None) -> MagicMock:
    prep = MagicMock()
    prep.id = uuid.uuid4()
    prep.user_id = user_id or uuid.uuid4()
    return prep


def _make_interview_response() -> MagicMock:
    resp = MagicMock()
    resp.id = uuid.uuid4()
    resp.video_url = None
    return resp


# ---------------------------------------------------------------------------
# Tests: upload_audio — extension validation
# ---------------------------------------------------------------------------


class TestUploadAudioExtensionValidation:
    """The endpoint must reject files with unsupported extensions."""

    @pytest.mark.asyncio
    async def test_rejects_txt_extension(self):
        file = _make_upload_file("recording.txt")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-session-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_exe_extension(self):
        file = _make_upload_file("malware.exe")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-session-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_no_extension(self):
        file = _make_upload_file("recording")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-session-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_empty_filename(self):
        """Empty filename yields empty suffix — should be rejected."""
        file = _make_upload_file("")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-session-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_none_filename(self):
        """None filename should be treated as empty and rejected."""
        file = _make_upload_file(None)  # type: ignore[arg-type]
        file.filename = None
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-session-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Tests: upload_audio — missing session_id and preparation_id
# ---------------------------------------------------------------------------


class TestUploadAudioMissingIds:
    """Without either session_id or preparation_id the endpoint must 400."""

    @pytest.mark.asyncio
    async def test_rejects_when_both_ids_absent(self):
        file = _make_upload_file("recording.webm")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=None,
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "session_id" in exc_info.value.detail or "preparation_id" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Tests: upload_audio — ownership verification via session_id
# ---------------------------------------------------------------------------


class TestUploadAudioSessionOwnership:
    """When session_id is provided the interview session must belong to the user."""

    @pytest.mark.asyncio
    async def test_raises_404_when_session_not_found(self):
        file = _make_upload_file("recording.webm")
        user = _make_user()
        # DB returns no session
        session = _make_session(first_return=None)

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=str(uuid.uuid4()),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 404
        assert "session" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_accepts_valid_session_and_saves_file(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"x" * 1024)

        fixed_uuid = "abcdef123456"
        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = fixed_uuid + "extras"
            result = await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )

        assert isinstance(result, AudioUploadResponse)
        assert result.audio_url.startswith("/uploads/audio/")
        assert result.file_size_bytes == 1024
        assert result.filename.endswith(".webm")

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_uses_question_id_in_filename_when_provided(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        q_id = str(uuid.uuid4())
        file = _make_upload_file("answer.mp3", content=b"audio")

        result = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=q_id,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )

        assert q_id in result.filename

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_falls_back_to_session_id_when_no_question_id(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        s_id = str(interview_session.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("answer.wav", content=b"audio")

        result = await upload_audio(
            file=file,
            session_id=s_id,
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )

        # secondary_id defaults to session_id when question_id is absent
        assert s_id in result.filename


# ---------------------------------------------------------------------------
# Tests: upload_audio — ownership verification via preparation_id
# ---------------------------------------------------------------------------


class TestUploadAudioPreparationOwnership:
    """When preparation_id is provided the preparation must belong to the user."""

    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        file = _make_upload_file("recording.ogg")
        user = _make_user()
        session = _make_session(first_return=None)

        from app.models.preparation import AnswerPreparation  # noqa: F401

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=None,
                question_id=None,
                preparation_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 404
        assert "preparation" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_accepts_valid_preparation_and_saves_file(self):
        user = _make_user()
        prep = _make_preparation(user_id=user.id)
        session = _make_session(first_return=prep)
        file = _make_upload_file("practice.m4a", content=b"y" * 512)

        result = await upload_audio(
            file=file,
            session_id=None,
            question_id=None,
            preparation_id=str(prep.id),
            current_user=user,
            db_session=session,
        )

        assert isinstance(result, AudioUploadResponse)
        assert result.file_size_bytes == 512
        assert result.audio_url.startswith("/uploads/audio/")


# ---------------------------------------------------------------------------
# Tests: upload_audio — file size validation
# ---------------------------------------------------------------------------


class TestUploadAudioFileSizeValidation:
    """File size must be within [1 byte, MAX_FILE_SIZE]."""

    @pytest.mark.asyncio
    async def test_rejects_empty_file(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"")

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        # One byte over the limit
        big_content = b"x" * (MAX_FILE_SIZE + 1)
        file = _make_upload_file("recording.webm", content=big_content)

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_accepts_exactly_max_size(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        exact_content = b"x" * MAX_FILE_SIZE
        file = _make_upload_file("recording.webm", content=exact_content)

        result = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )
        assert result.file_size_bytes == MAX_FILE_SIZE

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_accepts_one_byte_file(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"x")

        result = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )
        assert result.file_size_bytes == 1


# ---------------------------------------------------------------------------
# Tests: upload_audio — all allowed audio formats
# ---------------------------------------------------------------------------


class TestUploadAudioAllowedFormats:
    """Each format in ALLOWED_EXTENSIONS must be accepted end-to-end."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ext", sorted(ALLOWED_EXTENSIONS))
    @patch("builtins.open", mock_open())
    async def test_accepts_allowed_format(self, ext: str):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file(f"audio{ext}", content=b"data")

        result = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )
        assert result.filename.endswith(ext)


# ---------------------------------------------------------------------------
# Tests: upload_audio — response structure
# ---------------------------------------------------------------------------


class TestUploadAudioResponseStructure:
    """The response must contain audio_url, file_size_bytes, filename."""

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_response_url_format(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"content")

        result = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=session,
        )

        assert result.audio_url.startswith("/uploads/audio/")
        assert result.filename in result.audio_url
        assert result.file_size_bytes == len(b"content")

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_filename_contains_unique_hex(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"x")

        # Call twice — filenames must differ (UUID randomness)
        r1 = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=_make_session(first_return=interview_session),
        )
        file.read = AsyncMock(return_value=b"x")
        r2 = await upload_audio(
            file=file,
            session_id=str(interview_session.id),
            question_id=None,
            preparation_id=None,
            current_user=user,
            db_session=_make_session(first_return=interview_session),
        )

        assert r1.filename != r2.filename


# ---------------------------------------------------------------------------
# Tests: upload_video — feature flag gate
# ---------------------------------------------------------------------------


class TestUploadVideoFeatureFlag:
    """upload_video must raise HTTP 404 when video features are disabled."""

    @pytest.mark.asyncio
    async def test_raises_404_when_feature_disabled(self):
        file = _make_upload_file("video.mp4", content=b"video-data")
        user = _make_user()
        session = _make_session()

        with (
            patch("app.api.upload.require_video_features_enabled") as mock_flag,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_flag.side_effect = HTTPException(status_code=404, detail="not available")
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_feature_flag_called_before_any_other_logic(self):
        """Ensure require_video_features_enabled is called even with a bad extension."""
        file = _make_upload_file("malware.exe", content=b"bad")
        user = _make_user()
        session = _make_session()

        with (
            patch("app.api.upload.require_video_features_enabled") as mock_flag,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_flag.side_effect = HTTPException(status_code=404, detail="not available")
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 404
        mock_flag.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: upload_video — extension validation
# ---------------------------------------------------------------------------


class TestUploadVideoExtensionValidation:
    """Unsupported video extensions must be rejected with HTTP 400."""

    @pytest.mark.asyncio
    async def test_rejects_avi_extension(self):
        file = _make_upload_file("video.avi")
        user = _make_user()
        session = _make_session()

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_exe_extension(self):
        file = _make_upload_file("bad.exe")
        user = _make_user()
        session = _make_session()

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_none_filename(self):
        file = _make_upload_file("video.mp4")
        file.filename = None
        user = _make_user()
        session = _make_session()

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Tests: upload_video — ownership verification
# ---------------------------------------------------------------------------


class TestUploadVideoOwnership:
    """Response must belong to the current user; otherwise 404."""

    @pytest.mark.asyncio
    async def test_raises_404_when_response_not_found(self):
        file = _make_upload_file("video.webm")
        user = _make_user()
        session = _make_session(first_return=None)

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 404
        assert "denied" in exc_info.value.detail.lower() or "not found" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Tests: upload_video — file size validation
# ---------------------------------------------------------------------------


class TestUploadVideoFileSizeValidation:
    """Video file must be non-empty and within MAX_VIDEO_FILE_SIZE."""

    @pytest.mark.asyncio
    async def test_rejects_empty_video_file(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file("video.mp4", content=b"")

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_rejects_oversized_video_file(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        big_content = b"x" * (MAX_VIDEO_FILE_SIZE + 1)
        file = _make_upload_file("video.mp4", content=big_content)

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_accepts_exactly_max_video_size(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        exact_content = b"x" * MAX_VIDEO_FILE_SIZE
        file = _make_upload_file("video.mp4", content=exact_content)

        with patch("app.api.upload.require_video_features_enabled"):
            result = await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )
        assert result.file_size_bytes == MAX_VIDEO_FILE_SIZE


# ---------------------------------------------------------------------------
# Tests: upload_video — all allowed video formats
# ---------------------------------------------------------------------------


class TestUploadVideoAllowedFormats:
    """Each format in VIDEO_ALLOWED_EXTENSIONS must be accepted end-to-end."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ext", sorted(VIDEO_ALLOWED_EXTENSIONS))
    @patch("builtins.open", mock_open())
    async def test_accepts_allowed_format(self, ext: str):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file(f"video{ext}", content=b"data")

        with patch("app.api.upload.require_video_features_enabled"):
            result = await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )
        assert result.filename.endswith(ext)


# ---------------------------------------------------------------------------
# Tests: upload_video — response structure and side effects
# ---------------------------------------------------------------------------


class TestUploadVideoResponseStructure:
    """The response must contain video_url, file_size_bytes, filename.
    The InterviewResponse.video_url must be updated and the session committed."""

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_response_url_format(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file("clip.webm", content=b"video-bytes")

        with patch("app.api.upload.require_video_features_enabled"):
            result = await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )

        assert result.video_url.startswith("/uploads/video/")
        assert result.filename in result.video_url
        assert result.file_size_bytes == len(b"video-bytes")

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_updates_video_url_on_response_object(self):
        """The endpoint must set response.video_url before committing."""
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file("clip.mp4", content=b"v")

        with patch("app.api.upload.require_video_features_enabled"):
            result = await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )

        assert interview_response.video_url == result.video_url

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_commits_session_after_update(self):
        """DB session.commit() must be called exactly once on success."""
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file("clip.mov", content=b"data")

        with patch("app.api.upload.require_video_features_enabled"):
            await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )

        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("builtins.open", mock_open())
    async def test_filename_unique_per_call(self):
        """Two uploads for the same response_id must produce different filenames."""
        user = _make_user()
        r_id = str(uuid.uuid4())
        file = _make_upload_file("clip.mp4", content=b"v")

        with patch("app.api.upload.require_video_features_enabled"):
            r1 = await upload_video(
                file=file,
                response_id=r_id,
                current_user=user,
                db_session=_make_session(first_return=_make_interview_response()),
            )
            file.read = AsyncMock(return_value=b"v")
            r2 = await upload_video(
                file=file,
                response_id=r_id,
                current_user=user,
                db_session=_make_session(first_return=_make_interview_response()),
            )

        assert r1.filename != r2.filename


# ---------------------------------------------------------------------------
# Tests: path traversal protection — audio
# ---------------------------------------------------------------------------


class TestAudioPathTraversalProtection:
    r"""Filenames that resolve outside UPLOAD_DIR must be blocked.

    NOTE: The endpoint generates filenames itself from trusted components
    (resource_id, secondary_id, uuid hex) so path traversal is only
    possible through extremely unlikely UUID collisions.  We test the
    guard logic by patching Path.resolve to simulate a malicious path.
    """

    @pytest.mark.asyncio
    async def test_rejects_path_traversal_in_filename(self):
        """Simulate a case where resolve() returns a path outside UPLOAD_DIR."""
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        file = _make_upload_file("recording.webm", content=b"data")

        # Patch Path.resolve to return a path outside the upload dir
        outside_path = Path("/tmp/evil/file.webm")

        original_resolve = Path.resolve

        def fake_resolve(self, **kwargs):
            if "audio" in str(self):
                return outside_path
            return original_resolve(self, **kwargs)

        with (
            patch.object(Path, "resolve", fake_resolve),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Tests: path traversal protection — video
# ---------------------------------------------------------------------------


class TestVideoPathTraversalProtection:
    @pytest.mark.asyncio
    async def test_rejects_path_traversal_in_video_filename(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        file = _make_upload_file("clip.mp4", content=b"data")

        outside_path = Path("/tmp/evil/video.mp4")
        original_resolve = Path.resolve

        def fake_resolve(self, **kwargs):
            if "video" in str(self):
                return outside_path
            return original_resolve(self, **kwargs)

        with (
            patch("app.api.upload.require_video_features_enabled"),
            patch.object(Path, "resolve", fake_resolve),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )
        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Tests: DB query composition (exec called once per branch)
# ---------------------------------------------------------------------------


class TestDatabaseQueryBehavior:
    """Verify the endpoint calls db_session.exec() with a statement for ownership checks."""

    @pytest.mark.asyncio
    async def test_exec_called_for_session_id_path(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        db = _make_session(first_return=None)  # returns None → 404
        file = _make_upload_file("rec.webm")

        with pytest.raises(HTTPException):
            await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=db,
            )

        db.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exec_called_for_preparation_id_path(self):
        user = _make_user()
        prep = _make_preparation(user_id=user.id)
        db = _make_session(first_return=None)  # returns None → 404
        file = _make_upload_file("rec.ogg")

        with pytest.raises(HTTPException):
            await upload_audio(
                file=file,
                session_id=None,
                question_id=None,
                preparation_id=str(prep.id),
                current_user=user,
                db_session=db,
            )

        db.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exec_called_for_video_path(self):
        user = _make_user()
        db = _make_session(first_return=None)  # returns None → 404
        file = _make_upload_file("vid.webm")

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException),
        ):
            await upload_video(
                file=file,
                response_id=str(uuid.uuid4()),
                current_user=user,
                db_session=db,
            )

        db.exec.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: error message content
# ---------------------------------------------------------------------------


class TestErrorMessages:
    """Spot-check that error details communicate the right information."""

    @pytest.mark.asyncio
    async def test_extension_error_lists_allowed_types(self):
        file = _make_upload_file("recording.php")
        user = _make_user()
        session = _make_session()

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id="some-id",
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )

        detail = exc_info.value.detail
        # At least one allowed extension should appear in the message
        assert any(ext in detail for ext in ALLOWED_EXTENSIONS)

    @pytest.mark.asyncio
    async def test_size_error_mentions_max_mb(self):
        user = _make_user()
        interview_session = _make_interview_session(user_id=user.id)
        session = _make_session(first_return=interview_session)
        big_content = b"x" * (MAX_FILE_SIZE + 1)
        file = _make_upload_file("recording.webm", content=big_content)

        with pytest.raises(HTTPException) as exc_info:
            await upload_audio(
                file=file,
                session_id=str(interview_session.id),
                question_id=None,
                preparation_id=None,
                current_user=user,
                db_session=session,
            )

        assert "50" in exc_info.value.detail  # 50MB limit

    @pytest.mark.asyncio
    async def test_video_size_error_mentions_max_mb(self):
        user = _make_user()
        interview_response = _make_interview_response()
        session = _make_session(first_return=interview_response)
        big_content = b"x" * (MAX_VIDEO_FILE_SIZE + 1)
        file = _make_upload_file("video.mp4", content=big_content)

        with (
            patch("app.api.upload.require_video_features_enabled"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await upload_video(
                file=file,
                response_id=str(interview_response.id),
                current_user=user,
                db_session=session,
            )

        assert "200" in exc_info.value.detail  # 200MB limit
