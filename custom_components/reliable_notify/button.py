"""Queue management buttons."""
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RetryButton(manager)])


class RetryButton(ButtonEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:reload"

    def __init__(self, manager):
        self.manager = manager
        self._attr_name = "Reliable Notify Retry All"
        self._attr_unique_id = f"{manager.entry.entry_id}_retry"

    async def async_press(self):
        await self.manager.store.retry_all()
        self.manager.wakeup.set()