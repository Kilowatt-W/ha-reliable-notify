"""HMAC authenticated action tokens for Companion/Telegram acknowledgements."""
from __future__ import annotations
import hmac
import hashlib
import base64
import json
import time


def make_token(secret,key,action="ack"):
    if action not in ("ack","snooze","escalate"):
        raise ValueError("invalid action")
    if not key or len(key)>128:
        raise ValueError("invalid key")
    # stable opaque identifier; no incident details in push action.
    id_part=base64.urlsafe_b64encode(key.encode("utf8")).rstrip(b"=").decode("ascii")
    payload=f"RN2.{action}.{id_part}"
    mac=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()[:24]
    token=f"{payload}.{mac}"
    if len(token)>240:
        raise ValueError("dedup key too long for callback")
    return token


def read_token(secret,value):
    if not isinstance(value,str):
        return None
    parts=value.split(".")
    if len(parts)!=4 or parts[0]!="RN2" or parts[1] not in ("ack","snooze","escalate"):
        return None
    payload=".".join(parts[:3])
    expected=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()[:24]
    if not hmac.compare_digest(parts[3],expected):
        return None
    try:
        key=base64.urlsafe_b64decode(parts[2]+"="*(-len(parts[2])%4)).decode("utf8")
    except (ValueError,UnicodeDecodeError):
        return None
    if not key or len(key)>128:
        return None
    return (key,parts[1])
