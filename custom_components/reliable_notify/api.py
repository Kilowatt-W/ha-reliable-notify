"""Authenticated, opt-in outbound Reliable Notify REST interface for own apps.

Uses Home Assistant's existing Bearer/LLAT session authentication.
No separate API keys, bearer secrets or unrestricted cross-origin service.
"""
from __future__ import annotations
import asyncio
import time

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN

MAX_BYTES=16_384
DEFAULT_RATE=30


def validate_api_message(value, routes, allowed_routes):
    if not isinstance(value,dict):
        raise ValueError("JSON object required")
    if set(value)-{"message","title","recipients","priority","message_type",
                   "dedup_key","profile","archive","archive_days","ttl"}:
        raise ValueError("unsupported field")
    message=value.get("message")
    if not isinstance(message,str) or not message or len(message)>8192:
        raise ValueError("message required, max 8192 characters")
    names=value.get("recipients")
    if isinstance(names,str):names=[names]
    if not isinstance(names,list) or not 1<=len(names)<=20 or not all(isinstance(x,str) for x in names):
        raise ValueError("explicit recipients required")
    configured=set(routes.get("recipients",{})) | set(routes.get("persons",{})) | set(routes.get("groups",{}))
    if any(name not in configured for name in names):
        raise ValueError("unconfigured recipient")
    if any(name not in allowed_routes for name in names):
        raise ValueError("recipient not allowed through the external API")
    if value.get("priority","info") not in ("info","warning","critical"):
        raise ValueError("invalid priority")
    if value.get("priority")=="critical":
        raise ValueError("critical API messages require Home Assistant automation")
    if "archive_days" in value and (type(value["archive_days"]) is not int or not 0<=value["archive_days"]<=365):
        raise ValueError("invalid archive_days")
    if "ttl" in value and (type(value["ttl"]) is not int or not 0<=value["ttl"]<=86400):
        raise ValueError("invalid TTL")
    return {**value,"recipients":names}


class ReliableNotifyAPIView(HomeAssistantView):
    """External app endpoint, off by default and authenticated by HA."""

    url="/api/reliable_notify/v1/messages"
    name="api:reliable_notify:messages"
    requires_auth=True

    def __init__(self,hass):
        self.hass=hass
        self._rate={}
        self._lock=asyncio.Lock()

    async def post(self,request):
        manager=next(iter(self.hass.data.get(DOMAIN,{}).values()),None)
        if manager is None or manager.stopping:
            return web.json_response({"error":"unavailable"},status=503)
        options=manager.settings
        if not options.get("external_api_enabled",False):
            return web.json_response({"error":"disabled"},status=403)
        user=request.get("hass_user")
        if user is None or not user.is_admin:
            return web.json_response({"error":"administrator_required"},status=403)
        if request.content_length is not None and request.content_length>MAX_BYTES:
            return web.json_response({"error":"payload_too_large"},status=413)
        try:
            raw=await request.content.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:
                return web.json_response({"error":"payload_too_large"},status=413)
            data=await __import__("asyncio").to_thread(
                __import__("json").loads,raw.decode("utf8"))
            permitted=options.get("external_api_recipients",[])
            if not permitted:
                return web.json_response({"error":"no_allowed_recipients"},status=403)
            message=validate_api_message(data,manager.routes,set(permitted))
        except (ValueError,UnicodeDecodeError,TypeError):
            return web.json_response({"error":"invalid_payload"},status=400)
        now=time.monotonic()
        async with self._lock:
            # Per authenticated user; no IP-based restrictions needed.
            key=user.id
            window,used=self._rate.get(key,(now,0))
            if now-window>=60:
                window,used=now,0
            limit=min(60,max(1,int(options.get("external_api_rate",DEFAULT_RATE))))
            if used>=limit:
                return web.json_response({"error":"rate_limited"},status=429,
                                         headers={"Retry-After":str(max(1,int(60-now+window)))})
            self._rate[key]=(window,used+1)
            if len(self._rate)>1000:
                self._rate={k:v for k,v in self._rate.items() if now-v[0]<60}
        try:
            # Protect against mismatched profile overrides introducing extra recipients.
            if message.get("profile"):
                from .profiles import resolve_profile, DEFAULT
                expanded=resolve_profile(message,options.get("notification_profiles",DEFAULT))
                if expanded.get("priority")=="critical":
                    raise ValueError("critical API profile not allowed")
                if any(n not in permitted for n in expanded["recipients"]):
                    raise ValueError("profile selected forbidden recipient")
            await manager.enqueue(message)
        except (ValueError,OverflowError) as err:
            return web.json_response({"error":"queue_rejected","reason":type(err).__name__},status=422)
        return web.json_response({"status":"queued","receipt":"durable_queue","version":"1"},status=202)
