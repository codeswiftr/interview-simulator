"""Team and organization management endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user
from app.models.organization import (
    InvitationRead,
    InvitationStatus,
    MemberRole,
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.models.user import User
from app.services.team_service import TeamService

logger = logging.getLogger(__name__)

router = APIRouter()
_team_service = TeamService()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class TeamCreateRequest(SQLModel):
    name: str = Field(min_length=2, max_length=200)
    seat_count: int = Field(default=5, ge=2, le=100)


class InviteMembersRequest(SQLModel):
    emails: list[str] = Field(min_length=1, max_length=20)


class TeamMemberResponse(SQLModel):
    user_id: UUID
    full_name: str | None
    email: str
    role: MemberRole
    joined_at: datetime


class TeamResponse(SQLModel):
    id: UUID
    name: str
    slug: str
    seat_count: int
    seats_used: int
    subscription_status: str | None
    is_admin: bool
    members: list[TeamMemberResponse]
    pending_invitations: list[InvitationRead]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_org_or_404(session: AsyncSession, org_id: UUID) -> Organization:
    """Fetch an org by PK or raise 404."""
    result = await session.exec(select(Organization).where(Organization.id == org_id))
    org = result.first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


async def _require_member(
    session: AsyncSession,
    org: Organization,
    user: User,
) -> OrganizationMember:
    """Return the OrganizationMember record or raise 403."""
    result = await session.exec(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    member = result.first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )
    return member


async def _require_admin(
    session: AsyncSession,
    org: Organization,
    user: User,
) -> OrganizationMember:
    """Return the OrganizationMember record only if the user is ADMIN, else 403."""
    member = await _require_member(session, org, user)
    if member.role != MemberRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return member


async def _build_team_response(
    session: AsyncSession,
    org: Organization,
    current_user: User,
) -> TeamResponse:
    """Assemble a TeamResponse with full member list and pending invitations."""
    # Load members
    member_rows = (
        await session.exec(
            select(OrganizationMember).where(OrganizationMember.org_id == org.id)
        )
    ).all()

    # Batch-load users for members
    user_ids = [m.user_id for m in member_rows]
    users_result = await session.exec(select(User).where(User.id.in_(user_ids)))  # type: ignore[attr-defined]
    user_map: dict[UUID, User] = {u.id: u for u in users_result.all()}

    members: list[TeamMemberResponse] = [
        TeamMemberResponse(
            user_id=m.user_id,
            full_name=user_map[m.user_id].full_name if m.user_id in user_map else None,
            email=user_map[m.user_id].email if m.user_id in user_map else "",
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in member_rows
        if m.user_id in user_map
    ]

    # Load pending invitations
    invitations_result = await session.exec(
        select(OrganizationInvitation).where(
            OrganizationInvitation.org_id == org.id,
            OrganizationInvitation.status == InvitationStatus.PENDING,
        )
    )
    pending_invitations: list[InvitationRead] = [
        InvitationRead(
            id=inv.id,
            org_id=inv.org_id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at,
            accepted_at=inv.accepted_at,
            created_at=inv.created_at,
        )
        for inv in invitations_result.all()
    ]

    # Determine if current user is admin
    is_admin = any(
        m.user_id == current_user.id and m.role == MemberRole.ADMIN for m in member_rows
    )

    return TeamResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        seat_count=org.seat_count,
        seats_used=org.seats_used,
        subscription_status=org.subscription_status,
        is_admin=is_admin,
        members=members,
        pending_invitations=pending_invitations,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Create a new organization. The authenticated user becomes the admin owner."""
    org = await _team_service.create_organization(
        session=session,
        owner=current_user,
        name=payload.name,
        seat_count=payload.seat_count,
    )
    return await _build_team_response(session, org, current_user)


@router.get("/me", response_model=TeamResponse)
async def get_my_team(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Return the team the current user belongs to."""
    team_id = getattr(current_user, "team_id", None)
    if not team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of any team",
        )
    org = await _get_org_or_404(session, team_id)
    # Verify membership (handles edge case where team_id is stale)
    await _require_member(session, org, current_user)
    return await _build_team_response(session, org, current_user)


@router.get("/{org_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TeamMemberResponse]:
    """List all members of an organization. Admin only."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    member_rows = (
        await session.exec(
            select(OrganizationMember).where(OrganizationMember.org_id == org.id)
        )
    ).all()

    user_ids = [m.user_id for m in member_rows]
    users_result = await session.exec(select(User).where(User.id.in_(user_ids)))  # type: ignore[attr-defined]
    user_map: dict[UUID, User] = {u.id: u for u in users_result.all()}

    return [
        TeamMemberResponse(
            user_id=m.user_id,
            full_name=user_map[m.user_id].full_name if m.user_id in user_map else None,
            email=user_map[m.user_id].email if m.user_id in user_map else "",
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in member_rows
        if m.user_id in user_map
    ]


@router.post("/{org_id}/invitations", response_model=list[InvitationRead])
async def invite_members(
    org_id: UUID,
    payload: InviteMembersRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[InvitationRead]:
    """Send team invitations. Admin only. Returns invitation records for each email."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    results: list[InvitationRead] = []
    for email in payload.emails:
        email_lower = email.strip().lower()
        try:
            invitation = await _team_service.send_invitation(
                session=session,
                org=org,
                email=email_lower,
                invited_by=current_user,
            )
            results.append(
                InvitationRead(
                    id=invitation.id,
                    org_id=invitation.org_id,
                    email=invitation.email,
                    role=invitation.role,
                    status=invitation.status,
                    expires_at=invitation.expires_at,
                    accepted_at=invitation.accepted_at,
                    created_at=invitation.created_at,
                )
            )
        except Exception as exc:
            logger.warning("Failed to send invitation to %s: %s", email_lower, exc)
            # Continue processing remaining emails

    return results


@router.get("/invitations/{token}", response_model=InvitationRead)
async def validate_invitation(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> InvitationRead:
    """Validate an invitation token (public endpoint — no auth required).

    Returns the invitation details so the frontend can display org name and
    inviter before the user logs in or registers.
    """
    result = await session.exec(
        select(OrganizationInvitation).where(OrganizationInvitation.token == token)
    )
    invitation = result.first()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Invitation is no longer valid (status: {invitation.status})",
        )
    return InvitationRead(
        id=invitation.id,
        org_id=invitation.org_id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_at=invitation.created_at,
    )


@router.post("/invitations/{token}/accept", response_model=TeamResponse)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Accept a team invitation. Authenticated endpoint."""
    try:
        member = await _team_service.accept_invitation(
            session=session, token=token, user=current_user
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    org = await _get_org_or_404(session, member.org_id)
    return await _build_team_response(session, org, current_user)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove a member from the organization. Admin only."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    # Prevent admin from removing themselves if they are the only admin
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself. Transfer ownership first.",
        )

    await _team_service.remove_member(session=session, org=org, user_id=user_id)


@router.delete("/{org_id}/invitations/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    org_id: UUID,
    inv_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke a pending invitation. Admin only."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    result = await session.exec(
        select(OrganizationInvitation).where(
            OrganizationInvitation.id == inv_id,
            OrganizationInvitation.org_id == org_id,
        )
    )
    invitation = result.first()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke invitation with status '{invitation.status}'",
        )

    invitation.status = InvitationStatus.DECLINED
    session.add(invitation)
    await session.commit()


# ---------------------------------------------------------------------------
# Phase 2 schemas
# ---------------------------------------------------------------------------


class UpdateRoleRequest(SQLModel):
    role: MemberRole


class UpdateOrgRequest(SQLModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    seat_count: int | None = Field(default=None, ge=2, le=200)


class MemberUsageResponse(SQLModel):
    user_id: UUID
    full_name: str | None
    email: str
    role: MemberRole
    interviews_total: int
    interviews_this_month: int


# ---------------------------------------------------------------------------
# Phase 2 endpoints
# ---------------------------------------------------------------------------


@router.patch("/{org_id}", response_model=TeamResponse)
async def update_team(
    org_id: UUID,
    payload: UpdateOrgRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Update org name or seat count. Admin only."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)
    if payload.name is not None:
        org.name = payload.name
    if payload.seat_count is not None:
        if payload.seat_count < org.seats_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce seats below current usage ({org.seats_used} seats in use)",
            )
        org.seat_count = payload.seat_count
    from datetime import UTC, datetime
    org.updated_at = datetime.now(UTC)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return await _build_team_response(session, org, current_user)


@router.patch("/{org_id}/members/{user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    payload: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamMemberResponse:
    """Promote or demote a member's role. Admin only. Cannot demote the last admin."""
    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    result = await session.exec(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Guard: can't demote if this is the last admin
    if member.role == MemberRole.ADMIN and payload.role == MemberRole.MEMBER:
        admins = (
            await session.exec(
                select(OrganizationMember).where(
                    OrganizationMember.org_id == org_id,
                    OrganizationMember.role == MemberRole.ADMIN,
                )
            )
        ).all()
        if len(admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin. Promote another member first.",
            )

    member.role = payload.role
    session.add(member)
    await session.commit()
    await session.refresh(member)

    user_result = await session.exec(select(User).where(User.id == user_id))
    user = user_result.first()
    return TeamMemberResponse(
        user_id=member.user_id,
        full_name=user.full_name if user else None,
        email=user.email if user else "",
        role=member.role,
        joined_at=member.joined_at,
    )


@router.get("/{org_id}/usage", response_model=list[MemberUsageResponse])
async def get_team_usage(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MemberUsageResponse]:
    """Return per-member interview usage stats. Admin only."""
    from datetime import UTC, datetime
    from sqlalchemy import func
    from app.models.interview import InterviewSession

    org = await _get_org_or_404(session, org_id)
    await _require_admin(session, org, current_user)

    # Load members
    member_rows = (
        await session.exec(
            select(OrganizationMember).where(OrganizationMember.org_id == org.id)
        )
    ).all()

    user_ids = [m.user_id for m in member_rows]
    users_result = await session.exec(select(User).where(User.id.in_(user_ids)))  # type: ignore[attr-defined]
    user_map: dict[UUID, User] = {u.id: u for u in users_result.all()}

    now_utc = datetime.now(UTC)
    month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total interview counts per user_id
    total_counts_result = await session.exec(
        select(InterviewSession.user_id, func.count(InterviewSession.id).label("cnt"))
        .where(InterviewSession.user_id.in_(user_ids))  # type: ignore[attr-defined]
        .group_by(InterviewSession.user_id)
    )
    total_map: dict[UUID, int] = {row[0]: row[1] for row in total_counts_result.all()}

    # Monthly interview counts
    monthly_counts_result = await session.exec(
        select(InterviewSession.user_id, func.count(InterviewSession.id).label("cnt"))
        .where(
            InterviewSession.user_id.in_(user_ids),  # type: ignore[attr-defined]
            InterviewSession.created_at >= month_start,
        )
        .group_by(InterviewSession.user_id)
    )
    monthly_map: dict[UUID, int] = {row[0]: row[1] for row in monthly_counts_result.all()}

    return [
        MemberUsageResponse(
            user_id=m.user_id,
            full_name=user_map[m.user_id].full_name if m.user_id in user_map else None,
            email=user_map[m.user_id].email if m.user_id in user_map else "",
            role=m.role,
            interviews_total=total_map.get(m.user_id, 0),
            interviews_this_month=monthly_map.get(m.user_id, 0),
        )
        for m in member_rows
    ]
