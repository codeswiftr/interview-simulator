"""Content sanitization service for XSS prevention.

Provides HTML and markdown sanitization using html-sanitizer library.
"""

import re

from html_sanitizer import Sanitizer

# Default safe tags for sanitization
_DEFAULT_TAGS = {
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

# Default sanitizer config
_SANITIZER_CONFIG = {
    "tags": _DEFAULT_TAGS,
    "attributes": {
        "a": ("href",),
    },
    "empty": {"br"},
    "separate": {"a", "p", "li"},
    "whitespace": {"br"},
    "keep_typographic_whitespace": False,
    "add_nofollow": True,
    "autolink": False,
    "element_postprocessors": [],
}

# Default sanitizer instance
_sanitizer = Sanitizer(_SANITIZER_CONFIG)


class HTMLContentSanitizer:
    """HTML content sanitizer with configurable rules."""

    def __init__(self, allowed_tags: list[str] | None = None):
        """Initialize sanitizer with allowed tags.

        Args:
            allowed_tags: List of HTML tags to allow. If None, uses safe defaults.
        """
        self.allowed_tags = allowed_tags or list(_DEFAULT_TAGS)
        self._sanitizer = _sanitizer

    def sanitize(self, content: str) -> str:
        """Sanitize HTML content, removing dangerous elements.

        Args:
            content: Raw HTML content to sanitize.

        Returns:
            Sanitized HTML content safe for display.
        """
        if not content:
            return ""
        return self._sanitizer.sanitize(content)

    def strip_all_tags(self, content: str) -> str:
        """Remove all HTML tags, returning plain text.

        Args:
            content: HTML content to strip.

        Returns:
            Plain text with all HTML tags removed.
        """
        if not content:
            return ""
        # Simple tag stripping
        return re.sub(r"<[^>]+>", "", content)


def sanitize_html(content: str) -> str:
    """Sanitize HTML content using default settings.

    Args:
        content: Raw HTML content to sanitize.

    Returns:
        Sanitized HTML content.
    """
    sanitizer = HTMLContentSanitizer()
    return sanitizer.sanitize(content)


def sanitize_markdown(content: str) -> str:
    """Sanitize markdown content.

    Currently just strips any embedded HTML in markdown.

    Args:
        content: Markdown content that may contain HTML.

    Returns:
        Markdown with any embedded HTML sanitized.
    """
    if not content:
        return ""
    # Sanitize any HTML that might be embedded in markdown
    return sanitize_html(content)


def validate_content_type(content_type: str, allowed_types: list[str] | None = None) -> bool:
    """Validate that content type is allowed.

    Args:
        content_type: MIME type to validate (e.g., "text/html").
        allowed_types: List of allowed MIME types. Defaults to safe types.

    Returns:
        True if content type is allowed, False otherwise.
    """
    if allowed_types is None:
        allowed_types = [
            "text/plain",
            "text/html",
            "text/markdown",
            "application/json",
        ]

    # Normalize content type (strip charset, etc.)
    base_type = content_type.split(";")[0].strip().lower()

    return base_type in [t.lower() for t in allowed_types]
