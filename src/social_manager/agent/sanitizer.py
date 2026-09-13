from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlparse

# Patterns used to defang high-risk prompt injection and role hijacking phrases
PROMPT_OVERRIDE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?i)\b(ignore\s+(all\s+)?previous\s+instructions?)\b"),
        "[DEFANGED_PROMPT_OVERRIDE]",
    ),
    (
        re.compile(r"(?i)\b(disregard\s+(all\s+)?prior\s+instructions?)\b"),
        "[DEFANGED_PROMPT_OVERRIDE]",
    ),
    (
        re.compile(r"(?i)\b(system\s*(override|directive|prompt|message)?\s*:)"),
        "[DEFANGED_SYSTEM_PREFIX]:",
    ),
    (
        re.compile(r"(?i)\[\s*(system|system\s+override|instruction|admin)\s*\]"),
        "[DEFANGED_SYSTEM_TOKEN]",
    ),
    (
        re.compile(r"(?i)\b(you\s+are\s+now\s+(a|an|in|acting\s+as)\b)"),
        "[DEFANGED_ROLE_IMPERSONATION]",
    ),
    (
        re.compile(r"(?i)\b(human\s*:|assistant\s*:|developer\s*:)"),
        "[DEFANGED_ROLE_PREFIX]:",
    ),
    (
        re.compile(r"(?i)<\s*(system|instruction|prompt|developer)\s*>"),
        "&lt;DEFANGED_SYSTEM_TAG&gt;",
    ),
    (
        re.compile(r"(?i)<\s*/\s*(system|instruction|prompt|developer)\s*>"),
        "&lt;/DEFANGED_SYSTEM_TAG&gt;",
    ),
]

DISALLOWED_URL_SCHEMES = {
    "javascript",
    "data",
    "vbscript",
    "file",
    "blob",
    "about",
}


def sanitize_untrusted_text(text: str | None) -> str:
    """Neutralizes adversarial prompt injection tokens and normalizes control characters."""
    if not text:
        return ""

    cleaned = str(text)

    # Strip non-printable ASCII control characters (keeping standard newlines and tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Defang explicit prompt injection patterns
    for pattern, replacement in PROMPT_OVERRIDE_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)

    return cleaned.strip()


def wrap_untrusted_content(
    content: str | None,
    *,
    source_id: str | None = None,
    platform: str | None = None,
    content_type: str | None = None,
) -> str:
    """Encloses sanitized external text within explicit structural boundary tags."""
    sanitized = sanitize_untrusted_text(content)
    attrs: list[str] = []
    if platform:
        attrs.append(f'platform="{html.escape(str(platform), quote=True)}"')
    if content_type:
        attrs.append(f'type="{html.escape(str(content_type), quote=True)}"')
    if source_id:
        attrs.append(f'id="{html.escape(str(source_id), quote=True)}"')

    attr_str = f" {' '.join(attrs)}" if attrs else ""
    return f"<untrusted_external_content{attr_str}>\n{sanitized}\n</untrusted_external_content>"


def sanitize_external_item(item: dict[str, Any]) -> dict[str, Any]:
    """Returns a copy of an external content dict with text fields defanged and wrapped."""
    sanitized = dict(item)
    body = item.get("body")
    title = item.get("title")
    source_id = str(item.get("id") or item.get("external_id") or "") or None
    platform = str(item.get("platform") or "") or None
    content_type = str(item.get("content_type") or "") or None

    if body is not None:
        sanitized["body"] = wrap_untrusted_content(
            str(body),
            source_id=source_id,
            platform=platform,
            content_type=content_type,
        )
    if title is not None:
        sanitized["title"] = sanitize_untrusted_text(str(title))

    return sanitized


def is_safe_url(url: str | None) -> bool:
    """Validates that a URL uses a safe web scheme (http, https) and rejects injection schemes."""
    if not url:
        return True
    trimmed = str(url).strip()

    # Reject inline script patterns or HTML tags in URL
    lowered = trimmed.lower()
    for scheme in DISALLOWED_URL_SCHEMES:
        if lowered.startswith(f"{scheme}:") or f"{scheme}:" in lowered.replace(" ", ""):
            return False

    parsed = urlparse(trimmed)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return False

    return True


def detect_injection_indicators(text: str | None) -> list[str]:
    """Scans output text for suspicious leaked injection remnants or unsafe code execution."""
    if not text:
        return []

    indicators: list[str] = []
    lowered = text.lower()

    if "[defanged_prompt_override]" in lowered or "ignore all previous instructions" in lowered:
        indicators.append("contains_prompt_override_remnants")

    if "[defanged_system" in lowered or "[system override]" in lowered:
        indicators.append("contains_system_override_tokens")

    if any(f"{scheme}:" in lowered for scheme in DISALLOWED_URL_SCHEMES):
        indicators.append("contains_disallowed_url_scheme")

    return indicators
