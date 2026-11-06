"""Queue, transport and database diagnostic entities."""
import asyncio
from pathlib import Path
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
        DatabaseSizeSensor(manager), MaintenanceHealthSensor(manager),
        HealthSensor(manager), QueueAgeSensor(manager), MediaSizeSensor(manager),
        TransportStatusSensor(manager),
    ])


class BaseSensor(SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, manager, key, name, icon):
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
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

class DatabaseSizeSensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "database_size", "Database Size", "mdi:database")
        self._attr_native_unit_of_measurement = "MiB"

    async def async_update(self):
        info = self.manager.maintenance_info
        self._attr_native_value = round(info["database_bytes"] / 1048576, 2) if "database_bytes" in info else None
        self._attr_extra_state_attributes = {
            "last_integrity_check": info.get("integrity"),
            "critical_dead_letters": info.get("critical_dead_letters"),
            "dead_letters": info.get("dead_letters"),
        }


class MaintenanceHealthSensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "maintenance_health", "Maintenance Health", "mdi:database-check")

    async def async_update(self):
        info = self.manager.maintenance_info
        self._attr_native_value = "ok" if info.get("integrity") == "ok" else ("pending" if not info else "error")
        self._attr_extra_state_attributes = {
            "checkpoint_busy": info.get("checkpoint_busy"),
            "removed_dead_letters": info.get("removed_dead_letters"),
        }


class HealthSensor(BaseSensor):
    """Overall status never assumes a successful service call means phone delivery."""

    def __init__(self, manager):
        super().__init__(manager, "health", "Health", "mdi:heart-pulse")

    async def async_update(self):
        status = await self.manager.storage_status()
        info = self.manager.maintenance_info
        old = await self.manager.store.statistics(days=7)
        dead = await self.manager.store.dead_count()
        if not status["healthy"] or (info and info.get("integrity") != "ok"):
            health = "critical"
        elif info and ((old.get("oldest_queued_seconds") or 0) > 3600 or dead > 0):
            health = "degraded"
        elif not info:
            health = "unknown"
        else:
            health = "healthy"
        self._attr_native_value = health
        self._attr_extra_state_attributes = {
            "free_storage_healthy":status["healthy"],
            "maintenance_integrity":info.get("integrity"),
            "pending":old.get("queued",0),
            "dead_letters":dead,
            "oldest_queued_seconds":old.get("oldest_queued_seconds"),
        }


class QueueAgeSensor(BaseSensor):
    def __init__(self, manager):
        super().__init__(manager, "oldest_queued", "Oldest Queued", "mdi:timer-sand")
        self._attr_native_unit_of_measurement = "s"

    async def async_update(self):
        info=await self.manager.store.statistics(days=1)
        age=info.get("oldest_queued_seconds")
        self._attr_native_value = round(age) if age is not None else 0


class MediaSizeSensor(BaseSensor):
    def __init__(self,manager):
        super().__init__(manager,"media_size","Media Size","mdi:file-document-multiple")
        self._attr_native_unit_of_measurement="MiB"

    async def async_update(self):
        def measure():
            folder=Path("/media/reliable_notify")
            if not folder.exists():
                return 0
            return sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
        used=await asyncio.to_thread(measure)
        self._attr_native_value=round(used/1048576,2)


class TransportStatusSensor(BaseSensor):
    def __init__(self,manager):
        super().__init__(manager,"transport_health","Transport Health","mdi:network-check")

    async def async_update(self):
        report=await self.manager.store.statistics(days=7)
        transports=report["transports"]
        if not transports:
            self._attr_native_value="unknown"
        elif any(x["failed"] and not x["sent"] for x in transports):
            self._attr_native_value="degraded"
        else:
            self._attr_native_value="healthy"
        self._attr_extra_state_attributes={
            "transports":{x["action"]:{
                "events":x["events"],"sent":x["sent"],"failed":x["failed"],
                "avg_delivery_seconds":x["avg_delivery_seconds"]
            } for x in transports[:20]}
        }
