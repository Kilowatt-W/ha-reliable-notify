"""Native HTTPS transports for ntfy, Gotify, and explicit outgoing webhooks.

Credentials remain in Home Assistant route configuration, never in SQLite
job payloads or diagnostics. All requests are POST with redirects disabled.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit, urlunsplit, quote


NATIVE_ACTIONS=("reliable_notify.ntfy","reliable_notify.gotify","reliable_notify.webhook")
TOPIC=re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def checked_endpoint(value, allow_private=False):
    if not isinstance(value,str) or len(value)>2048:
        raise ValueError("HTTPS endpoint URL is required")
    url=urlsplit(value)
    if url.scheme.lower()!="https" or not url.hostname or url.username or url.password:
        raise ValueError("native endpoints require https and no embedded credentials")
    if url.fragment:
        raise ValueError("endpoint fragments are not supported")
    if url.hostname.lower() in ("localhost","localhost.localdomain") and not allow_private:
        raise ValueError("local endpoints require allow_private=true")
    try:
        ip=ipaddress.ip_address(url.hostname)
        if not ip.is_global and not allow_private:
            raise ValueError("nonpublic endpoint requires allow_private=true")
    except ValueError as exc:
        if "nonpublic endpoint" in str(exc):
            raise
    return urlunsplit((url.scheme,url.netloc,url.path.rstrip("/"),url.query,""))


def endpoint_hash(base_url):
    return hashlib.sha256(base_url.encode("utf8")).hexdigest()[:32]


def validate_native_route(action,data):
    if action not in NATIVE_ACTIONS:
        raise ValueError("unsupported native transport")
    if not isinstance(data,dict):
        raise ValueError("transport settings must be mapping")
    endpoint=checked_endpoint(data.get("base_url"),data.get("allow_private",False) is True)
    if action=="reliable_notify.ntfy":
        if not TOPIC.fullmatch(str(data.get("topic",""))):
            raise ValueError("ntfy requires topic (letters, digits, dash, underscore)")
    elif action=="reliable_notify.gotify":
        if not data.get("token"):
            raise ValueError("Gotify requires an application token")
    if action=="reliable_notify.webhook" and "token" in data and not isinstance(data["token"],str):
        raise ValueError("webhook token must be string")
    return endpoint


def native_public_payload(action,config,data):
    """Return job fields containing no token/URL or other secrets."""
    endpoint=validate_native_route(action,config)
    if data and not isinstance(data,dict):
        raise ValueError("native message metadata must be an object")
    if data and any(k in data for k in (
        "token","base_url","allow_private","Authorization","authorization","headers")):
        raise ValueError("endpoint/authentication settings must be configured on recipient")
    return {"endpoint_hash":endpoint_hash(endpoint),"extra":data or {}}


async def async_deliver_native(hass,action,route,item):
    """Deliver one queued native message with HA's shared HTTP session."""
    import aiohttp
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    config=route.get("data",{})
    endpoint=validate_native_route(action,config)
    raw=json.loads(item.get("payload_json") or "{}")
    if raw.get("endpoint_hash")!=endpoint_hash(endpoint):
        raise ValueError("endpoint changed since enqueue; manually retry with updated destination")
    content=item["message"]
    if not isinstance(content,str) or len(content.encode("utf8"))>65536:
        raise ValueError("native notification exceeds 64 KiB")
    token=config.get("token")
    headers={}
    if action=="reliable_notify.ntfy":
        url=endpoint+"/"+quote(str(config["topic"]),safe="")
        headers={"Title":item.get("title") or "Reliable Notify",
                 "Priority":str({"info":3,"warning":4,"critical":5}.get(item["priority"],3))}
        if token:headers["Authorization"]="Bearer "+str(token)
        kwargs={"data":content.encode("utf8")}
    elif action=="reliable_notify.gotify":
        url=endpoint+"/message"
        headers={"X-Gotify-Key":str(token)}
        kwargs={"json":{"title":item.get("title") or "Reliable Notify",
                        "message":content,
                        "priority":{"info":2,"warning":5,"critical":9}.get(item["priority"],2)}}
    else:
        url=endpoint
        headers={"Content-Type":"application/json"}
        if token:headers["Authorization"]="Bearer "+str(token)
        kwargs={"json":{"title":item.get("title") or "Reliable Notify",
                        "message":content,"priority":item["priority"]}}
    session=async_get_clientsession(hass)
    async with session.post(url,headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30),
                            allow_redirects=False,**kwargs) as response:
        if response.status < 200 or response.status >= 300:
            raise aiohttp.ClientResponseError(
                response.request_info,response.history,
                status=response.status,message="native provider rejected request")
