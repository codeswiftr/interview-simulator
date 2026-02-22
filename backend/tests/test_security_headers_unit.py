"""Pure unit tests for SecurityHeadersMiddleware.

Tests security header injection in debug and production modes.
No database required.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def middleware():
    app = MagicMock()
    return SecurityHeadersMiddleware(app)


def _make_response():
    response = MagicMock()
    response.headers = {}
    return response


class TestSecurityHeadersProduction:
    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_csp_header_set(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert "Content-Security-Policy" in result.headers

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_hsts_header_set(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert "Strict-Transport-Security" in result.headers
        assert "31536000" in result.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_x_frame_options(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert result.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_x_content_type_options(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert result.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_referrer_policy(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_permissions_policy(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        policy = result.headers["Permissions-Policy"]
        assert "microphone=(self)" in policy
        assert "camera=(self)" in policy
        assert "geolocation=()" in policy

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_csp_includes_api_domains(self, mock_settings, middleware):
        mock_settings.debug = False
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        csp = result.headers["Content-Security-Policy"]
        assert "api.openai.com" in csp
        assert "api.anthropic.com" in csp
        assert "api.stripe.com" in csp


class TestSecurityHeadersDebug:
    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_no_csp_in_debug(self, mock_settings, middleware):
        mock_settings.debug = True
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert "Content-Security-Policy" not in result.headers

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_no_hsts_in_debug(self, mock_settings, middleware):
        mock_settings.debug = True
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert "Strict-Transport-Security" not in result.headers

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_still_has_x_frame_options_in_debug(self, mock_settings, middleware):
        mock_settings.debug = True
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert result.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    @patch("app.middleware.security_headers.settings")
    async def test_still_has_nosniff_in_debug(self, mock_settings, middleware):
        mock_settings.debug = True
        response = _make_response()
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(MagicMock(), call_next)
        assert result.headers["X-Content-Type-Options"] == "nosniff"
