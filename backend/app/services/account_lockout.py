"""Account lockout service for brute force protection.

Tracks failed login attempts and enforces temporary lockouts.
After 5 failed attempts within 15 minutes, account is locked for 15 minutes.
"""

from datetime import UTC, datetime, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.login_attempt import LoginAttempt

# Constants
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15
LOCKOUT_DURATION_MINUTES = 15


class AccountLockoutService:
    """Service for managing account lockout based on failed login attempts."""

    def __init__(self) -> None:
        self.max_attempts = MAX_FAILED_ATTEMPTS
        self.window_minutes = LOCKOUT_WINDOW_MINUTES
        self.lockout_minutes = LOCKOUT_DURATION_MINUTES

    async def record_login_attempt(
        self,
        session: AsyncSession,
        email: str,
        ip_address: str,
        success: bool,
    ) -> None:
        """Record a login attempt.

        Args:
            session: Database session
            email: Email address attempted
            ip_address: IP address of the attempt
            success: Whether the login was successful
        """
        attempt = LoginAttempt(
            email=email.lower(),
            ip_address=ip_address,
            success=success,
            attempted_at=datetime.now(UTC),
        )
        session.add(attempt)
        await session.commit()

        # Clean up old attempts (older than 24 hours) to keep table size manageable
        if success:
            await self._cleanup_old_attempts(session, email)

    async def is_account_locked(
        self,
        session: AsyncSession,
        email: str,
    ) -> tuple[bool, datetime | None]:
        """Check if account is locked due to failed login attempts.

        Args:
            session: Database session
            email: Email address to check

        Returns:
            Tuple of (is_locked, lockout_expires_at)
            - is_locked: True if account is currently locked
            - lockout_expires_at: When the lockout expires (None if not locked)
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=self.window_minutes)

        # Get failed attempts within the window
        result = await session.exec(
            select(LoginAttempt)
            .where(
                LoginAttempt.email == email.lower(),
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.attempted_at >= window_start,
            )
            .order_by(LoginAttempt.attempted_at.desc())  # type: ignore[attr-defined]
        )
        failed_attempts = list(result.all())

        if len(failed_attempts) < self.max_attempts:
            return False, None

        # Account is locked - calculate when it expires
        # Lock expires LOCKOUT_DURATION_MINUTES after the 5th failed attempt
        fifth_attempt = failed_attempts[self.max_attempts - 1]
        lockout_expires_at = fifth_attempt.attempted_at + timedelta(minutes=self.lockout_minutes)

        # Check if lockout has expired
        if now >= lockout_expires_at:
            return False, None

        return True, lockout_expires_at

    async def get_failed_attempts_count(
        self,
        session: AsyncSession,
        email: str,
    ) -> int:
        """Get count of failed login attempts in the current window.

        Args:
            session: Database session
            email: Email address to check

        Returns:
            Number of failed attempts in the lockout window
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=self.window_minutes)

        result = await session.exec(
            select(LoginAttempt).where(
                LoginAttempt.email == email.lower(),
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.attempted_at >= window_start,
            )
        )
        return len(list(result.all()))

    async def clear_failed_attempts(
        self,
        session: AsyncSession,
        email: str,
    ) -> None:
        """Clear all failed login attempts for an email.

        Called after successful login to reset the counter.

        Args:
            session: Database session
            email: Email address to clear attempts for
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=self.window_minutes)

        result = await session.exec(
            select(LoginAttempt).where(
                LoginAttempt.email == email.lower(),
                LoginAttempt.attempted_at >= window_start,
            )
        )
        attempts = list(result.all())
        for attempt in attempts:
            await session.delete(attempt)
        await session.commit()

    async def _cleanup_old_attempts(
        self,
        session: AsyncSession,
        email: str,
    ) -> None:
        """Clean up login attempts older than 24 hours.

        Args:
            session: Database session
            email: Email address to clean up attempts for
        """
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        result = await session.exec(
            select(LoginAttempt).where(
                LoginAttempt.email == email.lower(),
                LoginAttempt.attempted_at < cutoff,
            )
        )
        old_attempts = list(result.all())
        for attempt in old_attempts:
            await session.delete(attempt)
        await session.commit()
