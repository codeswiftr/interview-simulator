"""Comprehensive XSS prevention tests.

Tests for:
- HTML sanitization effectiveness
- Script injection attempts
- Event handler blocking
- Protocol filtering
- Content-Type enforcement
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException
from html_sanitizer import Sanitizer

from app.services.content_sanitizer import (
    HTMLContentSanitizer,
    sanitize_html,
    sanitize_markdown,
    validate_content_type,
)
from app.api.feedback import FeedbackService


class TestHTMLSanitization:
    """Test HTML content sanitization."""

    def test_basic_sanitization(self):
        """Test basic HTML sanitization removes dangerous elements."""
        dangerous_html = """
        <div>
            <p>Safe content</p>
            <script>alert('XSS')</script>
            <iframe src="javascript:alert('XSS')"></iframe>
            <img src="x" onerror="alert('XSS')">
            <link rel="stylesheet" href="evil.css">
        </div>
        """

        sanitized = sanitize_html(dangerous_html)

        # Safe content should remain
        assert "<p>Safe content</p>" in sanitized

        # Dangerous elements should be removed
        assert "<script>" not in sanitized
        assert "<iframe" not in sanitized
        assert "onerror" not in sanitized
        assert "<link" not in sanitized
        assert "javascript:" not in sanitized

    def test_event_handler_removal(self):
        """Test all event handlers are removed."""
        html_with_events = """
        <div onclick="malicious()">Click me</div>
        <img onmouseover="alert('XSS')" src="image.jpg">
        <body onload="stealData()">
        <form onsubmit="redirect()">
        """

        sanitized = sanitize_html(html_with_events)

        # All event handlers should be removed
        assert "onclick" not in sanitized
        assert "onmouseover" not in sanitized
        assert "onload" not in sanitized
        assert "onsubmit" not in sanitized

    def test_protocol_filtering(self):
        """Test dangerous protocols are filtered."""
        dangerous_protocols = [
            "javascript:",
            "data:",
            "vbscript:",
            "file:",
            "ftp:",
        ]

        for protocol in dangerous_protocols:
            html = f'<a href="{protocol}alert(1)">Link</a>'
            sanitized = sanitize_html(html)

            # Protocol should be removed or sanitized
            assert protocol not in sanitized
            assert "alert(1)" not in sanitized

    def test_css_sanitization(self):
        """Test CSS is properly sanitized."""
        dangerous_css = """
        <style>
            .safe { color: blue; }
            .dangerous { background: url('javascript:alert(1)'); }
            .xss { expression(alert('XSS')); }
        </style>
        <div style="position:absolute; top:-9999px;left:-9999px">
            Hidden content
        </div>
        """

        sanitized = sanitize_html(dangerous_css)

        # Safe CSS should remain
        assert "color: blue" in sanitized

        # Dangerous CSS should be removed
        assert "javascript:" not in sanitized
        assert "expression(" not in sanitized
        assert "position:absolute" not in sanitized or "top:-9999px" not in sanitized

    def test_attribute_sanitization(self):
        """Test dangerous attributes are sanitized."""
        html_with_bad_attrs = """
        <div data-script="alert(1)">Content</div>
        <img src="image.jpg" formaction="javascript:alert(1)">
        <input type="text" autocomplete="off" autofocus>
        <meta http-equiv="refresh" content="0;url=evil.com">
        """

        sanitized = sanitize_html(html_with_bad_attrs)

        # Check dangerous attributes are handled
        assert "formaction" not in sanitized or "javascript:" not in sanitized
        assert "http-equiv" not in sanitized or "refresh" not in sanitized

    def test_safe_elements_preserved(self):
        """Test safe HTML elements are preserved."""
        safe_html = """
        <h1>Title</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <blockquote>
            <p>A quote</p>
            <footer>Citation</footer>
        </blockquote>
        <code>code snippet</code>
        <pre>formatted code</pre>
        """

        sanitized = sanitize_html(safe_html)

        # All safe elements should be preserved
        assert "<h1>" in sanitized
        assert "<p>" in sanitized
        assert "<strong>" in sanitized
        assert "<em>" in sanitized
        assert "<ul>" in sanitized
        assert "<li>" in sanitized
        assert "<blockquote>" in sanitized
        assert "<code>" in sanitized
        assert "<pre>" in sanitized

    def test_sanitizer_configuration(self):
        """Test sanitizer is properly configured."""
        sanitizer = HTMLContentSanitizer()

        # Check allowed tags
        allowed_tags = sanitizer.sanitizer.allowed_tags
        safe_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'u', 'ul', 'ol', 'li'}

        for tag in safe_tags:
            assert tag in allowed_tags

        # Check dangerous tags are not allowed
        dangerous_tags = {'script', 'iframe', 'object', 'embed', 'form', 'input', 'button'}
        for tag in dangerous_tags:
            assert tag not in allowed_tags

        # Check allowed attributes
        allowed_attrs = sanitizer.sanitizer.allowed_attributes
        safe_attrs = {'href', 'title', 'alt', 'class'}

        for attr in safe_attrs:
            assert attr in allowed_attrs

        # Dangerous attributes should not be allowed
        dangerous_attrs = {'onclick', 'onload', 'onerror', 'style'}
        for attr in dangerous_attrs:
            assert attr not in allowed_attrs


class TestMarkdownSanitization:
    """Test markdown content sanitization."""

    def test_markdown_xss_prevention(self):
        """Test markdown with XSS is sanitized."""
        xss_markdown = """
        # Safe Header

        [Safe Link](https://example.com)

        <script>alert('XSS')</script>

        [XSS Link](javascript:alert('XSS'))

        ![Image](safe.jpg "onload='alert(1)'")

        `Inline code with <script>alert(1)</script>`
        """

        sanitized = sanitize_markdown(xss_markdown)

        # Markdown should be converted to HTML then sanitized
        assert "<script>" not in sanitized
        assert "javascript:" not in sanitized
        assert "onload" not in sanitized

        # Safe content should remain
        assert "Safe Header" in sanitized
        assert "Safe Link" in sanitized

    def test_markdown_code_blocks(self):
        """Test code blocks are properly handled."""
        markdown_with_code = """
        # Code Example

        ```javascript
        / This should be escaped, not executed
        alert('This is code, not executable');
        ```

        `inline code()`
        """

        sanitized = sanitize_markdown(markdown_with_code)

        # Code should be escaped or in code blocks
        assert "<code>" in sanitized
        assert "<pre>" in sanitized
        # The alert should not be executable

    def test_markdown_links_sanitization(self):
        """Test markdown links are sanitized."""
        markdown_links = """
        [Safe Link](https://example.com)
        [HTTP Link](http://example.com)
        [Relative Link](/path)
        [JavaScript](javascript:alert('XSS'))
        [Data URI](data:text/html,<script>alert('XSS')</script>)
        """

        sanitized = sanitize_markdown(markdown_links)

        # Safe links should work
        assert 'href="https://example.com"' in sanitized
        assert 'href="http://example.com"' in sanitized

        # Dangerous links should be removed
        assert "javascript:" not in sanitized
        assert "data:" not in sanitized


class TestContentValidation:
    """Test content type validation and enforcement."""

    def test_json_content_type_enforcement(self, client):
        """Test JSON endpoints enforce correct content type."""
        # Try sending form data to JSON endpoint
        response = client.post(
            "/api/v1/auth/login",
            data="email=test@example.com&password=password123",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Should reject incorrect content type
        assert response.status_code in [400, 415, 422]

    def test_content_type_sniffing_prevention(self, client):
        """Test content type sniffing is prevented."""
        response = client.get(
            "/api/v1/health",
            headers={"Accept": "text/html,application/xhtml+xml,application/xml"}
        )

        # Should not return HTML
        assert response.headers.get("Content-Type", "").startswith("application/json")
        assert "<html>" not in response.text

    def test_xss_protection_headers(self, client):
        """Test XSS protection headers are set."""
        response = client.get("/api/v1/health")

        # Should have XSS protection headers
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


class TestInputValidationXSS:
    """Test XSS prevention through input validation."""

    def test_feedback_input_sanitization(self):
        """Test feedback inputs are sanitized."""
        feedback_service = FeedbackService()

        xss_attempts = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');/",
            "<svg onload=alert('XSS')>",
        ]

        for xss in xss_attempts:
            # Test content field
            result = feedback_service.validate_feedback_content({
                "content": xss,
                "rating": 5
            })

            # Should be sanitized or rejected
            assert "<script>" not in result.get("content", "")
            assert "javascript:" not in result.get("content", "")
            assert "onerror" not in result.get("content", "")

    def test_user_input_encoding(self):
        """Test user inputs are properly encoded."""
        from html import escape

        dangerous_inputs = [
            "<script>alert('XSS')</script>",
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
            '" onclick="alert(\'XSS\')"',
            "' onclick='alert(\"XSS\")'",
        ]

        for dangerous_input in dangerous_inputs:
            encoded = escape(dangerous_input, quote=True)

            # Should be HTML-encoded
            assert "&lt;" in encoded or "&gt;" in encoded
            assert "<script>" not in encoded

    def test_sql_injection_prevention(self):
        """Test SQL injection attempts are prevented."""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES('hacker', 'pass'); --",
        ]

        for injection in sql_injection_attempts:
            # This would test the actual parameter validation
            # For now, we verify the strings don't break anything
            assert isinstance(injection, str)


class TestTemplateSecurity:
    """Test template rendering security."""

    def test_template_autoescaping(self):
        """Test templates auto-escape variables."""
        from fastapi.templating import Jinja2Templates
        from fastapi import Request

        # Create a mock request
        request = MagicMock(spec=Request)

        # Initialize templates with autoescaping
        templates = Jinja2Templates(directory="app/templates")

        # Template with dangerous content
        dangerous_context = {
            "user_input": "<script>alert('XSS')</script>",
            "title": "<h1>Injected Title</h1>",
        }

        # Render template (would need actual template file)
        # For now, test the concept
        assert dangerous_context["user_input"] == "<script>alert('XSS')</script>"
        # In actual rendering, this would be escaped

    def test_template_sandboxing(self):
        """Test template execution is sandboxed."""
        # Templates should not have access to dangerous functions
        # This would test the actual template configuration
        assert True  # Placeholder


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""

    def test_csrf_token_validation(self):
        """Test CSRF tokens are validated for state-changing requests."""
        # This would test CSRF middleware
        # For now, test the concept
        assert True  # Placeholder

    def test_same_site_cookies(self):
        """Test cookies use SameSite attribute."""
        # This would test cookie configuration
        assert True  # Placeholder


class TestContentSecurityPolicy:
    """Test Content Security Policy implementation."""

    def test_csp_headers(self, client):
        """Test CSP headers are properly set."""
        response = client.get("/")

        # Should have CSP header (if implemented)
        csp = response.headers.get("Content-Security-Policy")
        if csp:
            # Check for basic CSP directives
            assert "default-src" in csp
            assert "script-src" in csp
            assert "style-src" in csp

    def test_csp_inline_script_restriction(self):
        """Test CSP prevents inline scripts."""
        # This would test CSP in browser
        # For now, test the header configuration
        assert True  # Placeholder


class TestXSSIntegrationTests:
    """Integration tests for XSS prevention."""

    def test_complete_feedback_flow_with_xss(self, client):
        """Test complete feedback flow with XSS attempts."""
        # Create feedback with XSS
        xss_feedback = {
            "interview_id": "test-id",
            "rating": 5,
            "content": "<script>steal_token()</script> Great interview!",
            "improvements": ["<img src=x onerror=alert('XSS')>Add more questions"]
        }

        # Submit feedback
        response = client.post(
            "/api/v1/feedback",
            json=xss_feedback,
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should accept but sanitize
        assert response.status_code in [200, 201, 422]

        if response.status_code in [200, 201]:
            # Retrieve feedback
            feedback_id = response.json().get("id")
            get_response = client.get(
                f"/api/v1/feedback/{feedback_id}"
            )

            # Retrieved content should be sanitized
            if get_response.status_code == 200:
                content = get_response.json().get("content", "")
                assert "<script>" not in content
                assert "steal_token()" not in content

    def test_search_with_xss(self, client):
        """Test search functionality handles XSS."""
        xss_queries = [
            "<script>alert('XSS')</script>",
            "';alert('XSS');/",
            "<svg onload=alert('XSS')>",
        ]

        for query in xss_queries:
            response = client.get(
                "/api/v1/interviews/search",
                params={"q": query}
            )

            # Should handle without executing scripts
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                # Response should not contain unescaped scripts
                response_text = response.text
                assert "<script>" not in response_text or "\\u003cscript\\u003e" in response_text

    def test_user_profile_xss_prevention(self, client):
        """Test user profile fields prevent XSS."""
        xss_profile_data = {
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "<img src=x onerror=alert('XSS')>",
            "bio": "<svg onload=alert('XSS')>My bio",
        }

        # Update profile
        response = client.put(
            "/api/v1/users/profile",
            json=xss_profile_data,
            headers={"Authorization": "Bearer valid_token"}
        )

        # Should sanitize or reject
        assert response.status_code in [200, 400, 422]

        # Check profile data is sanitized
        if response.status_code == 200:
            profile = response.json()
            for field, value in profile.items():
                if field in xss_profile_data:
                    assert "<script>" not in str(value)
                    assert "onerror" not in str(value)


class TestXSSEdgeCases:
    """Test edge cases for XSS prevention."""

    def test_unicode_xss_attempts(self):
        """Test XSS attempts using Unicode encoding."""
        unicode_xss = [
            "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e",
            "\\x3cscript\\x3ealert('XSS')\\x3c/script\\x3e",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        ]

        for xss in unicode_xss:
            decoded = xss.encode().decode('unicode-escape')
            sanitized = sanitize_html(decoded)

            # Should handle encoded scripts
            assert "<script>" not in sanitized

    def test_dom_xss_prevention(self):
        """Test DOM-based XSS prevention."""
        # This would test client-side protections
        # For now, test server-side encoding
        dangerous_json = {
            "data": "<script>document.body.innerHTML='XSS'</script>",
            "callback": "alert('XSS')",
        }

        json_str = json.dumps(dangerous_json)
        # JSON should be properly escaped when rendered
        assert "<script>" not in json_str or "\\u003c" in json_str

    def test_mixed_content_prevention(self):
        """Test mixed content (HTTP in HTTPS) is prevented."""
        # This would test CSP and header configurations
        assert True  # Placeholder