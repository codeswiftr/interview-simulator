"""Email service for sending password reset and notification emails."""

import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend (preferred) or SMTP fallback."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.resend_api_key = settings.resend_api_key

    def _load_html_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """Load and render HTML email template.

        Args:
            template_name: Name of template file (e.g., 'password_reset.html')
            **kwargs: Variables to render in template

        Returns:
            Tuple of (html_content, plain_text_content)
        """
        template_path = Path(__file__).parent.parent / "templates" / "emails" / template_name

        if template_path.exists():
            html_content = template_path.read_text()
            # Simple template rendering (replace placeholders)
            for key, value in kwargs.items():
                html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

            # Extract plain text from HTML (simple version)
            # Remove HTML tags for plain text fallback
            import re

            plain_text = re.sub(r"<[^>]+>", "", html_content)
            plain_text = re.sub(r"\s+", " ", plain_text).strip()

            return html_content, plain_text
        else:
            # Fallback to simple text template
            logger.warning(f"Email template not found: {template_path}, using fallback")
            return self._create_fallback_template(**kwargs)

    def _create_fallback_template(self, **kwargs) -> tuple[str, str]:
        """Create fallback plain text template."""
        reset_url = kwargs.get("reset_url", "")
        plain_text = f"""
Hello,

You requested to reset your password for CareerSwiftr Interview Simulator.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you didn't request this, please ignore this email.

Best regards,
CareerSwiftr Team
        """.strip()
        return plain_text, plain_text

    async def send_password_reset(self, email: str, reset_url: str) -> bool:
        """Send password reset email with reset link.

        Uses Resend API if configured, otherwise falls back to debug logging.

        Args:
            email: Recipient email address
            reset_url: Password reset URL with token

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Reset Your Interview Simulator Password"

        # Load HTML template
        html_content, plain_text = self._load_html_template(
            "password_reset.html", reset_url=reset_url
        )

        if settings.debug:
            # In debug mode, just log the email
            logger.info(
                f"[EMAIL DEBUG] Would send password reset email:\n"
                f"To: {email}\n"
                f"Subject: {subject}\n"
                f"Reset URL: {reset_url}\n"
                f"Body:\n{plain_text}"
            )
            return True

        # Try Resend first (preferred)
        if self.resend_api_key:
            try:
                import resend

                resend.api_key = self.resend_api_key

                # Use codeswiftr.com domain (verified in Resend)
                # Always use validated defaults - never send empty from field
                from_email = (
                    settings.resend_from_email
                    if settings.resend_from_email
                    else "hello@codeswiftr.com"
                )
                from_name = (
                    settings.resend_from_name
                    if settings.resend_from_name
                    else "Interview Simulator"
                )
                from_header = f"{from_name} <{from_email}>"

                # Resend SDK v2+ uses dict instead of Params class
                email_response = resend.Emails.send(
                    {
                        "from": from_header,
                        "to": [email],
                        "subject": subject,
                        "html": html_content,
                        "text": plain_text,
                    }
                )

                email_id = (
                    email_response.get("id")
                    if isinstance(email_response, dict)
                    else getattr(email_response, "id", None)
                )
                if email_id:
                    logger.info(
                        f"Password reset email sent via Resend to {email} (email_id: {email_id})"
                    )
                else:
                    logger.info(f"Password reset email sent via Resend to {email}")
                return True

            except ImportError:
                logger.warning("Resend package not installed. Install with: pip install resend")
            except Exception as e:
                logger.error(f"Failed to send email via Resend to {email}: {e}", exc_info=True)
                # Fall through to SMTP fallback

        # Fallback to SMTP if configured
        if self.smtp_host and self.smtp_user and self.smtp_password:
            try:
                from email.message import EmailMessage

                import aiosmtplib

                message = EmailMessage()
                message["From"] = self.from_email
                message["To"] = email
                message["Subject"] = subject
                message.set_content(plain_text)
                message.add_alternative(html_content, subtype="html")

                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    start_tls=True,
                )
                logger.info(
                    f"Password reset email sent via SMTP to {email} (host: {self.smtp_host})"
                )
                return True
            except ImportError:
                logger.warning("aiosmtplib not installed. Install with: pip install aiosmtplib")
            except Exception as e:
                logger.error(f"Failed to send email via SMTP to {email}: {e}", exc_info=True)

        # No email service configured
        logger.warning(
            f"Email service not configured for production. "
            f"Set RESEND_API_KEY or SMTP settings to enable email sending. "
            f"Would send password reset to {email} (reset_url: {reset_url})"
        )
        return False

    async def send_email_verification(self, email: str, verification_url: str) -> bool:
        """Send email verification email for email changes.

        Uses Resend API if configured, otherwise falls back to debug logging.

        Args:
            email: Recipient email address (new email)
            verification_url: Email verification URL with token

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Verify Your New Email Address - CareerSwiftr"

        # Simple template for email verification
        html_content = f"""
        <html>
        <body>
            <h2>Verify Your New Email Address</h2>
            <p>You requested to change your email address to: <strong>{email}</strong></p>
            <p>Click the link below to verify this email address (valid for 24 hours):</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>If you didn't request this change, please ignore this email or contact support.</p>
            <p>Best regards,<br>CareerSwiftr Team</p>
        </body>
        </html>
        """

        plain_text = f"""
        Verify Your New Email Address

        You requested to change your email address to: {email}

        Click the link below to verify this email address (valid for 24 hours):
        {verification_url}

        If you didn't request this change, please ignore this email or contact support.

        Best regards,
        CareerSwiftr Team
        """.strip()

        if settings.debug:
            logger.info(
                f"[EMAIL DEBUG] Would send email verification:\n"
                f"To: {email}\n"
                f"Subject: {subject}\n"
                f"Verification URL: {verification_url}\n"
                f"Body:\n{plain_text}"
            )
            return True

        # Try Resend first
        if self.resend_api_key:
            try:
                import resend

                resend.api_key = self.resend_api_key

                # Use codeswiftr.com domain (verified in Resend)
                # Always use validated defaults - never send empty from field
                from_email = (
                    settings.resend_from_email
                    if settings.resend_from_email
                    else "hello@codeswiftr.com"
                )
                from_name = (
                    settings.resend_from_name
                    if settings.resend_from_name
                    else "Interview Simulator"
                )
                from_header = f"{from_name} <{from_email}>"

                # Resend SDK v2+ uses dict instead of Params class
                email_response = resend.Emails.send(
                    {
                        "from": from_header,
                        "to": [email],
                        "subject": subject,
                        "html": html_content,
                        "text": plain_text,
                    }
                )

                email_id = (
                    email_response.get("id")
                    if isinstance(email_response, dict)
                    else getattr(email_response, "id", None)
                )
                if email_id:
                    logger.info(
                        f"Email verification sent via Resend to {email} (email_id: {email_id})"
                    )
                else:
                    logger.info(f"Email verification sent via Resend to {email}")
                return True

            except ImportError:
                logger.warning("Resend package not installed. Install with: pip install resend")
            except Exception as e:
                logger.error(f"Failed to send email via Resend to {email}: {e}", exc_info=True)

        # Fallback to SMTP
        if self.smtp_host and self.smtp_user and self.smtp_password:
            try:
                from email.message import EmailMessage

                import aiosmtplib

                message = EmailMessage()
                message["From"] = self.from_email
                message["To"] = email
                message["Subject"] = subject
                message.set_content(plain_text)
                message.add_alternative(html_content, subtype="html")

                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    start_tls=True,
                )
                logger.info(f"Email verification sent via SMTP to {email}")
                return True
            except ImportError:
                logger.warning("aiosmtplib not installed. Install with: pip install aiosmtplib")
            except Exception as e:
                logger.error(f"Failed to send email via SMTP to {email}: {e}", exc_info=True)

        logger.warning(f"Email service not configured. Would send verification email to {email}")
        return False

    async def send_team_invitation(
        self,
        to_email: str,
        org_name: str,
        inviter_name: str,
        token: str,
    ) -> None:
        """Send a team invitation email with an accept link.

        Args:
            to_email: Recipient email address.
            org_name: Name of the organization the user is being invited to.
            inviter_name: Display name (or email) of the person sending the invite.
            token: Invitation token embedded in the accept link.

        Raises:
            Exception: Re-raises on delivery failure so callers can handle best-effort.
        """
        from app.config import settings

        join_url = f"{settings.frontend_url}/join/{token}"
        subject = f"You're invited to join {org_name} on Interview Simulator"

        html_content = f"""
        <html>
        <body>
            <h2>You've been invited to join a team!</h2>
            <p>Hi there!</p>
            <p><strong>{inviter_name}</strong> has invited you to join
            <strong>{org_name}</strong> on Interview Simulator.</p>
            <p>
                <a href="{join_url}" style="
                    display:inline-block;
                    padding:12px 24px;
                    background:#4f46e5;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:6px;
                    font-weight:600;
                ">Accept Invitation</a>
            </p>
            <p>Or copy this link into your browser:<br>
            <a href="{join_url}">{join_url}</a></p>
            <p>This invitation expires in 7 days.</p>
            <p>If you did not expect this invitation, you can safely ignore this email.</p>
            <p>Best regards,<br>CareerSwiftr Team</p>
        </body>
        </html>
        """

        plain_text = (
            f"You've been invited to join {org_name} on Interview Simulator.\n\n"
            f"{inviter_name} sent you this invitation.\n\n"
            f"Accept here: {join_url}\n\n"
            "This invitation expires in 7 days.\n"
            "If you did not expect this, you can ignore this email."
        )

        if settings.debug:
            logger.info(
                "[EMAIL DEBUG] Would send team invitation:\n"
                "To: %s\nSubject: %s\nJoin URL: %s",
                to_email,
                subject,
                join_url,
            )
            return

        if self.resend_api_key:
            import resend

            resend.api_key = self.resend_api_key
            from_email = settings.resend_from_email or "hello@codeswiftr.com"
            from_name = settings.resend_from_name or "Interview Simulator"

            resend.Emails.send(
                {
                    "from": f"{from_name} <{from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                    "text": plain_text,
                }
            )
            logger.info("Team invitation sent via Resend to %s for org '%s'", to_email, org_name)
            return

        if self.smtp_host and self.smtp_user and self.smtp_password:
            from email.message import EmailMessage

            import aiosmtplib

            message = EmailMessage()
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(plain_text)
            message.add_alternative(html_content, subtype="html")

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            logger.info("Team invitation sent via SMTP to %s", to_email)
            return

        logger.warning(
            "Email service not configured. Would send team invitation to %s (join_url: %s)",
            to_email,
            join_url,
        )
