"""Test password validation utility.

Tests for relaxed password validation that allows simple passwords
while blocking only trivially weak ones.
"""

import pytest
from app.utils.password_validation import (
    PasswordValidator,
    PasswordValidationError,
    validate_password,
    is_password_valid,
    get_password_strength,
)


class TestPasswordValidator:
    """Test the PasswordValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PasswordValidator()

    def test_min_length_requirement(self):
        """Test password minimum length validation (6 chars)."""
        # Too short (5 chars)
        errors = self.validator.validate("abcde")
        assert PasswordValidationError.TOO_SHORT.value in errors

        # Just right (6 chars)
        assert self.validator.is_valid("secret") is True

        # Longer passwords work
        assert self.validator.is_valid("secret25") is True
        assert self.validator.is_valid("mysecretpassword") is True

    def test_simple_passwords_allowed(self):
        """Test that simple passwords are allowed (relaxed validation)."""
        # These should all pass - no complexity requirements
        simple_passwords = [
            "secret25",      # lowercase + numbers
            "mypassword",    # just lowercase
            "SECRET99",      # just uppercase + numbers
            "testing123",    # common word + numbers (but not blocked)
            "abcdef",        # just 6 lowercase letters
            "987654321",     # just numbers (not in blocked list)
        ]

        for password in simple_passwords:
            assert self.validator.is_valid(password) is True, f"{password} should be valid"

    def test_common_passwords_blocked(self):
        """Test that only the most common passwords are blocked."""
        blocked_passwords = [
            "password",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "password1",
            "password123",
            "admin",
            "letmein",
            "welcome",
        ]

        for password in blocked_passwords:
            errors = self.validator.validate(password)
            assert PasswordValidationError.COMMON_PASSWORD.value in errors
            assert self.validator.is_valid(password) is False, f"{password} should be blocked"

    def test_username_email_exact_match_blocking(self):
        """Test that passwords cannot exactly match username or email."""
        # Exact username match blocked
        errors = self.validator.validate("johndoe", username="johndoe")
        assert "Password cannot be the same as your username" in errors

        # Exact email local part match blocked
        errors = self.validator.validate("john", email="john@example.com")
        assert "Password cannot be the same as your email" in errors

        # Containing username is allowed (relaxed)
        assert self.validator.is_valid(
            "johndoe123",
            username="johndoe"
        ) is True

        # Different password is fine
        assert self.validator.is_valid(
            "secret25",
            username="johndoe",
            email="john@example.com"
        ) is True

    def test_password_strength_scoring(self):
        """Test password strength scoring for frontend feedback."""
        # Very weak password (short)
        strength = self.validator.get_password_strength("weak")
        assert strength["strength"] in ["Very Weak", "Weak", "Moderate"]
        assert strength["score"] < 60

        # Moderate password
        strength = self.validator.get_password_strength("secret25")
        assert strength["strength"] in ["Weak", "Moderate"]

        # Strong password
        strength = self.validator.get_password_strength("SecretPass123!")
        assert strength["strength"] in ["Moderate", "Strong", "Very Strong"]
        assert strength["score"] >= 40

        # Very strong password
        strength = self.validator.get_password_strength("V3ry$tr0ngP@ssw0rd!")
        assert strength["strength"] in ["Strong", "Very Strong"]
        assert strength["score"] >= 60

    def test_password_strength_feedback(self):
        """Test password strength feedback for frontend warnings."""
        strength = self.validator.get_password_strength("weak")
        assert "Add more characters to increase strength" in strength["feedback"]
        assert "Add uppercase letters" in strength["feedback"]
        assert "Add numbers" in strength["feedback"]
        assert "Add special characters" in strength["feedback"]


class TestPasswordValidationFunctions:
    """Test global password validation functions."""

    def test_validate_password_function(self):
        """Test the global validate_password function."""
        # Valid password
        errors = validate_password("secret25")
        assert len(errors) == 0

        # Invalid password (too short)
        errors = validate_password("weak")
        assert len(errors) > 0
        assert PasswordValidationError.TOO_SHORT.value in errors

        # Invalid password (common)
        errors = validate_password("password")
        assert PasswordValidationError.COMMON_PASSWORD.value in errors

    def test_is_password_valid_function(self):
        """Test the global is_password_valid function."""
        assert is_password_valid("secret25") is True
        assert is_password_valid("password123") is False  # common
        assert is_password_valid("weak") is False  # too short

    def test_get_password_strength_function(self):
        """Test the global get_password_strength function."""
        strength = get_password_strength("secret25")
        assert "score" in strength
        assert "strength" in strength
        assert "feedback" in strength


class TestPasswordValidationIntegration:
    """Integration tests for password validation with models."""

    def test_user_create_validation(self):
        """Test password validation in UserCreate model."""
        from app.models.user import UserCreate

        # Valid password (simple)
        user = UserCreate(
            email="test@example.com",
            password="secret25",
            full_name="Test User"
        )
        assert user.email == "test@example.com"

        # Invalid password (too short)
        with pytest.raises(Exception) as exc_info:
            UserCreate(
                email="test@example.com",
                password="weak",
                full_name="Test User"
            )
        assert "Password must be at least 6 characters long" in str(exc_info.value)

    def test_password_change_validation(self):
        """Test password validation in PasswordChange model."""
        from app.models.user import PasswordChange

        # Valid passwords (simple)
        change = PasswordChange(
            current_password="oldpass",
            new_password="newpass123"
        )
        assert change.new_password == "newpass123"

        # Invalid new password (too short)
        with pytest.raises(ValueError) as exc_info:
            PasswordChange(
                current_password="oldpass",
                new_password="weak"
            )
        assert "Password validation failed" in str(exc_info.value)

    def test_reset_password_validation(self):
        """Test password validation in ResetPasswordRequest."""
        from app.api.auth import ResetPasswordRequest

        # Valid password (simple)
        reset = ResetPasswordRequest(
            token="valid_token",
            new_password="secret25"
        )
        assert reset.new_password == "secret25"

        # Invalid password (too short)
        with pytest.raises(ValueError) as exc_info:
            ResetPasswordRequest(
                token="valid_token",
                new_password="weak"
            )
        assert "Password validation failed" in str(exc_info.value)


@pytest.mark.parametrize("password,expected", [
    ("secret25", True),           # Simple valid password
    ("password123", False),       # Common password
    ("weak", False),              # Too short
    ("123456", False),            # Common password
    ("qwerty", False),            # Common password
    ("mypassword", True),         # Simple but allowed
    ("Testing123", True),         # Mixed case + numbers (allowed)
    ("abcdefgh", True),           # Just letters (allowed if 6+ chars)
])
def test_password_validation_parametrized(password, expected):
    """Parametrized test for various password scenarios."""
    validator = PasswordValidator()
    assert validator.is_valid(password) == expected
