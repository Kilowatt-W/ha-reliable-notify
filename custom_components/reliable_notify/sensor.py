"""Queue status entities."""
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        QueueSizeSensor(manager), CounterSensor(manager, "sent", "Sent", "mdi:send-check"),
        CounterSensor(manager, "failures", "Failures", "mdi:alert-circle-outline"),
        DeadLetterSensor(manager), HistorySensor(manager), StorageFreeSensor(manager),
    ])


class BaseSensor(SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, manager, key, name, icon):
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon

    async def async_added_to_hass(self):
        self.async_on_remove(async_track_time_interval(
            self.hass, self._update, timedelta(seconds=15)
        ))
        await self._update(None)

    async def _update(self, _):
        await self.async_update()
        self.async_write_ha_state()


class QueueSizeSensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "queue_size", "Queue Size", "mdi:tray-full")

    async def async_update(self):
        self._attr_native_value = await self.manager.store.count()
        self._attr_extra_state_attributes = {
            "last_error": self.manager.last_error,
            "recent": await self.manager.store.recent(limit=10),
        }


class CounterSensor(BaseSensor):
    def __init__(self, manager, key, name, icon):
        super().__init__(manager, key, name, icon)
        self.key = key

    async def async_update(self):
        self._attr_native_value = (await self.manager.store.metrics()).get(self.key, 0)


class DeadLetterSensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "dead_letter_count", "Dead Letter Count", "mdi:email-alert-outline")

    async def async_update(self):
        self._attr_native_value = await self.manager.store.dead_count()
        self._attr_extra_state_attributes = {
            "recent": await self.manager.store.recent(limit=10, dead=True),
        }


class HistorySensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "history", "Delivery History", "mdi:history")

    async def async_update(self):
        history = await self.manager.store.history(limit=15)
        self._attr_native_value = len(history)
        self._attr_extra_state_attributes = {"recent": history}


class StorageFreeSensor(BaseSensor):
    """Automatic free-space health check every 15 seconds."""

    def __init__(self, manager):
        super().__init__(manager, "storage_free", "Storage Free", "mdi:harddisk")
        self._attr_native_unit_of_measurement = "MiB"

    async def async_update(self):
        result = await self.manager.storage_status()
        free = result['free_bytes']
        self._attr_native_value = round(free / (1024 * 1024), 1) if free is not None else None
        self._attr_extra_state_attributes = {
            'healthy': result['healthy'],
            'minimum_free_mib': round(result['minimum_free_bytes'] / (1024 * 1024)),
            'storage_path': '/media/reliable_notify',
        }