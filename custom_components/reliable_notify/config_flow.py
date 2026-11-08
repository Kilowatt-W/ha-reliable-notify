"""Setup and a single, fully expanded options form."""
from __future__ import annotations

import voluptuous as vol
import yaml
from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import CONF_INTERVAL, CONF_TARGET, DEFAULT_INTERVAL, DOMAIN
from .retry import validate_policies, DEFAULT_POLICIES
from .retention import validate_retention, DEFAULT_RETENTION
from .smart import validate_quiet_hours, DEFAULT_QUIET_HOURS
from .routing import is_own_entity
from .logging_utils import validate_transport_logging, TRANSPORTS, LEVELS


def number(low, high):
    return vol.All(vol.Coerce(int), vol.Range(min=low, max=high))


def choice(options, translation_key, multiple=False):
    """Dropdown whose option labels come from the 'selector' translations (DE/EN)."""
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=list(options), multiple=multiple, translation_key=translation_key,
        mode=selector.SelectSelectorMode.DROPDOWN))


def optional_target(value=None, exclude=()):
    """Do not suggest an invalid empty entity to HA's form control.

    Reliable Notify's own notify entities are excluded: as default target
    they would enqueue every fallback message again (endless loop).
    """
    description = {'suggested_value': value} if value else {}
    config = {'domain': 'notify', 'multiple': False}
    if exclude:
        config['exclude_entities'] = sorted(exclude)
    return {vol.Optional(CONF_TARGET, description=description): selector.EntitySelector(
        selector.EntitySelectorConfig(**config))}


class ReliableNotifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id('primary')
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title='Reliable Notify', data={**user_input, CONF_TARGET: user_input.get(CONF_TARGET) or ''})
        return self.async_show_form(step_id='user', data_schema=vol.Schema({
            **optional_target(),
            vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): number(10, 3600),
        }))

    @staticmethod
    def async_get_options_flow(config_entry):
        return ReliableNotifyOptionsFlow()


class ReliableNotifyOptionsFlow(config_entries.OptionsFlow):
    """All settings are visible together; routes are edited in the admin panel."""

    def _own_entities(self):
        try:
            from homeassistant.helpers import entity_registry as er
            registry = er.async_get(self.hass)
            return frozenset(item.entity_id for item in registry.entities.values()
                             if item.platform == DOMAIN and item.domain == 'notify')
        except Exception:  # registry unavailable: the prefix check still applies
            return frozenset()

    async def async_step_init(self, user_input=None):
        current = {**self.config_entry.data, **self.config_entry.options}
        errors = {}
        own = self._own_entities()
        if user_input is not None:
            try:
                general = user_input['general']
                smart = dict(user_input['smart'])
                quiet = validate_quiet_hours({key: smart.pop(key) for key in DEFAULT_QUIET_HOURS})
                testing = dict(user_input['testing'])
                recipients = [x.strip() for x in testing.pop('test_recipients', '').split(',') if x.strip()]
                if len(recipients) > 100 or any(len(x) > 100 for x in recipients):
                    raise ValueError('invalid test recipients')
                opts = {
                    **self.config_entry.options, **general, **smart, **testing,
                    'quiet_hours': quiet,
                    'retry_policies': validate_policies({
                        priority: user_input['retry_' + priority] for priority in DEFAULT_POLICIES}),
                    'archive_retention': validate_retention(user_input['retention']),
                    'transport_logging': validate_transport_logging(user_input['logging']),
                    'test_recipients': recipients,
                }
                opts[CONF_TARGET] = general.get(CONF_TARGET) or ''
                if is_own_entity(opts[CONF_TARGET], own):
                    errors['base'] = 'own_entity'
                    raise ValueError('own entity as default target')
                opts['archive_url'] = general.get('archive_url', '').strip()
                if user_input.get('show_yaml'):
                    self._pending = opts
                    return await self.async_step_yaml()
                return self.async_create_entry(title='', data=opts)
            except (ValueError, TypeError, KeyError):
                errors.setdefault('base', 'invalid_options')
        # Rebuild from submitted values on validation failures, keeping the user's edits.
        submitted = user_input or {}
        schema = {}

        def add(name, fields):
            schema[vol.Required(name)] = section(vol.Schema(fields), {'collapsed': False})

        general = {**current, **submitted.get('general', {})}
        target = submitted['general'].get(CONF_TARGET) if 'general' in submitted else current.get(CONF_TARGET)
        add('general', {
            **optional_target(target, own),
            vol.Required(CONF_INTERVAL, default=general.get(CONF_INTERVAL, DEFAULT_INTERVAL)): number(10, 3600),
            vol.Optional('archive_url', default=general.get('archive_url', '')): str,
            vol.Required('dead_letter_days', default=general.get('dead_letter_days', 30)): number(1, 365),
            vol.Required('legacy_notify_services', default=general.get('legacy_notify_services', True)): bool,
        })
        smart = {**DEFAULT_QUIET_HOURS, **current.get('quiet_hours', {}),
                 'rate_limit_per_minute': current.get('rate_limit_per_minute', 10),
                 'digest_window_seconds': current.get('digest_window_seconds', 300),
                 **submitted.get('smart', {})}
        add('smart', {
            vol.Required('enabled', default=smart['enabled']): bool,
            vol.Required('start', default=smart['start']): str,
            vol.Required('end', default=smart['end']): str,
            vol.Required('allow_priorities', default=smart['allow_priorities']): choice(
                ['info', 'warning', 'critical'], 'priority', multiple=True),
            vol.Required('rate_limit_per_minute', default=smart['rate_limit_per_minute']): number(1, 1000),
            vol.Required('digest_window_seconds', default=smart['digest_window_seconds']): number(10, 3600),
        })
        for priority, defaults in DEFAULT_POLICIES.items():
            values = {**defaults, **current.get('retry_policies', {}).get(priority, {}),
                      **submitted.get('retry_' + priority, {})}
            add('retry_' + priority, {
                vol.Required(key, default=values[key]): number(low, high)
                for key, low, high in [('max_attempts', 0, 10000), ('base_seconds', 1, 3600), ('max_delay', 1, 86400)]
            })
        retention = {**DEFAULT_RETENTION, **current.get('archive_retention', {}), **submitted.get('retention', {})}
        add('retention', {vol.Required(key, default=value): number(0, 365) for key, value in retention.items()})
        testing = {**current, **submitted.get('testing', {})}
        add('testing', {
            vol.Required('test_mode', default=testing.get('test_mode', 'off')): choice(['off', 'stage'], 'test_mode'),
            vol.Optional('test_recipients', default=(testing.get('test_recipients', '') if 'testing' in submitted
                else ','.join(current.get('test_recipients', [])))): str,
            vol.Required('backup_enabled', default=testing.get('backup_enabled', True)): bool,
            vol.Required('backup_keep', default=testing.get('backup_keep', 3)): number(1, 20),
        })
        logs = {**current.get('transport_logging', {}), **submitted.get('logging', {})}
        add('logging', {vol.Required(key, default=logs.get(key, 'warning')): choice(LEVELS, 'log_level') for key in TRANSPORTS})
        schema[vol.Optional('show_yaml', default=False)] = bool
        return self.async_show_form(step_id='init', errors=errors, data_schema=vol.Schema(schema))

    async def async_step_yaml(self, user_input=None):
        """Optional read-only YAML preview; no parsing or alternate write path."""
        if user_input is not None:
            return self.async_create_entry(title='', data=self._pending)
        return self.async_show_form(step_id='yaml', description_placeholders={
            'yaml': yaml.safe_dump(self._pending, allow_unicode=True, sort_keys=False)
        }, data_schema=vol.Schema({}))
