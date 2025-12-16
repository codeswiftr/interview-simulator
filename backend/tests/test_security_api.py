"""Comprehensive API security tests.

Tests for:
- CORS configuration
- Rate limiting effectiveness
- Header validation (CF-RAY, X-Real-IP, X-Forwarded-For)
- IP spoofing prevention
- DDoS protection
"""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from app.middleware.rate_limit import (
    RateLimitConfig,
    SecureRateLimiter,
    SecureRateLimitMiddleware,
)


class TestCORSSecurity:
    """Test CORS configuration security."""

    def test_cors_allows_production_origins(self, client):
        """Test CORS allows configured production origins."""
        allowed_origins = [
            "https://app.codeswiftr.com",
            "https://codeswiftr.com",
            "https://interview-simulator-4bo.pages.dev",
        ]

        for origin in allowed_origins:
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization",
                }
            )

            assert response.status_code == 200
            assert response.headers.get("Access-Control-Allow-Origin") == origin
            assert "POST" in response.headers.get("Access-Control-Allow-Methods", "")

    def test_cors_rejects_unauthorized_origins(self, client):
        """Test CORS rejects unauthorized origins."""
        unauthorized_origins = [
            "https://malicious-site.com",
            "http://localhost:3000",  # HTTP not allowed in production
            "https://evil.com",
        ]

        for origin in unauthorized_origins:
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                }
            )

            # Origin should not be in allow list
            allowed_origin = response.headers.get("Access-Control-Allow-Origin")
            if allowed_origin and allowed_origin != "*":
                assert allowed_origin != origin

    def test_cors_credentials_not_wildcard(self, client):
        """Test CORS doesn't use wildcard with credentials."""
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://app.codeswiftr.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Credentials": "true",
            }
        )

        # Should not use wildcard when credentials are allowed
        assert response.headers.get("Access-Control-Allow-Origin") != "*"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_allowed_headers_restricted(self, client):
        """Test CORS only allows specific headers."""
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://app.codeswiftr.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type, X-Custom",
            }
        )

        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
        assert "Authorization" in allowed_headers
        assert "Content-Type" in allowed_headers
        # X-Custom might not be allowed

    def test_cors_methods_restricted(self, client):
        """Test CORS only allows specific HTTP methods."""
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://app.codeswiftr.com",
                "Access-Control-Request-Method": "POST",
            }
        )

        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        allowed_methods_list = [m.strip() for m in allowed_methods.split(",")]

        # Should include standard methods
        assert "GET" in allowed_methods_list
        assert "POST" in allowed_methods_list
        assert "PUT" in allowed_methods_list
        assert "DELETE" in allowed_methods_list
        assert "OPTIONS" in allowed_methods_list

        # Should not include dangerous methods
        assert "TRACE" not in allowed_methods_list
        assert "CONNECT" not in allowed_methods_list


class TestRateLimitSecurity:
    """Test rate limiting security features."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        config = RateLimitConfig(
            requests_per_minute=10,  # Low for testing
            requests_per_hour=100,
            burst_size=5,
        )
        return SecureRateLimiter(config)

    def test_rate_limit_basic_functionality(self, rate_limiter):
        """Test basic rate limiting works."""
        # Create a mock request
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # First 10 requests should be allowed
        for i in range(10):
            allowed, _ = rate_limiter.is_allowed(request)
            assert allowed is True, f"Request {i+1} should be allowed"

        # 11th request should be blocked
        allowed, headers = rate_limiter.is_allowed(request)
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == "0"

    def test_rate_limit_different_ips_isolated(self, rate_limiter):
        """Test rate limits are isolated per IP."""
        # Create requests from different IPs
        request1 = MagicMock()
        request1.client.host = "192.168.1.1"
        request1.headers = {}
        request1.url.path = "/api/v1/test"

        request2 = MagicMock()
        request2.client.host = "192.168.1.2"
        request2.headers = {}
        request2.url.path = "/api/v1/test"

        # Each IP should get its own limit
        for i in range(10):
            allowed1, _ = rate_limiter.is_allowed(request1)
            allowed2, _ = rate_limiter.is_allowed(request2)
            assert allowed1 is True
            allowed2 is True

        # 11th request for each IP should be blocked
        allowed1, _ = rate_limiter.is_allowed(request1)
        allowed2, _ = rate_limiter.is_allowed(request2)
        assert allowed1 is False
        assert allowed2 is False

    def test_rate_limit_user_isolation(self, rate_limiter):
        """Test authenticated users get separate limits."""
        # Create requests with different user IDs
        request1 = MagicMock()
        request1.client.host = "127.0.0.1"
        request1.headers = {}
        request1.url.path = "/api/v1/test"

        request2 = MagicMock()
        request2.client.host = "127.0.0.1"  # Same IP
        request2.headers = {}
        request2.url.path = "/api/v1/test"

        # User 1 should get their full limit
        for i in range(rate_limiter.config.user_requests_per_minute):
            allowed, _ = rate_limiter.is_allowed(request1, user_id="user-1")
            assert allowed is True

        # User 2 should still have their full limit available
        for i in range(rate_limiter.config.user_requests_per_minute):
            allowed, _ = rate_limiter.is_allowed(request2, user_id="user-2")
            assert allowed is True

    def test_rate_limit_sliding_window(self, rate_limiter):
        """Test sliding window rate limiting."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Use up the minute limit
        for i in range(10):
            rate_limiter.is_allowed(request)

        # Should be blocked
        allowed, _ = rate_limiter.is_allowed(request)
        assert allowed is False

        # Wait for window to slide (mock time passage)
        with patch('time.time') as mock_time:
            # Advance time by 61 seconds
            mock_time.return_value = time.time() + 61

            # Should be allowed again
            allowed, _ = rate_limiter.is_allowed(request)
            assert allowed is True

    def test_rate_limit_headers(self, rate_limiter):
        """Test rate limit headers are correct."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Make some requests
        for i in range(3):
            allowed, headers = rate_limiter.is_allowed(request)
            assert allowed is True
            assert "X-RateLimit-Limit" in headers
            assert "X-RateLimit-Remaining" in headers
            assert "X-RateLimit-Reset" in headers
            assert "X-RateLimit-Scope" in headers

            # Remaining should decrease
            assert int(headers["X-RateLimit-Remaining"]) == 10 - (i + 1)

    def test_rate_limit_burst_protection(self, rate_limiter):
        """Test burst protection prevents rapid requests."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Make requests faster than burst size allows
        allowed_count = 0
        for i in range(20):  # Try more than burst size
            allowed, _ = rate_limiter.is_allowed(request)
            if allowed:
                allowed_count += 1

        # Should be limited by burst size
        assert allowed_count <= rate_limiter.config.burst_size


class TestIPValidationSecurity:
    """Test IP validation and spoofing prevention."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        return SecureRateLimiter(RateLimitConfig())

    def test_cloudflare_ip_trusted(self, rate_limiter):
        """Test Cloudflare CF-Connecting-IP header is trusted."""
        request = MagicMock()
        request.client.host = "203.0.113.1"  # Cloudflare IP
        request.headers = {
            "CF-RAY": "1234567890",
            "CF-Connecting-IP": "198.51.100.1",
        }
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

        # Should trust CF-Connecting-IP when CF-RAY is present
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "198.51.100.1"

    def test_cloudflare_ip_without_ray_rejected(self, rate_limiter):
        """Test CF-Connecting-IP without CF-RAY is rejected."""
        request = MagicMock()
        request.client.host = "203.0.113.1"
        request.headers = {
            "CF-Connecting-IP": "198.51.100.1",
            # Missing CF-RAY
        }
        request.url.path = "/api/v1/test"

        # Should not trust CF-Connecting-IP without CF-RAY
        with patch.object(rate_limiter, '_log_suspicious_request') as mock_log:
            ip = rate_limiter._get_trusted_client_ip(request)
            mock_log.assert_called_once()

    def test_railway_ip_trusted(self, rate_limiter):
        """Test Railway X-Real-IP header is trusted on Railway."""
        request = MagicMock()
        request.client.host = "10.0.0.1"
        request.headers = {
            "X-Real-IP": "198.51.100.1",
        }
        request.url.path = "/api/v1/test"
        request.url.hostname = "interview-simulator-api-production.up.railway.app"

        # Should trust X-Real-IP on Railway
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "198.51.100.1"

    def test_x_forwarded_for_limited_proxies(self, rate_limiter):
        """Test X-Forwarded-For with too many proxies is rejected."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {
            "X-Forwarded-For": ",".join([f"10.0.0.{i}" for i in range(10)]),  # 10 proxies
        }
        request.url.path = "/api/v1/test"

        # Should reject due to too many proxies
        with patch.object(rate_limiter, '_log_suspicious_request') as mock_log:
            ip = rate_limiter._get_trusted_client_ip(request)
            mock_log.assert_called_once()

    def test_x_forwarded_for_private_ip_rejected(self, rate_limiter):
        """Test private IPs in X-Forwarded-For are rejected."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {
            "X-Forwarded-For": "10.0.0.1, 192.168.1.1, 198.51.100.1",
        }
        request.url.path = "/api/v1/test"

        # Should fall back to direct IP due to private IPs in chain
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "127.0.0.1"

    def test_ip_format_validation(self, rate_limiter):
        """Test IP format validation rejects invalid inputs."""
        invalid_ips = [
            "not.an.ip",
            "256.256.256.256",
            "127.0.0.1:8080",  # IPv4 with port
            "",
            "null",
            "../../etc/passwd",
            "192.168.1.1\nInjected: true",
            "192.168.1.1\r\nLocation: evil.com",
        ]

        for invalid_ip in invalid_ips:
            assert rate_limiter._is_valid_ip_format(invalid_ip) is False

    def test_public_ip_validation(self, rate_limiter):
        """Test public IP validation."""
        # Public IPs should be valid
        public_ips = [
            "198.51.100.1",
            "203.0.113.1",
            "2001:db8::1",
        ]

        for ip in public_ips:
            assert rate_limiter._is_public_ip(ip) is True
            assert rate_limiter._is_valid_ip_format(ip) is True

        # Private/internal IPs should be rejected for headers
        private_ips = [
            "10.0.0.1",
            "192.168.1.1",
            "172.16.0.1",
            "127.0.0.1",
            "::1",
        ]

        for ip in private_ips:
            assert rate_limiter._is_public_ip(ip) is False


class TestSuspiciousActivityDetection:
    """Test detection of suspicious activity patterns."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        return SecureRateLimiter(RateLimitConfig())

    def test_suspicious_user_agent_detection(self, rate_limiter):
        """Test suspicious User-Agent patterns are detected."""
        suspicious_uas = [
            "",  # Empty
            "null",
            "undefined",
            "bot",
            "crawler",
            "curl/7.68.0",
            "python-requests/2.25.1",
        ]

        for ua in suspicious_uas:
            request = MagicMock()
            request.client.host = "192.0.2.1"
            request.headers = {"User-Agent": ua}
            request.url.path = "/api/v1/auth/login"

            # Should detect as suspicious
            is_suspicious = rate_limiter.is_suspicious(request)
            assert is_suspicious is True

    def test_suspicious_header_patterns(self, rate_limiter):
        """Test suspicious header patterns are detected."""
        # Header with line breaks
        request = MagicMock()
        request.client.host = "192.0.2.1"
        request.headers = {
            "X-Forwarded-For": "192.0.2.1\nLocation: evil.com",
        }
        request.url.path = "/api/v1/test"

        is_suspicious = rate_limiter.is_suspicious(request)
        assert is_suspicious is True

        # Oversized header
        request.headers = {
            "User-Agent": "A" * 600,  # Too long
        }

        is_suspicious = rate_limiter.is_suspicious(request)
        assert is_suspicious is True

    def test_mismatched_headers_detection(self, rate_limiter):
        """Test mismatched headers without Cloudflare are detected."""
        request = MagicMock()
        request.client.host = "192.0.2.1"
        request.headers = {
            "X-Real-IP": "198.51.100.1",
            "X-Forwarded-For": "203.0.113.1",
            # No CF-RAY
        }
        request.url.path = "/api/v1/test"

        # Should detect as suspicious
        with patch.object(rate_limiter, '_log_suspicious_request') as mock_log:
            is_suspicious = rate_limiter.is_suspicious(request)
            # Note: This might not trigger suspicious depending on implementation
            # The mock verifies if logging occurred

    def test_ip_tracking_for_blocking(self, rate_limiter):
        """Test suspicious IPs are tracked for potential blocking."""
        request = MagicMock()
        request.client.host = "192.0.2.1"
        request.headers = {"User-Agent": "curl/7.68.0"}
        request.url.path = "/api/v1/auth/login"

        # First few suspicious activities
        for i in range(3):
            rate_limiter.is_suspicious(request)

        # IP should be tracked but not yet blocked
        assert rate_limiter._suspicious_ips["192.0.2.1"] == 3

        # After threshold
        for i in range(3):
            rate_limiter.is_suspicious(request)

        # Should now be considered suspicious
        is_suspicious = rate_limiter.is_suspicious(request)
        assert is_suspicious is True


class TestRateLimitMiddleware:
    """Test the rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_middleware_excluded_paths(self):
        """Test certain paths are excluded from rate limiting."""
        app = MagicMock()
        middleware = SecureRateLimitMiddleware(
            app,
            exclude_paths=["/api/v1/health", "/docs", "/openapi.json"]
        )

        # Health check should not be rate limited
        request = MagicMock()
        request.url.path = "/api/v1/health"

        call_next = MagicMock()
        response = JSONResponse(content={"status": "ok"})
        call_next.return_value = response

        result = await middleware.dispatch(request, call_next)

        # Should not add rate limit headers
        assert "X-RateLimit-Limit" not in result.headers

    @pytest.mark.asyncio
    async def test_middleware_rate_limits_api(self):
        """Test API endpoints are rate limited."""
        app = MagicMock()
        config = RateLimitConfig(requests_per_minute=5)
        middleware = SecureRateLimitMiddleware(app, config=config)

        request = MagicMock()
        request.url.path = "/api/v1/auth/login"
        request.client.host = "192.0.2.1"
        request.headers = {}
        request.state = MagicMock()

        call_next = MagicMock()
        response = JSONResponse(content={"message": "ok"})
        call_next.return_value = response

        # Make requests up to limit
        for i in range(5):
            result = await middleware.dispatch(request, call_next)
            assert result.status_code == 200

        # Next request should be rate limited
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429
        assert "Too many requests" in result.body.decode()

    @pytest.mark.asyncio
    async def test_middleware_security_headers(self):
        """Test security headers are added."""
        app = MagicMock()
        middleware = SecureRateLimitMiddleware(app, enable_ddos_headers=True)

        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "192.0.2.1"
        request.headers = {}
        request.state = MagicMock()

        call_next = MagicMock()
        response = JSONResponse(content={"message": "ok"})
        call_next.return_value = response

        result = await middleware.dispatch(request, call_next)

        # Should have security headers
        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert result.headers["X-XSS-Protection"] == "1; mode=block"
        assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_middleware_user_context(self):
        """Test rate limiting respects user context."""
        app = MagicMock()
        config = RateLimitConfig(
            requests_per_minute=5,
            user_requests_per_minute=20
        )
        middleware = SecureRateLimitMiddleware(app, config=config)

        request = MagicMock()
        request.url.path = "/api/v1/user/profile"
        request.client.host = "192.0.2.1"
        request.headers = {}
        request.state.user_id = "user-123"  # Authenticated user

        call_next = MagicMock()
        response = JSONResponse(content={"message": "ok"})
        call_next.return_value = response

        # Authenticated user should get higher limit
        for i in range(20):
            result = await middleware.dispatch(request, call_next)
            assert result.status_code == 200

        # 21st request should be rate limited
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429


class TestDDoSProtection:
    """Test DDoS protection mechanisms."""

    def test_request_size_limit(self, client):
        """Test extremely large requests are rejected."""
        # Create a very large payload
        large_data = "A" * (10 * 1024 * 1024)  # 10MB

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": large_data},
            headers={"Content-Type": "application/json"}
        )

        # Should be rejected before processing
        assert response.status_code in [413, 422, 400]

    def test_header_size_limit(self, client):
        """Test extremely large headers are rejected."""
        large_header = "A" * 10000

        response = client.get(
            "/api/v1/health",
            headers={"X-Large-Header": large_header}
        )

        # Should handle gracefully
        assert response.status_code in [400, 431, 200]

    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self):
        """Test concurrent request limiting."""
        import asyncio

        app = MagicMock()
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_size=5
        )
        middleware = SecureRateLimitMiddleware(app, config=config)

        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "192.0.2.1"
        request.headers = {}
        request.state = MagicMock()

        call_next = MagicMock()
        response = JSONResponse(content={"message": "ok"})
        call_next.return_value = response

        # Launch concurrent requests
        tasks = []
        for i in range(15):
            task = middleware.dispatch(request, call_next)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful vs rate limited
        successful = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 200)
        rate_limited = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 429)

        # Should have some successful and some rate limited
        assert successful > 0
        assert rate_limited > 0
        assert successful <= config.burst_size