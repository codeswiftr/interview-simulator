"""Logging utilities for safe, privacy-preserving log output."""

import re


def mask_email(email: str) -> str:
    """Mask an email address for safe inclusion in log output.

    Replaces the local part (before @) and the domain label (before the TLD)
    with asterisks, preserving the first character of each segment so that
    logs remain useful for debugging without leaking PII.

    Examples:
        "user@example.com"       -> "u***@e***.com"
        "alice.bob@company.org"  -> "a***@c***.org"
        "a@b.co"                 -> "a***@b***.co"
        "invalid-email"          -> "***" (no @ found)

    Args:
        email: The raw email address string to mask.

    Returns:
        Masked email string safe for log output.
    """
    if not isinstance(email, str) or "@" not in email:
        return "***"

    try:
        local, domain = email.rsplit("@", 1)
    except ValueError:
        return "***"

    # Mask local part: keep first character, replace rest with ***
    masked_local = (local[0] if local else "*") + "***"

    # Mask domain: keep first character of the domain label, replace rest with ***
    # e.g. "example.com" -> "e***.com"
    dot_idx = domain.find(".")
    if dot_idx > 0:
        domain_label = domain[:dot_idx]
        tld = domain[dot_idx:]  # includes the leading dot, e.g. ".com"
        masked_domain = (domain_label[0] if domain_label else "*") + "***" + tld
    else:
        # No dot found — mask the whole domain
        masked_domain = (domain[0] if domain else "*") + "***"

    return f"{masked_local}@{masked_domain}"


# Pre-compiled pattern for bulk masking of emails embedded in longer strings
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def mask_emails_in_text(text: str) -> str:
    """Replace all email addresses found in a string with masked versions.

    Useful for sanitising exception messages or log records that may contain
    raw email addresses from user input.

    Args:
        text: Arbitrary text that may contain one or more email addresses.

    Returns:
        Text with all email addresses replaced by masked equivalents.
    """
    return _EMAIL_PATTERN.sub(lambda m: mask_email(m.group(0)), text)
