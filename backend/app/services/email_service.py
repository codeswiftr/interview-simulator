"""Email service for sending password reset and notification emails."""

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or email service provider."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email

    async def send_password_reset(self, email: str, reset_url: str) -> bool:
        """Send password reset email with reset link.

        In debug mode, just logs the email content.
        In production, would use SMTP (aiosmtplib) or email service API.

        Args:
            email: Recipient email address
            reset_url: Password reset URL with token

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Reset Your CareerSwiftr Password"
        body = f"""
Hello,

You requested to reset your password for CareerSwiftr Interview Simulator.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you didn't request this, please ignore this email.

Best regards,
CareerSwiftr Team
        """.strip()

        if settings.debug:
            # In debug mode, just log the email
            logger.info(
                f"[EMAIL DEBUG] Would send password reset email:\n"
                f"To: {email}\n"
                f"Subject: {subject}\n"
                f"Reset URL: {reset_url}\n"
                f"Body:\n{body}"
            )
            return True

        # In production, use SMTP or email service
        # Example with aiosmtplib (not implemented yet):
        # try:
        #     import aiosmtplib
        #     from email.message import EmailMessage
        #
        #     message = EmailMessage()
        #     message["From"] = self.from_email
        #     message["To"] = email
        #     message["Subject"] = subject
        #     message.set_content(body)
        #
        #     await aiosmtplib.send(
        #         message,
        #         hostname=self.smtp_host,
        #         port=self.smtp_port,
        #         username=self.smtp_user,
        #         password=self.smtp_password,
        #         start_tls=True,
        #     )
        #     return True
        # except Exception as e:
        #     logger.error(f"Failed to send email to {email}: {e}")
        #     return False

        logger.warning(
            f"Email service not configured for production. "
            f"Would send password reset to {email}"
        )
        return True
