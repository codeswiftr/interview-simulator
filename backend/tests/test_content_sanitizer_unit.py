"""Pure unit tests for content sanitizer service.

Covers HTMLContentSanitizer class, module-level functions, and XSS prevention.
No database or external APIs required.
"""

import pytest

from app.services.content_sanitizer import (
    _DEFAULT_TAGS,
    _SANITIZER_CONFIG,
    HTMLContentSanitizer,
    sanitize_html,
    sanitize_markdown,
    validate_content_type,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """Verify the module's public constants have the expected shape."""

    def test_default_tags_is_a_set(self):
        assert isinstance(_DEFAULT_TAGS, set)

    def test_default_tags_contains_expected_safe_tags(self):
        expected = {
            "a",
            "abbr",
            "b",
            "blockquote",
            "br",
            "code",
            "em",
            "h1",
            "h2",
            "h3",
            "i",
            "li",
            "ol",
            "p",
            "pre",
            "strong",
            "ul",
        }
        assert expected == _DEFAULT_TAGS

    def test_default_tags_excludes_dangerous_tags(self):
        dangerous = {"script", "style", "iframe", "object", "embed", "form", "input"}
        assert dangerous.isdisjoint(_DEFAULT_TAGS)

    def test_sanitizer_config_has_required_keys(self):
        required_keys = {
            "tags",
            "attributes",
            "empty",
            "separate",
            "whitespace",
            "keep_typographic_whitespace",
            "add_nofollow",
            "autolink",
            "element_postprocessors",
        }
        assert required_keys == set(_SANITIZER_CONFIG.keys())

    def test_sanitizer_config_add_nofollow_is_true(self):
        assert _SANITIZER_CONFIG["add_nofollow"] is True

    def test_sanitizer_config_autolink_is_false(self):
        assert _SANITIZER_CONFIG["autolink"] is False

    def test_sanitizer_config_anchor_allows_only_href(self):
        assert _SANITIZER_CONFIG["attributes"] == {"a": ("href",)}

    def test_sanitizer_config_br_is_empty_tag(self):
        assert "br" in _SANITIZER_CONFIG["empty"]


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.__init__
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerInit:
    """Initialization behavior of HTMLContentSanitizer."""

    def test_no_args_uses_default_tags(self):
        sanitizer = HTMLContentSanitizer()
        assert set(sanitizer.allowed_tags) == _DEFAULT_TAGS

    def test_no_args_allowed_tags_is_list(self):
        sanitizer = HTMLContentSanitizer()
        assert isinstance(sanitizer.allowed_tags, list)

    def test_custom_tags_stored_verbatim(self):
        tags = ["p", "b", "i"]
        sanitizer = HTMLContentSanitizer(allowed_tags=tags)
        assert sanitizer.allowed_tags == tags

    def test_custom_empty_list_falls_back_to_defaults(self):
        # allowed_tags=[] is falsy, so the `or list(_DEFAULT_TAGS)` branch fires
        # and the instance receives the full default tag set instead.
        sanitizer = HTMLContentSanitizer(allowed_tags=[])
        assert set(sanitizer.allowed_tags) == _DEFAULT_TAGS

    def test_none_arg_falls_back_to_defaults(self):
        sanitizer = HTMLContentSanitizer(allowed_tags=None)
        assert set(sanitizer.allowed_tags) == _DEFAULT_TAGS

    def test_sanitizer_instance_attached(self):
        sanitizer = HTMLContentSanitizer()
        assert sanitizer._sanitizer is not None


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — empty / falsy inputs
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerSanitizeEmptyInputs:
    """sanitize() with empty or falsy content."""

    def test_empty_string_returns_empty(self):
        assert HTMLContentSanitizer().sanitize("") == ""

    def test_none_returns_empty(self):
        assert HTMLContentSanitizer().sanitize(None) == ""  # type: ignore[arg-type]

    def test_zero_returns_empty(self):
        assert HTMLContentSanitizer().sanitize(0) == ""  # type: ignore[arg-type]

    def test_false_returns_empty(self):
        assert HTMLContentSanitizer().sanitize(False) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — safe HTML preserved
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerSanitizeSafeHtml:
    """sanitize() preserves allowed tags and content."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_plain_text_passes_through(self):
        result = self.s.sanitize("Hello world")
        assert "Hello world" in result

    def test_paragraph_tag_preserved(self):
        result = self.s.sanitize("<p>Paragraph</p>")
        assert "<p>" in result
        assert "Paragraph" in result

    def test_bold_tag_preserved(self):
        result = self.s.sanitize("<b>Bold</b>")
        assert "Bold" in result
        assert ("<b>" in result) or ("<strong>" in result)

    def test_strong_tag_preserved(self):
        result = self.s.sanitize("<strong>Strong</strong>")
        assert "Strong" in result
        assert "<strong>" in result

    def test_italic_tag_preserved(self):
        result = self.s.sanitize("<i>Italic</i>")
        assert "Italic" in result
        assert ("<i>" in result) or ("<em>" in result)

    def test_em_tag_preserved(self):
        result = self.s.sanitize("<em>Emphasis</em>")
        assert "Emphasis" in result
        assert "<em>" in result

    def test_h1_tag_preserved(self):
        result = self.s.sanitize("<h1>Heading 1</h1>")
        assert "<h1>" in result
        assert "Heading 1" in result

    def test_h2_tag_preserved(self):
        result = self.s.sanitize("<h2>Heading 2</h2>")
        assert "<h2>" in result

    def test_h3_tag_preserved(self):
        result = self.s.sanitize("<h3>Heading 3</h3>")
        assert "<h3>" in result

    def test_code_tag_preserved(self):
        result = self.s.sanitize("<code>x = 1</code>")
        assert "<code>" in result
        assert "x = 1" in result

    def test_pre_tag_preserved(self):
        result = self.s.sanitize("<pre>preformatted</pre>")
        assert "<pre>" in result

    def test_pre_code_nested_preserved(self):
        result = self.s.sanitize("<pre><code>def foo(): pass</code></pre>")
        assert "<pre>" in result
        assert "<code>" in result
        assert "def foo(): pass" in result

    def test_unordered_list_preserved(self):
        result = self.s.sanitize("<ul><li>One</li><li>Two</li></ul>")
        assert "<ul>" in result
        assert "<li>" in result

    def test_ordered_list_preserved(self):
        result = self.s.sanitize("<ol><li>First</li><li>Second</li></ol>")
        assert "<ol>" in result
        assert "<li>" in result

    def test_blockquote_preserved(self):
        result = self.s.sanitize("<blockquote>Quoted text</blockquote>")
        assert "<blockquote>" in result
        assert "Quoted text" in result

    def test_abbr_tag_preserved(self):
        result = self.s.sanitize("<abbr>HTML</abbr>")
        assert "HTML" in result

    def test_br_tag_preserved(self):
        result = self.s.sanitize("<p>line1<br>line2</p>")
        assert "line1" in result
        assert "line2" in result

    def test_anchor_with_https_href_preserved(self):
        result = self.s.sanitize('<a href="https://example.com">Link</a>')
        assert "<a" in result
        assert "https://example.com" in result
        assert "Link" in result

    def test_anchor_with_http_href_preserved(self):
        result = self.s.sanitize('<a href="http://example.com">Link</a>')
        assert "<a" in result
        assert "Link" in result

    def test_nofollow_added_to_anchor(self):
        """add_nofollow=True in config must insert rel=nofollow."""
        result = self.s.sanitize('<a href="https://example.com">Link</a>')
        assert 'rel="nofollow"' in result

    def test_anchor_attributes_other_than_href_stripped(self):
        """Only href is allowed on <a>; class/target must be removed."""
        result = self.s.sanitize('<a href="https://x.com" class="btn" target="_blank">Link</a>')
        assert "class=" not in result
        assert "target=" not in result
        assert "https://x.com" in result


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — dangerous tags removed
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerSanitizeDangerousTags:
    """sanitize() strips dangerous HTML elements."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_script_tag_removed(self):
        result = self.s.sanitize('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "alert" not in result

    def test_script_tag_with_src_removed(self):
        result = self.s.sanitize('<script src="https://evil.com/xss.js"></script>')
        assert "<script" not in result
        assert "evil.com" not in result

    def test_style_tag_removed(self):
        result = self.s.sanitize("<style>body { color: red }</style><p>text</p>")
        assert "<style>" not in result

    def test_iframe_removed(self):
        result = self.s.sanitize('<iframe src="http://evil.com"></iframe>')
        assert "iframe" not in result

    def test_object_tag_removed(self):
        result = self.s.sanitize('<object data="evil.swf"></object>')
        assert "object" not in result

    def test_embed_tag_removed(self):
        result = self.s.sanitize('<embed src="evil.swf">')
        assert "embed" not in result

    def test_form_tag_removed(self):
        result = self.s.sanitize('<form action="/steal"><input type="text"></form>')
        assert "form" not in result

    def test_meta_refresh_removed(self):
        result = self.s.sanitize('<meta http-equiv="refresh" content="0;url=evil.com">')
        assert "meta" not in result

    def test_svg_onload_removed(self):
        result = self.s.sanitize("<svg onload=\"alert('xss')\"></svg>")
        assert "onload" not in result
        assert "alert" not in result


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — event handler attributes stripped
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerEventHandlers:
    """sanitize() removes all on* event handler attributes."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_onclick_removed(self):
        result = self.s.sanitize('<p onclick="evil()">text</p>')
        assert "onclick" not in result
        assert "text" in result

    def test_onmouseover_removed(self):
        result = self.s.sanitize('<div onmouseover="evil()">hover</div>')
        assert "onmouseover" not in result

    def test_onfocus_removed(self):
        result = self.s.sanitize('<input onfocus="evil()">')
        assert "onfocus" not in result

    def test_onerror_removed(self):
        result = self.s.sanitize('<img src="x" onerror="evil()">')
        assert "onerror" not in result

    def test_onload_removed(self):
        result = self.s.sanitize('<body onload="evil()">text</body>')
        assert "onload" not in result

    def test_onkeypress_removed(self):
        result = self.s.sanitize('<input onkeypress="evil()">')
        assert "onkeypress" not in result


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — dangerous href schemes
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerDangerousHrefs:
    """sanitize() neutralizes dangerous href schemes."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_javascript_href_neutralized(self):
        result = self.s.sanitize("<a href=\"javascript:alert('xss')\">Click</a>")
        assert "javascript:" not in result.lower()

    def test_data_uri_in_href_neutralized(self):
        result = self.s.sanitize('<a href="data:text/html,<script>alert(1)</script>">Click</a>')
        assert "<script>" not in result

    def test_safe_https_href_survives(self):
        result = self.s.sanitize('<a href="https://safe.com">Link</a>')
        assert "https://safe.com" in result


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.sanitize — edge cases
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerSanitizeEdgeCases:
    """Boundary conditions for sanitize()."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_whitespace_only_returns_string(self):
        result = self.s.sanitize("   \n\t   ")
        assert isinstance(result, str)

    def test_malformed_unclosed_tags_handled(self):
        result = self.s.sanitize("<p>Unclosed<b>tags<i>everywhere")
        assert isinstance(result, str)
        assert "Unclosed" in result

    def test_deeply_nested_tags_handled(self):
        content = "<p>" * 50 + "Deep" + "</p>" * 50
        result = self.s.sanitize(content)
        assert "Deep" in result

    def test_null_bytes_do_not_raise(self):
        content = "<p>Hello\x00World</p>"
        result = self.s.sanitize(content)
        assert isinstance(result, str)

    def test_large_input_processed(self):
        content = "<p>" + "A" * 10_000 + "</p>"
        result = self.s.sanitize(content)
        assert len(result) > 0

    def test_unicode_preserved(self):
        result = self.s.sanitize("<p>Hello 世界 🌍</p>")
        assert "世界" in result
        assert "🌍" in result

    def test_rtl_text_preserved(self):
        result = self.s.sanitize("<p>مرحبا</p>")
        assert "مرحبا" in result

    def test_html_entities_handled(self):
        result = self.s.sanitize("<p>AT&amp;T</p>")
        assert isinstance(result, str)

    def test_ampersand_in_plain_text_escaped(self):
        result = self.s.sanitize("Hello & World")
        assert isinstance(result, str)
        # The library should produce safe output (escaped or stripped)
        assert "<script>" not in result


# ---------------------------------------------------------------------------
# HTMLContentSanitizer.strip_all_tags
# ---------------------------------------------------------------------------


class TestHTMLContentSanitizerStripAllTags:
    """strip_all_tags() removes every HTML tag, leaving plain text."""

    @pytest.fixture(autouse=True)
    def sanitizer(self):
        self.s = HTMLContentSanitizer()

    def test_empty_string_returns_empty(self):
        assert self.s.strip_all_tags("") == ""

    def test_none_returns_empty(self):
        assert self.s.strip_all_tags(None) == ""  # type: ignore[arg-type]

    def test_plain_text_unchanged(self):
        assert self.s.strip_all_tags("no tags here") == "no tags here"

    def test_paragraph_tag_removed(self):
        result = self.s.strip_all_tags("<p>Hello</p>")
        assert result == "Hello"

    def test_multiple_tags_removed(self):
        result = self.s.strip_all_tags("<p><b>Hello</b> <em>world</em></p>")
        assert result == "Hello world"

    def test_self_closing_br_removed(self):
        result = self.s.strip_all_tags("Hello<br/>world")
        assert result == "Helloworld"

    def test_self_closing_br_without_slash_removed(self):
        result = self.s.strip_all_tags("Hello<br>world")
        assert result == "Helloworld"

    def test_attributes_stripped_with_tag(self):
        result = self.s.strip_all_tags('<a href="https://example.com">Link</a>')
        assert result == "Link"
        assert "href" not in result

    def test_nested_tags_all_stripped(self):
        result = self.s.strip_all_tags("<div><p>Hello <b>World</b></p></div>")
        assert result == "Hello World"

    def test_tags_with_no_content_return_empty(self):
        result = self.s.strip_all_tags("<br><hr><img/>")
        assert result == ""

    def test_script_tag_content_remains_in_plain_text(self):
        # strip_all_tags is a simple regex — it removes the tag but keeps inner text.
        # This is distinct from sanitize() which also removes the payload.
        result = self.s.strip_all_tags("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "</script>" not in result
        # Inner text is kept (regex only removes the tags)
        assert "alert(1)" in result


# ---------------------------------------------------------------------------
# sanitize_html module-level function
# ---------------------------------------------------------------------------


class TestSanitizeHtml:
    """Module-level sanitize_html() function."""

    def test_empty_string_returns_empty(self):
        assert sanitize_html("") == ""

    def test_safe_html_preserved(self):
        result = sanitize_html("<p>Safe content</p>")
        assert "Safe content" in result
        assert "<p>" in result

    def test_img_onerror_removed(self):
        result = sanitize_html('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result

    def test_script_tag_removed(self):
        result = sanitize_html('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "alert" not in result

    def test_iframe_removed(self):
        result = sanitize_html('<iframe src="http://evil.com"></iframe>')
        assert "iframe" not in result

    def test_delegates_to_html_content_sanitizer(self):
        """sanitize_html must produce the same result as HTMLContentSanitizer().sanitize()."""
        content = "<p><b>Test</b></p>"
        assert sanitize_html(content) == HTMLContentSanitizer().sanitize(content)


# ---------------------------------------------------------------------------
# sanitize_markdown module-level function
# ---------------------------------------------------------------------------


class TestSanitizeMarkdown:
    """Module-level sanitize_markdown() function."""

    def test_empty_string_returns_empty(self):
        assert sanitize_markdown("") == ""

    def test_none_returns_empty(self):
        assert sanitize_markdown(None) == ""  # type: ignore[arg-type]

    def test_plain_text_passes_through(self):
        result = sanitize_markdown("Just plain text")
        assert "Just plain text" in result

    def test_heading_text_preserved(self):
        result = sanitize_markdown("# Heading\nSome text")
        assert "Heading" in result
        assert "Some text" in result

    def test_embedded_script_stripped(self):
        result = sanitize_markdown("# Title\n<script>alert('xss')</script>\nParagraph")
        assert "<script>" not in result
        assert "alert" not in result

    def test_code_fence_text_preserved(self):
        result = sanitize_markdown("```python\nprint('hello')\n```")
        assert "print" in result

    def test_delegates_to_sanitize_html(self):
        """sanitize_markdown must produce the same output as sanitize_html for the same input."""
        content = "<p>markdown with <b>html</b></p>"
        assert sanitize_markdown(content) == sanitize_html(content)

    def test_inline_html_sanitized(self):
        result = sanitize_markdown("Text with <em>emphasis</em> here")
        assert "emphasis" in result

    def test_dangerous_inline_html_removed(self):
        result = sanitize_markdown("Text <iframe src='evil'></iframe> end")
        assert "iframe" not in result


# ---------------------------------------------------------------------------
# validate_content_type
# ---------------------------------------------------------------------------


class TestValidateContentType:
    """validate_content_type() with default and custom allowed lists."""

    # Default allowed types
    def test_text_plain_allowed(self):
        assert validate_content_type("text/plain") is True

    def test_text_html_allowed(self):
        assert validate_content_type("text/html") is True

    def test_text_markdown_allowed(self):
        assert validate_content_type("text/markdown") is True

    def test_application_json_allowed(self):
        assert validate_content_type("application/json") is True

    # Default blocked types
    def test_application_octet_stream_blocked(self):
        assert validate_content_type("application/octet-stream") is False

    def test_application_javascript_blocked(self):
        assert validate_content_type("application/javascript") is False

    def test_text_javascript_blocked(self):
        assert validate_content_type("text/javascript") is False

    def test_image_png_blocked_by_default(self):
        assert validate_content_type("image/png") is False

    def test_unknown_type_blocked(self):
        assert validate_content_type("foo/bar") is False

    # Charset/parameter stripping
    def test_charset_parameter_stripped(self):
        assert validate_content_type("text/html; charset=utf-8") is True

    def test_json_with_charset_stripped(self):
        assert validate_content_type("application/json; charset=utf-8") is True

    def test_multiple_parameters_stripped(self):
        assert validate_content_type("text/html; charset=utf-8; boundary=something") is True

    # Case insensitivity
    def test_uppercase_allowed(self):
        assert validate_content_type("TEXT/HTML") is True

    def test_mixed_case_allowed(self):
        assert validate_content_type("Text/Html") is True

    def test_uppercase_json_allowed(self):
        assert validate_content_type("APPLICATION/JSON") is True

    # Custom allowed_types list
    def test_custom_list_allows_listed_type(self):
        assert validate_content_type("image/png", ["image/png", "image/jpeg"]) is True

    def test_custom_list_blocks_unlisted_type(self):
        assert validate_content_type("text/html", ["image/png"]) is False

    def test_custom_list_case_insensitive(self):
        assert validate_content_type("IMAGE/PNG", ["image/png"]) is True

    def test_custom_list_with_charset(self):
        assert validate_content_type("image/png; charset=utf-8", ["image/png"]) is True

    def test_empty_string_blocked(self):
        assert validate_content_type("") is False

    def test_whitespace_only_blocked(self):
        assert validate_content_type("   ") is False

    def test_empty_custom_list_blocks_everything(self):
        assert validate_content_type("text/html", []) is False

    def test_returns_bool_type(self):
        result = validate_content_type("text/plain")
        assert isinstance(result, bool)
