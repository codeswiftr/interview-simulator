"""Audio transcription API endpoints."""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.ai.transcriber import Transcriber, TranscriptionResult
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


class TranscriptionResponse(BaseModel):
    """Response model for transcription endpoint."""

    text: str
    duration_seconds: float | None = None
    language: str | None = None
    segments: list[dict] | None = None
    estimated_cost: float | None = None


class TranscriptionError(BaseModel):
    """Error response model."""

    detail: str
    error_type: str


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": TranscriptionError, "description": "Invalid audio file"},
        413: {"model": TranscriptionError, "description": "File too large"},
        422: {"model": TranscriptionError, "description": "Unsupported format"},
    },
)
async def transcribe_audio(
    file: UploadFile = File(...),
    include_timestamps: bool = False,
    language: str | None = None,
    current_user: User = Depends(get_current_user),
) -> TranscriptionResponse:
    """Transcribe an audio file using OpenAI Whisper.

    Accepts audio files up to 25MB in formats:
    mp3, mp4, mpeg, mpga, m4a, wav, webm

    Args:
        file: Audio file to transcribe
        include_timestamps: Include word-level timestamps in response
        language: Optional language hint (ISO 639-1 code, e.g., 'en')

    Returns:
        TranscriptionResponse with transcript text and metadata
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate content type
    allowed_content_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/wav",
        "audio/webm",
        "audio/x-m4a",
        "video/webm",  # webm can be video container with audio
        "application/octet-stream",  # Allow generic binary
    ]

    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_content_types:
        logger.warning(f"Received file with content type: {content_type}")
        # Don't reject outright - let Whisper handle format validation

    # Read file content
    content = await file.read()

    # Check file size (25MB limit)
    max_size = 25 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 25MB, got {len(content) / (1024 * 1024):.1f}MB",
        )

    # Write to temp file
    suffix = Path(file.filename).suffix or ".webm"
    tmp_path = None  # Initialize before try to avoid UnboundLocalError in finally
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe
        transcriber = Transcriber()
        result: TranscriptionResult = await transcriber.transcribe(
            tmp_path,
            language=language,
            include_timestamps=include_timestamps,
        )

        # Calculate cost estimate if we have duration
        estimated_cost = None
        if result.duration_seconds:
            estimated_cost = transcriber.estimate_cost(result.duration_seconds)

        return TranscriptionResponse(
            text=result.text,
            duration_seconds=result.duration_seconds,
            language=result.language,
            segments=result.segments,
            estimated_cost=estimated_cost,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from None
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {e!s}",
        ) from None
    finally:
        # Clean up temp file (only if it was created)
        if tmp_path is not None:
            import contextlib

            with contextlib.suppress(Exception):
                Path(tmp_path).unlink(missing_ok=True)


@router.get("/supported-formats")
async def get_supported_formats() -> dict:
    """Get list of supported audio formats and limits."""
    return {
        "formats": Transcriber.SUPPORTED_FORMATS,
        "max_file_size_mb": Transcriber.MAX_FILE_SIZE_MB,
        "cost_per_minute_usd": 0.006,
    }
