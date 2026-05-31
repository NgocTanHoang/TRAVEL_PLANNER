"""Utilities de sanitize secret va harden logging/telemetry."""
from __future__ import annotations

import logging
import re
from typing import Any

SENSITIVE_FIELD_MARKERS = (
    "authorization",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "bearer",
)
REDACTED = "[REDACTED]"

_JSON_STYLE_PATTERN = re.compile(
    r'(?P<key>"?(?:authorization|api[_-]?key|password|secret|token)"?\s*[:=]\s*["\']?)(?P<value>[^,"\'}\s]+)',
    re.IGNORECASE,
)
_BEARER_PATTERN = re.compile(r"(Bearer\s+)([A-Za-z0-9\-\._~\+/=]+)", re.IGNORECASE)


def sanitize_sensitive_string(value: str) -> str:
    """Mask common secret patterns in arbitrary text."""
    if not value:
        return value
    sanitized = _JSON_STYLE_PATTERN.sub(lambda match: f"{match.group('key')}{REDACTED}", value)
    sanitized = _BEARER_PATTERN.sub(lambda match: f"{match.group(1)}{REDACTED}", sanitized)
    return sanitized


def sanitize_sensitive_data(value: Any) -> Any:
    """Recursively redact sensitive dict fields and text payloads."""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in SENSITIVE_FIELD_MARKERS):
                sanitized[key] = REDACTED
            else:
                sanitized[key] = sanitize_sensitive_data(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_sensitive_data(item) for item in value)
    if isinstance(value, set):
        return {sanitize_sensitive_data(item) for item in value}
    if isinstance(value, str):
        return sanitize_sensitive_string(value)
    return value


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts secrets before records are emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitize_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_sensitive_data(record.args)
            else:
                record.args = tuple(sanitize_sensitive_data(arg) for arg in record.args)
        return True


def ensure_sensitive_log_filter(logger: logging.Logger) -> None:
    """Attach redaction filter once to the provided logger."""
    if any(isinstance(existing_filter, SensitiveDataFilter) for existing_filter in logger.filters):
        return
    logger.addFilter(SensitiveDataFilter())
