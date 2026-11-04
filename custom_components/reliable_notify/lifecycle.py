"""Companion App lifecycle identifiers.

Tags are deterministic, stable across HA restarts, and deliberately free of
message text or recipient data.
"""
import hashlib


def notification_tag(dedup_key):
    if not isinstance(dedup_key,str) or not dedup_key:
        raise ValueError("dedup_key required")
    return "rn_" + hashlib.sha256(dedup_key.encode("utf-8")).hexdigest()[:24]


def ensure_tag(payload, dedup_key):
    """Only modify Companion app's nested data dictionary."""
    result=dict(payload or {})
    data=dict(result.get("data") or {})
    data.setdefault("tag", notification_tag(dedup_key))
    result["data"]=data
    return result
