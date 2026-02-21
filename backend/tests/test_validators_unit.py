"""Pure unit tests for password validation.

Tests PasswordValidator, validate_password, get_password_strength.
No database required.
"""

import pytest

from app.utils.password_validation import (
    PasswordValidator,
    get_password_strength,
    is_password_valid,
    validate_password,
    validate_password_complexity,
)


class TestPasswordValidator:
    def test_valid_password(self):
        errors = validate_password("StrongPass1!")
        assert errors == []

    def test_too_short(self):
        errors = validate_password("Ab1!")
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase(self):
        errors = validate_password("alllowercase1")
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase(self):
        errors = validate_password("ALLUPPERCASE1")
        assert any("lowercase" in e for e in errors)

    def test_no_digit(self):
        errors = validate_password("NoDigitsHere!")
        assert any("number" in e for e in errors)

    def test_common_password_blocked(self):
        errors = validate_password("password")
        assert any("common" in e.lower() for e in errors)

    def test_password_matching_username(self):
        errors = validate_password("TestUser1", username="testuser1")
        assert any("username" in e for e in errors)

    def test_password_matching_email_local(self):
        errors = validate_password("JohnDoe1", email="johndoe1@example.com")
        assert any("email" in e for e in errors)

    def test_is_password_valid_returns_bool(self):
        assert is_password_valid("StrongPass1!") is True
        assert is_password_valid("weak") is False

    def test_validate_password_complexity_raises(self):
        with pytest.raises(ValueError):
            validate_password_complexity("short")


class TestGetPasswordStrength:
    def test_strong_password(self):
        result = get_password_strength("V3ryStr0ng!Pass#word")
        assert result["score"] >= 60
        assert result["strength"] in ("Strong", "Very Strong")

    def test_weak_password(self):
        result = get_password_strength("abcdefgh")
        assert result["score"] < 60
        assert len(result["feedback"]) > 0

    def test_common_password_low_score(self):
        result = get_password_strength("password")
        assert "Avoid common passwords" in result["feedback"]


class TestCustomValidator:
    def test_require_special_char(self):
        v = PasswordValidator(require_special=True)
        errors = v.validate("StrongPass1")
        assert any("special" in e for e in errors)

    def test_custom_min_length(self):
        v = PasswordValidator(min_length=12)
        errors = v.validate("Short1A!")
        assert any("12 characters" in e or "8 characters" in e for e in errors)
