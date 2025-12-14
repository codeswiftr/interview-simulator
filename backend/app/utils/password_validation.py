"""Password validation utilities for strong password requirements."""

import re
from typing import List
from enum import Enum


class PasswordValidationError(str, Enum):
    """Password validation error codes."""
    TOO_SHORT = "Password must be at least 12 characters long"
    MISSING_UPPERCASE = "Password must contain at least one uppercase letter (A-Z)"
    MISSING_LOWERCASE = "Password must contain at least one lowercase letter (a-z)"
    MISSING_NUMBER = "Password must contain at least one number (0-9)"
    MISSING_SPECIAL = "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    COMMON_PATTERN = "Password contains common patterns that are not allowed"
    DICTIONARY_WORD = "Password contains dictionary words"
    REPEATED_CHARS = "Password contains repeated characters (e.g., 'aaaaaa')"
    SEQUENTIAL_CHARS = "Password contains sequential characters (e.g., '123456')"


class PasswordValidator:
    """Strong password validation with comprehensive rules."""

    # Common password patterns to block
    COMMON_PATTERNS = [
        'password', '123456', '123456789', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'master',
        'hello', 'freedom', 'whatever', 'qazwsx', 'trustno1', 'iloveyou',
        'starwars', 'football', 'baseball', 'superman', 'asshole'
    ]

    # Special characters allowed
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Common dictionary words to avoid (basic set)
    DICTIONARY_WORDS = {
        'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
        'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being',
        'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do', 'does',
        'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
        'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
        'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its',
        'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor',
        'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our',
        'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should',
        'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them',
        'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through',
        'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what',
        'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with',
        'you', 'your', 'yours', 'yourself', 'yourselves'
    }

    def __init__(self, min_length: int = 12):
        """Initialize password validator.

        Args:
            min_length: Minimum password length (default: 12)
        """
        self.min_length = min_length

    def validate(self, password: str, username: str = None, email: str = None) -> List[str]:
        """Validate password against all security rules.

        Args:
            password: Password to validate
            username: Optional username to check against
            email: Optional email to check against

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Convert password to lowercase for pattern checks (except for case sensitivity checks)
        password_lower = password.lower()

        # 1. Length check
        if len(password) < self.min_length:
            errors.append(PasswordValidationError.TOO_SHORT.value)

        # 2. Character composition checks
        if not re.search(r'[A-Z]', password):
            errors.append(PasswordValidationError.MISSING_UPPERCASE.value)

        if not re.search(r'[a-z]', password):
            errors.append(PasswordValidationError.MISSING_LOWERCASE.value)

        if not re.search(r'\d', password):
            errors.append(PasswordValidationError.MISSING_NUMBER.value)

        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append(PasswordValidationError.MISSING_SPECIAL.value)

        # 3. Common pattern checks
        for pattern in self.COMMON_PATTERNS:
            if pattern in password_lower:
                errors.append(PasswordValidationError.COMMON_PATTERN.value)
                break

        # 4. Check against username and email
        if username and username.lower() in password_lower:
            errors.append("Password cannot contain your username")

        if email:
            email_local = email.split('@')[0].lower()
            if email_local and len(email_local) > 2 and email_local in password_lower:
                errors.append("Password cannot contain your email address")

        # 5. Dictionary word check (for words longer than 3 characters)
        for word in self.DICTIONARY_WORDS:
            if len(word) > 3 and word in password_lower:
                errors.append(PasswordValidationError.DICTIONARY_WORD.value)
                break

        # 6. Repeated characters check
        if re.search(r'(.)\1{5,}', password):  # 6 or more same characters
            errors.append(PasswordValidationError.REPEATED_CHARS.value)

        # 7. Sequential characters check
        if self._has_sequential_chars(password):
            errors.append(PasswordValidationError.SEQUENTIAL_CHARS.value)

        return errors

    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters (e.g., '123456', 'abcdef')."""
        password_lower = password.lower()

        # Check for sequential numbers
        for i in range(len(password_lower) - 5):
            substr = password_lower[i:i+6]
            if substr.isdigit():
                nums = [int(c) for c in substr]
                if all(nums[j] + 1 == nums[j + 1] for j in range(len(nums) - 1)):
                    return True
                if all(nums[j] - 1 == nums[j + 1] for j in range(len(nums) - 1)):
                    return True

        # Check for sequential letters
        for i in range(len(password_lower) - 5):
            substr = password_lower[i:i+6]
            if substr.isalpha():
                chars = [ord(c) for c in substr]
                if all(chars[j] + 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True
                if all(chars[j] - 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True

        return False

    def is_valid(self, password: str, username: str = None, email: str = None) -> bool:
        """Check if password is valid.

        Args:
            password: Password to validate
            username: Optional username to check against
            email: Optional email to check against

        Returns:
            True if password is valid, False otherwise
        """
        return len(self.validate(password, username, email)) == 0

    def get_password_strength(self, password: str) -> dict:
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
        if re.search(r'[A-Z]', password):
            score += 10
        else:
            feedback.append("Add uppercase letters")

        if re.search(r'[a-z]', password):
            score += 10
        else:
            feedback.append("Add lowercase letters")

        if re.search(r'\d', password):
            score += 10
        else:
            feedback.append("Add numbers")

        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
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
        has_common = any(pattern in password_lower for pattern in self.COMMON_PATTERNS)
        if not has_common:
            score += 15
        else:
            feedback.append("Avoid common patterns")

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

        return {
            "score": min(score, 100),
            "strength": strength,
            "feedback": feedback
        }


# Global validator instance
password_validator = PasswordValidator()


def validate_password(password: str, username: str = None, email: str = None) -> List[str]:
    """Validate password using the global validator.

    Args:
        password: Password to validate
        username: Optional username to check against
        email: Optional email to check against

    Returns:
        List of validation error messages
    """
    return password_validator.validate(password, username, email)


def is_password_valid(password: str, username: str = None, email: str = None) -> bool:
    """Check if password is valid using the global validator.

    Args:
        password: Password to validate
        username: Optional username to check against
        email: Optional email to check against

    Returns:
        True if password is valid, False otherwise
    """
    return password_validator.is_valid(password, username, email)


def get_password_strength(password: str) -> dict:
    """Get password strength metrics using the global validator.

    Args:
        password: Password to analyze

    Returns:
        Dictionary with strength metrics
    """
    return password_validator.get_password_strength(password)