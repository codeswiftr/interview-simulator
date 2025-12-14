"""Test password validation utility."""

import pytest
from typing import Any
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
        """Test password minimum length validation."""
        # Too short (11 chars)
        errors = self.validator.validate("Abcdef1!")
        assert PasswordValidationError.TOO_SHORT.value in errors

        # Just right (12 chars)
        assert self.validator.is_valid("A1b2c3d4e5f!") is True

        # Longer (16 chars)
        assert self.validator.is_valid("M1n2d3s4k5n6o7p!") is True

    def test_character_composition_requirements(self):
        """Test password character composition requirements."""
        # Base valid password (avoid "password" in the actual password)
        valid_password = "SecurePassw0rd!"

        # Missing uppercase
        errors = self.validator.validate("validpassword123!")
        assert PasswordValidationError.MISSING_UPPERCASE.value in errors

        # Missing lowercase
        errors = self.validator.validate("VALIDPASSWORD123!")
        assert PasswordValidationError.MISSING_LOWERCASE.value in errors

        # Missing number
        errors = self.validator.validate("ValidPassword!!!")
        assert PasswordValidationError.MISSING_NUMBER.value in errors

        # Missing special character
        errors = self.validator.validate("ValidPassword123")
        assert PasswordValidationError.MISSING_SPECIAL.value in errors

        # All requirements met
        assert self.validator.is_valid(valid_password) is True

    def test_common_patterns_blocked(self):
        """Test that common password patterns are blocked."""
        common_patterns = [
            "Password123!",
            "Qwerty123!",
            "Admin123!",
            "Welcome123!",
            "Monkey123!",
            "Letmein123!",
        ]

        for password in common_patterns:
            errors = self.validator.validate(password)
            assert PasswordValidationError.COMMON_PATTERN.value in errors
            assert self.validator.is_valid(password) is False

    def test_username_email_blocking(self):
        """Test that passwords cannot contain username or email."""
        # With username
        errors = self.validator.validate(
            "JohnDoe123!",
            username="JohnDoe"
        )
        assert "Password cannot contain your username" in errors

        # With email
        errors = self.validator.validate(
            "John123!@example.com",
            email="john@example.com"
        )
        assert "Password cannot contain your email address" in errors

        # With email local part
        errors = self.validator.validate(
            "John123!",
            email="john@example.com"
        )
        assert "Password cannot contain your email address" in errors

        # Valid without username/email match
        assert self.validator.is_valid(
            "SecurePassw0rd!",
            username="JohnDoe",
            email="john@example.com"
        ) is True

    def test_dictionary_words_blocked(self):
        """Test that dictionary words are blocked."""
        # Dictionary word in password
        errors = self.validator.validate("Between123!")
        assert PasswordValidationError.DICTIONARY_WORD.value in errors

        # No dictionary word
        assert self.validator.is_valid("B3tw33n12!") is True  # Leetspeak

    def test_repeated_characters_blocked(self):
        """Test that repeated characters are blocked."""
        # 6 same characters in a row
        errors = self.validator.validate("Passwordaaaaaa!")
        assert PasswordValidationError.REPEATED_CHARS.value in errors

        # 5 same characters (should be okay)
        assert self.validator.is_valid("X1aaaaa!") is True

    def test_sequential_characters_blocked(self):
        """Test that sequential characters are blocked."""
        # Sequential numbers
        errors = self.validator.validate("Password123456!")
        assert PasswordValidationError.SEQUENTIAL_CHARS.value in errors

        # Sequential letters
        errors = self.validator.validate("Passwordabcdef!")
        assert PasswordValidationError.SEQUENTIAL_CHARS.value in errors

        # Reverse sequential numbers
        errors = self.validator.validate("Password654321!")
        assert PasswordValidationError.SEQUENTIAL_CHARS.value in errors

        # Reverse sequential letters
        errors = self.validator.validate("Passwordfedcba!")
        assert PasswordValidationError.SEQUENTIAL_CHARS.value in errors

        # No sequential
        assert self.validator.is_valid("P@ssw0rd!z9x") is True

    def test_password_strength_scoring(self):
        """Test password strength scoring."""
        # Very weak password
        strength = self.validator.get_password_strength("weak")
        assert strength["strength"] == "Moderate"  # 4 chars gives 20 points
        assert strength["score"] >= 20
        assert strength["score"] < 40

        # Weak password
        strength = self.validator.get_password_strength("Weakpass123!")
        assert strength["strength"] in ["Weak", "Moderate", "Strong"]
        assert strength["score"] >= 40  # Length + variety gives at least 40

        # Moderate password
        strength = self.validator.get_password_strength("Moderate123!")
        assert strength["strength"] in ["Weak", "Moderate", "Strong"]
        assert strength["score"] >= 40

        # Strong password
        strength = self.validator.get_password_strength("StrongPassword123!")
        assert strength["strength"] in ["Moderate", "Strong"]  # Has common pattern
        assert strength["score"] >= 40

        # Very strong password (no common patterns)
        strength = self.validator.get_password_strength("V3ry$tr0ngP@ssw0rd!z9x")
        assert strength["strength"] == "Very Strong"
        assert strength["score"] >= 80

    def test_password_strength_feedback(self):
        """Test password strength feedback."""
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
        errors = validate_password("SecurePassw0rd!")
        assert len(errors) == 0

        # Invalid password
        errors = validate_password("weak")
        assert len(errors) > 0
        assert PasswordValidationError.TOO_SHORT.value in errors

    def test_is_password_valid_function(self):
        """Test the global is_password_valid function."""
        assert is_password_valid("SecurePassw0rd!") is True
        assert is_password_valid("weak") is False

    def test_get_password_strength_function(self):
        """Test the global get_password_strength function."""
        strength = get_password_strength("SecurePassw0rd!")
        assert "score" in strength
        assert "strength" in strength
        assert "feedback" in strength


class TestPasswordValidationIntegration:
    """Integration tests for password validation with models."""

    def test_user_create_validation(self):
        """Test password validation in UserCreate model."""
        from app.models.user import UserCreate

        # Valid password
        user = UserCreate(
            email="test@example.com",
            password="SecurePassw0rd!",
            full_name="Test User"
        )
        assert user.email == "test@example.com"

        # Invalid password
        with pytest.raises(Exception) as exc_info:
            UserCreate(
                email="test@example.com",
                password="weak",
                full_name="Test User"
            )
        assert "Password must be at least 12 characters long" in str(exc_info.value)

    def test_password_change_validation(self):
        """Test password validation in PasswordChange model."""
        from app.models.user import PasswordChange

        # Valid passwords
        change = PasswordChange(
            current_password="OldPassw0rd!",
            new_password="NewSecurePassw0rd!"
        )
        assert change.new_password == "NewSecurePassw0rd!"

        # Invalid new password
        with pytest.raises(Exception) as exc_info:
            PasswordChange(
                current_password="OldPassword123!",
                new_password="weak"
            )
        assert "Password must be at least 12 characters long" in str(exc_info.value)

    def test_reset_password_validation(self):
        """Test password validation in ResetPasswordRequest."""
        from app.api.auth import ResetPasswordRequest

        # Valid password
        reset = ResetPasswordRequest(
            token="valid_token",
            new_password="SecurePassw0rd!"
        )
        assert reset.new_password == "SecurePassw0rd!"

        # Invalid password
        with pytest.raises(Exception) as exc_info:
            ResetPasswordRequest(
                token="valid_token",
                new_password="weak"
            )
        assert "Password must be at least 12 characters long" in str(exc_info.value)


@pytest.mark.parametrize("password,expected", [
    ("SecurePassw0rd!", True),
    ("short", False),
    ("nouppercase123!", False),
    ("NOLOWERCASE123!", False),
    ("NoNumbers!!!", False),
    ("NoSpecialChars123", False),
    ("Password123!", False),  # Contains common pattern
    ("UserPassword123!", False),  # Contains username when username="User"
])
def test_password_validation_parametrized(password, expected):
    """Parametrized test for various password scenarios."""
    validator = PasswordValidator()
    assert validator.is_valid(password, username="User", email="user@example.com") == expected