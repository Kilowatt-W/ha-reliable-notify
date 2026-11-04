"""Admin-only WebSocket status for an interactive Lovelace card.

The card never receives notification bodies or provider credentials.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN
from .retry import validate_policies


def register_dashboard(hass):
    @websocket_api.websocket_command({vol.Required("type"): "reliable_notify/dashboard", vol.Optional("limit", default=50): vol.All(vol.Coerce(int), vol.Range(min=1, max=100))})
    @websocket_api.async_response
    async def get_dashboard(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        managers = hass.data.get(DOMAIN, {})
        if not managers:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        manager = next(iter(managers.values()))
        count, dead, metrics, recent, dead_recent, history = await __import__('asyncio').gather(
            manager.store.count(), manager.store.dead_count(), manager.store.metrics(),
            manager.store.recent(msg['limit']), manager.store.recent(msg['limit'], dead=True),
            manager.store.history(msg['limit']),
        )
        connection.send_result(msg['id'], {
            'count': count, 'dead': dead, 'metrics': metrics,
            'queue': recent, 'dead_letters': dead_recent, 'history': history,
            'policies': manager.policies, 'storage': await manager.storage_status(),
        })

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/set_retry_policies',
        vol.Required('policies'): dict,
    })
    @websocket_api.async_response
    async def set_policies(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        try:
            policies = validate_policies(msg['policies'])
        except ValueError as err:
            connection.send_error(msg['id'], 'invalid_policy', str(err))
            return
        hass.config_entries.async_update_entry(manager.entry, options={
            **manager.entry.options, 'retry_policies': policies,
        })
        connection.send_result(msg['id'], {'saved': True})

    websocket_api.async_register_command(hass, get_dashboard)
    websocket_api.async_register_command(hass, set_policies)