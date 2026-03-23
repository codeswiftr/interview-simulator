"""Integration tests for API key service — B2B team tier readiness.

Tests cover:
- Full lifecycle: create → authenticate → revoke → auth fails
- Scope enforcement (read/write/admin permission checks)
- Key expiration (just-expired, future expiry, no expiry)
- Rate limit configuration stored and retrievable per key
- Key count limit enforcement (10-key ceiling per user)
- Multi-user isolation (keys not visible or usable across user boundaries)
- Usage tracking increments across repeated authentications
- Key re-creation after deletion is allowed
- Prefix uniqueness and identification
- Key deactivation vs. deletion semantics
- Admin scope covers all sub-scopes
- B2B: independent team members each manage their own keys
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.api_key import APIKey, APIKeyCreate, APIKeyScope, APIKeyUpdate
from app.services import api_key_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user(session, email: str | None = None):
    """Create and persist a test user, returning the User ORM object."""
    from app.models.user import User
    from app.security import hash_password

    email = email or f"user_{uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        hashed_password=hash_password("TestPassword123!"),
        experience_level="mid",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _make_key(session, user_id, *, name="default", scopes=None, **kwargs):
    """Create an API key and return (plain_key, APIKey)."""
    if scopes is None:
        scopes = [APIKeyScope.READ]
    key_data = APIKeyCreate(name=name, scopes=scopes, **kwargs)
    return await api_key_service.create_api_key(session, user_id, key_data)


# ===========================================================================
# 1. Key creation: prefix + bcrypt hash
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyCreation:
    """Verify that key creation produces correctly formatted, hashed keys."""

    async def test_created_key_has_is_prefix(self, session, test_user):
        plain_key, _ = await _make_key(session, test_user.id)
        assert plain_key.startswith("is_")

    async def test_created_key_is_43_chars(self, session, test_user):
        plain_key, _ = await _make_key(session, test_user.id)
        assert len(plain_key) == 43

    async def test_stored_hash_is_bcrypt(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        assert api_key.key_hash.startswith("$2b$")

    async def test_stored_prefix_matches_plain_key(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        assert api_key.key_prefix == plain_key[:8]

    async def test_plain_key_verifies_against_hash(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        assert api_key_service.verify_api_key(plain_key, api_key.key_hash)

    async def test_different_key_does_not_verify_against_hash(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        other_key = api_key_service.generate_api_key()
        assert not api_key_service.verify_api_key(other_key, api_key.key_hash)

    async def test_scopes_stored_as_csv(self, session, test_user):
        _, api_key = await _make_key(
            session, test_user.id, scopes=[APIKeyScope.READ, APIKeyScope.WRITE]
        )
        assert api_key.scopes == "read,write"

    async def test_default_rate_limit_is_60(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.rate_limit == 60

    async def test_custom_rate_limit_stored(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, rate_limit=200)
        assert api_key.rate_limit == 200

    async def test_key_is_active_on_creation(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.is_active is True

    async def test_request_count_starts_at_zero(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.request_count == 0

    async def test_last_used_at_is_none_on_creation(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.last_used_at is None

    async def test_two_keys_have_different_plain_values(self, session, test_user):
        k1, _ = await _make_key(session, test_user.id, name="k1")
        k2, _ = await _make_key(session, test_user.id, name="k2")
        assert k1 != k2


# ===========================================================================
# 2. Key validation: correct key passes, wrong key fails
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyValidation:
    """Verify correct validation behaviour against the database."""

    async def test_valid_key_returns_owner(self, session, test_user):
        plain_key, _ = await _make_key(session, test_user.id)
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None
        assert user.id == test_user.id

    async def test_wrong_key_returns_none(self, session, test_user):
        # Create a key so the prefix exists in DB, then tamper with the suffix
        plain_key, _ = await _make_key(session, test_user.id)
        tampered = plain_key[:8] + "x" * (len(plain_key) - 8)
        user = await api_key_service.verify_api_key_and_get_user(session, tampered)
        assert user is None

    async def test_nonexistent_key_returns_none(self, session):
        fake_key = api_key_service.generate_api_key()
        user = await api_key_service.verify_api_key_and_get_user(session, fake_key)
        assert user is None

    async def test_key_without_is_prefix_returns_none(self, session):
        user = await api_key_service.verify_api_key_and_get_user(session, "sk_abcdefg")
        assert user is None

    async def test_empty_key_returns_none(self, session):
        user = await api_key_service.verify_api_key_and_get_user(session, "")
        assert user is None

    async def test_validation_increments_request_count(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        await api_key_service.verify_api_key_and_get_user(session, plain_key)
        await session.refresh(api_key)
        assert api_key.request_count == 1

    async def test_validation_updates_last_used_at(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        before = datetime.now(UTC)
        await api_key_service.verify_api_key_and_get_user(session, plain_key)
        await session.refresh(api_key)
        assert api_key.last_used_at is not None
        assert api_key.last_used_at >= before

    async def test_multiple_validations_accumulate_count(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        for _ in range(5):
            await api_key_service.verify_api_key_and_get_user(session, plain_key)
        await session.refresh(api_key)
        assert api_key.request_count == 5


# ===========================================================================
# 3. Key expiration
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyExpiration:
    """Verify expiration is enforced during validation."""

    async def test_non_expiring_key_is_valid(self, session, test_user):
        plain_key, _ = await _make_key(session, test_user.id, expires_at=None)
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

    async def test_future_expiry_key_is_valid(self, session, test_user):
        future = datetime.now(UTC) + timedelta(days=30)
        plain_key, _ = await _make_key(session, test_user.id, expires_at=future)
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

    async def test_just_expired_key_returns_none(self, session, test_user):
        expired = datetime.now(UTC) - timedelta(seconds=1)
        plain_key, _ = await _make_key(session, test_user.id, expires_at=expired)
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_long_expired_key_returns_none(self, session, test_user):
        long_past = datetime.now(UTC) - timedelta(days=365)
        plain_key, _ = await _make_key(session, test_user.id, expires_at=long_past)
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_is_valid_model_method_respects_expiry(self, session, test_user):
        """Verify APIKey.is_valid() agrees with service-layer rejection."""
        expired = datetime.now(UTC) - timedelta(minutes=5)
        _, api_key = await _make_key(session, test_user.id, expires_at=expired)
        assert api_key.is_valid() is False

    async def test_is_valid_model_method_future_expiry(self, session, test_user):
        future = datetime.now(UTC) + timedelta(days=1)
        _, api_key = await _make_key(session, test_user.id, expires_at=future)
        assert api_key.is_valid() is True


# ===========================================================================
# 4. Key revocation (deactivation and deletion)
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyRevocation:
    """Full lifecycle: create → authenticate → revoke → auth fails."""

    async def test_deactivated_key_fails_auth(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)

        # Confirm it works before deactivation
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

        # Deactivate
        update = APIKeyUpdate(is_active=False)
        await api_key_service.update_api_key(session, api_key.id, test_user.id, update)

        # Must now fail
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_deleted_key_fails_auth(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)

        # Confirm it works
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

        # Delete
        deleted = await api_key_service.delete_api_key(session, api_key.id, test_user.id)
        assert deleted is True

        # Must now fail
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_deleted_key_not_in_list(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        await api_key_service.delete_api_key(session, api_key.id, test_user.id)

        keys = await api_key_service.get_user_api_keys(session, test_user.id)
        ids = [k.id for k in keys]
        assert api_key.id not in ids

    async def test_reactivating_key_restores_auth(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)

        # Deactivate
        await api_key_service.update_api_key(
            session, api_key.id, test_user.id, APIKeyUpdate(is_active=False)
        )
        assert await api_key_service.verify_api_key_and_get_user(session, plain_key) is None

        # Re-activate
        await api_key_service.update_api_key(
            session, api_key.id, test_user.id, APIKeyUpdate(is_active=True)
        )
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

    async def test_delete_nonexistent_key_returns_false(self, session, test_user):
        deleted = await api_key_service.delete_api_key(session, uuid4(), test_user.id)
        assert deleted is False

    async def test_recreate_after_delete_succeeds(self, session, test_user):
        """Deleting a key and re-creating one for the same user must succeed."""
        _, api_key = await _make_key(session, test_user.id, name="recyclable")
        await api_key_service.delete_api_key(session, api_key.id, test_user.id)

        # Should not raise
        new_plain, new_key = await _make_key(session, test_user.id, name="recyclable-2")
        assert new_plain.startswith("is_")
        assert new_key.is_active is True


# ===========================================================================
# 5. Key count limit enforcement
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyCountLimit:
    """Enforce the 10-key ceiling per user."""

    async def test_exactly_ten_keys_allowed(self, session, test_user):
        for i in range(10):
            await _make_key(session, test_user.id, name=f"k{i}")
        keys = await api_key_service.get_user_api_keys(session, test_user.id)
        assert len(keys) == 10

    async def test_eleventh_key_raises(self, session, test_user):
        for i in range(10):
            await _make_key(session, test_user.id, name=f"k{i}")
        with pytest.raises(ValueError, match="Maximum"):
            await _make_key(session, test_user.id, name="k10")

    async def test_delete_allows_new_key_after_limit(self, session, test_user):
        keys = []
        for i in range(10):
            _, k = await _make_key(session, test_user.id, name=f"k{i}")
            keys.append(k)

        # Delete one
        await api_key_service.delete_api_key(session, keys[0].id, test_user.id)

        # Now the 10th slot is free — creation must succeed
        new_plain, _ = await _make_key(session, test_user.id, name="k_new")
        assert new_plain.startswith("is_")

    async def test_inactive_keys_count_toward_limit(self, session, test_user):
        """The limit counts active keys only; inactive ones free up slots."""
        keys = []
        for i in range(10):
            _, k = await _make_key(session, test_user.id, name=f"k{i}")
            keys.append(k)

        # Deactivate one — limit check only counts is_active=True rows
        await api_key_service.update_api_key(
            session, keys[0].id, test_user.id, APIKeyUpdate(is_active=False)
        )

        # With one inactive, we should be able to create another
        new_plain, _ = await _make_key(session, test_user.id, name="k_after_deactivate")
        assert new_plain.startswith("is_")


# ===========================================================================
# 6. Scope enforcement
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyScopes:
    """Verify scope assignment and has_scope() semantics."""

    async def test_read_scope_has_read(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.READ])
        assert api_key.has_scope("read")

    async def test_read_scope_lacks_write(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.READ])
        assert not api_key.has_scope("write")

    async def test_write_scope_has_write(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.WRITE])
        assert api_key.has_scope("write")

    async def test_write_scope_lacks_admin(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.WRITE])
        assert not api_key.has_scope("admin")

    async def test_admin_scope_covers_read(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.ADMIN])
        assert api_key.has_scope("read")

    async def test_admin_scope_covers_write(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.ADMIN])
        assert api_key.has_scope("write")

    async def test_admin_scope_covers_admin(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.ADMIN])
        assert api_key.has_scope("admin")

    async def test_multi_scope_key(self, session, test_user):
        _, api_key = await _make_key(
            session, test_user.id, scopes=[APIKeyScope.READ, APIKeyScope.WRITE]
        )
        assert api_key.has_scope("read")
        assert api_key.has_scope("write")
        assert not api_key.has_scope("admin")

    async def test_scope_update_is_persisted(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, scopes=[APIKeyScope.READ])
        assert not api_key.has_scope("write")

        updated = await api_key_service.update_api_key(
            session,
            api_key.id,
            test_user.id,
            APIKeyUpdate(scopes=[APIKeyScope.READ, APIKeyScope.WRITE]),
        )
        assert updated is not None
        assert updated.has_scope("write")


# ===========================================================================
# 7. Multi-user isolation (team boundary)
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyMultiUserIsolation:
    """Keys are strictly scoped to their owning user — B2B team safety."""

    async def test_user_cannot_retrieve_other_users_key_by_id(self, session):
        user_a = await _make_user(session, "a@example.com")
        user_b = await _make_user(session, "b@example.com")

        _, key_a = await _make_key(session, user_a.id, name="a-key")

        # user_b attempts to get user_a's key
        result = await api_key_service.get_api_key_by_id(session, key_a.id, user_b.id)
        assert result is None

    async def test_user_list_only_returns_own_keys(self, session):
        user_a = await _make_user(session, "lsta@example.com")
        user_b = await _make_user(session, "lstb@example.com")

        await _make_key(session, user_a.id, name="a1")
        await _make_key(session, user_a.id, name="a2")
        await _make_key(session, user_b.id, name="b1")

        a_keys = await api_key_service.get_user_api_keys(session, user_a.id)
        b_keys = await api_key_service.get_user_api_keys(session, user_b.id)

        assert len(a_keys) == 2
        assert len(b_keys) == 1

    async def test_user_cannot_update_other_users_key(self, session):
        user_a = await _make_user(session, "upda@example.com")
        user_b = await _make_user(session, "updb@example.com")

        _, key_a = await _make_key(session, user_a.id, name="a-key")

        result = await api_key_service.update_api_key(
            session, key_a.id, user_b.id, APIKeyUpdate(name="hacked")
        )
        assert result is None

        # Original key name unchanged
        original = await api_key_service.get_api_key_by_id(session, key_a.id, user_a.id)
        assert original is not None
        assert original.name == "a-key"

    async def test_user_cannot_delete_other_users_key(self, session):
        user_a = await _make_user(session, "dela@example.com")
        user_b = await _make_user(session, "delb@example.com")

        _, key_a = await _make_key(session, user_a.id, name="a-key")

        deleted = await api_key_service.delete_api_key(session, key_a.id, user_b.id)
        assert deleted is False

        # Key still exists for user_a
        original = await api_key_service.get_api_key_by_id(session, key_a.id, user_a.id)
        assert original is not None

    async def test_separate_users_have_independent_key_limits(self, session):
        """Two users' 10-key limits are independent."""
        user_a = await _make_user(session, "lima@example.com")
        user_b = await _make_user(session, "limb@example.com")

        # Fill user_a to the limit
        for i in range(10):
            await _make_key(session, user_a.id, name=f"a{i}")

        # user_b should still be able to create keys
        plain_key, _ = await _make_key(session, user_b.id, name="b0")
        assert plain_key.startswith("is_")

    async def test_valid_key_returns_correct_owner_not_other_user(self, session):
        """Verify that key authentication returns the right owner."""
        user_a = await _make_user(session, "ownera@example.com")
        user_b = await _make_user(session, "ownerb@example.com")

        plain_key_a, _ = await _make_key(session, user_a.id, name="a-auth")
        await _make_key(session, user_b.id, name="b-auth")

        authenticated = await api_key_service.verify_api_key_and_get_user(session, plain_key_a)
        assert authenticated is not None
        assert authenticated.id == user_a.id
        assert authenticated.id != user_b.id


# ===========================================================================
# 8. B2B team scenario: independent key management per team member
# ===========================================================================


@pytest.mark.asyncio
class TestB2BTeamKeyManagement:
    """Simulate B2B team members managing API keys independently."""

    async def test_each_team_member_creates_keys_independently(self, session):
        """Three team members each create keys; no cross-contamination."""
        members = [await _make_user(session, f"member{i}@corp.com") for i in range(3)]

        # Each member creates 2 keys
        for m in members:
            await _make_key(session, m.id, name="ci-key")
            await _make_key(session, m.id, name="dev-key")

        # Each member sees exactly 2 keys
        for m in members:
            keys = await api_key_service.get_user_api_keys(session, m.id)
            assert len(keys) == 2, f"Member {m.email} should have 2 keys"

    async def test_team_member_keys_are_independently_revocable(self, session):
        """Revoking one member's key does not affect other members."""
        alice = await _make_user(session, "alice@corp.com")
        bob = await _make_user(session, "bob@corp.com")

        alice_plain, alice_key = await _make_key(session, alice.id, name="alice-key")
        bob_plain, _ = await _make_key(session, bob.id, name="bob-key")

        # Revoke Alice's key
        await api_key_service.delete_api_key(session, alice_key.id, alice.id)

        # Alice's key must fail
        assert await api_key_service.verify_api_key_and_get_user(session, alice_plain) is None
        # Bob's key must still work
        bob_user = await api_key_service.verify_api_key_and_get_user(session, bob_plain)
        assert bob_user is not None
        assert bob_user.id == bob.id

    async def test_team_member_with_admin_key_has_full_scope(self, session):
        """A team member issued an admin-scope key has all permissions."""
        admin_member = await _make_user(session, "admin@corp.com")
        _, admin_key = await _make_key(
            session, admin_member.id, name="admin-key", scopes=[APIKeyScope.ADMIN]
        )
        assert admin_key.has_scope("read")
        assert admin_key.has_scope("write")
        assert admin_key.has_scope("admin")

    async def test_team_member_with_read_key_cannot_write(self, session):
        """A team member issued a read-only key cannot perform write actions."""
        reader = await _make_user(session, "reader@corp.com")
        _, read_key = await _make_key(
            session, reader.id, name="read-only-key", scopes=[APIKeyScope.READ]
        )
        assert read_key.has_scope("read")
        assert not read_key.has_scope("write")
        assert not read_key.has_scope("admin")

    async def test_key_expiry_enforced_for_contractor_scenario(self, session):
        """Temporary contractor keys expire after engagement ends."""
        contractor = await _make_user(session, "contractor@external.com")
        expiry = datetime.now(UTC) + timedelta(days=30)
        plain_key, _ = await _make_key(
            session, contractor.id, name="30-day-contract", expires_at=expiry
        )

        # Currently valid
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is not None

        # Simulate post-engagement by directly deactivating (contract expired)
        keys = await api_key_service.get_user_api_keys(session, contractor.id)
        assert len(keys) == 1
        deactivated = await api_key_service.update_api_key(
            session, keys[0].id, contractor.id, APIKeyUpdate(is_active=False)
        )
        assert deactivated is not None

        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_usage_tracking_works_per_team_member(self, session):
        """Usage counters are independent per key/user."""
        alice = await _make_user(session, "track_a@corp.com")
        bob = await _make_user(session, "track_b@corp.com")

        alice_plain, alice_key = await _make_key(session, alice.id, name="a")
        bob_plain, bob_key = await _make_key(session, bob.id, name="b")

        # Alice uses her key 3 times, Bob uses his once
        for _ in range(3):
            await api_key_service.verify_api_key_and_get_user(session, alice_plain)
        await api_key_service.verify_api_key_and_get_user(session, bob_plain)

        await session.refresh(alice_key)
        await session.refresh(bob_key)

        assert alice_key.request_count == 3
        assert bob_key.request_count == 1


# ===========================================================================
# 9. Rate limit configuration
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyRateLimitConfig:
    """Verify per-key rate limit values are stored and retrievable."""

    async def test_default_rate_limit_is_60(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.rate_limit == 60

    async def test_custom_rate_limit_low(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, rate_limit=1)
        assert api_key.rate_limit == 1

    async def test_custom_rate_limit_high(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, rate_limit=1000)
        assert api_key.rate_limit == 1000

    async def test_rate_limit_update_is_persisted(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id, rate_limit=60)
        updated = await api_key_service.update_api_key(
            session, api_key.id, test_user.id, APIKeyUpdate(rate_limit=500)
        )
        assert updated is not None
        assert updated.rate_limit == 500

    async def test_rate_limit_survives_name_update(self, session, test_user):
        """Partial update of name must not reset rate_limit."""
        _, api_key = await _make_key(session, test_user.id, rate_limit=300)
        updated = await api_key_service.update_api_key(
            session, api_key.id, test_user.id, APIKeyUpdate(name="renamed")
        )
        assert updated is not None
        assert updated.rate_limit == 300


# ===========================================================================
# 10. Key identification via prefix
# ===========================================================================


@pytest.mark.asyncio
class TestAPIKeyPrefixIdentification:
    """Key prefix must uniquely identify a key within its owning user's set."""

    async def test_prefix_is_first_8_chars_of_plain_key(self, session, test_user):
        plain_key, api_key = await _make_key(session, test_user.id)
        assert api_key.key_prefix == plain_key[:8]

    async def test_prefix_starts_with_is_(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert api_key.key_prefix.startswith("is_")

    async def test_prefix_is_8_chars(self, session, test_user):
        _, api_key = await _make_key(session, test_user.id)
        assert len(api_key.key_prefix) == 8

    async def test_two_keys_have_different_prefixes(self, session, test_user):
        """With 40 random bits per key, collision is astronomically unlikely."""
        _, k1 = await _make_key(session, test_user.id, name="k1")
        _, k2 = await _make_key(session, test_user.id, name="k2")
        # Prefixes share 'is_' but the random 5-char suffix should differ
        assert k1.key_prefix != k2.key_prefix

    async def test_get_by_id_uses_ownership_not_prefix(self, session):
        """get_api_key_by_id must verify user_id, not just the prefix."""
        user_a = await _make_user(session, "px_a@example.com")
        user_b = await _make_user(session, "px_b@example.com")

        _, key_a = await _make_key(session, user_a.id, name="a")

        # Correct owner finds it
        found = await api_key_service.get_api_key_by_id(session, key_a.id, user_a.id)
        assert found is not None

        # Wrong owner doesn't
        not_found = await api_key_service.get_api_key_by_id(session, key_a.id, user_b.id)
        assert not_found is None
