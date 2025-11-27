"""Audio file upload endpoints."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.models.interview import InterviewSession
from app.models.user import User

router = APIRouter()

# Upload directory for audio files (local storage for MVP)
UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed audio formats
ALLOWED_EXTENSIONS = {".webm", ".mp3", ".wav", ".ogg", ".m4a"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""

    audio_url: str
    file_size_bytes: int
    filename: str


@router.post("/audio", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    question_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
) -> AudioUploadResponse:
    """Upload an audio file for an interview response.

    Validates that:
    - File is an allowed audio format
    - File size is within limits
    - Interview session belongs to the current user
    """
    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Verify interview session exists and belongs to user
    result = await db_session.exec(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    interview = result.first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found",
        )

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
    filename = f"{session_id}_{question_id}_{unique_id}{file_ext}"
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
