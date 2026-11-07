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
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .routing import display_name

_LOGGER = logging.getLogger(__name__)
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def entity_name(routes, route_name):
    """Friendly name: the configured display name, else the historic alias-based name."""
    label = display_name(routes, route_name)
    return label if label != route_name else f"Reliable {route_name.replace('_', ' ')}"


def entity_id_for(route_name):
    """Same entity ID the alias-based name produced before display names existed.

    HA forbids double and trailing underscores in object IDs; slugifying the old
    name "Reliable <alias with spaces>" collapsed them the same way.
    """
    return "notify.reliable_" + re.sub(r"_+", "_", route_name).strip("_")


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
    active = available_routes(manager.routes)
    active_ids = {f"{entry.entry_id}_route_{name}" for name in active}
    registry = er.async_get(hass)
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (item.domain == "notify" and item.platform == DOMAIN
                and item.unique_id.startswith(f"{entry.entry_id}_route_")
                and item.unique_id not in active_ids):
            registry.async_remove(item.entity_id)
    async_add_entities([ReliableNotifyEntity(manager, name) for name in active])


class ReliableNotifyEntity(NotifyEntity):
    """Send a message through the Reliable Notify durable queue."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_icon = "mdi:bell-check"

    def __init__(self, manager, route_name: str) -> None:
        self.manager = manager
        self.route_name = route_name
        self._attr_name = entity_name(manager.routes, route_name)
        self._attr_unique_id = f"{manager.entry.entry_id}_route_{route_name}"
        # Keep the entity ID derived from the internal alias, independent of the
        # display name, so automations stay valid when the name changes.
        self.entity_id = entity_id_for(route_name)

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
