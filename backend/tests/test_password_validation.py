"""Test password validation utility.

Tests for password validation with complexity requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Blocks common passwords
"""

import pytest

from app.utils.password_validation import (
    PasswordValidationError,
    PasswordValidator,
    get_password_strength,
    is_password_valid,
    validate_password,
)


class TestPasswordValidator:
    """Test the PasswordValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PasswordValidator()

    def test_min_length_requirement(self):
        """Test password minimum length validation (8 chars)."""
        # Too short (7 chars)
        errors = self.validator.validate("Secret1")
        assert PasswordValidationError.TOO_SHORT.value in errors

        # Just right (8 chars, meets complexity)
        assert self.validator.is_valid("Secret25") is True

        # Longer passwords work (with complexity)
        assert self.validator.is_valid("Mysecretpassword1") is True
        assert self.validator.is_valid("Longpassword123") is True

    def test_complex_passwords_allowed(self):
        """Test that passwords meeting complexity requirements are allowed."""
        # These should all pass - 8+ chars with uppercase, lowercase, digit
        valid_passwords = [
            "Secret25",  # uppercase + lowercase + numbers (8 chars)
            "Mypassword1",  # mixed case + digit (11 chars)
            "SECRETPW99a",  # uppercase + lowercase + numbers (11 chars)
            "Testing1234",  # mixed case + numbers (11 chars)
            "Abcdefgh1",  # 8 chars with complexity
            "A987654321b",  # uppercase + numbers + lowercase (11 chars)
        ]

        for password in valid_passwords:
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
        errors = self.validator.validate("Johndoe1", username="johndoe1")
        assert "Password cannot be the same as your username" in errors

        # Exact email local part match blocked
        errors = self.validator.validate("John1", email="john1@example.com")
        assert "Password cannot be the same as your email" in errors

        # Containing username is allowed
        assert self.validator.is_valid("Johndoe123", username="johndoe") is True

        # Different password is fine
        assert (
            self.validator.is_valid("Secret25", username="johndoe", email="john@example.com")
            is True
        )

    def test_password_strength_scoring(self):
        """Test password strength scoring for frontend feedback."""
        # Very weak password (short)
        strength = self.validator.get_password_strength("weak")
        assert strength["strength"] in ["Very Weak", "Weak", "Moderate"]
        assert isinstance(strength["score"], int) and strength["score"] < 60

        # Moderate password (meets complexity)
        strength = self.validator.get_password_strength("Secret25")
        assert strength["strength"] in ["Weak", "Moderate", "Strong"]

        # Strong password
        strength = self.validator.get_password_strength("SecretPass123!")
        assert strength["strength"] in ["Moderate", "Strong", "Very Strong"]
        assert isinstance(strength["score"], int) and strength["score"] >= 40

        # Very strong password
        strength = self.validator.get_password_strength("V3ry$tr0ngP@ssw0rd!")
        assert strength["strength"] in ["Strong", "Very Strong"]
        assert isinstance(strength["score"], int) and strength["score"] >= 60

    def test_password_strength_feedback(self):
        """Test password strength feedback for frontend warnings."""
        strength = self.validator.get_password_strength("weak")
        feedback = str(strength["feedback"])
        assert "Add more characters" in feedback or "uppercase" in feedback.lower()


class TestPasswordValidationFunctions:
    """Test global password validation functions."""

    def test_validate_password_function(self):
        """Test the global validate_password function."""
        # Valid password (meets complexity)
        errors = validate_password("Secret25")
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
        assert is_password_valid("Secret25") is True
        assert is_password_valid("password123") is False  # common
        assert is_password_valid("weak") is False  # too short

    def test_get_password_strength_function(self):
        """Test the global get_password_strength function."""
        strength = get_password_strength("Secret25")
        assert "score" in strength
        assert "strength" in strength
        assert "feedback" in strength


class TestPasswordValidationIntegration:
    """Integration tests for password validation with models."""

    def test_user_create_validation(self):
        """Test password validation in UserCreate model."""
        from app.models.user import UserCreate

        # Valid password (meets complexity)
        user = UserCreate(email="test@example.com", password="Secret25", full_name="Test User")
        assert user.email == "test@example.com"

        # Invalid password (too short) - caught by Pydantic StringConstraints or custom validator
        with pytest.raises(Exception) as exc_info:
            UserCreate(email="test@example.com", password="weak", full_name="Test User")
        error_msg = str(exc_info.value)
        assert "8 characters" in error_msg or "string_too_short" in error_msg

    def test_password_change_validation(self):
        """Test password validation in PasswordChange model."""
        from app.models.user import PasswordChange

        # Valid passwords (meets complexity)
        change = PasswordChange(current_password="oldpass", new_password="Newpass123")
        assert change.new_password == "Newpass123"

        # Invalid new password (too short) - caught by Pydantic StringConstraints or custom validator
        with pytest.raises(Exception) as exc_info:
            PasswordChange(current_password="oldpass", new_password="weak")
        error_msg = str(exc_info.value)
        assert "8 characters" in error_msg or "string_too_short" in error_msg

    def test_reset_password_validation(self):
        """Test password validation in ResetPasswordRequest."""
        from app.api.auth import ResetPasswordRequest

        # Valid password (meets complexity)
        reset = ResetPasswordRequest(token="valid_token", new_password="Secret25")
        assert reset.new_password == "Secret25"

        # Invalid password (too short) - caught by Pydantic StringConstraints or custom validator
        with pytest.raises(Exception) as exc_info:
            ResetPasswordRequest(token="valid_token", new_password="weak")
        error_msg = str(exc_info.value)
        assert "8 characters" in error_msg or "string_too_short" in error_msg


@pytest.mark.parametrize(
    "password,expected",
    [
        ("Secret25", True),  # Valid password (8 chars, meets complexity)
        ("password123", False),  # Common password
        ("weak", False),  # Too short (4 chars)
        ("123456", False),  # Common password
        ("qwerty", False),  # Common password
        ("Mypassword1", True),  # Valid (10 chars, meets complexity)
        ("Testing123", True),  # Mixed case + numbers (10 chars)
        ("Abcdefgh1", True),  # Just letters + digit (8 chars)
        ("short", False),  # Too short (5 chars)
        ("seven77", False),  # Too short (7 chars)
        ("secret25", False),  # Missing uppercase
        ("SECRETPW", False),  # Missing lowercase and digit
        ("abcdefgh", False),  # Missing uppercase and digit
    ],
)
def test_password_validation_parametrized(password, expected):
    """Parametrized test for various password scenarios."""
    validator = PasswordValidator()
    assert validator.is_valid(password) == expected
