"""Pure unit tests for EmailService.

Tests template loading, fallback generation, and send logic paths.
No database or external services required.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email_service import EmailService


@pytest.fixture
def mock_settings():
    with patch("app.services.email_service.settings") as s:
        s.smtp_host = ""
        s.smtp_port = 587
        s.smtp_user = ""
        s.smtp_password = ""
        s.smtp_from_email = "test@example.com"
        s.resend_api_key = ""
        s.debug = True
        yield s


@pytest.fixture
def service(mock_settings):
    return EmailService()


class TestEmailServiceInit:
    def test_reads_settings(self, service, mock_settings):
        assert service.smtp_host == ""
        assert service.smtp_port == 587
        assert service.from_email == "test@example.com"
        assert service.resend_api_key == ""


class TestCreateFallbackTemplate:
    def test_contains_reset_url(self, service):
        html, text = service._create_fallback_template(reset_url="https://example.com/reset")
        assert "https://example.com/reset" in text

    def test_no_reset_url(self, service):
        html, text = service._create_fallback_template()
        assert "CareerSwiftr" in text

    def test_returns_same_html_and_text(self, service):
        html, text = service._create_fallback_template(reset_url="url")
        assert html == text


class TestLoadHtmlTemplate:
    @patch("pathlib.Path.exists", return_value=False)
    def test_uses_fallback_when_template_missing(self, mock_exists, service):
        html, text = service._load_html_template("nonexistent.html", reset_url="url")
        assert "url" in text

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="<html>Hello {{name}}</html>")
    def test_renders_template_variables(self, mock_read, mock_exists, service):
        html, text = service._load_html_template("test.html", name="World")
        assert "Hello World" in html
        assert "Hello World" in text

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="<p>Plain</p>")
    def test_strips_html_for_plain_text(self, mock_read, mock_exists, service):
        html, text = service._load_html_template("test.html")
        assert "<p>" in html
        assert "<p>" not in text
        assert "Plain" in text


class TestSendPasswordReset:
    @pytest.mark.asyncio
    async def test_debug_mode_returns_true(self, service, mock_settings):
        mock_settings.debug = True
        result = await service.send_password_reset("user@test.com", "https://reset")
        assert result is True

    @pytest.mark.asyncio
    async def test_no_service_configured_returns_false(self, mock_settings):
        mock_settings.debug = False
        mock_settings.resend_api_key = ""
        mock_settings.smtp_host = ""
        mock_settings.smtp_user = ""
        mock_settings.smtp_password = ""
        svc = EmailService()
        svc.resend_api_key = ""
        svc.smtp_host = ""
        svc.smtp_user = ""
        svc.smtp_password = ""

        result = await svc.send_password_reset("user@test.com", "https://reset")
        assert result is False

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=False)
    async def test_resend_success(self, mock_exists, mock_settings):
        mock_settings.debug = False
        mock_settings.resend_api_key = "re_test_key"
        mock_settings.resend_from_email = "hello@codeswiftr.com"
        mock_settings.resend_from_name = "IS"
        svc = EmailService()
        svc.resend_api_key = "re_test_key"

        with patch.dict("sys.modules", {"resend": MagicMock()}):
            import sys

            mock_resend = sys.modules["resend"]
            mock_resend.Emails.send.return_value = {"id": "email_123"}

            result = await svc.send_password_reset("u@t.com", "https://r")
            assert result is True


class TestSendEmailVerification:
    @pytest.mark.asyncio
    async def test_debug_mode_returns_true(self, service, mock_settings):
        mock_settings.debug = True
        result = await service.send_email_verification("new@test.com", "https://verify")
        assert result is True

    @pytest.mark.asyncio
    async def test_no_service_configured_returns_false(self, mock_settings):
        mock_settings.debug = False
        svc = EmailService()
        svc.resend_api_key = ""
        svc.smtp_host = ""
        svc.smtp_user = ""
        svc.smtp_password = ""

        result = await svc.send_email_verification("new@test.com", "https://verify")
        assert result is False
