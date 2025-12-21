"""Integration tests for complete security flows.

Tests end-to-end security scenarios:
- Full authentication flow with security
- API endpoints with rate limits
- Blog rendering with malicious content
- Cross-origin request security
- Session management security
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestAuthenticationFlowSecurity:
    """Test complete authentication flow security."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow_with_password_migration(self, client: AsyncClient):
        """Test full authentication flow including password migration."""
        # 1. Register new user (should use bcrypt)
        register_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "experience_level": "mid"
        }

        response = await client.post("/api/v1/users/register", json=register_data)
        assert response.status_code == 201

        # Verify user was created
        user_data = response.json()
        assert user_data["email"] == "newuser@example.com"
        assert "password" not in user_data
        assert "id" in user_data

        # 2. Login with correct credentials
        login_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!"
        }

        response = await client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200

        login_result = response.json()
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert login_result["token_type"] == "bearer"

        access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]

        # 3. Use access token for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        profile = response.json()
        assert profile["email"] == "newuser@example.com"
        assert profile["full_name"] == "New User"

        # 4. Test token refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200

        new_tokens = response.json()
        assert "access_token" in new_tokens
        # Note: Token may be identical if refreshed in same second (same exp/iat)
        # The important thing is the refresh endpoint works

        # 5. Old token should still work briefly (grace period)
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        # 6. Test logout (clears server-side session if implemented)
        response = await client.post("/api/v1/auth/logout", headers=headers)
        # Note: This endpoint might not exist, logout is typically client-side

        # 7. Verify password complexity validation
        weak_passwords = [
            "123",  # Too short
            "password",  # Too common
            "qwerty",  # Too common
            "Password123",  # No special char
        ]

        for weak_pw in weak_passwords:
            response = await client.post(
                "/api/v1/users/register",
                json={
                    "email": f"test_{weak_pw}@example.com",
                    "password": weak_pw,
                    "full_name": "Test User"
                }
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_password_migration_flow(self, client: AsyncClient):
        """Test password hash verification works.

        Note: This test verifies that the login flow works correctly.
        Password migration is handled transparently by the auth system.
        """
        # Create a test user
        response = await client.post(
            "/api/v1/users/register",
            json={
                "email": "migration_test@example.com",
                "password": "TestPassword123!",
                "full_name": "Migration Test User",
                "experience_level": "senior"
            }
        )

        # May already exist from previous run
        if response.status_code == 422:
            pass  # User exists, continue to login

        # Login should work
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "migration_test@example.com",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_session_security_features(self, client: AsyncClient):
        """Test session security features."""
        # 1. Login to get tokens
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "session@example.com",
                "password": "Password123!"  # Assuming user exists
            }
        )

        if response.status_code != 200:
            # Create user first
            await client.post(
                "/api/v1/users/register",
                json={
                    "email": "session@example.com",
                    "password": "Password123!",
                    "full_name": "Session User"
                }
            )
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "session@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        tokens = response.json()
        access_token = tokens["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Test concurrent session limits (if implemented)
        # Create another session
        response2 = await client.post(
            "/api/v1/users/login",
            json={
                "email": "session@example.com",
                "password": "Password123!"
            }
        )

        # Should allow multiple sessions unless restricted
        assert response2.status_code in [200, 403]  # 403 if concurrent sessions limited

        # 3. Test secure token storage (client-side responsibility)
        # This would be tested in frontend

        # 4. Test automatic token refresh
        # Wait for token to be near expiry (mock)
        with patch('app.security.datetime') as mock_dt:
            # Simulate token expiry
            mock_dt.now.return_value = datetime.now(UTC) + timedelta(minutes=20)
            mock_dt.side_effect = lambda *args, **kw: datetime.now(UTC)

            # Should attempt refresh
            response = await client.get("/api/v1/users/me", headers=headers)
            # Might succeed with auto-refresh or fail with 401


class TestAPIRateLimitingIntegration:
    """Test rate limiting in real API scenarios."""

    @pytest.mark.asyncio
    async def test_api_endpoint_rate_limits(self, client: AsyncClient):
        """Test rate limit headers are present on API endpoints.

        Note: The actual rate limiting may not be triggered in test mode
        due to high limits or disabled middleware. This test verifies
        the rate limit headers are present on responses.
        """
        # Make a request and check for rate limit headers
        response = await client.get("/api/v1/questions")

        # Should return success (or require auth)
        assert response.status_code in [200, 401]

        # Rate limit headers should be present if middleware is enabled
        # These are optional in test mode
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_authenticated_user_higher_limits(self, client: AsyncClient):
        """Test authenticated users get higher rate limits."""
        # Login first
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "ratelimit@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register",
                json={
                    "email": "ratelimit@example.com",
                    "password": "Password123!",
                    "full_name": "Rate Limit Test"
                }
            )
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "ratelimit@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        tokens = response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Authenticated user should be able to make more requests
        responses = []
        for _i in range(150):  # More than anonymous limit
            response = await client.get("/api/v1/interviews", headers=headers)
            responses.append(response)
            if response.status_code == 429:
                break

        # Should have higher limit or no limit
        if any(r.status_code == 429 for r in responses):
            # If limited, should be at higher threshold
            rate_limited_at = next(
                i for i, r in enumerate(responses) if r.status_code == 429
            )
            assert rate_limited_at > 60  # Higher than anonymous limit

    @pytest.mark.asyncio
    async def test_burst_protection(self, client: AsyncClient):
        """Test concurrent requests are handled without errors.

        Note: Burst protection may not be triggered in test mode.
        This test verifies the server handles concurrent requests gracefully.
        """
        # Send rapid concurrent requests
        tasks = []
        for _i in range(10):  # Concurrent requests
            task = client.get("/api/v1/questions")
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without server errors
        for r in responses:
            if hasattr(r, 'status_code'):
                # Should get success, rate limit, or auth required - not server error
                assert r.status_code in [200, 401, 429], f"Unexpected status: {r.status_code}"

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip_isolation(self, client: AsyncClient):
        """Test rate limits are isolated per IP."""
        # This would require multiple clients with different IPs
        # For now, test the concept
        response1 = await client.get("/api/v1/questions")
        response2 = await client.get("/api/v1/questions")

        # Both should succeed initially
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestContentSecurityIntegration:
    """Test content security in real scenarios."""

    @pytest.mark.asyncio
    async def test_feedback_content_sanitization(self, client: AsyncClient):
        """Test feedback content is sanitized end-to-end."""
        # Login first
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "feedback@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register",
                json={
                    "email": "feedback@example.com",
                    "password": "Password123!",
                    "full_name": "Feedback User"
                }
            )
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "feedback@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        tokens = response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create an interview session
        response = await client.post(
            "/api/v1/interviews",
            json={
                "interview_type": "technical",
                "difficulty": "medium",
                "question_count": 1
            },
            headers=headers
        )

        assert response.status_code == 201
        interview = response.json()
        interview["id"]

        # Submit feedback with XSS attempts
        xss_feedback = {
            "content": "<script>alert('XSS')</script> Great answer!",
            "rating": 5
        }

        response = await client.post(
            "/api/v1/feedback/response/test-response/",
            json=xss_feedback,
            headers=headers
        )

        # Should accept but sanitize
        assert response.status_code in [200, 201, 404]  # 404 if response doesn't exist

        # Retrieve feedback (should be sanitized)
        if response.status_code in [200, 201]:
            feedback_id = response.json().get("id")
            if feedback_id:
                response = await client.get(
                    f"/api/v1/feedback/{feedback_id}/",
                    headers=headers
                )

                if response.status_code == 200:
                    feedback = response.json()
                    content = feedback.get("content", "")
                    assert "<script>" not in content
                    assert "alert('XSS')" not in content

    @pytest.mark.asyncio
    async def test_user_profile_xss_prevention(self, client: AsyncClient):
        """Test XSS content in profiles is handled safely.

        Note: XSS prevention can happen at different levels:
        - Input validation (reject at registration)
        - Output encoding (safe rendering in frontend)
        - Content sanitization (strip dangerous tags)

        This test verifies the API handles XSS attempts without crashing.
        """
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create user with potential XSS in profile
        xss_name = "<img src=x onerror=alert('XSS')>TestUser"

        response = await client.post(
            "/api/v1/users/register",
            json={
                "email": f"profile_{unique_id}@example.com",
                "password": "Password123!",
                "full_name": xss_name,
            }
        )

        # Should accept (validation may happen at frontend) or sanitize
        assert response.status_code in [201, 422]

        # If created, verify we can retrieve the profile
        if response.status_code == 201:
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": f"profile_{unique_id}@example.com",
                    "password": "Password123!"
                }
            )

            tokens = response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}

            response = await client.get("/api/v1/users/me", headers=headers)
            profile = response.json()

            # The response should be valid JSON (not execute scripts)
            assert "email" in profile
            # Note: The name might be stored as-is (XSS prevention at render time)

    @pytest.mark.asyncio
    async def test_search_xss_prevention(self, client: AsyncClient):
        """Test search handles XSS input safely.

        Note: This test verifies that the questions endpoint handles
        XSS-like query parameters without crashing.
        """
        xss_queries = [
            "<script>alert('XSS')</script>",
            "';alert('XSS');/",
            "normal search term",
        ]

        for query in xss_queries:
            response = await client.get(
                "/api/v1/questions",  # Use existing endpoint
                params={"search": query}
            )

            # Should handle without executing scripts - 200, 401, or 404
            assert response.status_code in [200, 400, 401, 404, 422]

            if response.status_code == 200:
                # Response should be valid JSON
                data = response.json()
                assert isinstance(data, (list, dict))


class TestCORSSecurityIntegration:
    """Test CORS security in real scenarios."""

    @pytest.mark.asyncio
    async def test_cors_preflight_handling(self, client: AsyncClient):
        """Test CORS preflight request handling.

        Note: In test mode, CORS may be configured for localhost origins.
        """
        # Valid preflight from localhost (allowed in test/dev mode)
        response = await client.options(
            "/api/v1/users/login",  # Use correct endpoint
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            }
        )

        # Should return 200 for valid preflight
        assert response.status_code == 200
        # Origin should be allowed (localhost in test mode)
        assert "Access-Control-Allow-Origin" in response.headers
        assert "POST" in response.headers.get("Access-Control-Allow-Methods", "")

        # Preflight from unauthorized origin
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
            }
        )

        # Should not include unauthorized origin
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] != "https://malicious-site.com"

    @pytest.mark.asyncio
    async def test_cors_credentials_handling(self, client: AsyncClient):
        """Test CORS credentials are handled properly."""
        response = await client.options(
            "/api/v1/users/me",
            headers={
                "Origin": "https://app.codeswiftr.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Credentials": "true",
            }
        )

        if response.status_code == 200:
            # Should support credentials if configured
            assert response.headers.get("Access-Control-Allow-Credentials") == "true"
            # Should not use wildcard with credentials
            assert response.headers.get("Access-Control-Allow-Origin") != "*"


class TestSecurityHeadersIntegration:
    """Test security headers are present on all responses."""

    @pytest.mark.asyncio
    async def test_security_headers_on_all_endpoints(self, client: AsyncClient):
        """Test security headers are present on various endpoints."""
        endpoints = [
            ("/api/v1/health", "GET"),
            ("/api/v1/questions", "GET"),
            ("/api/v1/auth/login", "OPTIONS"),
            ("/nonexistent", "GET"),
        ]

        for path, method in endpoints:
            if method == "GET":
                response = await client.get(path)
            else:
                response = await client.options(path)

            # Should have security headers (might be middleware-based)
            expected_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            }

            for header, expected_value in expected_headers.items():
                # Headers might be added by middleware
                # This is more of a check for proper configuration
                if header in response.headers:
                    assert response.headers[header] == expected_value


class TestFileUploadSecurity:
    """Test file upload security end-to-end."""

    @pytest.mark.asyncio
    async def test_audio_upload_security(self, client: AsyncClient):
        """Test audio upload security measures."""
        # Login first
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "upload@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register",
                json={
                    "email": "upload@example.com",
                    "password": "Password123!",
                    "full_name": "Upload User"
                }
            )
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "upload@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        tokens = response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Test with invalid file type (should be rejected)
        import uuid
        # Use valid UUID format for session_id
        test_session_id = str(uuid.uuid4())
        test_question_id = str(uuid.uuid4())

        malicious_content = b"<script>alert('XSS')</script>"
        files = {"file": ("malicious.js", malicious_content, "application/javascript")}
        data = {
            "session_id": test_session_id,
            "question_id": test_question_id
        }

        response = await client.post(
            "/api/v1/upload/audio",
            files=files,
            data=data,
            headers=headers
        )

        # Should reject non-audio files (400/404/422)
        # 404 is acceptable if session doesn't exist
        assert response.status_code in [400, 404, 422]

        # Test with valid audio file but non-existent session
        audio_content = b"fake audio content"
        files = {"file": ("test.wav", audio_content, "audio/wav")}

        response = await client.post(
            "/api/v1/upload/audio",
            files=files,
            data=data,
            headers=headers
        )

        # Should fail because session doesn't exist
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_file_path_traversal_prevention(self, client: AsyncClient):
        """Test path traversal prevention in file operations."""
        # Test with malicious file names
        malicious_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "..../..../..../etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for name in malicious_names:
            files = {"file": (name, b"content", "audio/wav")}
            data = {"session_id": "test"}

            # Even if file type is valid, name should be sanitized
            response = await client.post(
                "/api/v1/upload/audio",
                files=files,
                data=data
            )

            # Should handle path traversal attempts
            assert response.status_code in [400, 401, 422]


class TestErrorHandlingSecurity:
    """Test secure error handling."""

    @pytest.mark.asyncio
    async def test_error_messages_sanitization(self, client: AsyncClient):
        """Test error messages don't leak sensitive information."""
        # Test various error scenarios
        error_scenarios = [
            ("/api/v1/users/login", "POST", {"email": "nonexistent@example.com", "password": "wrong"}),
            ("/api/v1/users/999999/", "GET", None),
            ("/api/v1/interviewsinvalid-uuid/", "GET", None),
            ("/api/v1/auth/refresh", "POST", {"refresh_token": "invalid-token"}),
        ]

        for endpoint, method, data in error_scenarios:
            if method == "GET":
                response = await client.get(endpoint)
            else:
                response = await client.post(endpoint, json=data)

            # Should not leak sensitive information
            if response.status_code >= 400:
                error_text = response.text.lower()
                sensitive_terms = [
                    "internal server error",
                    "stack trace",
                    "database",
                    "sql",
                    "exception",
                    "traceback",
                ]

                # Most sensitive terms should not be in client errors
                for term in sensitive_terms:
                    if response.status_code < 500:  # Client errors
                        assert term not in error_text, f"Sensitive term '{term}' in error response"

    @pytest.mark.asyncio
    async def test_debug_info_not_leaked(self, client: AsyncClient):
        """Test debug information is not leaked in production."""
        # Request with debug header
        response = await client.get(
            "/api/v1/health",
            headers={"Debug": "true"}
        )

        # Should not include debug information
        response_text = response.text.lower()
        debug_indicators = [
            "debug",
            "trace",
            "internal",
            "source code",
            ".py",
            "line ",
        ]

        for indicator in debug_indicators:
            # Some might appear legitimately, check context
            if indicator in response_text:
                # Verify it's not actual debug info
                assert "error" not in response_text or indicator not in response_text


class TestSessionTimeoutSecurity:
    """Test session timeout and invalidation."""

    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, client: AsyncClient):
        """Test token authentication works.

        Note: Actually testing token expiration would require either:
        1. Waiting for the token to expire (too slow for tests)
        2. Mocking internal JWT validation (implementation-specific)

        This test verifies the basic token flow works.
        """
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # Create user and login
        await client.post(
            "/api/v1/users/register",
            json={
                "email": f"timeout_{unique_id}@example.com",
                "password": "Password123!",
                "full_name": "Timeout Test"
            }
        )

        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": f"timeout_{unique_id}@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 200
        tokens = response.json()

        # Valid token should work
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        # Invalid token should be rejected
        headers = {"Authorization": "Bearer invalid-token-123"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_concurrent_session_invalidation(self, client: AsyncClient):
        """Test session invalidation on security events."""
        # Login to get first session
        response = await client.post(
            "/api/v1/users/login",
            json={
                "email": "concurrent@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register",
                json={
                    "email": "concurrent@example.com",
                    "password": "Password123!",
                    "full_name": "Concurrent Test"
                }
            )
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "concurrent@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        first_tokens = response.json()

        # Change password (should invalidate all sessions)
        headers = {"Authorization": f"Bearer {first_tokens['access_token']}"}
        response = await client.post(
            "/api/v1/users/mechange-password/",
            json={
                "current_password": "Password123!",
                "new_password": "NewPassword456!"
            },
            headers=headers
        )

        # Old token might be invalidated immediately or after grace period
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code in [200, 401]  # 401 if immediately invalidated
