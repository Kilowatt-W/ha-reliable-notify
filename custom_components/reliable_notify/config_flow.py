"""Config flow and built-in UI editor for recipient/group routes."""
from __future__ import annotations

import json

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_INTERVAL, CONF_TARGET, DEFAULT_INTERVAL, DOMAIN
from .routing import validate_config
from .retry import validate_policies, DEFAULT_POLICIES
from .retention import validate_retention, DEFAULT_RETENTION
from .smart import validate_quiet_hours, DEFAULT_QUIET_HOURS
from .logging_utils import validate_transport_logging


class ReliableNotifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id('primary')
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title='Reliable Notify', data=user_input)
        return self.async_show_form(step_id='user', data_schema=vol.Schema({
            vol.Optional(CONF_TARGET): selector.EntitySelector(
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
            'persons': dict(routes.get('persons', {})),
        }

    def _save_routes(self, routes):
        validate_config(routes)
        return self.async_create_entry(title='', data={**self.config_entry.options, 'routes': routes})

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            operation = user_input.get('manage', 'settings')
            if operation == 'smart':
                return await self.async_step_smart()
            if operation == 'testing':
                return await self.async_step_testing()
            if operation == 'retention':
                return await self.async_step_retention()
            if operation == 'retries':
                return await self.async_step_retries()
            if operation == 'recipient':
                return await self.async_step_recipient()
            if operation == 'person':
                return await self.async_step_person()
            if operation == 'group':
                return await self.async_step_group()
            if operation == 'delete':
                return await self.async_step_delete()
            return await self.async_step_settings()
        return self.async_show_form(step_id='init', data_schema=vol.Schema({
            vol.Required('manage', default='settings'): vol.In({
                'settings': 'General settings',
                'smart': 'Quiet hours, delivery limits and digests',
                'testing': 'Test mode, diagnostic logging and backup',
                'retries': 'Retry policies by priority',
                'retention': 'Archive retention by message type',
                'recipient': 'Add/update recipient',
                'group': 'Add/update group',
                'person': 'Add/update person',
                'delete': 'Delete UI-managed recipient/group',
            }),
        }))

    async def async_step_settings(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title='', data={
                **self.config_entry.options,
                CONF_TARGET: user_input.get(CONF_TARGET, ''),
                CONF_INTERVAL: user_input[CONF_INTERVAL],
                'archive_url': user_input.get('archive_url', '').strip(),
                'dead_letter_days': user_input.get('dead_letter_days',30),
                'legacy_notify_services': user_input.get('legacy_notify_services', True),
            })
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id='settings', data_schema=vol.Schema({
            vol.Optional(CONF_TARGET, description={"suggested_value": current.get(CONF_TARGET, "")}):
                selector.EntitySelector(selector.EntitySelectorConfig(domain='notify')),
            vol.Required(CONF_INTERVAL, default=current.get(CONF_INTERVAL, DEFAULT_INTERVAL)):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            vol.Optional('archive_url', description={
                'suggested_value': current.get('archive_url', '')
            }): str,
            vol.Optional('dead_letter_days',default=current.get('dead_letter_days',30)):
                vol.All(vol.Coerce(int), vol.Range(min=1,max=365)),
            vol.Required('legacy_notify_services',
                         default=current.get('legacy_notify_services',True)):bool,
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

    async def async_step_retries(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                result = validate_policies(json.loads(user_input['policies_json']))
                return self.async_create_entry(title='', data={
                    **self.config_entry.options, 'retry_policies': result,
                })
            except (ValueError, TypeError, json.JSONDecodeError):
                errors['base'] = 'invalid_route'
        current = self.config_entry.options.get('retry_policies', DEFAULT_POLICIES)
        return self.async_show_form(step_id='retries', errors=errors, data_schema=vol.Schema({
            vol.Required('policies_json', default=json.dumps(current, indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }))

    async def async_step_retention(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                result = validate_retention(json.loads(user_input['days_json']))
                return self.async_create_entry(title='', data={
                    **self.config_entry.options, 'archive_retention': result,
                })
            except (ValueError, TypeError, json.JSONDecodeError):
                errors['base'] = 'invalid_route'
        current = self.config_entry.options.get('archive_retention', DEFAULT_RETENTION)
        return self.async_show_form(step_id='retention', errors=errors, data_schema=vol.Schema({
            vol.Required('days_json', default=json.dumps(current, indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }))

    async def async_step_person(self, user_input=None):
        errors={}
        if user_input is not None:
            try:
                name=user_input["name"].strip()
                if not name or not name.replace("_","").isalnum():
                    raise ValueError("invalid name")
                spec=json.loads(user_input["settings_json"])
                if not isinstance(spec,dict):
                    raise ValueError("invalid mapping")
                routes=self._routes()
                routes["persons"][name]=spec
                return self._save_routes(routes)
            except (ValueError,TypeError,KeyError):
                errors["base"]="invalid_route"
        return self.async_show_form(step_id="person",errors=errors,data_schema=vol.Schema({
            vol.Required("name"):str,
            vol.Required("settings_json",default='{"entity":"person.example","channels":{"mobile":"mobile_recipient"},"preferred":{"info":"mobile"}}'):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }))

    async def async_step_smart(self, user_input=None):
        errors={}
        if user_input is not None:
            try:
                quiet=validate_quiet_hours(json.loads(user_input["quiet_hours_json"]))
                return self.async_create_entry(title='',data={
                    **self.config_entry.options,
                    "quiet_hours":quiet,
                    "rate_limit_per_minute":user_input["rate_limit_per_minute"],
                    "digest_window_seconds":user_input["digest_window_seconds"],
                })
            except (ValueError,TypeError):
                errors["base"]="invalid_route"
        current=self.config_entry.options
        return self.async_show_form(step_id='smart',errors=errors,data_schema=vol.Schema({
            vol.Required("quiet_hours_json",default=json.dumps(current.get("quiet_hours",DEFAULT_QUIET_HOURS),indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required("rate_limit_per_minute",default=current.get("rate_limit_per_minute",10)):
                vol.All(vol.Coerce(int),vol.Range(min=1,max=1000)),
            vol.Required("digest_window_seconds",default=current.get("digest_window_seconds",300)):
                vol.All(vol.Coerce(int),vol.Range(min=10,max=3600)),
        }))

    async def async_step_testing(self, user_input=None):
        errors={}
        if user_input is not None:
            try:
                recipients=[x.strip() for x in user_input["test_recipients"].split(",") if x.strip()]
                if len(recipients)>100:
                    raise ValueError("too many test recipients")
                config=validate_transport_logging(json.loads(user_input["transport_logging_json"]))
                return self.async_create_entry(title='',data={
                    **self.config_entry.options,
                    "test_mode":user_input["test_mode"],
                    "test_recipients":recipients,
                    "transport_logging":config,
                    "backup_enabled":user_input["backup_enabled"],
                    "backup_keep":user_input["backup_keep"],
                })
            except (ValueError,TypeError,json.JSONDecodeError):
                errors["base"]="invalid_route"
        current=self.config_entry.options
        return self.async_show_form(step_id="testing",errors=errors,data_schema=vol.Schema({
            vol.Required("test_mode",default=current.get("test_mode","off")):
                vol.In(("off","stage")),
            vol.Optional("test_recipients",default=",".join(current.get("test_recipients",[]))):str,
            vol.Required("transport_logging_json",
                default=json.dumps(current.get("transport_logging",{}),indent=2)):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required("backup_enabled",default=current.get("backup_enabled",True)):bool,
            vol.Required("backup_keep",default=current.get("backup_keep",3)):
                vol.All(vol.Coerce(int),vol.Range(min=1,max=20)),
        }))
