"""Optional compatibility services notify.reliable_<route> for old automations.

Modern Home Assistant users should use notify.send_message and notify
entities; classic services cannot be expected to remain supported forever.
"""
from __future__ import annotations

import re

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .notify import available_routes

NOTIFY_DOMAIN = "notify"
COMPAT_PREFIX = "reliable_"
SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("data"): dict,
    },
    extra=vol.PREVENT_EXTRA,
)
EXTRAS = frozenset((
    "priority", "message_type", "archive", "archive_days",
    "dedup_key", "strategy", "ttl", "test_mode", "only_if",
    "acknowledgement",
))


async def async_register_compat(hass: HomeAssistant, manager) -> list[str]:
    """Register only nonconflicting service names; return owned registrations."""
    registered = []
    if not manager.settings.get("legacy_notify_services", True):
        return registered

    for route in available_routes(manager.routes):
        service = COMPAT_PREFIX + route
        if hass.services.has_service(NOTIFY_DOMAIN, service):
            # Never overwrite another integration's service.
            continue

        async def send(call: ServiceCall, route_name=route):
            opts = dict(call.data.get("data") or {})
            request = {
                "recipients": [route_name],
                "message": call.data["message"],
            }
            if "title" in call.data:
                request["title"] = call.data["title"]
            for key in list(opts):
                if key in EXTRAS:
                    request[key] = opts.pop(key)
            if opts:
                request["data"] = opts
            await manager.enqueue(request)

        hass.services.async_register(
            NOTIFY_DOMAIN, service, send, schema=SCHEMA
        )
        registered.append(service)
    return registered


def async_unregister_compat(hass: HomeAssistant, services: list[str]) -> None:
    for service in services:
        if hass.services.has_service(NOTIFY_DOMAIN, service):
            hass.services.async_remove(NOTIFY_DOMAIN, service)
