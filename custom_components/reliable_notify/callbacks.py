"""Compact HMAC-authenticated Companion and Telegram callback commands.

Telegram callback_data is limited to 64 bytes. No plaintext incident key
or credentials are embedded in a notification button.
"""
from __future__ import annotations
import hmac
import hashlib


def action_id(key):
    if not isinstance(key,str) or not key:
        raise ValueError("invalid acknowledgement key")
    return hashlib.sha256(key.encode("utf8")).hexdigest()[:16]


def make_token(secret,key,action="ack"):
    if action not in ("ack","snooze","escalate"):
        raise ValueError("invalid action")
    identity=action_id(key)
    payload=f"RN2.{action}.{identity}"
    digest=hmac.new(secret.encode("ascii"),payload.encode("ascii"),hashlib.sha256).hexdigest()[:20]
    token=f"{payload}.{digest}"
    if len(token)>64:
        raise ValueError("callback token exceeds Telegram limits")
    return token


def read_token(secret,value):
    if not isinstance(value,str) or len(value)>64:
        return None
    parts=value.split(".")
    if len(parts)!=4 or parts[0]!="RN2" or parts[1] not in ("ack","snooze","escalate"):
        return None
    if len(parts[2])!=16 or any(c not in "0123456789abcdef" for c in parts[2]):
        return None
    payload=".".join(parts[:3])
    expected=hmac.new(secret.encode("ascii"),payload.encode("ascii"),hashlib.sha256).hexdigest()[:20]
    if not hmac.compare_digest(parts[3],expected):
        return None
    return (parts[2],parts[1])
