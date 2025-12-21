"""Tests for password migration from pbkdf2_sha256 to bcrypt."""

from passlib.hash import pbkdf2_sha256

from app.security import (
    hash_password,
    is_legacy_hash,
    migrate_password_hash,
    needs_rehash,
    verify_password,
)


class TestPasswordMigration:
    """Test suite for password migration functionality."""

    def test_hash_password_uses_bcrypt(self):
        """Test that new passwords are hashed with bcrypt."""
        password = "test123"  # Short password to avoid bcrypt limit
        hashed = hash_password(password)

        # Should start with bcrypt prefix
        assert hashed.startswith("$2b$")

        # Should verify correctly
        assert verify_password(password, hashed) is True

        # Should NOT verify with wrong password
        assert verify_password("wrong_password", hashed) is False

    def test_is_legacy_hash_detection(self):
        """Test detection of legacy vs modern password hashes."""
        # Test bcrypt hash (modern)
        bcrypt_hash = hash_password("test123")
        assert is_legacy_hash(bcrypt_hash) is False

        # Test pbkdf2_sha256 hash (legacy)
        legacy_hash = pbkdf2_sha256.hash("test123")
        assert is_legacy_hash(legacy_hash) is True

    def test_needs_rehash_detection(self):
        """Test detection of hashes that need rehashing."""
        # New bcrypt hash shouldn't need rehash
        bcrypt_hash = hash_password("test123")
        assert needs_rehash(bcrypt_hash) is False

        # Legacy pbkdf2 hash should need rehash
        legacy_hash = pbkdf2_sha256.hash("test123")
        assert needs_rehash(legacy_hash) is True

    def test_verify_password_supports_both(self):
        """Test that password verification works for both hash types."""
        password = "test123"

        # Test bcrypt hash
        bcrypt_hash = hash_password(password)
        assert verify_password(password, bcrypt_hash) is True
        assert verify_password("wrong", bcrypt_hash) is False

        # Test legacy pbkdf2 hash
        legacy_hash = pbkdf2_sha256.hash(password)
        assert verify_password(password, legacy_hash) is True
        assert verify_password("wrong", legacy_hash) is False

    def test_migrate_password_hash(self):
        """Test password migration from legacy to modern hashing."""
        password = "test123"

        # Create a legacy hash
        legacy_hash = pbkdf2_sha256.hash(password)

        # Migrate it
        new_hash = migrate_password_hash(password)

        # New hash should be bcrypt
        assert new_hash.startswith("$2b$")
        assert is_legacy_hash(new_hash) is False
        assert needs_rehash(new_hash) is False

        # Should still verify with the same password
        assert verify_password(password, new_hash) is True
        assert verify_password("wrong", new_hash) is False

        # Should be different from the original legacy hash
        assert new_hash != legacy_hash

    def test_migrated_password_verifies(self):
        """Test that migrated passwords verify correctly."""
        password = "test456"

        # Create legacy hash
        legacy_hash = pbkdf2_sha256.hash(password)

        # Verify the legacy hash works
        assert verify_password(password, legacy_hash) is True
        assert is_legacy_hash(legacy_hash) is True
        assert needs_rehash(legacy_hash) is True

        # Migrate to bcrypt
        new_hash = migrate_password_hash(password)

        # Verify the new hash works
        assert verify_password(password, new_hash) is True
        assert is_legacy_hash(new_hash) is False
        assert needs_rehash(new_hash) is False

        # Password should still be the same
        assert verify_password(password, new_hash)

    def test_password_verification_error_handling(self):
        """Test that password verification handles errors gracefully."""
        # Test with invalid hash formats
        invalid_hashes = [
            "",
            "invalid_hash",
            "$invalid$",
            "$2b$12$invalidlengthhash",
        ]

        for invalid_hash in invalid_hashes:
            assert verify_password("password", invalid_hash) is False

    def test_bcrypt_security_parameters(self):
        """Test that bcrypt uses appropriate security parameters."""
        password = "secure789"
        hashed = hash_password(password)

        # Extract rounds from bcrypt hash
        # Format: $2b$[rounds]$[salt][hash]
        parts = hashed.split("$")
        assert len(parts) == 4
        assert parts[1] == "2b"  # bcrypt algorithm

        # Should use at least 12 rounds (configured in security.py)
        rounds = int(parts[2])
        assert rounds >= 12

    def test_consistent_bcrypt_hashing(self):
        """Test that bcrypt hashing is consistent but produces different hashes."""
        password = "testconsistency"

        # Hash the same password multiple times
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify the password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_migration_flow_simulation(self):
        """Simulate the complete migration flow."""
        # Simulate existing user with pbkdf2 password
        user_password = "user123"
        legacy_hash = pbkdf2_sha256.hash(user_password)

        # Check initial state
        assert is_legacy_hash(legacy_hash) is True
        assert needs_rehash(legacy_hash) is True
        assert verify_password(user_password, legacy_hash) is True

        # User logs in - password verifies
        assert verify_password(user_password, legacy_hash) is True

        # System detects need for migration and migrates
        if needs_rehash(legacy_hash):
            new_hash = migrate_password_hash(user_password)

            # Verify migration
            assert is_legacy_hash(new_hash) is False
            assert needs_rehash(new_hash) is False
            assert verify_password(user_password, new_hash) is True

            # Future logins use the new hash
            assert verify_password(user_password, new_hash) is True
            assert needs_rehash(new_hash) is False  # No longer needs migration
