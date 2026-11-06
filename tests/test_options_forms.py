"""Exercise the options submission contract without a running HA instance."""
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import voluptuous as vol

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'


class Flow:
    def __init_subclass__(cls, **kwargs):
        pass

    def async_show_form(self, **kwargs):
        return {'type': 'form', **kwargs}

    def async_create_entry(self, **kwargs):
        return {'type': 'create_entry', **kwargs}


class Select:
    def __init__(self, config):
        self.config = config

    def __call__(self, value):
        return value


def load_flow():
    package = types.ModuleType('rn_options')
    package.__path__ = [str(ROOT)]
    ha = types.ModuleType('homeassistant')
    ha.config_entries = types.SimpleNamespace(ConfigFlow=Flow, OptionsFlow=Flow)
    forms = types.ModuleType('homeassistant.data_entry_flow')
    def section(schema, options):
        schema.section_options = options
        return schema
    forms.section = section
    helpers = types.ModuleType('homeassistant.helpers')
    helpers.selector = types.SimpleNamespace(EntitySelector=Select, EntitySelectorConfig=dict,
        SelectSelector=Select, SelectSelectorConfig=dict)
    with patch.dict(sys.modules, {'rn_options': package, 'homeassistant': ha,
            'homeassistant.data_entry_flow': forms, 'homeassistant.helpers': helpers}):
        spec = importlib.util.spec_from_file_location('rn_options.config_flow', ROOT/'config_flow.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


class OptionsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.module = load_flow()
        self.flow = self.module.ReliableNotifyOptionsFlow()
        self.original = {'routes': {'recipients': {'phone': {'action': 'notify.mobile_app_phone'}}},
            'notification_profiles': {'custom': {'priority': 'warning'}},
            'archive_retention': {'windows': 12}, 'unknown_future_option': {'keep': True}}
        self.flow.config_entry = types.SimpleNamespace(data={}, options=copy.deepcopy(self.original))
        self.form = await self.flow.async_step_init()
        self.input = self.form['data_schema']({key.schema: {} for key in self.form['data_schema'].schema
            if key.schema != 'show_yaml'})

    async def test_all_sections_visible_and_no_json_fields(self):
        schema = self.form['data_schema'].schema
        self.assertNotIn('manage', [key.schema for key in schema])
        sections = [value for value in schema.values() if isinstance(value, vol.Schema)]
        self.assertEqual(len(sections), 8)
        for section in sections:
            self.assertEqual(section.section_options, {'collapsed': False})
            self.assertFalse(any('json' in str(key.schema) for key in section.schema))

    async def test_default_target_optional_in_both_forms_without_empty_suggestion(self):
        initial = await self.module.ReliableNotifyConfigFlow().async_step_user()
        general = next(v for k, v in self.form['data_schema'].schema.items() if k.schema == 'general')
        for schema in (initial['data_schema'], general):
            key = next(k for k in schema.schema if k.schema == 'target_entity')
            self.assertIsInstance(key, vol.Optional)
            self.assertNotIn('suggested_value', key.description)
            self.assertNotIn('target_entity', schema({}))
        result = await self.flow.async_step_init(self.input)
        self.assertEqual(result['data']['target_entity'], '')

    async def test_clear_existing_default_overrides_setup_value(self):
        self.flow.config_entry.data = {'target_entity': 'notify.old'}
        form = await self.flow.async_step_init()
        general = next(v for k, v in form['data_schema'].schema.items() if k.schema == 'general')
        key = next(k for k in general.schema if k.schema == 'target_entity')
        self.assertEqual(key.description['suggested_value'], 'notify.old')
        for value in (None, ''):
            self.input['general']['target_entity'] = value
            result = await self.flow.async_step_init(self.input)
            self.assertEqual(result['data']['target_entity'], '')
        self.input['general'].pop('target_entity')
        result = await self.flow.async_step_init(self.input)
        self.assertEqual(result['data']['target_entity'], '')
        self.input['general']['target_entity'] = 'notify.new'
        self.assertEqual((await self.flow.async_step_init(self.input))['data']['target_entity'], 'notify.new')

    async def test_save_preserves_unrelated_options_and_custom_retention(self):
        self.input['retry_critical']['max_attempts'] = 0
        self.input['smart']['start'] = '23:15'
        self.input['logging']['gotify'] = 'debug'
        result = await self.flow.async_step_init(self.input)
        self.assertEqual(result['type'], 'create_entry')
        saved = result['data']
        for key in ('routes', 'notification_profiles', 'unknown_future_option'):
            self.assertEqual(saved[key], self.original[key])
        self.assertEqual(saved['archive_retention']['windows'], 12)
        self.assertEqual(saved['quiet_hours']['start'], '23:15')
        self.assertEqual(saved['transport_logging']['gotify'], 'debug')
        self.assertEqual(self.flow.config_entry.options, self.original)

    async def test_invalid_retry_or_time_retains_edits(self):
        self.input['retry_warning'].update(base_seconds=500, max_delay=200)
        self.input['general']['archive_url'] = 'https://example.test/archive'
        result = await self.flow.async_step_init(self.input)
        self.assertEqual(result['errors'], {'base': 'invalid_options'})
        schema = result['data_schema']
        values = schema({key.schema: {} for key in schema.schema if key.schema != 'show_yaml'})
        self.assertEqual(values['general']['archive_url'], 'https://example.test/archive')
        self.assertEqual(values['retry_warning']['base_seconds'], 500)
        self.input['retry_warning']['max_delay'] = 600
        self.input['smart']['end'] = self.input['smart']['start']
        self.assertIn('base', (await self.flow.async_step_init(self.input))['errors'])

    async def test_yaml_preview_does_not_save_until_confirmed(self):
        self.input['show_yaml'] = True
        preview = await self.flow.async_step_init(self.input)
        self.assertEqual(preview['step_id'], 'yaml')
        self.assertIn('retry_policies:', preview['description_placeholders']['yaml'])
        self.assertEqual(self.flow.config_entry.options, self.original)
        result = await self.flow.async_step_yaml({})
        self.assertEqual(result['data']['archive_retention']['windows'], 12)
        self.assertNotIn('show_yaml', result['data'])


class RouteEditorAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_full_route_requires_admin_and_does_not_change_inventory_contract(self):
        package = types.ModuleType('rn_dashboard_forms')
        package.__path__ = [str(ROOT)]
        callbacks = {}
        def command(schema):
            name = next(value for key, value in schema.items() if key.schema == 'type')
            def decorate(fn):
                callbacks[name] = fn
                return fn
            return decorate
        components = types.ModuleType('homeassistant.components')
        components.websocket_api = types.SimpleNamespace(websocket_command=command,
            async_response=lambda fn: fn, async_register_command=lambda *args: None)
        with patch.dict(sys.modules, {'rn_dashboard_forms': package,
                'homeassistant': types.ModuleType('homeassistant'),
                'homeassistant.components': components}):
            spec = importlib.util.spec_from_file_location('rn_dashboard_forms.dashboard', ROOT/'dashboard.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        definition = {'action': 'reliable_notify.gotify', 'data': {'base_url': 'https://push.test', 'token': 'secret'}}
        manager = types.SimpleNamespace(routes={'recipients': {'push': definition}})
        hass = types.SimpleNamespace(data={'reliable_notify': {'entry': manager}})
        mod.register_dashboard(hass)
        results, errors = [], []
        connection = types.SimpleNamespace(user=types.SimpleNamespace(is_admin=False),
            send_error=lambda *args: errors.append(args), send_result=lambda *args: results.append(args))
        msg = {'id': 1, 'category': 'recipients', 'name': 'push'}
        callback = callbacks['reliable_notify/route_definition']
        await callback(hass, connection, msg)
        self.assertEqual(errors[-1][1], 'unauthorized')
        self.assertEqual(results, [])
        connection.user.is_admin = True
        await callback(hass, connection, msg)
        self.assertEqual(results[-1][1], {'definition': definition})
        await callback(hass, connection, {**msg, 'name': 'missing'})
        self.assertEqual(errors[-1][1], 'not_found')
