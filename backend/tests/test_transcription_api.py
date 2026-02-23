"""Tests for transcription API endpoints."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


async def create_test_user_and_login(client: AsyncClient, email: str = "test@example.com") -> str:
    """Create a test user, login, and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "SecureTest123!"})
    resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": "SecureTest123!"}
    )
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_transcribe_audio_success(client: AsyncClient):
    """Test successful audio transcription."""
    token = await create_test_user_and_login(client)

    # Create a mock audio file
    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    # Mock the Transcriber
    mock_result = MagicMock()
    mock_result.text = "This is transcribed text"
    mock_result.duration_seconds = 30.0
    mock_result.language = "en"
    mock_result.segments = None

    with patch("app.api.transcription.Transcriber") as MockTranscriber:
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(return_value=mock_result)
        mock_transcriber_instance.estimate_cost.return_value = 0.003

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "This is transcribed text"
        assert data["duration_seconds"] == 30.0
        assert data["language"] == "en"
        assert data["estimated_cost"] == 0.003


@pytest.mark.asyncio
async def test_transcribe_audio_no_filename(client: AsyncClient):
    """Test transcription with no filename returns 422 (FastAPI validation error)."""
    token = await create_test_user_and_login(client)

    # Create file without filename - FastAPI returns 422 for invalid file uploads
    files = {"file": (None, BytesIO(b"content"), "audio/webm")}

    response = await client.post(
        "/api/v1/transcription/transcribe",
        headers={"Authorization": token},
        files=files,
    )

    # FastAPI returns 422 for validation errors on file uploads without filenames
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_transcribe_audio_file_too_large(client: AsyncClient):
    """Test transcription with file exceeding 25MB returns 413."""
    token = await create_test_user_and_login(client)

    # Create a file larger than 25MB
    large_content = b"0" * (26 * 1024 * 1024)  # 26MB
    files = {"file": ("large.webm", BytesIO(large_content), "audio/webm")}

    response = await client.post(
        "/api/v1/transcription/transcribe",
        headers={"Authorization": token},
        files=files,
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transcribe_audio_unsupported_format_error(client: AsyncClient):
    """Test transcription with unsupported format returns 422."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"
    files = {"file": ("audio.txt", BytesIO(audio_content), "text/plain")}

    with patch("app.api.transcription.Transcriber") as MockTranscriber:
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(
            side_effect=ValueError("Unsupported audio format: txt")
        )

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
        )

        assert response.status_code == 422
        assert "unsupported" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transcribe_audio_with_timestamps(client: AsyncClient):
    """Test transcription with timestamps."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    mock_result = MagicMock()
    mock_result.text = "Hello world"
    mock_result.duration_seconds = 2.5
    mock_result.language = "en"
    mock_result.segments = [{"start": 0.0, "end": 2.5, "text": "Hello world"}]

    with patch("app.api.transcription.Transcriber") as MockTranscriber:
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(return_value=mock_result)
        mock_transcriber_instance.estimate_cost.return_value = 0.000025

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
            params={"include_timestamps": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["segments"] is not None
        assert len(data["segments"]) == 1


@pytest.mark.asyncio
async def test_transcribe_audio_with_language_hint(client: AsyncClient):
    """Test transcription with language hint."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    mock_result = MagicMock()
    mock_result.text = "Bonjour le monde"
    mock_result.duration_seconds = 5.0
    mock_result.language = "fr"
    mock_result.segments = None

    with patch("app.api.transcription.Transcriber") as MockTranscriber:
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(return_value=mock_result)
        mock_transcriber_instance.estimate_cost.return_value = 0.0005

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
            params={"language": "fr"},
        )

        assert response.status_code == 200
        # Verify language hint was passed to transcriber
        mock_transcriber_instance.transcribe.assert_called_once()
        call_args = mock_transcriber_instance.transcribe.call_args
        assert call_args.kwargs.get("language") == "fr"


@pytest.mark.asyncio
async def test_transcribe_audio_general_exception(client: AsyncClient):
    """Test transcription handles general exceptions and returns 500."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    with patch("app.api.transcription.Transcriber") as MockTranscriber:
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(side_effect=Exception("Unexpected error"))

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
        )

        assert response.status_code == 500
        assert "transcription failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transcribe_audio_requires_authentication(client: AsyncClient):
    """Test transcription endpoint requires authentication."""
    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    response = await client.post(
        "/api/v1/transcription/transcribe",
        files=files,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_supported_formats(client: AsyncClient):
    """Test getting supported formats list."""
    response = await client.get("/api/v1/transcription/supported-formats")

    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    assert "max_file_size_mb" in data
    assert "cost_per_minute_usd" in data
    assert data["max_file_size_mb"] == 25
    assert data["cost_per_minute_usd"] == 0.006


@pytest.mark.asyncio
async def test_transcribe_audio_file_not_found_error(client: AsyncClient):
    """Test transcription handles FileNotFoundError and returns 400."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"
    files = {"file": ("audio.webm", BytesIO(audio_content), "audio/webm")}

    with (
        patch("app.api.transcription.Transcriber") as MockTranscriber,
        patch("tempfile.NamedTemporaryFile") as mock_temp,
    ):
        # Simulate file write failure
        mock_temp.return_value.__enter__.return_value.name = "/nonexistent/path/file.webm"
        mock_transcriber_instance = MockTranscriber.return_value
        mock_transcriber_instance.transcribe = AsyncMock(
            side_effect=FileNotFoundError("File not found")
        )

        response = await client.post(
            "/api/v1/transcription/transcribe",
            headers={"Authorization": token},
            files=files,
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_transcribe_audio_content_type_handling(client: AsyncClient):
    """Test transcription handles various content types."""
    token = await create_test_user_and_login(client)

    audio_content = b"fake audio content"

    # Test with different content types that should be allowed
    content_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/webm",
        "application/octet-stream",  # Generic binary
    ]

    mock_result = MagicMock()
    mock_result.text = "Transcribed text"
    mock_result.duration_seconds = 10.0
    mock_result.language = "en"
    mock_result.segments = None

    for content_type in content_types:
        files = {"file": ("audio.webm", BytesIO(audio_content), content_type)}

        with patch("app.api.transcription.Transcriber") as MockTranscriber:
            mock_transcriber_instance = MockTranscriber.return_value
            mock_transcriber_instance.transcribe = AsyncMock(return_value=mock_result)
            mock_transcriber_instance.estimate_cost.return_value = 0.001

            response = await client.post(
                "/api/v1/transcription/transcribe",
                headers={"Authorization": token},
                files=files,
            )

            assert response.status_code == 200, f"Failed for content type: {content_type}"
