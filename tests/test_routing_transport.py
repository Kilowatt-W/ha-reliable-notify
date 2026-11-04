import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
BASE = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'
pkg = types.ModuleType('reliable_notify_test')
pkg.__path__ = [str(BASE)]
sys.modules[pkg.__name__] = pkg

def load(name):
    spec = importlib.util.spec_from_file_location(f'reliable_notify_test.{name}', BASE / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
routing = load('routing')
transport = load('transport')
store = load('store')

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.config = {'recipients': {
            'tg': {'action': 'telegram_bot.send_message', 'data': {'chat_id': 123}},
            'mail': {'action': 'notify.email', 'data': {}},
            'phone': {'target_entity': 'notify.mobile_app_test'}},
            'groups': {'person': ['tg', 'phone'], 'ops': ['person', 'mail', 'tg']}}

    def test_expansion_deduplicates(self):
        routing.validate_config(self.config)
        self.assertEqual([x[0] for x in routing.resolve(self.config, ['ops'])], ['tg', 'phone', 'mail'])

    def test_cyclic_group_fails(self):
        self.config['groups']['person'].append('ops')
        with self.assertRaisesRegex(ValueError, 'cyclic'):
            routing.validate_config(self.config)

    def test_unknown_member_fails(self):
        self.config['groups']['ops'].append('other')
        with self.assertRaisesRegex(ValueError, 'unknown'):
            routing.validate_config(self.config)

    def test_reject_arbitrary_service(self):
        self.config['recipients']['mail']['action'] = 'shell_command.delete_files'
        with self.assertRaises(ValueError):
            routing.validate_config(self.config)

    def test_photo_keyboard(self):
        (domain, action), payload = transport.create_payload({
            'action': 'telegram_bot.send_photo', 'message': 'Movement detected',
            'title': 'Alert', 'payload_json': '{"chat_id":123,"file":"/media/cam.jpg","inline_keyboard":["View:/view"]}'})
        self.assertEqual((domain, action), ('telegram_bot', 'send_photo'))
        self.assertEqual(payload['caption'], 'Alert\nMovement detected')
        self.assertEqual(payload['inline_keyboard'], ['View:/view'])
        self.assertNotIn('message', payload)

    def test_text_keyboard(self):
        _, payload = transport.create_payload({'action':'telegram_bot.send_message',
            'message':'Door open', 'title':'Alert', 'payload_json':'{"chat_id":123,"inline_keyboard":["OK:/ok"]}'})
        self.assertEqual(payload['message'], 'Alert\nDoor open')
        self.assertEqual(payload['inline_keyboard'], ['OK:/ok'])

class FanoutTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = store.QueueStore(str(Path(self.tmp.name) / 'queue.db'))
    async def asyncTearDown(self):
        self.tmp.cleanup()
    async def test_atomic_fanout_limit(self):
        jobs = [dict(message='x', title=None, target=f't{i}', priority='info', ttl=0,
                     action='notify.email', payload={}, strategy='always') for i in range(3)]
        with self.assertRaises(OverflowError):
            await self.db.enqueue_many(jobs, 2)
        self.assertEqual(await self.db.count(), 0)
        self.assertEqual(len(await self.db.enqueue_many(jobs, 10)), 3)
    async def test_dead_letter_retry(self):
        i = await self.db.enqueue('x', None, 't1', 'critical', 0, None, 'always', 10)
        await self.db.failed(i, 1, 'invalid', 10, permanent=True)
        self.assertEqual(await self.db.count(), 0)
        self.assertEqual(await self.db.dead_count(), 1)
        await self.db.retry_dead()
        self.assertEqual(await self.db.dead_count(), 0)
        self.assertEqual(await self.db.count(), 1)