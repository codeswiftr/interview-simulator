"""Password validation utilities.

Requires minimum 8 characters and blocks common passwords.
Use get_password_strength() for frontend warnings about weak passwords.
"""

import re
from enum import StrEnum


class PasswordValidationError(StrEnum):
    """Password validation error codes."""

    TOO_SHORT = "Password must be at least 8 characters long"
    COMMON_PASSWORD = "Password is too common and easily guessed"
    NO_UPPERCASE = "Password must contain at least one uppercase letter"
    NO_LOWERCASE = "Password must contain at least one lowercase letter"
    NO_DIGIT = "Password must contain at least one number"
    NO_SPECIAL = "Password must contain at least one special character"


class PasswordValidator:
    """Password validation with configurable complexity requirements.

    Default mode enforces:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - Blocks common passwords

    Use get_password_strength() for detailed feedback on the frontend.
    """

    # Only block the most common/trivial passwords
    BLOCKED_PASSWORDS = [
        "password",
        "123456",
        "12345678",
        "123456789",
        "qwerty",
        "abc123",
        "password1",
        "password123",
        "111111",
        "123123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
        "qwerty123",
        "iloveyou",
    ]

    # Special characters (for strength scoring only)
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False,
    ):
        """Initialize password validator.

        Args:
            min_length: Minimum password length (default: 8)
            require_uppercase: Require at least one uppercase letter (default: True)
            require_lowercase: Require at least one lowercase letter (default: True)
            require_digit: Require at least one digit (default: True)
            require_special: Require at least one special character (default: False)
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(
        self, password: str, username: str | None = None, email: str | None = None
    ) -> list[str]:
        """Validate password with complexity requirements.

        Args:
            password: Password to validate
            username: Optional username to check against
            email: Optional email to check against

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        password_lower = password.lower()

        # 1. Minimum length
        if len(password) < self.min_length:
            errors.append(PasswordValidationError.TOO_SHORT.value)

        # 2. Complexity requirements
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append(PasswordValidationError.NO_UPPERCASE.value)

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append(PasswordValidationError.NO_LOWERCASE.value)

        if self.require_digit and not re.search(r"\d", password):
            errors.append(PasswordValidationError.NO_DIGIT.value)

        if self.require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            errors.append(PasswordValidationError.NO_SPECIAL.value)

        # 3. Block only the most common passwords
        if password_lower in self.BLOCKED_PASSWORDS:
            errors.append(PasswordValidationError.COMMON_PASSWORD.value)

        # 4. Don't allow password to exactly match username or email local part
        if username and password_lower == username.lower():
            errors.append("Password cannot be the same as your username")

        if email:
            email_local = email.split("@")[0].lower()
            if email_local and password_lower == email_local:
                errors.append("Password cannot be the same as your email")

        return errors

    def is_valid(
        self, password: str, username: str | None = None, email: str | None = None
    ) -> bool:
        """Check if password is valid.

        Args:
            password: Password to validate
            username: Optional username to check against
            email: Optional email to check against

        Returns:
            True if password is valid, False otherwise
        """
        return len(self.validate(password, username, email)) == 0

    def get_password_strength(self, password: str) -> dict[str, int | str | list[str]]:
        """Get password strength metrics.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with strength metrics and score (0-100)
        """
        score = 0
        feedback = []

        # Length scoring (up to 30 points)
        length = len(password)
        if length >= 12:
            score += 20
            if length >= 16:
                score += 10
        else:
            feedback.append("Add more characters to increase strength")

        # Character variety (up to 40 points)
        if re.search(r"[A-Z]", password):
            score += 10
        else:
            feedback.append("Add uppercase letters")

        if re.search(r"[a-z]", password):
            score += 10
        else:
            feedback.append("Add lowercase letters")

        if re.search(r"\d", password):
            score += 10
        else:
            feedback.append("Add numbers")

        if re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            score += 10
        else:
            feedback.append("Add special characters")

        # Complexity bonus (up to 30 points)
        unique_chars = len(set(password))
        if unique_chars >= length * 0.6:
            score += 15
        elif unique_chars >= length * 0.4:
            score += 10
        else:
            feedback.append("Use more unique characters")

        # No common patterns (up to 15 points)
        password_lower = password.lower()
        has_common = password_lower in self.BLOCKED_PASSWORDS
        if not has_common:
            score += 15
        else:
            feedback.append("Avoid common passwords")

        # Determine strength level
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Moderate"
        elif score >= 20:
            strength = "Weak"
        else:
            strength = "Very Weak"

        return {"score": min(score, 100), "strength": strength, "feedback": feedback}


# Global validator instance
password_validator = PasswordValidator()


def validate_password(
    password: str, username: str | None = None, email: str | None = None
) -> list[str]:
    """Validate password using the global validator.

    Args:
        password: Password to validate
        username: Optional username to check against
        email: Optional email to check against

    Returns:
        List of validation error messages
    """
    return password_validator.validate(password, username, email)


def is_password_valid(password: str, username: str | None = None, email: str | None = None) -> bool:
    """Check if password is valid using the global validator.

    Args:
        password: Password to validate
        username: Optional username to check against
        email: Optional email to check against

    Returns:
        True if password is valid, False otherwise
    """
    return password_validator.is_valid(password, username, email)


def get_password_strength(password: str) -> dict[str, int | str | list[str]]:
    """Get password strength metrics using the global validator.

    Args:
        password: Password to analyze

    Returns:
        Dictionary with strength metrics
    """
    return password_validator.get_password_strength(password)


def validate_password_complexity(password: str) -> None:
    """Validate password complexity, raising ValueError if invalid.

    Args:
        password: Password to validate

    Raises:
        ValueError: If password doesn't meet complexity requirements
    """
    errors = password_validator.validate(password)
    if errors:
        raise ValueError("; ".join(errors))
