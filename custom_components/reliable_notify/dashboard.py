"""Admin-only WebSocket status for an interactive Lovelace card.

The card never receives notification bodies or provider credentials.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN
from .retry import validate_policies
from .retention import validate_retention


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
        count, dead, metrics, recent, dead_recent, history, staged = await __import__('asyncio').gather(
            manager.store.count(), manager.store.dead_count(), manager.store.metrics(),
            manager.store.recent(msg['limit']), manager.store.recent(msg['limit'], dead=True),
            manager.store.history(msg['limit']), manager.store.staged(msg['limit']),
        )
        connection.send_result(msg['id'], {
            'count': count, 'dead': dead, 'metrics': metrics,
            'queue': recent, 'dead_letters': dead_recent, 'history': history,
            'staged': staged, 'staged_count': len(staged),
            'recipient_names': sorted(manager.routes['recipients']),
            'policies': manager.policies, 'retention': manager.archive_retention, 'storage': await manager.storage_status(),
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

    @websocket_api.websocket_command({vol.Required('type'): 'reliable_notify/send_staged',
                                       vol.Required('id'): vol.All(vol.Coerce(int), vol.Range(min=1)),
                                       vol.Required('recipient'): str})
    @websocket_api.async_response
    async def send_staged(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        recipient = manager.routes['recipients'].get(msg['recipient'])
        if not recipient:
            connection.send_error(msg['id'], 'invalid_recipient', 'Select a configured individual recipient')
            return
        from .routing import valid_action
        action = recipient.get('action', 'notify.send_message')
        if not valid_action(action):
            connection.send_error(msg['id'], 'invalid_action', 'Invalid recipient action')
            return
        target = recipient.get('target_entity', '') if action in ('notify.send_message','smtp.send_message') else msg['recipient']
        updated = await manager.store.assign_staged(msg['id'], action, target, recipient.get('data', {}))
        if not updated:
            connection.send_error(msg['id'], 'not_found', 'Staged message no longer available')
            return
        manager.wakeup.set()
        connection.send_result(msg['id'], {'assigned': True})


    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/archive',
        vol.Optional('limit', default=50): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional('search', default=''): vol.All(str, vol.Length(max=200)),
    })
    @websocket_api.async_response
    async def archive_search(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        rows = await manager.store.archive_list(msg['limit'], msg['search'])
        connection.send_result(msg['id'], {'items': rows})

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/archive_detail',
        vol.Required('message_id'): vol.All(vol.Coerce(int), vol.Range(min=1)),
    })
    @websocket_api.async_response
    async def archive_detail(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        item = await manager.store.archive_detail(msg['message_id'])
        if item is None:
            connection.send_error(msg['id'], 'not_found', 'Message not in archive')
            return
        connection.send_result(msg['id'], item)

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/set_archive_retention',
        vol.Required('retention'): dict,
    })
    @websocket_api.async_response
    async def set_retention(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        try:
            configured = validate_retention(msg['retention'])
        except ValueError as err:
            connection.send_error(msg['id'], 'invalid_retention', str(err))
            return
        hass.config_entries.async_update_entry(manager.entry, options={
            **manager.entry.options, 'archive_retention': configured,
        })
        connection.send_result(msg['id'], {'saved': True})

    websocket_api.async_register_command(hass, get_dashboard)
    websocket_api.async_register_command(hass, set_retention)
    websocket_api.async_register_command(hass, archive_search)
    websocket_api.async_register_command(hass, archive_detail)
    websocket_api.async_register_command(hass, send_staged)
    websocket_api.async_register_command(hass, set_policies)