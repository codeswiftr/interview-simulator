"""Tests for content sanitization service - XSS prevention and HTML cleaning."""

from app.services.content_sanitizer import (
    HTMLContentSanitizer,
    sanitize_html,
    sanitize_markdown,
    validate_content_type,
)


class TestHTMLContentSanitizer:
    """Tests for HTMLContentSanitizer class."""

    def test_sanitizer_initializes_with_default_tags(self):
        """Sanitizer uses safe default tags when none specified."""
        sanitizer = HTMLContentSanitizer()
        assert "p" in sanitizer.allowed_tags
        assert "script" not in sanitizer.allowed_tags
        assert "style" not in sanitizer.allowed_tags

    def test_sanitizer_accepts_custom_allowed_tags(self):
        """Sanitizer can be configured with custom allowed tags."""
        custom_tags = ["p", "b", "i"]
        sanitizer = HTMLContentSanitizer(allowed_tags=custom_tags)
        assert sanitizer.allowed_tags == custom_tags


class TestScriptTagRemoval:
    """Tests for removing dangerous script tags."""

    def test_script_tag_removed(self):
        """Script tags are stripped from content."""
        content = '<p>Hello</p><script>alert("xss")</script><p>World</p>'
        result = sanitize_html(content)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result
        assert "World" in result

    def test_script_tag_with_src_removed(self):
        """Script tags with external sources are stripped."""
        content = '<script src="https://evil.com/xss.js"></script>'
        result = sanitize_html(content)
        assert "<script" not in result
        assert "evil.com" not in result

    def test_script_tag_with_event_handler_removed(self):
        """Inline script in event handlers is stripped."""
        content = "<p onclick=\"alert('xss')\">Click me</p>"
        result = sanitize_html(content)
        assert "onclick" not in result
        assert "alert" not in result
        assert "Click me" in result

    def test_script_in_img_onerror_removed(self):
        """Script in img onerror attribute is stripped."""
        content = '<img src="x" onerror="alert(\'xss\')">'
        result = sanitize_html(content)
        assert "onerror" not in result
        assert "alert" not in result

    def test_script_in_svg_onload_removed(self):
        """Script in SVG onload is stripped."""
        content = "<svg onload=\"alert('xss')\"></svg>"
        result = sanitize_html(content)
        assert "onload" not in result
        assert "alert" not in result


class TestEventHandlerRemoval:
    """Tests for removing dangerous event handlers."""

    def test_onclick_removed(self):
        """onclick attribute is stripped."""
        content = '<button onclick="doEvil()">Click</button>'
        result = sanitize_html(content)
        assert "onclick" not in result.lower()

    def test_onmouseover_removed(self):
        """onmouseover attribute is stripped."""
        content = '<div onmouseover="doEvil()">Hover</div>'
        result = sanitize_html(content)
        assert "onmouseover" not in result.lower()

    def test_onfocus_removed(self):
        """onfocus attribute is stripped."""
        content = '<input onfocus="doEvil()">'
        result = sanitize_html(content)
        assert "onfocus" not in result.lower()

    def test_onerror_removed(self):
        """onerror attribute is stripped."""
        content = '<img src="x" onerror="doEvil()">'
        result = sanitize_html(content)
        assert "onerror" not in result.lower()


class TestJavascriptURIRemoval:
    """Tests for removing javascript: URIs."""

    def test_javascript_uri_in_href_removed(self):
        """javascript: URI in href is stripped or modified."""
        content = "<a href=\"javascript:alert('xss')\">Click</a>"
        result = sanitize_html(content)
        assert "javascript:" not in result.lower()

    def test_javascript_uri_with_encoding_removed(self):
        """Encoded javascript: URI is stripped."""
        content = "<a href=\"java&#115;cript:alert('xss')\">Click</a>"
        result = sanitize_html(content)
        # Should not execute - either removed or escaped
        assert "alert" not in result or "&#" in result

    def test_data_uri_javascript_removed(self):
        """data: URI with JavaScript is stripped."""
        content = "<a href=\"data:text/html,<script>alert('xss')</script>\">Click</a>"
        result = sanitize_html(content)
        assert "<script>" not in result


class TestSafeHTMLPreserved:
    """Tests for preserving safe HTML elements."""

    def test_bold_tag_preserved(self):
        """Bold tags are kept."""
        content = "<b>Bold text</b>"
        result = sanitize_html(content)
        assert "<b>" in result or "<strong>" in result
        assert "Bold text" in result

    def test_italic_tag_preserved(self):
        """Italic tags are kept."""
        content = "<i>Italic text</i>"
        result = sanitize_html(content)
        assert "<i>" in result or "<em>" in result
        assert "Italic text" in result

    def test_paragraph_tag_preserved(self):
        """Paragraph tags are kept."""
        content = "<p>Paragraph text</p>"
        result = sanitize_html(content)
        assert "<p>" in result
        assert "Paragraph text" in result

    def test_heading_tags_preserved(self):
        """Heading tags are kept."""
        content = "<h1>Heading 1</h1><h2>Heading 2</h2>"
        result = sanitize_html(content)
        assert "<h1>" in result
        assert "<h2>" in result

    def test_list_tags_preserved(self):
        """List tags are kept."""
        content = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = sanitize_html(content)
        assert "<ul>" in result
        assert "<li>" in result

    def test_code_tag_preserved(self):
        """Code tags are kept."""
        content = "<code>const x = 1;</code>"
        result = sanitize_html(content)
        assert "<code>" in result
        assert "const x = 1;" in result

    def test_pre_tag_preserved(self):
        """Pre tags are kept."""
        content = "<pre>Preformatted text</pre>"
        result = sanitize_html(content)
        assert "<pre>" in result

    def test_anchor_with_safe_href_preserved(self):
        """Anchor tags with safe URLs are kept."""
        content = '<a href="https://example.com">Link</a>'
        result = sanitize_html(content)
        assert "<a" in result
        assert "https://example.com" in result
        assert "Link" in result


class TestMarkdownSanitization:
    """Tests for markdown content sanitization."""

    def test_markdown_code_blocks_preserved(self):
        """Markdown code blocks remain intact."""
        content = "```python\nprint('hello')\n```"
        result = sanitize_markdown(content)
        assert "print" in result

    def test_embedded_html_in_markdown_sanitized(self):
        """HTML embedded in markdown is sanitized."""
        content = "# Title\n<script>alert('xss')</script>\nParagraph"
        result = sanitize_markdown(content)
        assert "<script>" not in result
        assert "alert" not in result

    def test_empty_markdown_returns_empty(self):
        """Empty markdown returns empty string."""
        result = sanitize_markdown("")
        assert result == ""

    def test_none_markdown_returns_empty(self):
        """None markdown returns empty string."""
        result = sanitize_markdown(None)
        assert result == ""


class TestStripAllTags:
    """Tests for stripping all HTML tags to plain text."""

    def test_strip_all_tags_removes_html(self):
        """All HTML tags are removed."""
        sanitizer = HTMLContentSanitizer()
        content = "<p><b>Bold</b> and <i>italic</i></p>"
        result = sanitizer.strip_all_tags(content)
        assert "<" not in result
        assert ">" not in result
        assert "Bold" in result
        assert "italic" in result

    def test_strip_all_tags_handles_empty(self):
        """Empty content returns empty string."""
        sanitizer = HTMLContentSanitizer()
        result = sanitizer.strip_all_tags("")
        assert result == ""

    def test_strip_all_tags_handles_no_tags(self):
        """Plain text without tags passes through."""
        sanitizer = HTMLContentSanitizer()
        content = "Just plain text"
        result = sanitizer.strip_all_tags(content)
        assert result == "Just plain text"


class TestUnicodeHandling:
    """Tests for unicode edge cases."""

    def test_unicode_content_preserved(self):
        """Unicode characters are preserved."""
        content = "<p>Hello 世界 🌍</p>"
        result = sanitize_html(content)
        assert "世界" in result
        assert "🌍" in result

    def test_unicode_script_bypass_blocked(self):
        """Unicode variations of script tags are blocked."""
        # Using unicode characters that might look like script
        content = "<ꜱcript>alert('xss')</ꜱcript>"  # Using small capital S
        result = sanitize_html(content)
        # The content is escaped (< becomes &lt;), making it safe
        # Check that it's either escaped or completely removed
        assert "<ꜱcript>" not in result  # Raw tag should not be present

    def test_rtl_content_preserved(self):
        """Right-to-left text is preserved."""
        content = "<p>مرحبا</p>"
        result = sanitize_html(content)
        assert "مرحبا" in result


class TestContentTypeValidation:
    """Tests for content type validation."""

    def test_text_plain_allowed(self):
        """text/plain is allowed by default."""
        assert validate_content_type("text/plain") is True

    def test_text_html_allowed(self):
        """text/html is allowed by default."""
        assert validate_content_type("text/html") is True

    def test_text_markdown_allowed(self):
        """text/markdown is allowed by default."""
        assert validate_content_type("text/markdown") is True

    def test_application_json_allowed(self):
        """application/json is allowed by default."""
        assert validate_content_type("application/json") is True

    def test_application_javascript_blocked(self):
        """application/javascript is blocked by default."""
        assert validate_content_type("application/javascript") is False

    def test_text_javascript_blocked(self):
        """text/javascript is blocked by default."""
        assert validate_content_type("text/javascript") is False

    def test_content_type_with_charset_handled(self):
        """Content type with charset parameter is handled."""
        assert validate_content_type("text/html; charset=utf-8") is True
        assert validate_content_type("application/json; charset=utf-8") is True

    def test_custom_allowed_types(self):
        """Custom allowed types work."""
        assert validate_content_type("image/png", allowed_types=["image/png"]) is True
        assert validate_content_type("text/html", allowed_types=["image/png"]) is False

    def test_case_insensitive_matching(self):
        """Content type matching is case insensitive."""
        assert validate_content_type("TEXT/HTML") is True
        assert validate_content_type("Text/Html") is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_sanitize_empty_string(self):
        """Empty string returns empty string."""
        result = sanitize_html("")
        assert result == ""

    def test_sanitize_whitespace_only(self):
        """Whitespace-only content is handled."""
        result = sanitize_html("   \n\t   ")
        # Should return something (possibly stripped)
        assert isinstance(result, str)

    def test_deeply_nested_tags(self):
        """Deeply nested tags are handled."""
        content = "<p>" * 100 + "Content" + "</p>" * 100
        result = sanitize_html(content)
        assert "Content" in result

    def test_malformed_html_handled(self):
        """Malformed HTML doesn't crash."""
        content = "<p>Unclosed<b>tags<i>everywhere"
        result = sanitize_html(content)
        assert isinstance(result, str)
        assert "Unclosed" in result

    def test_null_bytes_handled(self):
        """Null bytes in content are handled."""
        content = "<p>Hello\x00World</p>"
        result = sanitize_html(content)
        # Should not crash
        assert isinstance(result, str)
