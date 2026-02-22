"""Pure unit tests for content sanitizer.

Tests HTMLContentSanitizer and module-level functions. No database required.
"""

import pytest

from app.services.content_sanitizer import (
    HTMLContentSanitizer,
    _DEFAULT_TAGS,
    sanitize_html,
    sanitize_markdown,
    validate_content_type,
)


class TestHTMLContentSanitizerInit:
    def test_default_tags(self):
        sanitizer = HTMLContentSanitizer()
        assert set(sanitizer.allowed_tags) == _DEFAULT_TAGS

    def test_custom_tags(self):
        sanitizer = HTMLContentSanitizer(allowed_tags=["p", "b"])
        assert sanitizer.allowed_tags == ["p", "b"]


class TestHTMLContentSanitizerSanitize:
    def test_empty_string(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer.sanitize("") == ""

    def test_none_returns_empty(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer.sanitize(None) == ""

    def test_plain_text_passthrough(self):
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.sanitize("Hello world")
        assert "Hello world" in result

    def test_safe_tags_preserved(self):
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.sanitize("<p><strong>Bold</strong></p>")
        assert "<strong>" in result or "<b>" in result
        assert "Bold" in result

    def test_script_tags_removed(self):
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.sanitize('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "alert" not in result or "<script>" not in result


class TestHTMLContentSanitizerStripAllTags:
    def test_empty_string(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer.strip_all_tags("") == ""

    def test_none_returns_empty(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer.strip_all_tags(None) == ""

    def test_strips_all_html(self):
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.strip_all_tags("<p><b>Hello</b> <em>world</em></p>")
        assert result == "Hello world"

    def test_strips_self_closing_tags(self):
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.strip_all_tags("Hello<br/>world")
        assert result == "Helloworld"

    def test_plain_text_unchanged(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer.strip_all_tags("no tags here") == "no tags here"


class TestSanitizeHtml:
    def test_empty_string(self):
        assert sanitize_html("") == ""

    def test_sanitizes_dangerous_html(self):
        result = sanitize_html('<img src=x onerror="alert(1)">')
        assert "onerror" not in result

    def test_preserves_safe_content(self):
        result = sanitize_html("<p>Safe content</p>")
        assert "Safe content" in result


class TestSanitizeMarkdown:
    def test_empty_string(self):
        assert sanitize_markdown("") == ""

    def test_none_returns_empty(self):
        assert sanitize_markdown(None) == ""

    def test_plain_markdown_passthrough(self):
        result = sanitize_markdown("# Heading\nSome text")
        assert "Heading" in result
        assert "Some text" in result

    def test_strips_embedded_html(self):
        result = sanitize_markdown('Text with <script>bad</script> content')
        assert "<script>" not in result


class TestValidateContentType:
    def test_allowed_text_plain(self):
        assert validate_content_type("text/plain") is True

    def test_allowed_text_html(self):
        assert validate_content_type("text/html") is True

    def test_allowed_text_markdown(self):
        assert validate_content_type("text/markdown") is True

    def test_allowed_application_json(self):
        assert validate_content_type("application/json") is True

    def test_rejects_unknown_type(self):
        assert validate_content_type("application/octet-stream") is False

    def test_strips_charset(self):
        assert validate_content_type("text/html; charset=utf-8") is True

    def test_case_insensitive(self):
        assert validate_content_type("TEXT/HTML") is True

    def test_custom_allowed_types(self):
        assert validate_content_type("image/png", ["image/png", "image/jpeg"]) is True

    def test_custom_rejects_unlisted(self):
        assert validate_content_type("text/html", ["image/png"]) is False
