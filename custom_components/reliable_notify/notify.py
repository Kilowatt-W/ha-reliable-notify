"""Native Home Assistant notify entities for Reliable Notify routes.

Only a committed queue entry is acknowledged, never provider/device delivery.
Compatible with the modern notify.send_message entity action.
"""
from __future__ import annotations

import logging
import re

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def available_routes(routes):
    """Return stable unique aliases for safely addressable routes."""
    names = set(routes.get("recipients", {}))
    names.update(routes.get("groups", {}))
    names.update(routes.get("persons", {}))
    return sorted(name for name in names if SAFE_NAME.fullmatch(name))


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Register a modern entity for each named route."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [ReliableNotifyEntity(manager, name) for name in available_routes(manager.routes)]
    )


class ReliableNotifyEntity(NotifyEntity):
    """Send a message through the Reliable Notify durable queue."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_icon = "mdi:bell-check"

    def __init__(self, manager, route_name: str) -> None:
        self.manager = manager
        self.route_name = route_name
        self._attr_name = f"Reliable {route_name.replace('_', ' ')}"
        self._attr_unique_id = f"{manager.entry.entry_id}_route_{route_name}"

    @property
    def available(self) -> bool:
        return (
            not self.manager.stopping
            and self.route_name in set(available_routes(self.manager.routes))
        )

    async def async_send_message(
        self, message: str, title: str | None = None
    ) -> None:
        """Persist a notification; an exception means it was not queued."""
        if not self.available:
            raise ValueError(f"Reliable Notify route no longer exists: {self.route_name}")
        data = {"recipients": [self.route_name], "message": message}
        if title is not None:
            data["title"] = title
        await self.manager.enqueue(data)
