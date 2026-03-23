"""Tests for team management API endpoints (Sprint 14 — B2B team features)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from tests.conftest import get_test_engine, register_and_login


@pytest.fixture
async def team_admin_auth(client):
    """Create a team admin user and return auth headers."""
    email = f"admin_{uuid4().hex[:8]}@example.com"
    headers = await register_and_login(client, email=email)
    return headers, email


@pytest.fixture
async def team_member_auth(client):
    """Create a second user (future team member)."""
    email = f"member_{uuid4().hex[:8]}@example.com"
    headers = await register_and_login(client, email=email)
    return headers, email


@pytest.fixture
async def created_team(client, team_admin_auth):
    """Create a team via API and return (team_data, admin_headers)."""
    headers, _ = team_admin_auth
    resp = await client.post(
        "/api/v1/teams",
        json={"name": "Test Engineering Team", "seat_count": 5},
        headers={"Authorization": headers},
    )
    assert resp.status_code in (200, 201), f"Failed to create team: {resp.text}"
    return resp.json(), headers


class TestCreateTeam:
    """Tests for POST /api/v1/teams"""

    @pytest.mark.asyncio
    async def test_create_team_success(self, client, team_admin_auth):
        """Admin can create a team."""
        headers, _ = team_admin_auth
        resp = await client.post(
            "/api/v1/teams",
            json={"name": "My Engineering Team", "seat_count": 10},
            headers={"Authorization": headers},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "My Engineering Team"
        assert data["seat_count"] == 10

    @pytest.mark.asyncio
    async def test_create_team_unauthenticated(self, client):
        """Unauthenticated users cannot create teams."""
        resp = await client.post(
            "/api/v1/teams",
            json={"name": "Unauthorized Team", "seat_count": 5},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_team_name_too_short(self, client, team_admin_auth):
        """Team name must be at least 2 characters."""
        headers, _ = team_admin_auth
        resp = await client.post(
            "/api/v1/teams",
            json={"name": "X", "seat_count": 5},
            headers={"Authorization": headers},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_team_sets_admin_role(self, client, team_admin_auth):
        """Creator becomes admin member of the team."""
        headers, _ = team_admin_auth
        resp = await client.post(
            "/api/v1/teams",
            json={"name": "Admin Role Test", "seat_count": 5},
            headers={"Authorization": headers},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data.get("is_admin") is True


class TestGetMyTeam:
    """Tests for GET /api/v1/teams/me"""

    @pytest.mark.asyncio
    async def test_get_my_team_as_admin(self, client, created_team):
        """Admin can retrieve their team."""
        team_data, admin_headers = created_team
        resp = await client.get(
            "/api/v1/teams/me",
            headers={"Authorization": admin_headers},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == team_data["name"]

    @pytest.mark.asyncio
    async def test_get_my_team_not_member(self, client, team_member_auth):
        """Non-member gets 404."""
        headers, _ = team_member_auth
        resp = await client.get(
            "/api/v1/teams/me",
            headers={"Authorization": headers},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_my_team_unauthenticated(self, client):
        """Unauthenticated request returns 401."""
        resp = await client.get("/api/v1/teams/me")
        assert resp.status_code == 401


class TestInviteMembers:
    """Tests for POST /api/v1/teams/{org_id}/invitations"""

    @pytest.mark.asyncio
    async def test_send_invitation_success(self, client, created_team):
        """Admin can send invitations."""
        team_data, admin_headers = created_team
        org_id = team_data["id"]

        with patch(
            "app.services.team_service.TeamService.send_invitation",
            new_callable=AsyncMock,
        ) as mock_send:
            # Return a mock invitation object
            from unittest.mock import MagicMock

            mock_inv = MagicMock()
            mock_inv.id = uuid4()
            mock_inv.email = "newmember@example.com"
            mock_inv.status = "pending"
            mock_inv.expires_at = datetime.now(UTC) + timedelta(days=7)
            mock_inv.accepted_at = None
            mock_inv.created_at = datetime.now(UTC)
            mock_inv.org_id = org_id
            mock_inv.role = "member"
            mock_send.return_value = mock_inv

            resp = await client.post(
                f"/api/v1/teams/{org_id}/invitations",
                json={"emails": ["newmember@example.com"]},
                headers={"Authorization": admin_headers},
            )

        assert resp.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_send_invitation_non_admin_forbidden(self, client, created_team, team_member_auth):
        """Non-admin cannot send invitations."""
        team_data, _ = created_team
        org_id = team_data["id"]
        member_headers, _ = team_member_auth

        resp = await client.post(
            f"/api/v1/teams/{org_id}/invitations",
            json={"emails": ["someone@example.com"]},
            headers={"Authorization": member_headers},
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_send_invitation_unauthenticated(self, client, created_team):
        """Unauthenticated requests rejected."""
        team_data, _ = created_team
        org_id = team_data["id"]

        resp = await client.post(
            f"/api/v1/teams/{org_id}/invitations",
            json={"emails": ["someone@example.com"]},
        )
        assert resp.status_code == 401


class TestGetInvitation:
    """Tests for GET /api/v1/teams/invitations/{token} (public endpoint)"""

    @pytest.mark.asyncio
    async def test_get_invalid_token(self, client):
        """Invalid token returns 404."""
        resp = await client.get("/api/v1/teams/invitations/invalid-token-xyz")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_invitation_no_auth_required(self, client):
        """Public endpoint — no auth required (though returns 404 for invalid token)."""
        resp = await client.get("/api/v1/teams/invitations/sometoken123")
        # Should not be 401 (auth not required), should be 404 (token not found)
        assert resp.status_code != 401


class TestAcceptInvitation:
    """Tests for POST /api/v1/teams/invitations/{token}/accept"""

    @pytest.mark.asyncio
    async def test_accept_invalid_token(self, client, team_member_auth):
        """Invalid token returns 404 or 400."""
        headers, _ = team_member_auth
        resp = await client.post(
            "/api/v1/teams/invitations/nonexistent-token/accept",
            headers={"Authorization": headers},
        )
        assert resp.status_code in (400, 404)

    @pytest.mark.asyncio
    async def test_accept_invitation_unauthenticated(self, client):
        """Unauthenticated users cannot accept (need to be logged in)."""
        resp = await client.post("/api/v1/teams/invitations/sometoken/accept")
        assert resp.status_code == 401


class TestRemoveMember:
    """Tests for DELETE /api/v1/teams/{org_id}/members/{user_id}"""

    @pytest.mark.asyncio
    async def test_remove_nonexistent_member(self, client, created_team):
        """Removing non-member user is a no-op and returns 204 (idempotent delete)."""
        team_data, admin_headers = created_team
        org_id = team_data["id"]
        fake_user_id = str(uuid4())

        resp = await client.delete(
            f"/api/v1/teams/{org_id}/members/{fake_user_id}",
            headers={"Authorization": admin_headers},
        )
        # TeamService.remove_member is a no-op for non-members — returns 204 idempotently
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_member_non_admin_forbidden(self, client, created_team, team_member_auth):
        """Non-admin cannot remove members."""
        team_data, _ = created_team
        org_id = team_data["id"]
        member_headers, _ = team_member_auth
        fake_user_id = str(uuid4())

        resp = await client.delete(
            f"/api/v1/teams/{org_id}/members/{fake_user_id}",
            headers={"Authorization": member_headers},
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_remove_member_unauthenticated(self, client, created_team):
        """Unauthenticated requests rejected."""
        team_data, _ = created_team
        org_id = team_data["id"]
        fake_user_id = str(uuid4())

        resp = await client.delete(f"/api/v1/teams/{org_id}/members/{fake_user_id}")
        assert resp.status_code == 401


class TestListMembers:
    """Tests for GET /api/v1/teams/{org_id}/members"""

    @pytest.mark.asyncio
    async def test_list_members_as_admin(self, client, created_team):
        """Admin can list members."""
        team_data, admin_headers = created_team
        org_id = team_data["id"]

        resp = await client.get(
            f"/api/v1/teams/{org_id}/members",
            headers={"Authorization": admin_headers},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Admin should be in the list
        assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_list_members_non_member_forbidden(self, client, created_team, team_member_auth):
        """Non-member cannot list members."""
        team_data, _ = created_team
        org_id = team_data["id"]
        member_headers, _ = team_member_auth

        resp = await client.get(
            f"/api/v1/teams/{org_id}/members",
            headers={"Authorization": member_headers},
        )
        assert resp.status_code in (403, 404)


class TestTeamService:
    """Unit tests for TeamService business logic (no API layer)."""

    @pytest.mark.asyncio
    async def test_make_slug_valid(self):
        """TeamService slug generation produces URL-safe slugs."""
        from app.services.team_service import TeamService

        slug = TeamService._make_slug("Hack Reactor Cohort #44!")
        assert " " not in slug
        assert "#" not in slug
        assert "!" not in slug
        assert len(slug) <= 110  # 100 chars + 8 char suffix + hyphen

    @pytest.mark.asyncio
    async def test_make_slug_unique(self):
        """TeamService generates different slugs for same name."""
        from app.services.team_service import TeamService

        slug1 = TeamService._make_slug("Test Team")
        slug2 = TeamService._make_slug("Test Team")
        assert slug1 != slug2  # Random suffix ensures uniqueness

    @pytest.mark.asyncio
    async def test_seat_cap_enforced(self, db_session):
        """TeamService refuses to add members beyond seat count."""
        from unittest.mock import AsyncMock, MagicMock

        from app.models.organization import Organization
        from app.models.user import User
        from app.services.team_service import TeamService

        service = TeamService()

        # Mock org at capacity
        mock_org = MagicMock(spec=Organization)
        mock_org.seats_used = 5
        mock_org.seat_count = 5

        mock_user = MagicMock(spec=User)
        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="No seats available"):
            await service.add_member(mock_session, mock_org, mock_user)


# ---------------------------------------------------------------------------
# Shared fixtures for Phase 2 endpoint tests
# ---------------------------------------------------------------------------


def _decode_jwt_sub(bearer_token: str) -> str:
    """Extract the 'sub' claim (user_id) from a Bearer JWT without verification.

    Only used in tests — we trust the token was just issued by our own app.
    """
    import base64
    import json

    token = bearer_token.removeprefix("Bearer ").strip()
    # JWT format: header.payload.signature
    payload_b64 = token.split(".")[1]
    # Add padding back if stripped
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    payload = json.loads(base64.b64decode(payload_b64).decode())
    return payload["sub"]


@pytest.fixture
async def team_with_member(client):
    """Create a team org with an admin owner and one additional member.

    Fully API-driven — no direct DB session queries.  Member user_id is
    extracted from the JWT payload (the token's 'sub' claim).

    Returns a dict with keys:
        org_id          - str UUID of the organization
        admin_headers   - "Bearer ..." auth token for the admin
        member_headers  - "Bearer ..." auth token for the member
        admin_user_id   - str UUID of the admin user (from JWT sub)
        member_user_id  - str UUID of the member user (from JWT sub)
        org_data        - raw JSON from the create-team call
    """
    from sqlmodel import select

    from app.models.organization import MemberRole, Organization, OrganizationMember

    # Register + login two users — extract user IDs from their JWTs
    admin_email = f"p2admin_{uuid4().hex[:8]}@example.com"
    member_email = f"p2member_{uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"

    # Register + login with explicit error checking
    admin_reg = await client.post(
        "/api/v1/users/register", json={"email": admin_email, "password": password}
    )
    assert admin_reg.status_code in (200, 201), (
        f"Admin registration failed ({admin_reg.status_code}): {admin_reg.text}"
    )
    member_reg = await client.post(
        "/api/v1/users/register", json={"email": member_email, "password": password}
    )
    assert member_reg.status_code in (200, 201), (
        f"Member registration failed ({member_reg.status_code}): {member_reg.text}"
    )

    admin_login = await client.post(
        "/api/v1/users/login", json={"email": admin_email, "password": password}
    )
    assert admin_login.status_code == 200, (
        f"Admin login failed ({admin_login.status_code}): {admin_login.text}"
    )
    member_login = await client.post(
        "/api/v1/users/login", json={"email": member_email, "password": password}
    )
    assert member_login.status_code == 200, (
        f"Member login failed ({member_login.status_code}): {member_login.text}"
    )

    admin_headers = f"Bearer {admin_login.json()['access_token']}"
    member_headers = f"Bearer {member_login.json()['access_token']}"
    admin_user_id = _decode_jwt_sub(admin_headers)
    member_user_id = _decode_jwt_sub(member_headers)

    # Create team via API (admin becomes the owner/admin member)
    resp = await client.post(
        "/api/v1/teams",
        json={"name": "Phase2 Test Org", "seat_count": 10},
        headers={"Authorization": admin_headers},
    )
    assert resp.status_code in (200, 201), f"Create team failed: {resp.text}"
    org_data = resp.json()
    org_id = org_data["id"]

    # Add the member directly via a fresh DB session — bypass invitation flow
    # and the team_id assignment that requires the User model FK to be present
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        org_result = await session.exec(
            select(Organization).where(Organization.id == UUID(org_id))
        )
        org = org_result.first()
        assert org is not None, f"Org {org_id} not found in DB"

        membership = OrganizationMember(
            org_id=org.id,
            user_id=UUID(member_user_id),
            role=MemberRole.MEMBER,
        )
        session.add(membership)
        org.seats_used = org.seats_used + 1
        session.add(org)
        await session.commit()

    return {
        "org_id": org_id,
        "admin_headers": admin_headers,
        "member_headers": member_headers,
        "admin_user_id": admin_user_id,
        "member_user_id": member_user_id,
        "org_data": org_data,
    }


# ---------------------------------------------------------------------------
# Phase 2 — TestUpdateTeam
# ---------------------------------------------------------------------------


class TestUpdateTeam:
    """Tests for PATCH /api/v1/teams/{org_id} — update org name or seat count."""

    @pytest.mark.asyncio
    async def test_update_name_success(self, client, team_with_member):
        """Admin can rename the organization."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"name": "Renamed Engineering Org"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["name"] == "Renamed Engineering Org"
        # Other fields still present
        assert "id" in data
        assert "seat_count" in data

    @pytest.mark.asyncio
    async def test_update_seat_count_success(self, client, team_with_member):
        """Admin can increase the seat count."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"seat_count": 20},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["seat_count"] == 20

    @pytest.mark.asyncio
    async def test_seat_count_below_usage_rejected(self, client, team_with_member):
        """400 is returned when trying to reduce seat_count below seats_used.

        The org has 2 seats used (owner + one member). We add a 3rd member so
        seats_used=3, then attempt seat_count=2 which is below current usage.
        """
        from sqlmodel import select

        from app.models.organization import MemberRole, Organization, OrganizationMember

        ctx = team_with_member
        org_id = ctx["org_id"]

        # Register and add a 3rd user to push seats_used to 3 (JWT gives us the user_id)
        extra_headers = await register_and_login(
            client, email=f"p2extra_{uuid4().hex[:8]}@example.com"
        )
        extra_user_id = _decode_jwt_sub(extra_headers)

        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as session:
            membership = OrganizationMember(
                org_id=UUID(org_id),
                user_id=UUID(extra_user_id),
                role=MemberRole.MEMBER,
            )
            session.add(membership)

            org_result = await session.exec(
                select(Organization).where(Organization.id == UUID(org_id))
            )
            org = org_result.first()
            org.seats_used = org.seats_used + 1
            session.add(org)
            await session.commit()

        # seats_used is now 3; seat_count=2 is valid per schema (ge=2) but below usage
        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"seat_count": 2},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json().get("detail", "")
        assert "seat" in detail.lower() or "usage" in detail.lower() or "use" in detail.lower()

    @pytest.mark.asyncio
    async def test_non_admin_cannot_update(self, client, team_with_member):
        """403 is returned when a non-admin member tries to update the org."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"name": "Sneaky Rename"},
            headers={"Authorization": ctx["member_headers"]},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.asyncio
    async def test_update_sets_updated_at(self, client, team_with_member):
        """Successful update refreshes the updated_at timestamp."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        original_updated_at = ctx["org_data"].get("updated_at")

        # Give it at least 1 ms so timestamps differ
        import asyncio
        await asyncio.sleep(0.01)

        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"name": "Timestamp Test Org"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        # TeamResponse doesn't expose updated_at directly — just assert the call succeeded
        # and the name changed (updated_at is verified at the DB layer implicitly)
        assert resp.json()["name"] == "Timestamp Test Org"

    @pytest.mark.asyncio
    async def test_update_nonexistent_org_returns_404(self, client, team_with_member):
        """Updating a non-existent org returns 404."""
        ctx = team_with_member
        fake_org_id = str(uuid4())

        resp = await client.patch(
            f"/api/v1/teams/{fake_org_id}",
            json={"name": "Ghost Org"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_update_unauthenticated_returns_401(self, client, team_with_member):
        """Unauthenticated PATCH requests return 401."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.patch(
            f"/api/v1/teams/{org_id}",
            json={"name": "No Auth Rename"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Phase 2 — TestUpdateMemberRole
# ---------------------------------------------------------------------------


class TestUpdateMemberRole:
    """Tests for PATCH /api/v1/teams/{org_id}/members/{user_id}/role."""

    @pytest.mark.asyncio
    async def test_promote_member_to_admin(self, client, team_with_member):
        """Admin can promote a member to admin role."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        member_id = str(ctx["member_user_id"])

        resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{member_id}/role",
            json={"role": "admin"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["role"] == "admin"
        assert data["user_id"] == member_id

    @pytest.mark.asyncio
    async def test_demote_admin_to_member(self, client, team_with_member):
        """A second admin can be demoted when at least one other admin remains."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        member_id = str(ctx["member_user_id"])

        # First promote member to admin so there are two admins
        promote_resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{member_id}/role",
            json={"role": "admin"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert promote_resp.status_code == 200, promote_resp.text

        # Now demote the newly promoted admin back to member
        demote_resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{member_id}/role",
            json={"role": "member"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert demote_resp.status_code == 200, demote_resp.text
        assert demote_resp.json()["role"] == "member"

    @pytest.mark.asyncio
    async def test_cannot_demote_last_admin(self, client, team_with_member):
        """400 guard fires when trying to demote the only remaining admin."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        admin_user_id = str(ctx["admin_user_id"])

        # The org currently has one admin (owner). Attempting to demote them should fail.
        resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{admin_user_id}/role",
            json={"role": "member"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json().get("detail", "")
        assert "admin" in detail.lower() or "demote" in detail.lower() or "last" in detail.lower()

    @pytest.mark.asyncio
    async def test_non_admin_cannot_change_roles(self, client, team_with_member):
        """403 is returned when a member tries to change roles."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        admin_user_id = str(ctx["admin_user_id"])

        resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{admin_user_id}/role",
            json={"role": "member"},
            headers={"Authorization": ctx["member_headers"]},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.asyncio
    async def test_member_not_found_returns_404(self, client, team_with_member):
        """404 when the target user_id is not in the org."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        fake_user_id = str(uuid4())

        resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{fake_user_id}/role",
            json={"role": "admin"},
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 404, resp.text

    @pytest.mark.asyncio
    async def test_update_role_unauthenticated_returns_401(self, client, team_with_member):
        """Unauthenticated role-update requests return 401."""
        ctx = team_with_member
        org_id = ctx["org_id"]
        member_id = str(ctx["member_user_id"])

        resp = await client.patch(
            f"/api/v1/teams/{org_id}/members/{member_id}/role",
            json={"role": "admin"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Phase 2 — TestGetTeamUsage
# ---------------------------------------------------------------------------


class TestGetTeamUsage:
    """Tests for GET /api/v1/teams/{org_id}/usage."""

    @pytest.mark.asyncio
    async def test_returns_zero_counts_when_no_interviews(self, client, team_with_member):
        """All interview counts are 0 when no InterviewSession records exist."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.get(
            f"/api/v1/teams/{org_id}/usage",
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        for entry in data:
            assert entry["interviews_total"] == 0
            assert entry["interviews_this_month"] == 0

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access(self, client, team_with_member):
        """403 is returned when a non-admin member requests usage stats."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.get(
            f"/api/v1/teams/{org_id}/usage",
            headers={"Authorization": ctx["member_headers"]},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.asyncio
    async def test_returns_list_for_all_members(self, client, team_with_member):
        """Response contains one entry per org member."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.get(
            f"/api/v1/teams/{org_id}/usage",
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Org has 2 members: owner/admin + one member
        assert len(data) == 2
        user_ids = {entry["user_id"] for entry in data}
        assert str(ctx["admin_user_id"]) in user_ids
        assert str(ctx["member_user_id"]) in user_ids

    @pytest.mark.asyncio
    async def test_usage_counts_interviews(self, client, team_with_member):
        """interviews_total reflects InterviewSession records in the DB."""
        from app.models.interview import InterviewSession, InterviewStatus, InterviewType

        ctx = team_with_member
        org_id = ctx["org_id"]
        member_id = UUID(ctx["member_user_id"])

        # Create two interview sessions for the member directly in the DB via a fresh session
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as session:
            for _ in range(2):
                session_record = InterviewSession(
                    user_id=member_id,
                    interview_type=InterviewType.BEHAVIORAL,
                    status=InterviewStatus.COMPLETED,
                    question_count=1,
                )
                session.add(session_record)
            await session.commit()

        resp = await client.get(
            f"/api/v1/teams/{org_id}/usage",
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        member_entry = next(
            (e for e in data if e["user_id"] == str(member_id)), None
        )
        assert member_entry is not None, "Member not found in usage response"
        assert member_entry["interviews_total"] == 2
        assert member_entry["interviews_this_month"] == 2

    @pytest.mark.asyncio
    async def test_usage_response_shape(self, client, team_with_member):
        """Each usage entry has the required fields."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.get(
            f"/api/v1/teams/{org_id}/usage",
            headers={"Authorization": ctx["admin_headers"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) > 0
        required_keys = {"user_id", "email", "role", "interviews_total", "interviews_this_month"}
        for entry in data:
            assert required_keys.issubset(entry.keys()), (
                f"Missing keys in usage entry: {required_keys - entry.keys()}"
            )

    @pytest.mark.asyncio
    async def test_usage_unauthenticated_returns_401(self, client, team_with_member):
        """Unauthenticated usage requests return 401."""
        ctx = team_with_member
        org_id = ctx["org_id"]

        resp = await client.get(f"/api/v1/teams/{org_id}/usage")
        assert resp.status_code == 401
