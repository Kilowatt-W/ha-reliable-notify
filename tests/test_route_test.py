"""Admin-only target tests use the existing durable enqueue pipeline."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'


class RouteTestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        package = types.ModuleType('rn_test_routes')
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
        with patch.dict(sys.modules, {'rn_test_routes': package,
                'homeassistant': types.ModuleType('homeassistant'), 'homeassistant.components': components}):
            spec = importlib.util.spec_from_file_location('rn_test_routes.dashboard', ROOT/'dashboard.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        self.manager = types.SimpleNamespace(
            routes={'recipients': {'phone': {'action': 'notify.mobile_app_phone'}},
                    'groups': {'family': ['phone']}, 'persons': {'wolfgang': {'channels': {'mobile': 'phone'}}}},
            preview=lambda data: {'not_before': 42}, enqueue=AsyncMock(return_value=[5, 6]))
        self.hass = types.SimpleNamespace(data={'reliable_notify': {'entry': self.manager}})
        mod.register_dashboard(self.hass)
        self.errors, self.results = [], []
        self.conn = types.SimpleNamespace(user=types.SimpleNamespace(is_admin=True),
            send_error=lambda *args: self.errors.append(args), send_result=lambda *args: self.results.append(args))
        self.handler = callbacks['reliable_notify/test_route']
        self.msg = {'id': 1, 'category': 'recipients', 'name': 'phone', 'language': 'en'}

    async def test_nonadmin_and_missing_target_never_send(self):
        self.conn.user.is_admin = False
        await self.handler(self.hass, self.conn, self.msg)
        self.assertEqual(self.errors[-1][1], 'unauthorized')
        self.conn.user.is_admin = True
        await self.handler(self.hass, self.conn, {**self.msg, 'name': 'missing'})
        self.assertEqual(self.errors[-1][1], 'not_found')
        self.manager.enqueue.assert_not_awaited()

    async def test_real_test_uses_saved_alias_and_normal_delivery_policies(self):
        for category, name in [('recipients', 'phone'), ('groups', 'family'), ('persons', 'wolfgang')]:
            await self.handler(self.hass, self.conn, {**self.msg, 'category': category, 'name': name})
            data = self.manager.enqueue.await_args.args[0]
            self.assertEqual(data['recipients'], [name])
            self.assertEqual(data['priority'], 'info')
            self.assertEqual(data['archive_days'], 1)
            self.assertEqual(data['ttl'], 86400)
            self.assertNotIn('test_mode', data)
            self.assertNotIn('action', data)
            self.assertNotIn('acknowledgement', data)
            self.assertIn('Test notification', data['message'])
            self.assertEqual(self.results[-1][1], {'ids': [5, 6], 'not_before': 42})
        await self.handler(self.hass, self.conn, {**self.msg, 'language': 'de'})
        self.assertIn('Testnachricht', self.manager.enqueue.await_args.args[0]['message'])

    async def test_enqueue_errors_do_not_expose_transport_credentials(self):
        self.manager.enqueue.side_effect = ValueError('secret-token-123')
        await self.handler(self.hass, self.conn, self.msg)
        self.assertEqual(self.errors[-1][1], 'test_failed')
        self.assertNotIn('secret-token-123', str(self.errors))
        self.assertEqual(self.results, [])
