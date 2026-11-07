"""v3.3.0: display names (Klarnamen) for targets and German/English backend texts."""
import importlib.util
import json
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'


def load(module, package='rn_v330'):
    spec = importlib.util.spec_from_file_location(f'{package}.{module}', ROOT / f'{module}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


routing = load('routing')
i18n = load('i18n')

ROUTES = {
    'recipients': {'tg_wolfgang': {'action': 'notify.mobile_app_phone'},
                   'mail': {'action': 'notify.send_message', 'target_entity': 'notify.mail'}},
    'groups': {'family': ['tg_wolfgang', 'mail']},
    'persons': {},
}


class LabelValidationTests(unittest.TestCase):
    def test_labels_are_optional_free_text_and_never_change_routing(self):
        config = {**ROUTES, 'labels': {'tg_wolfgang': 'Telegram Wölfi – Büro (privat)', 'family': 'Familie & Freunde'}}
        validated = routing.validate_config(config)
        self.assertEqual([name for name, _ in routing.resolve(validated, ['family'])], ['tg_wolfgang', 'mail'])
        self.assertEqual(routing.display_name(validated, 'tg_wolfgang'), 'Telegram Wölfi – Büro (privat)')
        self.assertEqual(routing.display_name(validated, 'mail'), 'mail')
        routing.validate_config(dict(ROUTES))  # no labels at all

    def test_invalid_labels_are_rejected(self):
        for labels in ({'mail': ''}, {'mail': '   '}, {'mail': 'x' * 101}, {'mail': 'a\nb'},
                       {'mail': 5}, ['mail'], {'mail': 'tab\there'}):
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                routing.validate_config({**ROUTES, 'labels': labels})
        routing.validate_config({**ROUTES, 'labels': {'mail': 'x' * 100}})

    def test_merge_prefers_ui_and_drops_labels_of_removed_routes(self):
        file_routes = {'recipients': {'mail': ROUTES['recipients']['mail']}, 'groups': {},
                       'persons': {}, 'labels': {'mail': 'YAML Mail', 'gone': 'Old'}}
        ui = {'recipients': {'tg_wolfgang': ROUTES['recipients']['tg_wolfgang']},
              'labels': {'mail': 'UI Mail', 'tg_wolfgang': 'Telegram'}}
        merged = routing.merge_routes(file_routes, ui)
        self.assertEqual(set(merged['recipients']), {'mail', 'tg_wolfgang'})
        self.assertEqual(merged['labels'], {'mail': 'UI Mail', 'tg_wolfgang': 'Telegram'})
        routing.validate_config(merged)


class BackendLanguageTests(unittest.TestCase):
    def test_language_selection_and_fallback(self):
        for code, expected in (('de', 'de'), ('de-AT', 'de'), ('de_CH', 'de'), ('DE', 'de'),
                               ('en', 'en'), ('fr', 'en'), (None, 'en'), ('', 'en')):
            self.assertEqual(i18n.language(code), expected)
        self.assertEqual(i18n.text('de', 'ack'), 'Bestätigen')
        self.assertEqual(i18n.text('en-GB', 'ack'), 'Acknowledge')
        self.assertEqual(i18n.text('de', 'test_message', name='Telegram Wölfi'),
                         'Testnachricht von Reliable Notify an Telegram Wölfi.')
        hass = types.SimpleNamespace(config=types.SimpleNamespace(language='de-DE'))
        self.assertEqual(i18n.ha_text(hass, 'action_applied'), 'Aktion übernommen')
        self.assertEqual(i18n.ha_text(types.SimpleNamespace(), 'action_applied'), 'Action applied')

    def test_every_text_exists_in_both_languages_and_is_telegram_keyboard_safe(self):
        for key, value in i18n.TEXTS.items():
            self.assertEqual(set(value), {'de', 'en'}, key)
            self.assertTrue(all(value.values()), key)
        for key in ('ack', 'snooze', 'escalate'):
            for title in i18n.TEXTS[key].values():
                # Telegram inline keyboards use "Title:data, Title:data".
                self.assertNotRegex(title, r'[:,]')

    def test_no_hard_coded_german_button_texts_left_in_manager(self):
        source = (ROOT / '__init__.py').read_text(encoding='utf8')
        for text in ('"Bestätigen"', '15 Min. später"', '"Eskalieren"', 'Aktion übernommen'):
            self.assertNotIn(text, source)


class SelectorTranslationTests(unittest.TestCase):
    def test_every_select_in_services_and_options_has_bilingual_option_labels(self):
        services = yaml.safe_load((ROOT / 'services.yaml').read_text(encoding='utf8'))
        used = {}
        for service in services.values():
            for field in (service or {}).get('fields', {}).values():
                select = field.get('selector', {}).get('select')
                if select:
                    self.assertIn('translation_key', select)
                    used.setdefault(select['translation_key'], set()).update(map(str, select['options']))
        flow = (ROOT / 'config_flow.py').read_text(encoding='utf8')
        self.assertNotIn('vol.In(', flow)
        for key in re.findall(r"choice\([^)]*?'([a-z_]+)'(?:, multiple=True)?\)", flow):
            used.setdefault(key, set())
        used['log_level'] = {'off', 'error', 'warning', 'info', 'debug'}
        source = json.loads((ROOT / 'strings.json').read_text(encoding='utf8'))
        for name in ('translations/en.json', 'translations/de.json'):
            data = json.loads((ROOT / name).read_text(encoding='utf8'))
            for key, options in used.items():
                labels = data['selector'][key]['options']
                self.assertTrue(options <= set(labels), (name, key))
                self.assertTrue(all(labels.values()))
        self.assertEqual(source['selector'], json.loads((ROOT / 'translations/en.json').read_text(encoding='utf8'))['selector'])
        german = json.loads((ROOT / 'translations/de.json').read_text(encoding='utf8'))['selector']
        self.assertEqual(german['priority']['options']['critical'], 'Kritisch')


class NotifyEntityNameTests(unittest.TestCase):
    def load_notify(self):
        package = types.ModuleType('rn_v330_notify')
        package.__path__ = [str(ROOT)]
        notify = types.ModuleType('homeassistant.components.notify')
        notify.NotifyEntity = object
        notify.NotifyEntityFeature = types.SimpleNamespace(TITLE=1)
        modules = {'rn_v330_notify': package, 'homeassistant': types.ModuleType('homeassistant'),
                   'homeassistant.components': types.ModuleType('homeassistant.components'),
                   'homeassistant.components.notify': notify,
                   'homeassistant.config_entries': types.SimpleNamespace(ConfigEntry=object),
                   'homeassistant.core': types.SimpleNamespace(HomeAssistant=object),
                   'homeassistant.helpers': types.ModuleType('homeassistant.helpers'),
                   'homeassistant.helpers.entity_platform': types.SimpleNamespace(AddEntitiesCallback=object),
                   'homeassistant.helpers.entity_registry': types.ModuleType('homeassistant.helpers.entity_registry')}
        with patch.dict(sys.modules, modules):
            return load('notify', 'rn_v330_notify')

    def test_entity_uses_display_name_but_keeps_alias_based_entity_id(self):
        notify = self.load_notify()
        manager = types.SimpleNamespace(routes={**ROUTES, 'labels': {'tg_wolfgang': 'Telegram Wölfi'}},
                                        entry=types.SimpleNamespace(entry_id='abc'), stopping=False)
        labelled = notify.ReliableNotifyEntity(manager, 'tg_wolfgang')
        self.assertEqual(labelled._attr_name, 'Telegram Wölfi')
        self.assertEqual(labelled.entity_id, 'notify.reliable_tg_wolfgang')
        self.assertEqual(labelled._attr_unique_id, 'abc_route_tg_wolfgang')
        plain = notify.ReliableNotifyEntity(manager, 'mail')
        self.assertEqual(plain._attr_name, 'Reliable mail')
        self.assertEqual(plain.entity_id, 'notify.reliable_mail')
        # HA object IDs may not contain double or trailing underscores.
        self.assertEqual(notify.entity_id_for('a__b_'), 'notify.reliable_a_b')


class SetRouteLabelTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        package = types.ModuleType('rn_v330_dash')
        package.__path__ = [str(ROOT)]
        self.file_routes = {'recipients': {}, 'groups': {}, 'persons': {}, 'labels': {}}
        package._load_routes = lambda path: self.file_routes
        callbacks = {}

        def command(schema):
            name = next(value for key, value in schema.items() if key.schema == 'type')
            def decorate(fn):
                callbacks[name] = (schema, fn)
                return fn
            return decorate
        components = types.ModuleType('homeassistant.components')
        components.websocket_api = types.SimpleNamespace(websocket_command=command,
            async_response=lambda fn: fn, async_register_command=lambda *args: None)
        # Keep the package importable while handlers run (relative imports at call time).
        patcher = patch.dict(sys.modules, {'rn_v330_dash': package,
            'homeassistant': types.ModuleType('homeassistant'), 'homeassistant.components': components})
        patcher.start()
        self.addCleanup(patcher.stop)
        mod = load('dashboard', 'rn_v330_dash')
        self.options = {'routes': {'recipients': {}, 'groups': {}, 'persons': {}}, 'other': 1}
        self.entry = types.SimpleNamespace(options=self.options)
        self.manager = types.SimpleNamespace(entry=self.entry, route_path='unused',
            routes={'recipients': {}, 'groups': {}, 'persons': {}, 'labels': {}})

        def update(entry, options):
            entry.options = options
        self.hass = types.SimpleNamespace(data={'reliable_notify': {'x': self.manager}},
            config_entries=types.SimpleNamespace(async_update_entry=update))
        mod.register_dashboard(self.hass)
        self.schema, self.handler = callbacks['reliable_notify/set_route']
        self.errors, self.results = [], []
        self.conn = types.SimpleNamespace(user=types.SimpleNamespace(is_admin=True),
            send_error=lambda *args: self.errors.append(args), send_result=lambda *args: self.results.append(args))

    async def call(self, **msg):
        import voluptuous as vol
        data = vol.Schema(self.schema)({'type': 'reliable_notify/set_route', 'category': 'recipients', **msg})
        await self.handler(self.hass, self.conn, {'id': 1, **data})

    async def test_label_saved_trimmed_updated_and_removed_with_route(self):
        definition = {'action': 'notify.mobile_app_phone'}
        await self.call(name='tg_wolfgang', definition=definition, label='  Telegram Wölfi  ')
        self.assertEqual(self.errors, [])
        routes = self.entry.options['routes']
        self.assertEqual(routes['labels'], {'tg_wolfgang': 'Telegram Wölfi'})
        self.assertEqual(routes['recipients']['tg_wolfgang'], definition)
        self.assertEqual(self.entry.options['other'], 1)
        await self.call(name='tg_wolfgang', definition=definition, label='Telegram Büro')
        self.assertEqual(self.entry.options['routes']['labels'], {'tg_wolfgang': 'Telegram Büro'})
        # Saving without a label key keeps it; an empty label or one equal to the alias removes it.
        await self.call(name='tg_wolfgang', definition=definition)
        self.assertEqual(self.entry.options['routes']['labels'], {'tg_wolfgang': 'Telegram Büro'})
        await self.call(name='tg_wolfgang', definition=definition, label='tg_wolfgang')
        self.assertNotIn('labels', self.entry.options['routes'])
        await self.call(name='tg_wolfgang', definition=definition, label='Telegram')
        await self.call(name='tg_wolfgang', delete=True)
        self.assertNotIn('labels', self.entry.options['routes'])
        self.assertEqual(self.entry.options['routes']['recipients'], {})

    async def test_invalid_label_or_alias_is_rejected_without_saving(self):
        definition = {'action': 'notify.mobile_app_phone'}
        await self.call(name='tg_wolfgang', definition=definition, label='x' * 101)
        self.assertEqual(self.errors[-1][1], 'invalid_label')
        await self.call(name='tg_wolfgang', definition=definition, label='line\nbreak')
        self.assertEqual(self.errors[-1][1], 'invalid_label')
        self.assertEqual(self.entry.options, self.options)
        import voluptuous as vol
        with self.assertRaises(vol.Invalid):
            await self.call(name='Telegram Wölfi', definition=definition)


if __name__ == '__main__':
    unittest.main()
