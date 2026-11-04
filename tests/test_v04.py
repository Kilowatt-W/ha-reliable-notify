"""Standalone tests (no HA runtime) for queue lanes, photo cache and migration."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'

def load(name):
    spec = importlib.util.spec_from_file_location(name, BASE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

QueueStore = load('store').QueueStore
media = load('media')

class ReliableNotifyV04Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = QueueStore(str(Path(self.tmp.name)/'rn.db'))
    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_independent_lanes(self):
        await self.db.enqueue('telegram', None, 'tg', 'info', 0, None, 'always', 100,
                              action='telegram_bot.send_message')
        await self.db.enqueue('email', None, 'notify.email', 'info', 0, None, 'always', 100,
                              action='notify.send_message')
        mail = await self.db.claim_due(lane='notify')
        self.assertEqual(mail['message'], 'email')
        tg = await self.db.claim_due(lane='telegram')
        self.assertEqual(tg['message'], 'telegram')

    async def test_critical_unlimited_retries(self):
        job = await self.db.enqueue('critical', None, 'tg', 'critical', 0, None, 'always', 100)
        for attempt in range(1, 15):
            await self.db.failed(job, attempt, 'offline', 1, max_attempts=None)
            await self.db.retry_all()
        self.assertEqual(await self.db.dead_count(), 0)
        self.assertEqual(await self.db.count(), 1)

    async def test_photo_persists_after_source_overwrite(self):
        source = Path(self.tmp.name)/'source.jpg'
        source.write_bytes(b'first')
        cached = media.snapshot_file(str(source), str(Path(self.tmp.name)/'media'))
        source.write_bytes(b'second')
        self.assertEqual(Path(cached).read_bytes(), b'first')
        media.cleanup_media(str(Path(self.tmp.name)/'media'), {cached})
        self.assertTrue(Path(cached).exists())
        media.cleanup_media(str(Path(self.tmp.name)/'media'), set())
        self.assertFalse(Path(cached).exists())

    async def test_upgrade_old_db(self):
        await self.db.enqueue('old',None,'t','info',0,None,'always',10)
        with sqlite3.connect(self.db.path) as con:
            self.assertIn('media_path', [row[1] for row in con.execute('PRAGMA table_info(messages)')])
            self.assertIn('media_path', [row[1] for row in con.execute('PRAGMA table_info(dead_letters)')])

    async def test_retry_dead_with_photo_path(self):
        job = (await self.db.enqueue_many([dict(message='pic', title=None, target='telegram',
            priority='warning', ttl=0, dedup_key=None, strategy='always', action='telegram_bot.send_photo',
            payload={'file':'/media/reliable_notify/foo.jpg'}, media_path='/media/reliable_notify/foo.jpg')], 10))[0]
        await self.db.failed(job, 12, 'offline', 1, max_attempts=12)
        self.assertIn('/media/reliable_notify/foo.jpg',await self.db.pending_media_paths())
        await self.db.retry_dead()
        self.assertEqual((await self.db.claim_due())['media_path'], '/media/reliable_notify/foo.jpg')

if __name__ == '__main__':
    unittest.main()