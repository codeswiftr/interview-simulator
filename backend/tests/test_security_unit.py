"""Pure unit tests for security module.

Tests password hashing, verification, migration, and token functions.
No database required.
"""

from app.security import (
    BCRYPT_PREFIX,
    PBKDF2_PREFIX,
    REFRESH_TOKEN_EXPIRE_DAYS,
    hash_password,
    is_legacy_hash,
    migrate_password_hash,
    needs_rehash,
    verify_password,
)


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        h = hash_password("test_password")
        assert h.startswith(BCRYPT_PREFIX)

    def test_different_passwords_different_hashes(self):
        h1 = hash_password("pass1")
        h2 = hash_password("pass2")
        assert h1 != h2

    def test_same_password_different_salts(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_bcrypt_password(self):
        h = hash_password("my_password")
        assert verify_password("my_password", h) is True

    def test_wrong_bcrypt_password(self):
        h = hash_password("correct")
        assert verify_password("wrong", h) is False

    def test_invalid_hash_returns_false(self):
        assert verify_password("pass", "not_a_valid_hash") is False

    def test_long_password_truncated(self):
        long_pass = "a" * 100
        h = hash_password(long_pass)
        assert verify_password(long_pass, h) is True


class TestNeedsRehash:
    def test_bcrypt_no_rehash(self):
        assert needs_rehash("$2b$12$somehash") is False

    def test_pbkdf2_needs_rehash(self):
        assert needs_rehash("$pbkdf2-sha256$29000$somehash") is True

    def test_unknown_needs_rehash(self):
        assert needs_rehash("random_string") is True


class TestIsLegacyHash:
    def test_pbkdf2_is_legacy(self):
        assert is_legacy_hash("$pbkdf2-sha256$29000$hash") is True

    def test_bcrypt_not_legacy(self):
        assert is_legacy_hash("$2b$12$hash") is False


class TestMigratePasswordHash:
    def test_returns_bcrypt(self):
        h = migrate_password_hash("password")
        assert h.startswith(BCRYPT_PREFIX)

    def test_verifies_after_migration(self):
        h = migrate_password_hash("migrated_pass")
        assert verify_password("migrated_pass", h) is True


class TestConstants:
    def test_refresh_token_expire_days(self):
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_bcrypt_prefix(self):
        assert BCRYPT_PREFIX == "$2b$"

    def test_pbkdf2_prefix(self):
        assert PBKDF2_PREFIX == "$pbkdf2-sha256$"
