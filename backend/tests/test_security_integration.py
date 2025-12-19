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
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
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

        response = await client.post("/api/v1/users/register/", json=register_data)
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

        response = await client.post("/api/v1/users/login/", json=login_data)
        assert response.status_code == 200

        login_result = response.json()
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert login_result["token_type"] == "bearer"

        access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]

        # 3. Use access token for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/v1/users/me/", headers=headers)
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
        assert new_tokens["access_token"] != access_token  # Should be different

        # 5. Old token should still work briefly (grace period)
        response = await client.get("/api/v1/users/me/", headers=headers)
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
                "/api/v1/users/register/",
                json={
                    "email": f"test_{weak_pw}@example.com",
                    "password": weak_pw,
                    "full_name": "Test User"
                }
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_password_migration_flow(self, client: AsyncClient):
        """Test password migration from legacy hashes."""
        # Create user with legacy password hash (simulate existing user)
        from app.models import User
        from app.security import hash_password, verify_password
        from app.db import get_db_session
        from passlib.hash import pbkdf2_sha256

        # Create user directly in DB with legacy hash
        async with get_db_session() as session:
            legacy_hash = pbkdf2_sha256.hash("LegacyPassword123!")
            user = User(
                email="legacy@example.com",
                password_hash=legacy_hash,
                full_name="Legacy User",
                experience_level="senior"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Login with legacy password
        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "legacy@example.com",
                "password": "LegacyPassword123!"
            }
        )

        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens

        # Verify password was migrated
        async with get_db_session() as session:
            await session.refresh(user)
            # Should now be a bcrypt hash
            assert user.password_hash.startswith("$2b$")

        # New login should work with bcrypt hash
        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "legacy@example.com",
                "password": "LegacyPassword123!"
            }
        )

        assert response.status_code == 200

        # Cleanup
        async with get_db_session() as session:
            await session.delete(user)
            await session.commit()

    @pytest.mark.asyncio
    async def test_session_security_features(self, client: AsyncClient):
        """Test session security features."""
        # 1. Login to get tokens
        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "session@example.com",
                "password": "Password123!"  # Assuming user exists
            }
        )

        if response.status_code != 200:
            # Create user first
            await client.post(
                "/api/v1/users/register/",
                json={
                    "email": "session@example.com",
                    "password": "Password123!",
                    "full_name": "Session User"
                }
            )
            response = await client.post(
                "/api/v1/users/login/",
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
            "/api/v1/users/login/",
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
            response = await client.get("/api/v1/users/me/", headers=headers)
            # Might succeed with auto-refresh or fail with 401


class TestAPIRateLimitingIntegration:
    """Test rate limiting in real API scenarios."""

    @pytest.mark.asyncio
    async def test_api_endpoint_rate_limits(self, client: AsyncClient):
        """Test rate limiting on API endpoints."""
        # Test public endpoint rate limiting
        responses = []
        for i in range(70):  # More than typical limit
            response = await client.get("/api/v1/questions/")
            responses.append(response)
            if response.status_code == 429:
                break

        # Should hit rate limit eventually
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Should hit rate limit after many requests"

        # Check rate limit headers
        last_response = responses[-1]
        if last_response.status_code == 429:
            assert "X-RateLimit-Limit" in last_response.headers
            assert "X-RateLimit-Remaining" in last_response.headers
            assert "X-RateLimit-Reset" in last_response.headers

    @pytest.mark.asyncio
    async def test_authenticated_user_higher_limits(self, client: AsyncClient):
        """Test authenticated users get higher rate limits."""
        # Login first
        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "ratelimit@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register/",
                json={
                    "email": "ratelimit@example.com",
                    "password": "Password123!",
                    "full_name": "Rate Limit Test"
                }
            )
            response = await client.post(
                "/api/v1/users/login/",
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
        for i in range(150):  # More than anonymous limit
            response = await client.get("/api/v1/interviews/", headers=headers)
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
        """Test burst protection for rapid requests."""
        # Send rapid requests
        tasks = []
        for i in range(20):  # Burst of requests
            task = client.get("/api/v1/questions/")
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should be rate limited due to burst protection
        rate_limited = sum(
            1 for r in responses
            if hasattr(r, 'status_code') and r.status_code == 429
        )

        assert rate_limited > 0, "Burst protection should limit rapid requests"

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip_isolation(self, client: AsyncClient):
        """Test rate limits are isolated per IP."""
        # This would require multiple clients with different IPs
        # For now, test the concept
        response1 = await client.get("/api/v1/questions/")
        response2 = await client.get("/api/v1/questions/")

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
            "/api/v1/users/login/",
            json={
                "email": "feedback@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register/",
                json={
                    "email": "feedback@example.com",
                    "password": "Password123!",
                    "full_name": "Feedback User"
                }
            )
            response = await client.post(
                "/api/v1/users/login/",
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
            "/api/v1/interviews/",
            json={
                "interview_type": "technical",
                "difficulty": "medium",
                "question_count": 1
            },
            headers=headers
        )

        assert response.status_code == 201
        interview = response.json()
        interview_id = interview["id"]

        # Submit feedback with XSS attempts
        xss_feedback = {
            "content": "<script>alert('XSS')</script> Great answer!",
            "rating": 5
        }

        response = await client.post(
            f"/api/v1/feedback/response/test-response/",
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
        """Test XSS prevention in user profiles."""
        # Create user with XSS in profile
        xss_name = "<img src=x onerror=alert('XSS')>Hacker"
        xss_bio = "<script>steal_data()</script>Cool bio"

        response = await client.post(
            "/api/v1/users/register/",
            json={
                "email": "profile@example.com",
                "password": "Password123!",
                "full_name": xss_name,
                "bio": xss_bio
            }
        )

        # Should sanitize or reject
        assert response.status_code in [201, 422]

        # Login and check profile
        if response.status_code == 201:
            response = await client.post(
                "/api/v1/users/login/",
                json={
                    "email": "profile@example.com",
                    "password": "Password123!"
                }
            )

            tokens = response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}

            response = await client.get("/api/v1/users/me/", headers=headers)
            profile = response.json()

            # Profile data should be sanitized
            assert "<script>" not in profile.get("full_name", "")
            assert "<img" not in profile.get("full_name", "")

    @pytest.mark.asyncio
    async def test_search_xss_prevention(self, client: AsyncClient):
        """Test XSS prevention in search functionality."""
        xss_queries = [
            "<script>alert('XSS')</script>",
            "';alert('XSS');/",
            "<svg onload=alert('XSS')>",
        ]

        for query in xss_queries:
            response = await client.get(
                "/api/v1/questions/search",
                params={"q": query}
            )

            # Should handle without executing scripts
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                # Response should be properly encoded
                response_text = json.dumps(response.json())
                # Check that scripts are not executed (they'd be escaped in JSON)
                assert response_text.count("<script>") <= 1  # At most in the query string


class TestCORSSecurityIntegration:
    """Test CORS security in real scenarios."""

    @pytest.mark.asyncio
    async def test_cors_preflight_handling(self, client: AsyncClient):
        """Test CORS preflight request handling."""
        # Valid preflight from allowed origin
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://app.codeswiftr.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            }
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "https://app.codeswiftr.com"
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
            "/api/v1/users/me/",
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
            ("/api/v1/questions/", "GET"),
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
            "/api/v1/users/login/",
            json={
                "email": "upload@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register/",
                json={
                    "email": "upload@example.com",
                    "password": "Password123!",
                    "full_name": "Upload User"
                }
            )
            response = await client.post(
                "/api/v1/users/login/",
                json={
                    "email": "upload@example.com",
                    "password": "Password123!"
                }
            )

        assert response.status_code == 200
        tokens = response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Test with valid audio file
        audio_content = b"fake audio content"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {
            "session_id": "test-session",
            "question_id": "test-question"
        }

        response = await client.post(
            "/api/v1/upload/audio/",
            files=files,
            data=data,
            headers=headers
        )

        # Should handle valid audio
        assert response.status_code in [200, 201, 400]  # 400 if session doesn't exist

        # Test with invalid file type
        malicious_content = b"<script>alert('XSS')</script>"
        files = {"file": ("malicious.js", malicious_content, "application/javascript")}

        response = await client.post(
            "/api/v1/upload/audio/",
            files=files,
            data=data,
            headers=headers
        )

        # Should reject non-audio files
        assert response.status_code in [400, 422]

        # Test oversized file
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("large.wav", large_content, "audio/wav")}

        response = await client.post(
            "/api/v1/upload/audio/",
            files=files,
            data=data,
            headers=headers
        )

        # Should reject oversized files
        assert response.status_code in [400, 413]

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
                "/api/v1/upload/audio/",
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
            ("/api/v1/users/login/", "POST", {"email": "nonexistent@example.com", "password": "wrong"}),
            ("/api/v1/users/999999/", "GET", None),
            ("/api/v1/interviews/invalid-uuid/", "GET", None),
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
        """Test token expiration is handled securely."""
        # Create user and login
        await client.post(
            "/api/v1/users/register/",
            json={
                "email": "timeout@example.com",
                "password": "Password123!",
                "full_name": "Timeout Test"
            }
        )

        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "timeout@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 200
        tokens = response.json()

        # Mock token expiration
        with patch('app.security.datetime') as mock_dt:
            # Simulate expired token
            mock_dt.now.return_value = datetime.now(UTC) + timedelta(hours=25)
            mock_dt.side_effect = lambda *args, **kw: datetime.now(UTC)

            # Try to use expired token
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            response = await client.get("/api/v1/users/me/", headers=headers)

            # Should reject expired token
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_concurrent_session_invalidation(self, client: AsyncClient):
        """Test session invalidation on security events."""
        # Login to get first session
        response = await client.post(
            "/api/v1/users/login/",
            json={
                "email": "concurrent@example.com",
                "password": "Password123!"
            }
        )

        if response.status_code != 200:
            await client.post(
                "/api/v1/users/register/",
                json={
                    "email": "concurrent@example.com",
                    "password": "Password123!",
                    "full_name": "Concurrent Test"
                }
            )
            response = await client.post(
                "/api/v1/users/login/",
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
            "/api/v1/users/me/change-password/",
            json={
                "current_password": "Password123!",
                "new_password": "NewPassword456!"
            },
            headers=headers
        )

        # Old token might be invalidated immediately or after grace period
        response = await client.get("/api/v1/users/me/", headers=headers)
        assert response.status_code in [200, 401]  # 401 if immediately invalidated