"""Tests for enhanced password complexity validation.

Tests the updated password validation that enforces:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Blocks common passwords
"""

import pytest
from pydantic import ValidationError

from app.models.user import PasswordChange, UserCreate
from app.utils.password_validation import PasswordValidator, validate_password


class TestPasswordComplexity:
    """Test enhanced password complexity requirements."""

    def test_password_requires_uppercase(self):
        """Test password must contain uppercase letter."""
        errors = validate_password("lowercase123")
        assert any("uppercase" in err.lower() for err in errors)

    def test_password_requires_lowercase(self):
        """Test password must contain lowercase letter."""
        errors = validate_password("UPPERCASE123")
        assert any("lowercase" in err.lower() for err in errors)

    def test_password_requires_digit(self):
        """Test password must contain at least one number."""
        errors = validate_password("NoDigitsHere")
        assert any("number" in err.lower() for err in errors)

    def test_password_minimum_length(self):
        """Test password must be at least 8 characters."""
        errors = validate_password("Short1")
        assert any("8 characters" in err for err in errors)

    def test_valid_password_passes(self):
        """Test valid password with all requirements passes."""
        errors = validate_password("ValidPass123")
        assert len(errors) == 0

    def test_blocks_common_passwords(self):
        """Test blocks common passwords even if they meet complexity."""
        # password123 meets complexity but is blocked
        errors = validate_password("Password123")
        # Should fail because "password123" is in blocked list
        assert len(errors) > 0

    def test_rejects_password_matching_email(self):
        """Test password cannot match email local part."""
        errors = validate_password("myemail123", email="myemail123@example.com")
        assert any("email" in err.lower() for err in errors)

    def test_rejects_password_matching_username(self):
        """Test password cannot match username."""
        errors = validate_password("myusername", username="myusername")
        assert any("username" in err.lower() for err in errors)

    def test_accepts_strong_password(self):
        """Test strong password is accepted."""
        errors = validate_password("MyStr0ngP@ssw0rd!")
        assert len(errors) == 0


class TestPasswordValidatorClass:
    """Test PasswordValidator class directly."""

    def test_default_requirements(self):
        """Test validator with default requirements."""
        validator = PasswordValidator()
        assert validator.min_length == 8
        assert validator.require_uppercase is True
        assert validator.require_lowercase is True
        assert validator.require_digit is True
        assert validator.require_special is False

    def test_custom_requirements(self):
        """Test validator with custom requirements."""
        validator = PasswordValidator(
            min_length=12,
            require_uppercase=False,
            require_special=True,
        )
        assert validator.min_length == 12
        assert validator.require_uppercase is False
        assert validator.require_special is True

    def test_special_character_requirement(self):
        """Test special character can be required."""
        validator = PasswordValidator(require_special=True)
        errors = validator.validate("NoSpecial123")
        assert any("special" in err.lower() for err in errors)

        # Valid with special character
        errors = validator.validate("WithSpecial123!")
        assert len(errors) == 0

    def test_relaxed_validator(self):
        """Test validator with relaxed requirements."""
        validator = PasswordValidator(
            min_length=6,
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
        )
        errors = validator.validate("simple")
        assert len(errors) == 0

    def test_is_valid_method(self):
        """Test is_valid convenience method."""
        validator = PasswordValidator()
        assert validator.is_valid("ValidPass123")
        assert not validator.is_valid("weak")


class TestUserCreateValidation:
    """Test password validation in UserCreate model."""

    def test_user_create_rejects_weak_password(self):
        """Test UserCreate rejects passwords failing complexity."""
        with pytest.raises(ValidationError) as exc:
            UserCreate(
                email="test@example.com",
                password="weakpass",
            )
        assert "validation failed" in str(exc.value).lower()

    def test_user_create_accepts_strong_password(self):
        """Test UserCreate accepts passwords meeting complexity."""
        user = UserCreate(
            email="test@example.com",
            password="StrongPass123",
        )
        assert user.email == "test@example.com"

    def test_user_create_checks_email_match(self):
        """Test UserCreate rejects password matching email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="myemail@example.com",
                password="myemail",
            )

    def test_user_create_checks_username_match(self):
        """Test UserCreate rejects password matching full_name."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="testuser",
                full_name="testuser",
            )


class TestPasswordChangeValidation:
    """Test password validation in PasswordChange model."""

    def test_password_change_rejects_weak_password(self):
        """Test PasswordChange rejects weak new password."""
        with pytest.raises(ValidationError):
            PasswordChange(
                current_password="OldPass123",
                new_password="weak",
            )

    def test_password_change_accepts_strong_password(self):
        """Test PasswordChange accepts strong new password."""
        change = PasswordChange(
            current_password="OldPass123",
            new_password="NewStr0ngPass",
        )
        assert change.new_password == "NewStr0ngPass"


class TestPasswordStrength:
    """Test password strength scoring."""

    def test_very_weak_password(self):
        """Test very weak password gets low score."""
        from app.utils.password_validation import get_password_strength

        result = get_password_strength("weak")
        assert result["score"] <= 40
        assert result["strength"] in ["Very Weak", "Weak", "Moderate"]

    def test_moderate_password(self):
        """Test moderate password gets medium score."""
        from app.utils.password_validation import get_password_strength

        result = get_password_strength("Moderate1")
        assert 40 <= result["score"] < 80
        assert result["strength"] in ["Moderate", "Strong"]

    def test_strong_password(self):
        """Test strong password gets high score."""
        from app.utils.password_validation import get_password_strength

        result = get_password_strength("VeryStr0ng!Pass")
        assert result["score"] >= 60
        assert result["strength"] in ["Strong", "Very Strong"]

    def test_very_strong_password(self):
        """Test very strong password gets maximum score."""
        from app.utils.password_validation import get_password_strength

        result = get_password_strength("Sup3rStr0ng!P@ssw0rd#2024")
        assert result["score"] >= 80
        assert result["strength"] == "Very Strong"

    def test_strength_includes_feedback(self):
        """Test strength analysis includes improvement feedback."""
        from app.utils.password_validation import get_password_strength

        result = get_password_strength("weak")
        assert "feedback" in result
        assert len(result["feedback"]) > 0


class TestPasswordValidationEdgeCases:
    """Test edge cases in password validation."""

    def test_empty_password(self):
        """Test empty password is rejected."""
        errors = validate_password("")
        assert len(errors) > 0

    def test_whitespace_password(self):
        """Test whitespace-only password is rejected."""
        errors = validate_password("        ")
        assert len(errors) > 0

    def test_unicode_password(self):
        """Test unicode characters in password."""
        # Should work - we don't restrict to ASCII
        errors = validate_password("Üñíc0dé123")
        # May have errors for other reasons, but should not crash
        assert isinstance(errors, list)

    def test_very_long_password(self):
        """Test very long password is accepted."""
        long_pass = "A1" + "x" * 100
        errors = validate_password(long_pass)
        # Should pass - no maximum length restriction
        assert len(errors) == 0

    def test_case_sensitivity_for_blocked(self):
        """Test blocked password check is case-insensitive."""
        errors = validate_password("PASSWORD123")
        # Should be blocked even with different case
        assert len(errors) > 0
