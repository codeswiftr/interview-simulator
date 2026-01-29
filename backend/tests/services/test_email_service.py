"""Unit tests for EmailService."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.email_service import EmailService
from app.config import settings

@pytest.fixture
def service():
    return EmailService()

def test_load_html_template_fallback(service):
    """Test loading template when file doesn't exist."""
    with patch("app.services.email_service.Path.exists", return_value=False):
        html, text = service._load_html_template("nonexistent.html", reset_url="http://test.com")
        assert "Click the link below to reset your password" in html
        assert "http://test.com" in html
        assert html == text

@pytest.mark.asyncio
async def test_send_password_reset_debug(service):
    """Test sending password reset in debug mode."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = True
        result = await service.send_password_reset("test@example.com", "http://reset.com")
        assert result is True

@pytest.mark.asyncio
async def test_send_password_reset_resend_success(service):
    """Test sending password reset via Resend."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = False
        mock_settings.resend_api_key = "fake_key"
        mock_settings.resend_from_email = "hello@test.com"
        mock_settings.resend_from_name = "Test"
        
        service.resend_api_key = "fake_key"
        
        with patch("resend.Emails.send", return_value={"id": "email_123"}) as mock_send:
            result = await service.send_password_reset("test@example.com", "http://reset.com")
            assert result is True
            mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_send_password_reset_smtp_success(service):
    """Test sending password reset via SMTP."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = False
        mock_settings.resend_api_key = None
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "password"
        
        service.resend_api_key = None
        service.smtp_host = "smtp.test.com"
        service.smtp_user = "user"
        service.smtp_password = "password"
        
        # Mock aiosmtplib module
        import sys
        mock_aiosmtplib = MagicMock()
        mock_aiosmtplib.send = AsyncMock()
        sys.modules["aiosmtplib"] = mock_aiosmtplib
        
        result = await service.send_password_reset("test@example.com", "http://reset.com")
        assert result is True
        mock_aiosmtplib.send.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_verification_debug(service):
    """Test sending email verification in debug mode."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = True
        result = await service.send_email_verification("test@example.com", "http://verify.com")
        assert result is True

@pytest.mark.asyncio
async def test_send_email_verification_resend_success(service):
    """Test sending email verification via Resend."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = False
        mock_settings.resend_api_key = "fake_key"
        service.resend_api_key = "fake_key"
        
        with patch("resend.Emails.send", return_value={"id": "email_456"}):
            result = await service.send_email_verification("test@example.com", "http://verify.com")
            assert result is True

@pytest.mark.asyncio
async def test_send_email_verification_no_service(service):
    """Test failure when no service is configured."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.debug = False
        mock_settings.resend_api_key = None
        mock_settings.smtp_host = None
        service.resend_api_key = None
        service.smtp_host = None
        
        result = await service.send_email_verification("test@example.com", "http://verify.com")
        assert result is False
