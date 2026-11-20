"""Alarm window: on while a critical incident is open and not acknowledged."""
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .incidents import summary


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CriticalOpenBinarySensor(hass.data[DOMAIN][entry.entry_id])])


class CriticalOpenBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "critical_open"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_should_poll = False

    def __init__(self, manager):
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_critical_open"
        self._attr_is_on = False

    async def async_added_to_hass(self):
        async def refresh(_=None):
            data = summary(await self.manager.store.incidents())
            self._attr_is_on = data["critical_unacknowledged"] > 0
            self._attr_extra_state_attributes = {"count": data["critical_unacknowledged"]}
            self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen("reliable_notify_incident", refresh))
        self.async_on_remove(async_track_time_interval(self.hass, refresh, timedelta(seconds=60)))
        await refresh()
