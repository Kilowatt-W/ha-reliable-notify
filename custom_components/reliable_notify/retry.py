"""Provider error categories and centralized retry policies.

Never mistake a provider's acceptance for end-device delivery.
"""
from __future__ import annotations

import re
import ssl
import smtplib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    kind: str
    retryable: bool
    retry_after: int | None = None
    # False: waiting for HA (service not loaded yet) does not use up an attempt.
    counts: bool = True


class ServiceNotLoaded(Exception):
    """The HA action of a transport is not registered (yet), e.g. during HA start."""


class TargetUnavailable(Exception):
    """The notify entity is missing or unavailable; HA would silently skip it."""


# HA/voluptuous validation errors: the call can never succeed unchanged.
VALIDATION_ERRORS = frozenset(("Invalid", "MultipleInvalid", "ServiceValidationError",
                               "ServiceNotSupported", "ServiceNotFound"))
_REDACTIONS = (
    (re.compile(r"https?://\S+", re.I), "<url>"),
    (re.compile(r"\bbot\d+:[A-Za-z0-9_-]+"), "<secret>"),
    (re.compile(r"(?i)\b(token|password|passwd|secret|api[_-]?key|authorization)(['\"]?\s*[:=]\s*)\S+"), r"\1\2<secret>"),
    (re.compile(r"\b[A-Za-z0-9_-]{32,}\b"), "<secret>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"-?\b\d{6,}\b"), "<id>"),
)


def sanitize_error(err: Exception, limit: int = 240) -> str:
    """Exception class and message with URLs, tokens, e-mails and IDs masked.

    Gives admins the reason of a failure without storing credentials or
    chat/phone identifiers. HA translation keys are kept when present.
    """
    text = " ".join(str(err).split())
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    key = getattr(err, "translation_key", None)
    name = type(err).__name__
    detail = f"{name}: {text}" if text else name
    if isinstance(key, str) and key and key not in detail:
        detail += f" ({key})"
    return detail[:limit]


def classify_error(err: Exception) -> Failure:
    """Categorize provider failures without persisting sensitive error text."""
    names = {cls.__name__ for cls in type(err).__mro__}
    if "ServiceNotLoaded" in names:
        return Failure("service_not_loaded", True, 60, counts=False)
    if "TargetUnavailable" in names:
        return Failure("target_unavailable", True)
    if names & VALIDATION_ERRORS:
        return Failure("invalid_payload", False)
    if isinstance(err, ssl.SSLCertVerificationError):
        return Failure("tls_certificate", False)
    if isinstance(err, smtplib.SMTPAuthenticationError):
        return Failure("authentication", False)
    if isinstance(err, smtplib.SMTPRecipientsRefused):
        return Failure("invalid_recipient", False)
    if isinstance(err, smtplib.SMTPResponseException):
        code=int(err.smtp_code)
        if code in (530, 534, 535):
            return Failure("authentication",False)
        if 400<=code<500:
            return Failure("provider_unavailable",True)
        if code in (550,551,553):
            return Failure("invalid_recipient",False)
        return Failure("invalid_payload",False)
    if isinstance(err, (ValueError, TypeError, KeyError)):
        return Failure("invalid_payload",False)

    detail=str(err).lower()
    if any(x in detail for x in (
        "certificate verify failed","self signed certificate",
        "unknown ca","hostname mismatch")):
        return Failure("tls_certificate",False)

    code=getattr(err,"status",None) or getattr(err,"status_code",None)
    try:
        code=int(code)
    except (TypeError,ValueError):
        code=None

    retry_after=None
    headers=getattr(err,"headers",None)
    if headers is not None:
        raw=headers.get("Retry-After") or headers.get("retry-after")
        if raw is not None:
            try:
                retry_after=int(raw)
            except (TypeError,ValueError):
                try:
                    deadline=parsedate_to_datetime(raw)
                    retry_after=int((deadline-datetime.now(timezone.utc)).total_seconds())
                except (TypeError,ValueError,OverflowError):
                    pass
    if retry_after is None:
        match=re.search(r"retry.after\D{0,8}(\d+)",detail)
        if match:retry_after=int(match.group(1))
    if retry_after is not None:
        retry_after=max(1,min(86400,retry_after))

    if code==429 or "too many requests" in detail or "flood control" in detail:
        return Failure("rate_limit",True,retry_after)
    if code in (401,403) or any(x in detail for x in (
        "unauthorized","forbidden","chat not found","invalid token")):
        return Failure("authentication",False)
    if code in (400,404,413,415,422) or any(x in detail for x in (
        "bad request","invalid chat id","unsupported file")):
        return Failure("invalid_payload",False)
    if code is not None and 300<=code<=399:
        return Failure("unexpected_redirect",False)
    if code in (408,425) or (code is not None and 500<=code<=599):
        return Failure("provider_unavailable",True,retry_after)
    if isinstance(err, (TimeoutError, ConnectionError, OSError)):
        return Failure("network",True,retry_after)
    if any(x in detail for x in (
        "timed out","connection reset","network unreachable",
        "service unavailable","temporary failure")):
        return Failure("network",True,retry_after)
    return Failure("unknown",True,retry_after)


# max_attempts 0 = unlimited; max_hours = give up after this long in a failing state
# (0 = never). A time limit survives longer outages better than an attempt count.
DEFAULT_POLICIES = {
    "info": {"max_attempts": 0, "base_seconds": 30, "max_delay": 1800, "max_hours": 6},
    "warning": {"max_attempts": 0, "base_seconds": 30, "max_delay": 3600, "max_hours": 24},
    "critical": {"max_attempts": 0, "base_seconds": 15, "max_delay": 3600, "max_hours": 0},
}
# Defaults up to 3.3.x. Stored policies identical to them were never customised
# and move to the new time-based defaults.
LEGACY_DEFAULTS = {
    "info": {"max_attempts": 8, "base_seconds": 30, "max_delay": 1800},
    "warning": {"max_attempts": 20, "base_seconds": 30, "max_delay": 3600},
}


def migrate_policies(raw):
    """Replace untouched pre-3.4 defaults by the current defaults."""
    if not isinstance(raw, dict):
        return raw
    migrated = dict(raw)
    for priority, old in LEGACY_DEFAULTS.items():
        if migrated.get(priority) == old:
            migrated[priority] = dict(DEFAULT_POLICIES[priority])
    return migrated


def validate_policies(raw):
    if not isinstance(raw, dict):
        raise ValueError("retry policies must be an object")
    result = {}
    for priority, default in DEFAULT_POLICIES.items():
        custom = raw.get(priority, {})
        if not isinstance(custom, dict):
            raise ValueError(f"{priority} policy must be an object")
        if set(custom) - set(default):
            raise ValueError(f"unknown policy keys for {priority}")
        policy = {**default, **custom}
        for key, min_value, max_value in (("max_attempts", 0, 10000), ("base_seconds", 1, 3600),
                                          ("max_delay", 1, 86400), ("max_hours", 0, 720)):
            value = policy[key]
            if isinstance(value, bool) or not isinstance(value, int) or not min_value <= value <= max_value:
                raise ValueError(f"{priority}.{key} out of range")
        if policy["base_seconds"] > policy["max_delay"]:
            raise ValueError(f"{priority}: base_seconds exceeds max_delay")
        result[priority] = policy
    return result