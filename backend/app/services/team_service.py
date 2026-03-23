"""Team and organization management service."""

import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.organization import (
    InvitationStatus,
    MemberRole,
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.models.user import SubscriptionTier, User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class TeamService:
    """Service for organization and team membership management."""

    def __init__(self) -> None:
        self.email_service = EmailService()

    async def create_organization(
        self,
        session: AsyncSession,
        owner: User,
        name: str,
        seat_count: int = 5,
    ) -> Organization:
        """Create a new organization and add the owner as an ADMIN member.

        Args:
            session: Async database session.
            owner: User who will own and administer the organization.
            name: Human-readable organization name.
            seat_count: Number of licensed seats (default 5).

        Returns:
            The newly created Organization.
        """
        slug = self._make_slug(name)
        org = Organization(
            name=name,
            slug=slug,
            owner_id=owner.id,
            seat_count=seat_count,
            seats_used=1,
        )
        session.add(org)
        await session.flush()  # populate org.id before using it

        member = OrganizationMember(
            org_id=org.id,
            user_id=owner.id,
            role=MemberRole.ADMIN,
        )
        session.add(member)

        owner.team_id = org.id  # type: ignore[attr-defined]  # column added via migration
        owner.subscription_tier = SubscriptionTier.TEAM
        session.add(owner)

        await session.commit()
        await session.refresh(org)
        return org

    async def add_member(
        self,
        session: AsyncSession,
        org: Organization,
        user: User,
        role: MemberRole = MemberRole.MEMBER,
        invited_by: UUID | None = None,
    ) -> OrganizationMember:
        """Add a user to an organization.

        Args:
            session: Async database session.
            org: Target organization.
            user: User to add.
            role: Role to assign (default MEMBER).
            invited_by: UUID of the inviting user, if applicable.

        Returns:
            The new OrganizationMember record.

        Raises:
            ValueError: If no seats are available.
        """
        if org.seats_used >= org.seat_count:
            raise ValueError(
                f"No seats available ({org.seats_used}/{org.seat_count}). "
                "Upgrade your plan to add more seats."
            )

        member = OrganizationMember(
            org_id=org.id,
            user_id=user.id,
            role=role,
            invited_by=invited_by,
        )
        session.add(member)

        org.seats_used += 1
        session.add(org)

        user.team_id = org.id  # type: ignore[attr-defined]
        user.subscription_tier = SubscriptionTier.TEAM
        session.add(user)

        await session.commit()
        await session.refresh(member)
        return member

    async def remove_member(
        self,
        session: AsyncSession,
        org: Organization,
        user_id: UUID,
    ) -> None:
        """Remove a member from an organization.

        Reverts the user to FREE tier and clears their team_id.
        No-op if the user is not a member.

        Args:
            session: Async database session.
            org: Organization to remove the member from.
            user_id: UUID of the user to remove.
        """
        stmt = select(OrganizationMember).where(
            OrganizationMember.org_id == org.id,
            OrganizationMember.user_id == user_id,
        )
        result = await session.exec(stmt)
        member = result.first()
        if not member:
            return

        await session.delete(member)

        user_stmt = select(User).where(User.id == user_id)
        user_result = await session.exec(user_stmt)
        user = user_result.first()
        if user:
            user.team_id = None  # type: ignore[attr-defined]
            user.subscription_tier = SubscriptionTier.FREE
            session.add(user)

        org.seats_used = max(0, org.seats_used - 1)
        session.add(org)

        await session.commit()

    async def send_invitation(
        self,
        session: AsyncSession,
        org: Organization,
        email: str,
        invited_by: User,
    ) -> OrganizationInvitation:
        """Create and send a team invitation email.

        Idempotent: if a PENDING invitation already exists for this (org, email)
        pair the existing record is returned without creating a duplicate.

        Args:
            session: Async database session.
            org: Organization the invite is for.
            email: Email address of the invitee.
            invited_by: User sending the invitation.

        Returns:
            The OrganizationInvitation record (new or existing PENDING).
        """
        # Return existing pending invite rather than creating a duplicate
        stmt = select(OrganizationInvitation).where(
            OrganizationInvitation.org_id == org.id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.status == InvitationStatus.PENDING,
        )
        result = await session.exec(stmt)
        existing = result.first()
        if existing:
            return existing

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        invitation = OrganizationInvitation(
            org_id=org.id,
            email=email,
            invited_by=invited_by.id,
            token=token,
            expires_at=expires_at,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)

        # Send email best-effort — don't fail the API call if email delivery fails
        try:
            await self.email_service.send_team_invitation(
                to_email=email,
                org_name=org.name,
                inviter_name=invited_by.full_name or invited_by.email,
                token=token,
            )
        except Exception as exc:
            logger.warning(
                "Failed to send team invitation email to %s for org %s: %s",
                email,
                org.id,
                exc,
            )

        return invitation

    async def accept_invitation(
        self,
        session: AsyncSession,
        token: str,
        user: User,
    ) -> OrganizationMember:
        """Accept a team invitation by its token.

        Args:
            session: Async database session.
            token: Invitation token from the email link.
            user: Authenticated user accepting the invite.

        Returns:
            The new OrganizationMember record.

        Raises:
            ValueError: On invalid token, already-used token, expired token,
                        or inactive organization.
        """
        stmt = select(OrganizationInvitation).where(
            OrganizationInvitation.token == token
        )
        result = await session.exec(stmt)
        invitation = result.first()

        if not invitation:
            raise ValueError("Invitation not found")
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Invitation already {invitation.status}")

        # Normalize timezone: stored timestamps may be naive UTC from older rows
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            from datetime import timezone
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(UTC):
            invitation.status = InvitationStatus.EXPIRED
            session.add(invitation)
            await session.commit()
            raise ValueError("Invitation has expired")

        org_stmt = select(Organization).where(Organization.id == invitation.org_id)
        org_result = await session.exec(org_stmt)
        org = org_result.first()
        if not org or not org.is_active:
            raise ValueError("Organization not found or inactive")

        member = await self.add_member(
            session, org, user, invited_by=invitation.invited_by
        )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(UTC)
        session.add(invitation)
        await session.commit()

        return member

    @staticmethod
    def _make_slug(name: str) -> str:
        """Generate a URL-safe slug from an organization name.

        Appends a random hex suffix to ensure uniqueness.
        """
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
        slug = slug.strip("-")[:95]  # leave room for the 9-char suffix
        return slug + "-" + secrets.token_hex(4)
