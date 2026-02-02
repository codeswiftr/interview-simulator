"""Tests for security headers middleware.

This test suite ensures the SecurityHeadersMiddleware properly applies
security headers in production mode and skips them in debug mode.

Coverage targets:
- Security headers applied in production mode (0% → 90%+)
- Headers skipped in debug mode
- CSP directives validation
- HSTS header verification
- X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- Permissions-Policy validation
"""

from unittest.mock import patch

import pytest

from tests.conftest import register_and_login, requires_db


@pytest.mark.asyncio
@requires_db
async def test_security_headers_applied_in_production_mode(client):
    """Test that security headers are applied when debug=False (production mode)."""
    # Mock settings to simulate production mode
    with patch("app.config.settings.debug", False):
        # Register and login to create a valid session
        token = await register_and_login(client, email="security_test_prod@example.com")

        # Make a request to any endpoint
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        # Verify the request succeeded
        assert resp.status_code == 200

        # Verify all security headers are present in production mode
        headers = resp.headers

        # Content-Security-Policy should be present
        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

        # HSTS should be present in production
        assert "Strict-Transport-Security" in headers
        assert headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


@pytest.mark.asyncio
@requires_db
async def test_security_headers_skipped_in_debug_mode(client):
    """Test that CSP and HSTS headers are skipped when debug=True (development mode)."""
    # Mock settings to simulate debug mode
    with patch("app.config.settings.debug", True):
        token = await register_and_login(client, email="security_test_debug@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        assert resp.status_code == 200
        headers = resp.headers

        # CSP and HSTS should NOT be present in debug mode
        assert "Content-Security-Policy" not in headers
        assert "Strict-Transport-Security" not in headers


@pytest.mark.asyncio
@requires_db
async def test_csp_directive_default_src_self(client):
    """Test that CSP includes 'default-src self' directive."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="csp_default@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp


@pytest.mark.asyncio
@requires_db
async def test_csp_directive_script_src_allows_unsafe_inline(client):
    """Test that CSP script-src allows 'unsafe-inline' for frontend frameworks."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="csp_script@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        csp = resp.headers.get("Content-Security-Policy", "")
        # Frontend frameworks need unsafe-inline and unsafe-eval
        assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp


@pytest.mark.asyncio
@requires_db
async def test_csp_directive_connect_src_includes_ai_apis(client):
    """Test that CSP connect-src includes necessary AI API endpoints."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="csp_connect@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        csp = resp.headers.get("Content-Security-Policy", "")
        # Should allow connections to AI service providers
        assert "connect-src" in csp
        assert "https://api.openai.com" in csp
        assert "https://openrouter.ai" in csp
        assert "https://api.anthropic.com" in csp
        assert "https://api.resend.com" in csp
        assert "https://api.stripe.com" in csp


@pytest.mark.asyncio
@requires_db
async def test_csp_directive_frame_ancestors_none(client):
    """Test that CSP frame-ancestors is set to 'none' to prevent clickjacking."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="csp_frame@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        csp = resp.headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in csp


@pytest.mark.asyncio
@requires_db
async def test_hsts_header_includes_subdomains(client):
    """Test that HSTS header includes includeSubDomains directive."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="hsts_test@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        hsts = resp.headers.get("Strict-Transport-Security", "")
        assert "max-age=31536000" in hsts  # 1 year
        assert "includeSubDomains" in hsts


@pytest.mark.asyncio
@requires_db
async def test_x_frame_options_always_set(client):
    """Test that X-Frame-Options is set to DENY in both debug and production."""
    # Test in debug mode
    with patch("app.config.settings.debug", True):
        token = await register_and_login(client, email="xfo_debug@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        assert resp.headers.get("X-Frame-Options") == "DENY"

    # Test in production mode
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="xfo_prod@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        assert resp.headers.get("X-Frame-Options") == "DENY"


@pytest.mark.asyncio
@requires_db
async def test_x_content_type_options_nosniff(client):
    """Test that X-Content-Type-Options is set to 'nosniff'."""
    token = await register_and_login(client, email="xcto_test@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.asyncio
@requires_db
async def test_referrer_policy_strict_origin(client):
    """Test that Referrer-Policy is set to 'strict-origin-when-cross-origin'."""
    token = await register_and_login(client, email="referrer_test@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
@requires_db
async def test_permissions_policy_geolocation_disabled(client):
    """Test that Permissions-Policy blocks geolocation."""
    token = await register_and_login(client, email="permissions_geo@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    permissions = resp.headers.get("Permissions-Policy", "")
    assert "geolocation=()" in permissions


@pytest.mark.asyncio
@requires_db
async def test_permissions_policy_microphone_allowed(client):
    """Test that Permissions-Policy allows microphone for interview recording."""
    token = await register_and_login(client, email="permissions_mic@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    permissions = resp.headers.get("Permissions-Policy", "")
    # Microphone should be allowed for same origin (interview recording)
    assert "microphone=(self)" in permissions


@pytest.mark.asyncio
@requires_db
async def test_permissions_policy_camera_allowed(client):
    """Test that Permissions-Policy allows camera for interview recording."""
    token = await register_and_login(client, email="permissions_cam@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    permissions = resp.headers.get("Permissions-Policy", "")
    # Camera should be allowed for same origin (interview recording)
    assert "camera=(self)" in permissions


@pytest.mark.asyncio
@requires_db
async def test_permissions_policy_payment_disabled(client):
    """Test that Permissions-Policy blocks payment (using Stripe hosted pages)."""
    token = await register_and_login(client, email="permissions_pay@example.com")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": token},
    )

    permissions = resp.headers.get("Permissions-Policy", "")
    assert "payment=()" in permissions


@pytest.mark.asyncio
@requires_db
async def test_security_headers_on_public_endpoint(client):
    """Test that security headers are applied to public endpoints (health check)."""
    # Health check endpoint should have security headers
    resp = await client.get("/api/v1/health")

    # Even public endpoints should have basic security headers
    # (though CSP/HSTS only in production)
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
@requires_db
async def test_security_headers_on_error_response(client):
    """Test that security headers are applied even on error responses."""
    # Try to access a protected endpoint without authentication (should fail)
    resp = await client.get("/api/v1/users/me")

    # Should get 401 Unauthorized
    assert resp.status_code == 401

    # But security headers should still be present
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
@requires_db
async def test_security_headers_on_post_request(client):
    """Test that security headers are applied to POST requests."""
    with patch("app.config.settings.debug", False):
        # Try to register a new user (POST request)
        resp = await client.post(
            "/api/v1/users/register",
            json={
                "email": "post_test@example.com",
                "password": "SecurePassword123!"
            }
        )

        # Should succeed
        assert resp.status_code in [200, 201]

        # Security headers should be present
        assert "Content-Security-Policy" in resp.headers
        assert resp.headers.get("X-Frame-Options") == "DENY"


@pytest.mark.asyncio
@requires_db
async def test_all_security_headers_present_production(client):
    """Integration test: verify all expected security headers in production mode."""
    with patch("app.config.settings.debug", False):
        token = await register_and_login(client, email="all_headers@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        headers = resp.headers

        # All security headers should be present
        expected_headers = [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        ]

        for header in expected_headers:
            assert header in headers, f"Missing security header: {header}"

        # Verify key values
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "max-age=31536000" in headers["Strict-Transport-Security"]


@pytest.mark.asyncio
@requires_db
async def test_minimal_headers_in_debug_mode(client):
    """Integration test: verify minimal headers in debug mode (development)."""
    with patch("app.config.settings.debug", True):
        token = await register_and_login(client, email="debug_headers@example.com")

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )

        headers = resp.headers

        # CSP and HSTS should NOT be present in debug mode
        assert "Content-Security-Policy" not in headers
        assert "Strict-Transport-Security" not in headers

        # But these should still be present (always set)
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in headers
