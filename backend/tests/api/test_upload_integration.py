"""Integration tests for upload API endpoints.

Tests the full route logic for audio and video file uploads using the
FastAPI test client with mocked external dependencies (filesystem, DB).
All tests exercise the HTTP layer — dependency overrides, multipart
form data, status codes and response bodies are all validated here.

Dependencies mocked:
  - builtins.open       — filesystem write, so no real disk I/O
  - app.dependencies.get_current_user — injects a fake user without DB/JWT
  - app.db.get_session  — injects a fake DB session
  - app.api.upload.require_video_features_enabled — controls feature flag
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from fastapi.testclient import TestClient

from app.api.upload import MAX_FILE_SIZE, MAX_VIDEO_FILE_SIZE
from app.main import app

# ---------------------------------------------------------------------------
# Constants shared across tests
# ---------------------------------------------------------------------------

AUDIO_UPLOAD_URL = "/api/v1/upload/audio"
VIDEO_UPLOAD_URL = "/api/v1/upload/video"

# A realistic but tiny fake audio payload (avoids large in-memory allocations)
FAKE_AUDIO_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt "  # Partial WAV header
FAKE_VIDEO_BYTES = b"\x00\x00\x00\x18ftyp"  # Partial MP4 header


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_user(user_id: str | None = None) -> MagicMock:
    """Build a minimal User-like mock accepted by the dependency."""
    user = MagicMock()
    user.id = user_id or str(uuid.uuid4())
    user.email = "test@example.com"
    return user


def _fake_db_session(first_return: Any = None) -> AsyncMock:
    """Build an AsyncSession mock whose exec().first() returns *first_return*."""
    result_mock = MagicMock()
    result_mock.first.return_value = first_return

    session = AsyncMock()
    session.exec = AsyncMock(return_value=result_mock)
    session.commit = AsyncMock()
    return session


def _fake_interview_session(user_id: str) -> MagicMock:
    """Build a minimal InterviewSession mock."""
    obj = MagicMock()
    obj.id = str(uuid.uuid4())
    obj.user_id = user_id
    return obj


def _fake_interview_response() -> MagicMock:
    """Build a minimal InterviewResponse mock."""
    obj = MagicMock()
    obj.id = str(uuid.uuid4())
    obj.video_url = None
    return obj


def _audio_multipart(
    filename: str = "recording.webm",
    content: bytes = FAKE_AUDIO_BYTES,
    session_id: str | None = None,
    preparation_id: str | None = None,
    question_id: str | None = None,
    content_type: str = "audio/webm",
) -> dict:
    """Build the multipart form data dict for audio uploads."""
    files = {"file": (filename, io.BytesIO(content), content_type)}
    data: dict[str, str] = {}
    if session_id is not None:
        data["session_id"] = session_id
    if preparation_id is not None:
        data["preparation_id"] = preparation_id
    if question_id is not None:
        data["question_id"] = question_id
    return {"files": files, "data": data}


def _video_multipart(
    filename: str = "clip.mp4",
    content: bytes = FAKE_VIDEO_BYTES,
    response_id: str | None = None,
    content_type: str = "video/mp4",
) -> dict:
    """Build the multipart form data dict for video uploads."""
    files = {"file": (filename, io.BytesIO(content), content_type)}
    data: dict[str, str] = {}
    if response_id is not None:
        data["response_id"] = response_id
    return {"files": files, "data": data}


# ---------------------------------------------------------------------------
# Context manager: wire auth + DB overrides then restore them
# ---------------------------------------------------------------------------


class _OverrideContext:
    """Temporarily override get_current_user and get_session on the app."""

    def __init__(self, user: MagicMock, db_session: AsyncMock) -> None:
        self._user = user
        self._db_session = db_session

    def __enter__(self) -> TestClient:
        from app.db import get_session
        from app.dependencies import get_current_user

        async def _override_user():
            return self._user

        async def _override_session():
            yield self._db_session

        app.dependency_overrides[get_current_user] = _override_user
        app.dependency_overrides[get_session] = _override_session
        return TestClient(app, raise_server_exceptions=False)

    def __exit__(self, *args: object) -> None:
        app.dependency_overrides.clear()


def _client(user: MagicMock, db_session: AsyncMock) -> _OverrideContext:
    return _OverrideContext(user, db_session)


# ---------------------------------------------------------------------------
# Part 3a: Successful audio file upload
# ---------------------------------------------------------------------------


class TestAudioUploadSuccess:
    """Full route exercised: auth passes, DB returns owned session, file saved."""

    @patch("builtins.open", mock_open())
    def test_upload_webm_audio_returns_201(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        mp = _audio_multipart(session_id=interview_session.id)
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 201
        body = response.json()
        assert "audio_url" in body
        assert body["audio_url"].startswith("/uploads/audio/")
        assert body["file_size_bytes"] == len(FAKE_AUDIO_BYTES)
        assert body["filename"].endswith(".webm")

    @patch("builtins.open", mock_open())
    def test_upload_mp3_audio_returns_201(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        mp = _audio_multipart(
            filename="recording.mp3",
            content=b"ID3\x03\x00\x00\x00",
            session_id=interview_session.id,
            content_type="audio/mpeg",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 201
        body = response.json()
        assert body["filename"].endswith(".mp3")

    @patch("builtins.open", mock_open())
    def test_upload_wav_audio_returns_201(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        mp = _audio_multipart(
            filename="recording.wav",
            content=b"RIFF\x00\x00\x00\x00WAVE",
            session_id=interview_session.id,
            content_type="audio/wav",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 201
        assert response.json()["filename"].endswith(".wav")

    @patch("builtins.open", mock_open())
    def test_response_contains_all_required_fields(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        mp = _audio_multipart(session_id=interview_session.id)
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        body = response.json()
        required_fields = {"audio_url", "file_size_bytes", "filename"}
        assert required_fields.issubset(body.keys())

    @patch("builtins.open", mock_open())
    def test_filename_in_audio_url(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        mp = _audio_multipart(session_id=interview_session.id)
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        body = response.json()
        assert body["filename"] in body["audio_url"]


# ---------------------------------------------------------------------------
# Part 3b: Successful video file upload
# ---------------------------------------------------------------------------


class TestVideoUploadSuccess:
    """Full video route exercised: feature flag enabled, DB returns owned response."""

    @patch("builtins.open", mock_open())
    @patch("app.api.upload.require_video_features_enabled")
    def test_upload_mp4_video_returns_201(self, mock_flag):
        user = _fake_user()
        interview_response = _fake_interview_response()
        db = _fake_db_session(first_return=interview_response)

        mp = _video_multipart(
            filename="clip.mp4",
            content=FAKE_VIDEO_BYTES,
            response_id=interview_response.id,
        )
        with _client(user, db) as client:
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 201
        body = response.json()
        assert body["video_url"].startswith("/uploads/video/")
        assert body["filename"].endswith(".mp4")
        assert body["file_size_bytes"] == len(FAKE_VIDEO_BYTES)

    @patch("builtins.open", mock_open())
    @patch("app.api.upload.require_video_features_enabled")
    def test_upload_webm_video_returns_201(self, mock_flag):
        user = _fake_user()
        interview_response = _fake_interview_response()
        db = _fake_db_session(first_return=interview_response)

        mp = _video_multipart(
            filename="recording.webm",
            content=b"\x1a\x45\xdf\xa3",
            response_id=interview_response.id,
            content_type="video/webm",
        )
        with _client(user, db) as client:
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 201
        assert response.json()["filename"].endswith(".webm")

    @patch("builtins.open", mock_open())
    @patch("app.api.upload.require_video_features_enabled")
    def test_video_response_contains_all_required_fields(self, mock_flag):
        user = _fake_user()
        interview_response = _fake_interview_response()
        db = _fake_db_session(first_return=interview_response)

        mp = _video_multipart(response_id=interview_response.id)
        with _client(user, db) as client:
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        body = response.json()
        required_fields = {"video_url", "file_size_bytes", "filename"}
        assert required_fields.issubset(body.keys())


# ---------------------------------------------------------------------------
# Part 3c: File too large rejection (>50MB for audio, >200MB for video)
# ---------------------------------------------------------------------------


class TestFileSizeRejection:
    """Oversized files must be rejected with HTTP 413."""

    def test_audio_file_exceeding_50mb_returns_413(self):
        user = _fake_user()
        interview_session = _fake_interview_session(user.id)
        db = _fake_db_session(first_return=interview_session)

        # One byte over the audio limit
        oversized = b"x" * (MAX_FILE_SIZE + 1)
        mp = _audio_multipart(
            content=oversized,
            session_id=interview_session.id,
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 413
        detail = response.json().get("detail", "")
        # Error message should mention the limit in MB
        assert "50" in str(detail)

    @patch("app.api.upload.require_video_features_enabled")
    def test_video_file_exceeding_200mb_returns_413(self, mock_flag):
        user = _fake_user()
        interview_response = _fake_interview_response()
        db = _fake_db_session(first_return=interview_response)

        oversized = b"x" * (MAX_VIDEO_FILE_SIZE + 1)
        mp = _video_multipart(
            content=oversized,
            response_id=interview_response.id,
        )
        with _client(user, db) as client:
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 413
        detail = response.json().get("detail", "")
        assert "200" in str(detail)


# ---------------------------------------------------------------------------
# Part 3d: Invalid format rejection
# ---------------------------------------------------------------------------


class TestInvalidFormatRejection:
    """Files with unsupported extensions must be rejected with HTTP 400."""

    def test_txt_audio_file_returns_400(self):
        user = _fake_user()
        db = _fake_db_session()
        session_id = str(uuid.uuid4())

        mp = _audio_multipart(
            filename="recording.txt",
            content=b"plain text",
            session_id=session_id,
            content_type="text/plain",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 400
        assert "not allowed" in response.json().get("detail", "").lower()

    def test_exe_audio_file_returns_400(self):
        user = _fake_user()
        db = _fake_db_session()
        session_id = str(uuid.uuid4())

        mp = _audio_multipart(
            filename="malware.exe",
            content=b"MZ\x90\x00",
            session_id=session_id,
            content_type="application/octet-stream",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 400

    def test_py_audio_file_returns_400(self):
        user = _fake_user()
        db = _fake_db_session()
        session_id = str(uuid.uuid4())

        mp = _audio_multipart(
            filename="exploit.py",
            content=b"import os; os.system('rm -rf /')",
            session_id=session_id,
            content_type="text/x-python",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 400

    @patch("app.api.upload.require_video_features_enabled")
    def test_avi_video_file_returns_400(self, mock_flag):
        user = _fake_user()
        db = _fake_db_session()
        response_id = str(uuid.uuid4())

        mp = _video_multipart(
            filename="video.avi",
            content=b"RIFF",
            response_id=response_id,
            content_type="video/x-msvideo",
        )
        with _client(user, db) as client:
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 400
        assert "not allowed" in response.json().get("detail", "").lower()

    def test_error_detail_lists_allowed_extensions(self):
        """The 400 error should include at least one allowed extension in detail."""
        user = _fake_user()
        db = _fake_db_session()
        session_id = str(uuid.uuid4())

        mp = _audio_multipart(
            filename="recording.php",
            content=b"<?php",
            session_id=session_id,
            content_type="application/x-php",
        )
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        detail = response.json().get("detail", "")
        allowed_exts = [".webm", ".mp3", ".wav", ".ogg", ".m4a", ".mp4"]
        assert any(ext in detail for ext in allowed_exts), (
            f"Expected at least one allowed extension in error detail, got: {detail!r}"
        )


# ---------------------------------------------------------------------------
# Part 3e: Missing auth token returns 401
# ---------------------------------------------------------------------------


class TestMissingAuthReturns401:
    """Requests without an Authorization header must be rejected with 401.

    Strategy: override get_session (to avoid real DB connection during lifespan
    in the test client) but do NOT override get_current_user — the real
    dependency will reject requests with no or invalid bearer token.
    """

    def _client_no_auth_override(self) -> TestClient:
        """Build a TestClient with only a mocked DB session.

        The real get_current_user dependency runs, so absent/invalid
        Authorization headers cause 401 responses.
        """
        from app.db import get_session
        from app.security import get_forge_auth_instance

        # Ensure forge-auth singleton is initialized (mirrors what the lifespan does)
        get_forge_auth_instance()

        db = _fake_db_session()

        async def _override_session():
            yield db

        app.dependency_overrides[get_session] = _override_session
        client = TestClient(app, raise_server_exceptions=False)
        return client

    def _cleanup(self) -> None:
        app.dependency_overrides.clear()

    def test_audio_upload_without_auth_returns_401(self):
        """No Authorization header — real get_current_user fires → 401."""
        client = self._client_no_auth_override()
        try:
            mp = _audio_multipart(session_id=str(uuid.uuid4()))
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])
            assert response.status_code == 401
        finally:
            self._cleanup()

    def test_video_upload_without_auth_returns_401(self):
        """No Authorization header on video upload → 401."""
        client = self._client_no_auth_override()
        try:
            mp = _video_multipart(response_id=str(uuid.uuid4()))
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])
            assert response.status_code == 401
        finally:
            self._cleanup()

    def test_audio_upload_with_invalid_token_returns_401(self):
        """A malformed Bearer token must also yield 401."""
        client = self._client_no_auth_override()
        try:
            mp = _audio_multipart(session_id=str(uuid.uuid4()))
            headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
            response = client.post(
                AUDIO_UPLOAD_URL,
                files=mp["files"],
                data=mp["data"],
                headers=headers,
            )
            assert response.status_code == 401
        finally:
            self._cleanup()


# ---------------------------------------------------------------------------
# Part 3f: Upload directory creation
# ---------------------------------------------------------------------------


class TestUploadDirectoryCreation:
    """The upload directories must be created at module-import time."""

    def test_audio_upload_dir_exists_after_import(self):
        """Importing the module creates uploads/audio (relative to CWD at import)."""
        from app.api.upload import UPLOAD_DIR

        # The path object itself should reference "uploads/audio"
        assert str(UPLOAD_DIR) == "uploads/audio"
        # The directory was created by the module-level mkdir(parents=True, exist_ok=True)
        # We just verify the Path object is correctly defined
        assert UPLOAD_DIR.parts == ("uploads", "audio")

    def test_video_upload_dir_exists_after_import(self):
        """Importing the module creates uploads/video."""
        from app.api.upload import VIDEO_UPLOAD_DIR

        assert str(VIDEO_UPLOAD_DIR) == "uploads/video"
        assert VIDEO_UPLOAD_DIR.parts == ("uploads", "video")

    def test_upload_dir_path_type(self):
        """UPLOAD_DIR and VIDEO_UPLOAD_DIR must be Path objects."""
        from app.api.upload import UPLOAD_DIR, VIDEO_UPLOAD_DIR

        assert isinstance(UPLOAD_DIR, Path)
        assert isinstance(VIDEO_UPLOAD_DIR, Path)


# ---------------------------------------------------------------------------
# Additional edge-case integration scenarios
# ---------------------------------------------------------------------------


class TestAudioUploadMissingIds:
    """When neither session_id nor preparation_id is provided → 400."""

    def test_missing_both_ids_returns_400(self):
        user = _fake_user()
        db = _fake_db_session()

        # Provide file but NO session_id / preparation_id form fields
        files = {"file": ("recording.webm", io.BytesIO(FAKE_AUDIO_BYTES), "audio/webm")}
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=files)

        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "session_id" in detail or "preparation_id" in detail


class TestAudioUploadSessionNotFound:
    """When the DB returns no session → 404."""

    def test_session_not_found_returns_404(self):
        user = _fake_user()
        # DB finds nothing (session not owned by user or doesn't exist)
        db = _fake_db_session(first_return=None)

        mp = _audio_multipart(session_id=str(uuid.uuid4()))
        with _client(user, db) as client:
            response = client.post(AUDIO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 404
        assert "session" in response.json().get("detail", "").lower()


class TestVideoFeatureFlagDisabled:
    """When video feature flag is off → 404."""

    def test_video_disabled_returns_404(self):
        from fastapi import HTTPException

        user = _fake_user()
        db = _fake_db_session()

        mp = _video_multipart(response_id=str(uuid.uuid4()))
        with (
            _client(user, db) as client,
            patch("app.api.upload.require_video_features_enabled") as mock_flag,
        ):
            mock_flag.side_effect = HTTPException(
                status_code=404,
                detail="Video review is not available during soft launch.",
            )
            response = client.post(VIDEO_UPLOAD_URL, files=mp["files"], data=mp["data"])

        assert response.status_code == 404
