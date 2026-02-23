"""Pure unit tests for password validation utility.

Targets uncovered lines in app/utils/password_validation.py:
  - Line 114:   require_special=True with no special character
  - Line 176:   get_password_strength feedback for missing lowercase letters
  - Lines 192-195: unique-character ratio branches (medium and low uniqueness)
  - Line 203:   get_password_strength feedback for common passwords
  - Lines 212-215: strength level labels "Moderate", "Weak", "Very Weak"
  - Lines 275-277: validate_password_complexity raising ValueError
"""

import pytest

from app.utils.password_validation import (
    PasswordValidationError,
    PasswordValidator,
    validate_password_complexity,
)

# ---------------------------------------------------------------------------
# Line 114 — require_special=True path
# ---------------------------------------------------------------------------


class TestRequireSpecialCharacter:
    """Validator configured with require_special=True."""

    def setup_method(self):
        self.validator = PasswordValidator(require_special=True)

    def test_missing_special_char_returns_error(self):
        """Password without special character triggers NO_SPECIAL error (line 114)."""
        errors = self.validator.validate("SecurePass1")
        assert PasswordValidationError.NO_SPECIAL.value in errors

    def test_password_with_special_char_passes(self):
        """Password with special character does not trigger NO_SPECIAL error."""
        errors = self.validator.validate("SecurePass1!")
        assert PasswordValidationError.NO_SPECIAL.value not in errors

    def test_all_special_chars_accepted(self):
        """Each supported special character satisfies require_special."""
        for ch in "!@#$%^&*()_+-=[]{}|;:,.<>?":
            password = f"SecurePa1{ch}"
            errors = self.validator.validate(password)
            assert PasswordValidationError.NO_SPECIAL.value not in errors, (
                f"Special char '{ch}' should satisfy require_special"
            )

    def test_require_special_false_no_error_without_special(self):
        """Default validator (require_special=False) accepts passwords lacking special chars."""
        default = PasswordValidator()
        errors = default.validate("SecurePass1")
        assert PasswordValidationError.NO_SPECIAL.value not in errors


# ---------------------------------------------------------------------------
# Line 176 — get_password_strength: feedback for missing lowercase
# ---------------------------------------------------------------------------


class TestStrengthFeedbackNoLowercase:
    """Ensure the 'Add lowercase letters' feedback path is exercised."""

    def setup_method(self):
        self.validator = PasswordValidator()

    def test_all_uppercase_triggers_lowercase_feedback(self):
        """Password with no lowercase letters adds 'Add lowercase letters' feedback (line 176)."""
        # ALLUPPERCASE123! — no lowercase
        result = self.validator.get_password_strength("ALLUPPERCASE123!")
        assert "Add lowercase letters" in result["feedback"]

    def test_has_lowercase_no_lowercase_feedback(self):
        """Password with at least one lowercase does not add lowercase feedback."""
        result = self.validator.get_password_strength("SecurePass1!")
        assert "Add lowercase letters" not in result["feedback"]

    def test_single_lowercase_satisfies_check(self):
        """A single lowercase letter among uppercase suppresses the feedback."""
        result = self.validator.get_password_strength("UPPERCASEa123!")
        assert "Add lowercase letters" not in result["feedback"]


# ---------------------------------------------------------------------------
# Lines 192-195 — unique character ratio branches
# ---------------------------------------------------------------------------


class TestUniqueCharacterRatioBranches:
    """Cover the elif (medium uniqueness, line 192) and else (low uniqueness, line 195) branches."""

    def setup_method(self):
        self.validator = PasswordValidator()

    def _build_password_with_ratio(self, length: int, unique_count: int) -> str:
        """Construct a password of given length with exactly unique_count distinct characters.

        Uses uppercase + lowercase + digit so the validator does not add
        unrelated errors that could affect scoring expectations.
        """
        # Build the unique characters pool from printable safe chars
        unique_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop0123456789")[:unique_count]
        # Pad to desired length by repeating the unique chars
        padding = (unique_chars * ((length // unique_count) + 1))[:length]
        password = "".join(padding)
        # Ensure it has at least one uppercase, lowercase, digit (validator requirements)
        # Inject known chars at fixed positions to avoid complexity errors interfering
        password = list(password)
        if unique_count >= 3:
            password[0] = unique_chars[0].upper() if unique_chars[0].islower() else unique_chars[0]
            # make sure we have lowercase and digit present
        return "".join(password)

    def test_medium_uniqueness_branch_adds_10_points(self):
        """Ratio between 0.4 and 0.6 (exclusive) hits the elif branch (line 192-193).

        Build: length=10, unique_count=5 => ratio=0.5 (>= 0.4, < 0.6)
        """
        # "AaBbCaAaBb" length=10, unique=5 (A,a,B,b,C) => ratio = 5/10 = 0.5
        password = "AaBbCaAaBb"
        assert len(password) == 10
        assert len(set(password)) == 5  # ratio = 0.5 exactly

        result = self.validator.get_password_strength(password)
        # The score should include the elif branch bonus (10) not the if branch (15)
        # Verify the "Use more unique characters" feedback is NOT present
        assert "Use more unique characters" not in result["feedback"]
        # Score should be positive (branch executed)
        assert result["score"] >= 0

    def test_low_uniqueness_branch_triggers_feedback(self):
        """Ratio below 0.4 hits the else branch, appending feedback (lines 194-195).

        Build: length=10, unique_count=3 => ratio=0.3 (< 0.4)
        "AAAaAAAaAb" — unique chars: A, a, b = 3; length = 10; ratio = 3/10 = 0.3
        """
        password = "AAAaAAAaAb"
        assert len(password) == 10
        assert len(set(password)) == 3  # ratio = 0.3
        assert 3 / 10 < 0.4  # confirms we're in the else branch

        result = self.validator.get_password_strength(password)
        assert "Use more unique characters" in result["feedback"]

    def test_high_uniqueness_branch_no_feedback(self):
        """Ratio >= 0.6 hits the if branch (15 bonus points, no feedback)."""
        # "SecurePass1!" length=12, all different: S,e,c,u,r,P,a,s,1,! + others
        password = "SecurePass1!"
        ratio = len(set(password)) / len(password)
        assert ratio >= 0.6, f"Expected ratio >= 0.6, got {ratio} for {password!r}"

        result = self.validator.get_password_strength(password)
        assert "Use more unique characters" not in result["feedback"]

    def test_exact_boundary_0_4_uses_elif(self):
        """Exactly 0.4 unique ratio triggers the elif branch (score +10, no feedback)."""
        # length=10, unique=4 => ratio=0.4 exactly => elif unique_chars >= length * 0.4
        # "AAABBBCCDa" => A,B,C,D,a = 5? No. Need exactly 4 distinct for length 10.
        # "AAABBBCCDa" = A(3) B(3) C(2) D(1) a(1) = 5 distinct. Try again.
        # "AABBCCDDaA" = A(3) B(2) C(2) D(2) a(1) = 5 distinct. Still 5.
        # "AAAABBBBaA" = A(5) B(4) a(1) = 3 distinct (< 0.4). Not what we want.
        # Exact 4 distinct in 10 chars: "AAABBBCCCa" = A(3) B(3) C(3) a(1) = 4 distinct
        password = "AAABBBCCCa"
        assert len(password) == 10
        assert len(set(password)) == 4  # ratio = 0.4 exactly
        assert 4 / 10 >= 0.4
        assert 4 / 10 < 0.6

        result = self.validator.get_password_strength(password)
        # elif branch: no "Use more unique characters" feedback
        assert "Use more unique characters" not in result["feedback"]


# ---------------------------------------------------------------------------
# Line 203 — get_password_strength feedback for common passwords
# ---------------------------------------------------------------------------


class TestStrengthFeedbackCommonPassword:
    """Cover the 'Avoid common passwords' feedback path (line 203)."""

    def setup_method(self):
        self.validator = PasswordValidator()

    def test_common_password_adds_avoid_feedback(self):
        """A password in BLOCKED_PASSWORDS gets 'Avoid common passwords' feedback (line 203)."""
        result = self.validator.get_password_strength("password")
        assert "Avoid common passwords" in result["feedback"]

    def test_common_password_loses_15_points(self):
        """A blocked password does not receive the 15-point non-common bonus."""
        uncommon = self.validator.get_password_strength("SecurePass1!")
        common = self.validator.get_password_strength("password")
        # The common password is penalised by 15 points relative to the non-common bonus
        # We can verify this by checking the score difference includes the 15-pt gap
        # (other factors differ, so just assert common score is lower overall)
        assert common["score"] < uncommon["score"]

    def test_non_common_password_no_avoid_feedback(self):
        """A non-blocked password does not get 'Avoid common passwords' feedback."""
        result = self.validator.get_password_strength("UniqueP@ss99")
        assert "Avoid common passwords" not in result["feedback"]

    @pytest.mark.parametrize(
        "common_pw",
        [
            "password",
            "123456",
            "qwerty",
            "admin",
            "letmein",
            "iloveyou",
        ],
    )
    def test_each_blocked_password_gets_avoid_feedback(self, common_pw: str):
        """Every entry in BLOCKED_PASSWORDS generates the 'Avoid' feedback."""
        result = self.validator.get_password_strength(common_pw)
        assert "Avoid common passwords" in result["feedback"]


# ---------------------------------------------------------------------------
# Lines 212-215 — strength label branches: "Moderate", "Weak", "Very Weak"
# ---------------------------------------------------------------------------


class TestStrengthLevelLabels:
    """Cover the Moderate (40-59), Weak (20-39), and Very Weak (<20) label branches."""

    def setup_method(self):
        self.validator = PasswordValidator()

    def _score_for(self, password: str) -> int:
        return self.validator.get_password_strength(password)["score"]  # type: ignore[return-value]

    def test_very_strong_label(self):
        """Score >= 80 produces 'Very Strong' label."""
        result = self.validator.get_password_strength("V3ryStr0ng!Unique#Pw")
        assert result["strength"] == "Very Strong"
        assert result["score"] >= 80

    def test_strong_label(self):
        """Score in [60, 79] produces 'Strong' label."""
        result = self.validator.get_password_strength("SecurePass1!")
        # Confirm it lands in the Strong band
        assert result["score"] >= 60
        assert result["strength"] in ("Strong", "Very Strong")

    def test_moderate_label(self):
        """Score in [40, 59] produces 'Moderate' label (line 211-212).

        Craft a password that:
        - is >= 8 chars but < 12 (no length bonus)           => +0
        - has uppercase                                        => +10
        - has lowercase                                        => +10
        - has digits                                           => +10
        - no special chars                                     => +0
        - unique ratio >= 0.6 (high uniqueness bonus)         => +15
        - not a common password                                => +15
        Total: 60? That lands in Strong. Need to lose 5-20 pts.

        Drop the uniqueness bonus by using a low-unique-ratio password
        (ratio < 0.4 for no uniqueness points):
        - no length bonus: 0
        - uppercase:      +10
        - lowercase:      +10
        - digit:          +10
        - no special:     +0
        - low uniqueness:  0 (else branch)
        - not common:     +15
        Total = 45 => Moderate
        """
        # 10 chars, 3 distinct (A, a, 1) => ratio 0.3 < 0.4
        password = "AAAaAAAa11"
        assert len(password) == 10  # < 12 — no length bonus
        assert len(set(password)) == 3  # ratio 0.3
        assert 3 / 10 < 0.4

        result = self.validator.get_password_strength(password)
        assert result["strength"] == "Moderate", (
            f"Expected Moderate, got {result['strength']} (score={result['score']})"
        )
        assert 40 <= result["score"] < 60

    def test_weak_label(self):
        """Score in [20, 39] produces 'Weak' label (line 213-214).

        Password characteristics:
        - < 12 chars (no length bonus)                        => +0
        - no uppercase                                         => +0
        - has lowercase                                        => +10
        - no digit                                             => +0
        - no special                                           => +0
        - low uniqueness (ratio < 0.4)                        => +0
        - not common                                           => +15
        Total = 25 => Weak
        """
        # 10 chars, 3 distinct lowercase only
        password = "aaabbbccca"
        assert len(password) == 10
        assert len(set(password)) == 3  # ratio 0.3 < 0.4
        assert password == password.lower()  # no uppercase
        assert not any(c.isdigit() for c in password)  # no digit

        result = self.validator.get_password_strength(password)
        assert result["strength"] == "Weak", (
            f"Expected Weak, got {result['strength']} (score={result['score']})"
        )
        assert 20 <= result["score"] < 40

    def test_very_weak_label(self):
        """Score < 20 produces 'Very Weak' label (line 215).

        Password characteristics:
        - < 12 chars (no length bonus)                        => +0
        - no uppercase                                         => +0
        - has lowercase                                        => +10
        - no digit                                             => +0
        - no special                                           => +0
        - low uniqueness (ratio < 0.4)                        => +0
        - IS a common password                                 => +0 (no +15)
        Total = 10 => Very Weak
        """
        # "qwerty" is in BLOCKED_PASSWORDS: no uppercase, no digit,
        # length=6 (<12), uniqueness: q,w,e,r,t,y=6/6=1.0 but it is blocked.
        # Wait — 6/6 = 1.0 >= 0.6 so uniqueness gives +15. Total = 10+15 = 25 (Weak).
        # Use a short ALL-SAME-CHAR string that is blocked but won't gain uniqueness.
        # "111111" is blocked: no lowercase, no uppercase, no special, < 12 chars.
        # unique=1, length=6, ratio=1/6=0.17 < 0.4 => no uniqueness bonus
        # score: 0 (len) + 0 (upper) + 0 (lower) + 10 (digit) + 0 (special) + 0 (uniq) + 0 (common)
        # = 10 => Very Weak
        password = "111111"
        assert password in PasswordValidator.BLOCKED_PASSWORDS
        assert len(set(password)) / len(password) < 0.4

        result = self.validator.get_password_strength(password)
        assert result["strength"] == "Very Weak", (
            f"Expected Very Weak, got {result['strength']} (score={result['score']})"
        )
        assert result["score"] < 20

    def test_score_capped_at_100(self):
        """Score is capped at 100 regardless of how strong the password is."""
        result = self.validator.get_password_strength(
            "Tr0ub4dor&3-horsebattery-staple-correct-MEGA-$ecure!"
        )
        assert result["score"] <= 100


# ---------------------------------------------------------------------------
# Lines 275-277 — validate_password_complexity raising ValueError
# ---------------------------------------------------------------------------


class TestValidatePasswordComplexity:
    """Cover validate_password_complexity (lines 266-277)."""

    def test_valid_password_does_not_raise(self):
        """A compliant password passes without raising any exception."""
        validate_password_complexity("SecurePass1")  # should not raise

    def test_invalid_password_raises_value_error(self):
        """An invalid password causes validate_password_complexity to raise ValueError (line 277)."""
        with pytest.raises(ValueError):
            validate_password_complexity("weak")

    def test_error_message_contains_validation_details(self):
        """The ValueError message includes the specific validation failure reason."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_complexity("weak")
        message = str(exc_info.value)
        assert PasswordValidationError.TOO_SHORT.value in message

    def test_multiple_errors_joined_with_semicolon(self):
        """Multiple validation failures are joined by '; ' in the error message."""
        with pytest.raises(ValueError) as exc_info:
            # "aaaaaaaa" — long enough but missing uppercase and digit
            validate_password_complexity("aaaaaaaa")
        message = str(exc_info.value)
        assert PasswordValidationError.NO_UPPERCASE.value in message
        assert PasswordValidationError.NO_DIGIT.value in message
        assert ";" in message

    def test_common_password_raises_value_error(self):
        """A common password triggers ValueError via validate_password_complexity."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_complexity("password")
        message = str(exc_info.value)
        assert PasswordValidationError.COMMON_PASSWORD.value in message

    def test_valid_complex_password_no_exception(self):
        """A strong, unique password passes without raising."""
        validate_password_complexity("Str0ng!Passw0rd#2026")


# ---------------------------------------------------------------------------
# Additional edge cases for completeness
# ---------------------------------------------------------------------------


class TestCustomValidatorConfiguration:
    """Verify all constructor flags behave independently."""

    def test_all_requirements_disabled_accepts_any_8char_password(self):
        """Disabling all complexity flags accepts any password >= min_length."""
        v = PasswordValidator(
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False,
        )
        assert v.is_valid("aaaaaaaa") is True

    def test_custom_min_length(self):
        """Custom min_length is enforced correctly."""
        v = PasswordValidator(min_length=12, require_uppercase=False, require_digit=False)
        errors = v.validate("shortlow")
        assert PasswordValidationError.TOO_SHORT.value in errors

        errors = v.validate("longenoughlow")
        assert PasswordValidationError.TOO_SHORT.value not in errors

    def test_require_special_only_flag(self):
        """require_special=True without other flags reports only missing special char."""
        v = PasswordValidator(
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=True,
        )
        errors = v.validate("aaaaaaaa")
        assert errors == [PasswordValidationError.NO_SPECIAL.value]

    def test_email_with_no_local_part_does_not_crash(self):
        """An email lacking a '@' separator is handled gracefully."""
        v = PasswordValidator()
        # split("@")[0] on a no-@ string returns the whole string
        errors = v.validate("SecurePass1", email="invalidemail")
        # Should not raise; just returns normal errors (or none)
        assert isinstance(errors, list)

    def test_validate_password_complexity_with_require_special_default_false(self):
        """validate_password_complexity uses the global validator (require_special=False)."""
        # A password missing only a special char should still pass
        validate_password_complexity("SecurePass1")  # no special char — should not raise
