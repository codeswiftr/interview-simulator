"""Audio file upload endpoints."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.feature_flags import require_video_features_enabled
from app.models.interview import InterviewResponse, InterviewSession
from app.models.user import User

router = APIRouter()

# Upload directory for audio files (local storage for MVP)
UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed audio formats
ALLOWED_EXTENSIONS = {".webm", ".mp3", ".wav", ".ogg", ".m4a", ".mp4"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Upload directory for video files
VIDEO_UPLOAD_DIR = Path("uploads/video")
VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_ALLOWED_EXTENSIONS = {".webm", ".mp4", ".mov", ".mkv"}
MAX_VIDEO_FILE_SIZE = 200 * 1024 * 1024  # 200MB


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""

    audio_url: str
    file_size_bytes: int
    filename: str


class VideoUploadResponse(BaseModel):
    """Response model for video upload."""

    video_url: str
    file_size_bytes: int
    filename: str


@router.post("/audio", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...),
    session_id: str | None = Form(None),
    question_id: str | None = Form(None),
    preparation_id: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
) -> AudioUploadResponse:
    """Upload an audio file for an interview response or practice attempt.

    Validates that:
    - File is an allowed audio format
    - File size is within limits
    - Interview session or preparation belongs to the current user
    """
    from app.models.preparation import AnswerPreparation

    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate that either session_id or preparation_id is provided
    if not session_id and not preparation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either session_id or preparation_id must be provided",
        )

    # Verify ownership - interview session or preparation
    if session_id:
        result = await db_session.exec(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == current_user.id,
            )
        )
        resource = result.first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found",
            )
        # Use session_id and question_id for filename
        resource_id = session_id
        secondary_id = question_id or session_id
    elif preparation_id:
        result = await db_session.exec(
            select(AnswerPreparation).where(
                AnswerPreparation.id == preparation_id,
                AnswerPreparation.user_id == current_user.id,
            )
        )
        resource = result.first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preparation not found",
            )
        # Use preparation_id for filename
        resource_id = preparation_id
        secondary_id = preparation_id

    # Read and validate file size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file not allowed",
        )

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    filename = f"{resource_id}_{secondary_id}_{unique_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Generate URL (for local development, use relative path)
    # In production, this would be an S3 URL or similar
    audio_url = f"/uploads/audio/{filename}"

    return AudioUploadResponse(
        audio_url=audio_url,
        file_size_bytes=file_size,
        filename=filename,
    )


@router.post("/video", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    response_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
) -> VideoUploadResponse:
    """Upload a video file for a specific interview response.

    Validates:
    - File extension and size
    - Response ownership (response belongs to current user)
    """
    require_video_features_enabled()

    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in VIDEO_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "File type not allowed. Allowed types: "
                f"{', '.join(sorted(VIDEO_ALLOWED_EXTENSIONS))}"
            ),
        )

    # Verify response ownership
    result = await db_session.exec(
        select(InterviewResponse)
        .join(InterviewSession, InterviewResponse.session_id == InterviewSession.id)
        .where(InterviewResponse.id == response_id, InterviewSession.user_id == current_user.id)
    )
    response = result.first()
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found or access denied",
        )

    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file not allowed",
        )

    if file_size > MAX_VIDEO_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "File too large. Maximum size is "
                f"{MAX_VIDEO_FILE_SIZE // (1024 * 1024)}MB"
            ),
        )

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    filename = f"{response_id}_{unique_id}{file_ext}"
    file_path = VIDEO_UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(content)

    video_url = f"/uploads/video/{filename}"
    response.video_url = video_url
    await db_session.commit()

    return VideoUploadResponse(
        video_url=video_url,
        file_size_bytes=file_size,
        filename=filename,
    )
