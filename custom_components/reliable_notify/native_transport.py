"""Native HTTPS transports for ntfy, Gotify, and explicit outgoing webhooks.

Credentials remain in Home Assistant route configuration, never in SQLite
job payloads or diagnostics. All requests are POST with redirects disabled.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit, urlunsplit


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
    if action!="reliable_notify.webhook" and urlsplit(endpoint).query:
        raise ValueError("ntfy and Gotify base URLs must not include query parameters")
    if action=="reliable_notify.ntfy":
        if not TOPIC.fullmatch(str(data.get("topic",""))):
            raise ValueError("ntfy requires topic (letters, digits, dash, underscore)")
    elif action=="reliable_notify.gotify":
        if not data.get("token"):
            raise ValueError("Gotify requires an application token")
    if action=="reliable_notify.webhook" and "token" in data and not isinstance(data["token"],str):
        raise ValueError("webhook token must be string")
    return endpoint


# Per-message extras each native transport understands (None: any JSON fields).
NATIVE_EXTRAS={
    "reliable_notify.ntfy":frozenset(("click","attach","icon","tags","actions","filename")),
    "reliable_notify.gotify":frozenset(("click","image")),
    "reliable_notify.webhook":None,
}
NTFY_ACTIONS=("view","http")
PRIORITY_NTFY={"info":3,"warning":4,"critical":5}
PRIORITY_GOTIFY={"info":2,"warning":5,"critical":9}


def _plain_text(value,field,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
        raise ValueError(f"{field} must be text up to {limit} characters without line breaks")
    return value.strip()


def _link(value,field):
    text=_plain_text(value,field,2048)
    parts=urlsplit(text)
    if parts.scheme.lower() not in ("http","https") or not parts.netloc or " " in text:
        raise ValueError(f"{field} must be an http(s) URL")
    return text


def validate_native_extras(action,extra):
    """Check per-message extras (buttons, images, click links) for a native transport."""
    extra=dict(extra or {})
    allowed=NATIVE_EXTRAS[action]
    if allowed is None:
        try:
            if len(json.dumps(extra,allow_nan=False))>16384:
                raise ValueError("webhook data exceeds 16 KiB")
        except (TypeError,ValueError) as err:
            raise ValueError(f"webhook data must be JSON: {err}") from err
        return extra
    unknown=set(extra)-allowed
    if unknown:
        raise ValueError("unsupported fields for "+action+": "+", ".join(sorted(unknown)))
    clean={}
    for key in ("click","attach","icon","image"):
        if key in extra:
            clean[key]=_link(extra[key],key)
    if "filename" in extra:
        clean["filename"]=_plain_text(extra["filename"],"filename",255)
    if "tags" in extra:
        tags=[extra["tags"]] if isinstance(extra["tags"],str) else extra["tags"]
        if not isinstance(tags,list) or len(tags)>10:
            raise ValueError("tags must be a text or a list of up to 10 texts")
        clean["tags"]=[_plain_text(tag,"tag",64) for tag in tags]
    if "actions" in extra:
        buttons=extra["actions"]
        if not isinstance(buttons,list) or not 1<=len(buttons)<=3:
            raise ValueError("ntfy actions must be a list of 1 to 3 buttons")
        clean["actions"]=[]
        for button in buttons:
            if not isinstance(button,dict) or button.get("action","view") not in NTFY_ACTIONS:
                raise ValueError("ntfy button needs action view or http, label and url")
            item={"action":button.get("action","view"),
                  "label":_plain_text(button.get("label"),"button label",40),
                  "url":_link(button.get("url"),"button url")}
            if button.get("clear") is True:
                item["clear"]=True
            clean["actions"].append(item)
    return clean


def native_public_payload(action,config,data):
    """Return job fields containing no token/URL or other secrets."""
    endpoint=validate_native_route(action,config)
    if data and not isinstance(data,dict):
        raise ValueError("native message metadata must be an object")
    if data and any(k in data for k in (
        "token","base_url","allow_private","Authorization","authorization","headers")):
        raise ValueError("endpoint/authentication settings must be configured on recipient")
    return {"endpoint_hash":endpoint_hash(endpoint),"extra":validate_native_extras(action,data)}


def build_native_request(action,config,item,extra):
    """URL, headers and body of one native delivery (no I/O, testable)."""
    endpoint=validate_native_route(action,config)
    content=item["message"]
    if not isinstance(content,str) or len(content.encode("utf8"))>65536:
        raise ValueError("native notification exceeds 64 KiB")
    title=item.get("title") or "Reliable Notify"
    token=config.get("token")
    allowed=NATIVE_EXTRAS[action]
    if allowed is not None:  # jobs queued before 3.5 may carry fields that were ignored then
        extra={k:v for k,v in (extra or {}).items() if k in allowed}
    extra=validate_native_extras(action,extra)
    if action=="reliable_notify.ntfy":
        # JSON publishing to the base URL: UTF-8 titles and button labels are safe
        # (HTTP headers would need special encoding for umlauts).
        headers={"Content-Type":"application/json"}
        if token:
            headers["Authorization"]="Bearer "+str(token)
        body={"topic":str(config["topic"]),"message":content,"title":title,
              "priority":PRIORITY_NTFY.get(item["priority"],3),**extra}
        return endpoint,headers,body
    if action=="reliable_notify.gotify":
        body={"title":title,"message":content,"priority":PRIORITY_GOTIFY.get(item["priority"],2)}
        notification={}
        if "click" in extra:
            notification["click"]={"url":extra["click"]}
        if "image" in extra:
            notification["bigImageUrl"]=extra["image"]
        if notification:
            body["extras"]={"client::notification":notification}
        return endpoint+"/message",{"X-Gotify-Key":str(token)},body
    headers={"Content-Type":"application/json"}
    if token:
        headers["Authorization"]="Bearer "+str(token)
    body={"title":title,"message":content,"priority":item["priority"]}
    if extra:
        body["data"]=extra
    return endpoint,headers,body


async def async_deliver_native(hass,action,route,item):
    """Deliver one queued native message with HA's shared HTTP session."""
    import aiohttp
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    config=route.get("data",{})
    endpoint=validate_native_route(action,config)
    raw=json.loads(item.get("payload_json") or "{}")
    if raw.get("endpoint_hash")!=endpoint_hash(endpoint):
        raise ValueError("endpoint changed since enqueue; manually retry with updated destination")
    url,headers,body=build_native_request(action,config,item,raw.get("extra"))
    kwargs={"json":body}
    session=async_get_clientsession(hass)
    async with session.post(url,headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30),
                            allow_redirects=False,**kwargs) as response:
        if response.status < 200 or response.status >= 300:
            raise aiohttp.ClientResponseError(
                response.request_info,response.history,
                status=response.status,message="native provider rejected request")
