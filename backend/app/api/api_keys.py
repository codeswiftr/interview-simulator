"""API Key management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.models.api_key import APIKeyCreate, APIKeyCreateResponse, APIKeyRead, APIKeyUpdate
from app.models.user import User
from app.services import api_key_service

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIKeyCreateResponse:
    """Create a new API key.

    The plain key is only returned once in this response. Store it securely
    as it cannot be retrieved later.

    Args:
        key_data: API key creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The created API key with the plain key (shown only once)

    Raises:
        HTTPException 400: If key limit exceeded or invalid data
    """
    try:
        plain_key, api_key = await api_key_service.create_api_key(
            session, current_user.id, key_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Convert to read schema
    api_key_read = APIKeyRead(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        request_count=api_key.request_count,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )

    return APIKeyCreateResponse(key=plain_key, api_key=api_key_read)


@router.get("/", response_model=list[APIKeyRead])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[APIKeyRead]:
    """List all API keys for the current user.

    Args:
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of API keys (without the actual keys)
    """
    keys = await api_key_service.get_user_api_keys(session, current_user.id)

    return [
        APIKeyRead(
            id=key.id,
            user_id=key.user_id,
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=key.scopes,
            rate_limit=key.rate_limit,
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            request_count=key.request_count,
            expires_at=key.expires_at,
            created_at=key.created_at,
        )
        for key in keys
    ]


@router.get("/{key_id}", response_model=APIKeyRead)
async def get_api_key(
    key_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIKeyRead:
    """Get a specific API key by ID.

    Args:
        key_id: ID of the API key
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The API key details

    Raises:
        HTTPException 404: If key not found or not owned by user
    """
    api_key = await api_key_service.get_api_key_by_id(session, key_id, current_user.id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return APIKeyRead(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        request_count=api_key.request_count,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.patch("/{key_id}", response_model=APIKeyRead)
async def update_api_key(
    key_id: UUID,
    update_data: APIKeyUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIKeyRead:
    """Update an API key.

    Args:
        key_id: ID of the API key to update
        update_data: Update data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated API key

    Raises:
        HTTPException 404: If key not found or not owned by user
    """
    api_key = await api_key_service.update_api_key(
        session, key_id, current_user.id, update_data
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return APIKeyRead(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        request_count=api_key.request_count,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an API key.

    Args:
        key_id: ID of the API key to delete
        current_user: Currently authenticated user
        session: Database session

    Raises:
        HTTPException 404: If key not found or not owned by user
    """
    deleted = await api_key_service.delete_api_key(session, key_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
