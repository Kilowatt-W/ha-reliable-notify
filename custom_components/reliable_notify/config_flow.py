"""Config flow and built-in UI editor for recipient/group routes."""
from __future__ import annotations

import json

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_INTERVAL, CONF_TARGET, DEFAULT_INTERVAL, DOMAIN
from .routing import validate_config


class ReliableNotifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id('primary')
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title='Reliable Notify', data=user_input)
        return self.async_show_form(step_id='user', data_schema=vol.Schema({
            vol.Required(CONF_TARGET): selector.EntitySelector(
                selector.EntitySelectorConfig(domain='notify', multiple=False)),
            vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        }))

    @staticmethod
    def async_get_options_flow(config_entry):
        return ReliableNotifyOptionsFlow()


class ReliableNotifyOptionsFlow(config_entries.OptionsFlow):
    """UI-managed routes stored in entry options, YAML routes remain supported.

    UI routes shadow entries of the same name from the routes YAML file.
    """

    def _routes(self):
        routes = self.config_entry.options.get('routes', {})
        return {
            'recipients': dict(routes.get('recipients', {})),
            'groups': dict(routes.get('groups', {})),
        }

    def _save_routes(self, routes):
        validate_config(routes)
        return self.async_create_entry(title='', data={**self.config_entry.options, 'routes': routes})

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            operation = user_input.get('manage', 'settings')
            if operation == 'recipient':
                return await self.async_step_recipient()
            if operation == 'group':
                return await self.async_step_group()
            if operation == 'delete':
                return await self.async_step_delete()
            return await self.async_step_settings()
        return self.async_show_form(step_id='init', data_schema=vol.Schema({
            vol.Required('manage', default='settings'): vol.In({
                'settings': 'General settings',
                'recipient': 'Add/update recipient',
                'group': 'Add/update group',
                'delete': 'Delete UI-managed recipient/group',
            }),
        }))

    async def async_step_settings(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title='', data={
                **self.config_entry.options,
                CONF_TARGET: user_input[CONF_TARGET],
                CONF_INTERVAL: user_input[CONF_INTERVAL],
            })
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id='settings', data_schema=vol.Schema({
            vol.Required(CONF_TARGET, default=current[CONF_TARGET]):
                selector.EntitySelector(selector.EntitySelectorConfig(domain='notify')),
            vol.Required(CONF_INTERVAL, default=current.get(CONF_INTERVAL, DEFAULT_INTERVAL)):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        }))

    async def async_step_recipient(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                name = user_input['name'].strip()
                if not name or not name.replace('_', '').isalnum():
                    raise ValueError('bad name')
                data = json.loads(user_input.get('data_json') or '{}')
                if not isinstance(data, dict):
                    raise ValueError('data must be JSON object')
                record = {'action': user_input['action'], 'data': data}
                if user_input.get('target_entity'):
                    record['target_entity'] = user_input['target_entity']
                routes = self._routes()
                routes['recipients'][name] = record
                return self._save_routes(routes)
            except (ValueError, TypeError):
                errors['base'] = 'invalid_route'
        return self.async_show_form(step_id='recipient', errors=errors, data_schema=vol.Schema({
            vol.Required('name'): str,
            vol.Required('action', default='telegram_bot.send_message'): str,
            vol.Optional('target_entity'): str,
            vol.Optional('data_json', default='{}'): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)),
        }))

    async def async_step_group(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                name = user_input['name'].strip()
                if not name or not name.replace('_', '').isalnum():
                    raise ValueError('bad name')
                members = [part.strip() for part in user_input['members'].split(',') if part.strip()]
                routes = self._routes()
                routes['groups'][name] = members
                return self._save_routes(routes)
            except (ValueError, TypeError):
                errors['base'] = 'invalid_route'
        return self.async_show_form(step_id='group', errors=errors, data_schema=vol.Schema({
            vol.Required('name'): str,
            vol.Required('members'): str,
        }))

    async def async_step_delete(self, user_input=None):
        routes = self._routes()
        choices = {f'{category}:{name}': f'{category}: {name}'
                   for category, records in routes.items() for name in records}
        if not choices:
            return self.async_abort(reason='no_routes')
        if user_input is not None:
            category, name = user_input['route'].split(':', 1)
            routes[category].pop(name, None)
            try:
                return self._save_routes(routes)
            except ValueError:
                return self.async_show_form(step_id='delete', errors={'base': 'invalid_route'},
                    data_schema=vol.Schema({vol.Required('route'): vol.In(choices)}))
        return self.async_show_form(step_id='delete', data_schema=vol.Schema({
            vol.Required('route'): vol.In(choices),
        }))