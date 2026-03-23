"""Quick validation of security headers middleware without full test setup."""

import asyncio
from unittest.mock import patch

from app.middleware.security_headers import SecurityHeadersMiddleware
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def homepage(request):
    """Test endpoint."""
    return JSONResponse({"message": "test"})


async def test_security_headers_production():
    """Test security headers in production mode."""
    # Create test app
    routes = [Route("/", homepage)]
    app = Starlette(routes=routes)
    app.add_middleware(SecurityHeadersMiddleware)

    # Mock settings to simulate production
    with patch("app.middleware.security_headers.settings") as mock_settings:
        mock_settings.debug = False

        # Make request
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/")

            # Check headers
            assert resp.status_code == 200
            assert "Content-Security-Policy" in resp.headers
            assert "Strict-Transport-Security" in resp.headers
            assert resp.headers["X-Frame-Options"] == "DENY"
            assert resp.headers["X-Content-Type-Options"] == "nosniff"

            print("✓ Production mode test passed")


async def test_security_headers_debug():
    """Test security headers in debug mode."""
    # Create test app
    routes = [Route("/", homepage)]
    app = Starlette(routes=routes)
    app.add_middleware(SecurityHeadersMiddleware)

    # Mock settings to simulate debug mode
    with patch("app.middleware.security_headers.settings") as mock_settings:
        mock_settings.debug = True

        # Make request
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/")

            # Check headers
            assert resp.status_code == 200
            assert "Content-Security-Policy" not in resp.headers
            assert "Strict-Transport-Security" not in resp.headers
            assert resp.headers["X-Frame-Options"] == "DENY"  # Always set
            assert resp.headers["X-Content-Type-Options"] == "nosniff"  # Always set

            print("✓ Debug mode test passed")


async def main():
    """Run all quick tests."""
    print("Running security headers quick tests...")
    await test_security_headers_production()
    await test_security_headers_debug()
    print("\n✓ All quick tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
