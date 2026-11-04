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


def classify_error(err: Exception) -> Failure:
    """Categorize provider failures without persisting sensitive error text."""
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
    if code in (408,425) or (code is not None and 500<=code<=599):
        return Failure("provider_unavailable",True,retry_after)
    if isinstance(err, (TimeoutError, ConnectionError, OSError)):
        return Failure("network",True,retry_after)
    if any(x in detail for x in (
        "timed out","connection reset","network unreachable",
        "service unavailable","temporary failure")):
        return Failure("network",True,retry_after)
    return Failure("unknown",True,retry_after)


DEFAULT_POLICIES = {
    "info": {"max_attempts": 8, "base_seconds": 30, "max_delay": 1800},
    "warning": {"max_attempts": 20, "base_seconds": 30, "max_delay": 3600},
    "critical": {"max_attempts": 0, "base_seconds": 15, "max_delay": 3600},
}


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
        for key, min_value, max_value in (("max_attempts", 0, 10000), ("base_seconds", 1, 3600), ("max_delay", 1, 86400)):
            value = policy[key]
            if isinstance(value, bool) or not isinstance(value, int) or not min_value <= value <= max_value:
                raise ValueError(f"{priority}.{key} out of range")
        if policy["base_seconds"] > policy["max_delay"]:
            raise ValueError(f"{priority}: base_seconds exceeds max_delay")
        result[priority] = policy
    return result