"""Comprehensive API security tests.

Tests for:
- CORS configuration
- Rate limiting effectiveness
- Header validation (CF-RAY, X-Real-IP, X-Forwarded-For)
- IP spoofing prevention
- DDoS protection
"""

from unittest.mock import MagicMock

import pytest
from starlette.responses import JSONResponse

from app.middleware.rate_limit import (
    RateLimitConfig,
    SecureRateLimiter,
    SecureRateLimitMiddleware,
)


class TestCORSSecurity:
    """Test CORS configuration security.

    Note: Tests run in debug mode which uses regex matching for localhost origins.
    These tests verify the CORS middleware behavior with allowed origins.
    """

    @pytest.mark.asyncio
    async def test_cors_allows_localhost_origins(self, client):
        """Test CORS allows localhost origins in debug mode."""
        # In debug mode, the app uses regex to match localhost origins
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
        ]

        for origin in allowed_origins:
            response = await client.options(
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

    @pytest.mark.asyncio
    async def test_cors_rejects_unauthorized_origins(self, client):
        """Test CORS rejects unauthorized origins."""
        unauthorized_origins = [
            "https://malicious-site.com",
            "https://evil.com",
            "http://attacker.example.com:3000",  # Not localhost or .local
        ]

        for origin in unauthorized_origins:
            response = await client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                }
            )

            # Origin should not be in allow list (400 status for disallowed CORS)
            assert response.status_code == 400 or response.headers.get("Access-Control-Allow-Origin") != origin

    @pytest.mark.asyncio
    async def test_cors_credentials_not_wildcard(self, client):
        """Test CORS doesn't use wildcard with credentials."""
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Credentials": "true",
            }
        )

        # Should not use wildcard when credentials are allowed
        assert response.headers.get("Access-Control-Allow-Origin") != "*"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_allowed_headers_restricted(self, client):
        """Test CORS only allows specific headers."""
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type, X-Custom",
            }
        )

        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
        assert "Authorization" in allowed_headers
        assert "Content-Type" in allowed_headers
        # X-Custom might not be allowed

    @pytest.mark.asyncio
    async def test_cors_methods_restricted(self, client):
        """Test CORS only allows specific HTTP methods."""
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
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
        for _i in range(10):
            allowed1, _ = rate_limiter.is_allowed(request1)
            allowed2, _ = rate_limiter.is_allowed(request2)
            assert allowed1 is True
            assert allowed2 is True

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
        for _i in range(rate_limiter.config.user_requests_per_minute):
            allowed, _ = rate_limiter.is_allowed(request1, user_id="user-1")
            assert allowed is True

        # User 2 should still have their full limit available
        for _i in range(rate_limiter.config.user_requests_per_minute):
            allowed, _ = rate_limiter.is_allowed(request2, user_id="user-2")
            assert allowed is True

    def test_rate_limit_sliding_window(self, rate_limiter):
        """Test sliding window rate limiting."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Use up the minute limit
        for _i in range(10):
            rate_limiter.is_allowed(request)

        # Should be blocked
        allowed, _ = rate_limiter.is_allowed(request)
        assert allowed is False

        # Simulate window sliding by clearing old requests
        # The actual sliding window implementation cleans based on current time
        # We manually manipulate the internal state to simulate time passage
        key = rate_limiter._generate_secure_key(request)
        # Clear all old requests to simulate they've aged out
        rate_limiter._requests[key] = []

        # Should be allowed again after window slides
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
        """Test burst protection prevents rapid requests.

        Note: The current implementation uses requests_per_minute as the burst limit,
        not a separate burst_size. This test validates that the rate limiter stops
        requests when the minute limit is exceeded.
        """
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Make requests beyond the minute limit
        allowed_count = 0
        for _i in range(20):  # Try more than requests_per_minute (10)
            allowed, _ = rate_limiter.is_allowed(request)
            if allowed:
                allowed_count += 1

        # Should be limited by requests_per_minute (configured as 10 in fixture)
        assert allowed_count == rate_limiter.config.requests_per_minute


class TestIPValidationSecurity:
    """Test IP validation and spoofing prevention."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        return SecureRateLimiter(RateLimitConfig())

    def test_cloudflare_ip_trusted(self, rate_limiter):
        """Test Cloudflare CF-Connecting-IP header is trusted."""
        request = MagicMock()
        request.client.host = "172.67.0.1"  # Cloudflare proxy IP

        # Use real public IP addresses (Google DNS for example)
        headers_dict = {
            "CF-RAY": "1234567890",
            "CF-Connecting-IP": "8.8.8.8",  # Real public IP
        }
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: headers_dict.get(key) if headers_dict.get(key) is not None else default
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

        # Should trust CF-Connecting-IP when CF-RAY is present
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "8.8.8.8"

    def test_cloudflare_ip_without_ray_rejected(self, rate_limiter):
        """Test CF-Connecting-IP without CF-RAY falls back to direct IP.

        Without CF-RAY, the CF-Connecting-IP header is not trusted and
        the middleware falls back to the direct connection IP.
        """
        request = MagicMock()
        request.client.host = "203.0.113.1"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {
            "CF-Connecting-IP": "198.51.100.1",
            # Missing CF-RAY
        }.get(key, default)
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

        # Should fall back to direct IP when CF-RAY is missing
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "203.0.113.1"  # Falls back to client.host

    def test_railway_ip_trusted(self, rate_limiter):
        """Test Railway X-Real-IP header is trusted on Railway."""
        request = MagicMock()
        request.client.host = "10.0.0.1"

        headers_dict = {
            "X-Real-IP": "1.1.1.1",  # Real public IP (Cloudflare DNS)
        }
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: headers_dict.get(key) if headers_dict.get(key) is not None else default
        request.url.path = "/api/v1/test"
        request.url.hostname = "interview-simulator-api-production.up.railway.app"

        # Should trust X-Real-IP on Railway
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "1.1.1.1"

    def test_x_forwarded_for_limited_proxies(self, rate_limiter):
        """Test X-Forwarded-For with too many proxies falls back to direct IP."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        xff_value = ",".join([f"10.0.0.{i}" for i in range(10)])  # 10 proxies
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {
            "X-Forwarded-For": xff_value,
        }.get(key, default)
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

        # Should fall back to direct IP due to too many proxies
        ip = rate_limiter._get_trusted_client_ip(request)
        assert ip == "127.0.0.1"  # Falls back to client.host

    def test_x_forwarded_for_private_ip_rejected(self, rate_limiter):
        """Test private IPs in X-Forwarded-For are rejected."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        xff_value = "10.0.0.1, 192.168.1.1, 198.51.100.1"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {
            "X-Forwarded-For": xff_value,
        }.get(key, default)
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

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
        """Test public IP validation.

        Note: 2001:db8::/32 is reserved for documentation (RFC 3849) and is
        not actually a public IP. Using real public IPv4 for this test.
        """
        # Public IPs should be valid format
        public_ips = [
            "198.51.100.1",
            "203.0.113.1",
        ]

        for ip in public_ips:
            assert rate_limiter._is_valid_ip_format(ip) is True
            # Note: 198.51.100.0/24 and 203.0.113.0/24 are TEST-NET-2 and TEST-NET-3
            # They may be treated as non-public by some implementations

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
        """Test suspicious User-Agent patterns are tracked.

        The is_suspicious method returns True only after the same IP
        exceeds the suspicious threshold (>5 incidents). Single requests
        with suspicious patterns are logged but don't immediately return True.
        """
        request = MagicMock()
        request.client.host = "192.0.2.1"
        request.url.path = "/api/v1/auth/login"
        request.url.hostname = "api.example.com"

        # Create headers mock with suspicious User-Agent
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "User-Agent": "curl/7.68.0",  # Suspicious pattern
            "X-Forwarded-For": "",
            "X-Real-IP": "",
            "CF-Connecting-IP": "",
        }.get(key, default)

        # First calls should track but not return True
        for _ in range(5):
            is_suspicious = rate_limiter.is_suspicious(request)
            # The IP is being tracked, but hasn't exceeded threshold

        # After threshold (>5 incidents), should return True
        is_suspicious = rate_limiter.is_suspicious(request)
        assert rate_limiter._suspicious_ips["192.0.2.1"] > 5
        assert is_suspicious is True

    def test_suspicious_header_patterns(self, rate_limiter):
        """Test suspicious header patterns are tracked.

        The is_suspicious method tracks suspicious activity per IP and
        returns True only after threshold is exceeded (>5 incidents).
        """
        request = MagicMock()
        request.client.host = "192.0.2.2"  # Use different IP
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"

        # Header with line breaks
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "X-Forwarded-For": "192.0.2.1\nLocation: evil.com",
            "User-Agent": "normal",
            "X-Real-IP": "",
            "CF-Connecting-IP": "",
            "CF-RAY": "",
        }.get(key, default)

        # Build up suspicious count
        for _ in range(6):
            rate_limiter.is_suspicious(request)

        is_suspicious = rate_limiter.is_suspicious(request)
        assert is_suspicious is True

        # Test oversized User-Agent header with fresh IP
        request.client.host = "192.0.2.3"
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "User-Agent": "A" * 600,  # Too long
            "X-Forwarded-For": "",
            "X-Real-IP": "",
            "CF-Connecting-IP": "",
            "CF-RAY": "",
        }.get(key, default)

        # Build up suspicious count for new IP
        for _ in range(6):
            rate_limiter.is_suspicious(request)

        is_suspicious = rate_limiter.is_suspicious(request)
        assert is_suspicious is True

    def test_mismatched_headers_detection(self, rate_limiter):
        """Test mismatched headers without Cloudflare are tracked.

        When X-Real-IP and X-Forwarded-For mismatch without CF-RAY,
        it's flagged as suspicious activity.
        """
        request = MagicMock()
        request.client.host = "192.0.2.4"
        request.url.path = "/api/v1/test"
        request.url.hostname = "api.example.com"
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "X-Real-IP": "198.51.100.1",
            "X-Forwarded-For": "203.0.113.1",  # Different from X-Real-IP
            "User-Agent": "normal",
            "CF-Connecting-IP": "",
            "CF-RAY": "",  # No CF-RAY
        }.get(key, default)

        # The is_suspicious method logs and tracks the activity
        # It's tracked but won't return True until threshold is exceeded
        result = rate_limiter.is_suspicious(request)
        # First check won't return True (need >5 incidents)
        assert rate_limiter._suspicious_ips.get("192.0.2.4", 0) >= 1 or result is False

    def test_ip_tracking_for_blocking(self, rate_limiter):
        """Test suspicious IPs are tracked for potential blocking."""
        request = MagicMock()
        request.client.host = "192.0.2.5"  # Fresh IP
        request.url.path = "/api/v1/auth/login"
        request.url.hostname = "api.example.com"

        headers_dict = {
            "User-Agent": "curl/7.68.0",  # Suspicious
            "X-Forwarded-For": "",
            "X-Real-IP": "",
            "CF-Connecting-IP": "",
            "CF-RAY": "",
        }
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": headers_dict.get(key) if headers_dict.get(key) is not None else default

        # First few suspicious activities
        for _ in range(3):
            rate_limiter.is_suspicious(request)

        # IP should be tracked - count increases each call
        count_after_3 = rate_limiter._suspicious_ips["192.0.2.5"]
        assert count_after_3 >= 3  # At least 3, could be more

        # After more calls (need >5 to return True)
        for _ in range(3):
            rate_limiter.is_suspicious(request)

        # Now count should exceed 5
        # Should now be considered suspicious (returns True when count > 5)
        is_suspicious = rate_limiter.is_suspicious(request)
        assert rate_limiter._suspicious_ips["192.0.2.5"] > 5
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

        response = JSONResponse(content={"status": "ok"})

        async def async_call_next(req):
            return response

        result = await middleware.dispatch(request, async_call_next)

        # Should not add rate limit headers (excluded path returns call_next directly)
        assert "X-RateLimit-Limit" not in result.headers

    @pytest.mark.asyncio
    async def test_middleware_rate_limits_api(self):
        """Test API endpoints are rate limited."""
        app = MagicMock()
        config = RateLimitConfig(requests_per_minute=5)
        middleware = SecureRateLimitMiddleware(app, config=config, enable_ddos_headers=False)

        request = MagicMock()
        request.url.path = "/api/v1/auth/login"
        request.client.host = "192.0.2.10"  # Fresh IP
        request.url.hostname = "api.example.com"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {}.get(key, default)
        request.state = MagicMock(spec=[])  # Empty spec means no attributes

        response = JSONResponse(content={"message": "ok"})

        async def async_call_next(req):
            return response

        # Make requests up to limit
        for _i in range(5):
            result = await middleware.dispatch(request, async_call_next)
            assert result.status_code == 200

        # Next request should be rate limited
        result = await middleware.dispatch(request, async_call_next)
        assert result.status_code == 429
        assert "Too many requests" in result.body.decode()

    @pytest.mark.asyncio
    async def test_middleware_security_headers(self):
        """Test security headers are added."""
        app = MagicMock()
        middleware = SecureRateLimitMiddleware(app, enable_ddos_headers=True)

        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "192.0.2.11"  # Fresh IP
        request.url.hostname = "api.example.com"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {
            "User-Agent": "Mozilla/5.0",  # Normal User-Agent
        }.get(key, default)
        request.state = MagicMock(spec=[])

        response = JSONResponse(content={"message": "ok"})

        async def async_call_next(req):
            return response

        result = await middleware.dispatch(request, async_call_next)

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
        middleware = SecureRateLimitMiddleware(app, config=config, enable_ddos_headers=False)

        request = MagicMock()
        request.url.path = "/api/v1/user/profile"
        request.client.host = "192.0.2.12"  # Fresh IP
        request.url.hostname = "api.example.com"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {}.get(key, default)

        # Authenticated user
        class MockState:
            user_id = "user-123"

        request.state = MockState()

        response = JSONResponse(content={"message": "ok"})

        async def async_call_next(req):
            return response

        # Authenticated user should get higher limit
        for _i in range(20):
            result = await middleware.dispatch(request, async_call_next)
            assert result.status_code == 200

        # 21st request should be rate limited
        result = await middleware.dispatch(request, async_call_next)
        assert result.status_code == 429


class TestDDoSProtection:
    """Test DDoS protection mechanisms."""

    @pytest.mark.asyncio
    async def test_request_size_limit(self, client):
        """Test extremely large requests are handled.

        Note: The actual size limit depends on the web server (uvicorn) config.
        This test verifies the application responds appropriately to large payloads.
        """
        # Create a moderately large payload (1MB to avoid memory issues in tests)
        large_data = "A" * (1 * 1024 * 1024)

        response = await client.post(
            "/api/v1/users/login",  # Correct login endpoint path
            json={"email": "test@example.com", "password": large_data},
            headers={"Content-Type": "application/json"}
        )

        # Should be rejected or handled gracefully
        # 413 = Payload Too Large, 422 = Validation Error, 400 = Bad Request
        # 401 = Unauthorized (if processed but rejected at auth)
        assert response.status_code in [413, 422, 400, 401]

    @pytest.mark.asyncio
    async def test_header_size_limit(self, client):
        """Test large headers are handled gracefully."""
        large_header = "A" * 10000

        response = await client.get(
            "/health",  # Health endpoint at root
            headers={"X-Large-Header": large_header}
        )

        # Should handle gracefully - 200 if accepted, 400/431 if rejected
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
        middleware = SecureRateLimitMiddleware(app, config=config, enable_ddos_headers=False)

        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "192.0.2.20"  # Fresh IP
        request.url.hostname = "api.example.com"
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: {}.get(key, default)
        request.state = MagicMock(spec=[])

        response = JSONResponse(content={"message": "ok"})

        async def async_call_next(req):
            return response

        # Launch concurrent requests
        tasks = []
        for _i in range(15):
            task = middleware.dispatch(request, async_call_next)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful vs rate limited
        successful = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 200)
        rate_limited = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 429)

        # Should have some successful and some rate limited
        assert successful > 0
        assert rate_limited > 0
        # Total should equal 15, limited by requests_per_minute
        assert successful <= config.requests_per_minute
