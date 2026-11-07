"""Run: python -m unittest discover -s tests -v (from repo root)."""
import importlib.util
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location("reliable_notify_store", Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify" / "store.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
QueueStore = module.QueueStore


class QueueStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "queue.db")
        self.db = QueueStore(self.path)

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def add(self, message="hi", key=None, strategy="always", ttl=0):
        return await self.db.enqueue(message, None, "notify.example", "warning", ttl,
                                     key, strategy, 100)

    async def test_persistence_and_ack(self):
        job = await self.add()
        reopened = QueueStore(self.path)
        self.assertEqual((await reopened.next_due())["id"], job)
        await reopened.succeeded(job)
        self.assertEqual(await self.db.count(), 0)

    async def test_replace(self):
        await self.add("old", "k", "replace")
        await self.add("new", "k", "replace")
        self.assertEqual(await self.db.count(), 1)
        self.assertEqual((await self.db.next_due())["message"], "new")

    async def test_retry_and_manual_retry(self):
        job = await self.add()
        await self.db.failed(job, 1, "offline", 30)
        self.assertIsNone(await self.db.next_due())
        await self.db.retry_all()
        self.assertEqual((await self.db.next_due())["attempts"], 1)

    async def test_queue_limit(self):
        await self.db.enqueue("a", None, "notify.example", "info", 0, None,
                              "always", 1)
        with self.assertRaises(OverflowError):
            await self.db.enqueue("b", None, "notify.example", "info", 0, None,
                                  "always", 1)

    async def test_scoped_replace(self):
        await self.db.enqueue('a', None, 'notify.one', 'info', 0, 'same', 'replace', 100)
        await self.db.enqueue('b', None, 'notify.two', 'info', 0, 'same', 'replace', 100)
        self.assertEqual(await self.db.count(), 2)
        await self.db.enqueue('c', None, 'notify.one', 'info', 0, 'same', 'replace', 100)
        self.assertEqual(await self.db.count(), 2)

    async def test_claim_lease_and_reopen(self):
        job = await self.add()
        first = await self.db.claim_due()
        self.assertEqual(first['id'], job)
        self.assertIsNone(await self.db.claim_due())
        reopened = QueueStore(self.path)
        self.assertIsNone(await reopened.next_due())
        await reopened.failed(job, 1, 'offline', 30)
        await reopened.retry_all()
        self.assertEqual((await reopened.claim_due())['id'], job)

    async def test_payload_and_metrics(self):
        job = await self.db.enqueue('alert', 'title', '', 'critical', 0, 'key',
                                    'always', 100, action='telegram_bot.send_message',
                                    payload={'target': 123, 'parse_mode': 'HTML'})
        import json
        item = await self.db.claim_due()
        self.assertEqual(json.loads(item['payload_json'])['target'], 123)
        await self.db.failed(job, 1, 'network', 10)
        await self.db.retry_all()
        item = await self.db.claim_due()
        await self.db.succeeded(item['id'])
        self.assertEqual(await self.db.metrics(), {'failures': 1, 'sent': 1})
        self.assertEqual((await QueueStore(self.path).metrics())['sent'], 1)

    async def test_cancel_and_inflight_safety(self):
        job = await self.add('old', 'window', 'replace')
        await self.db.claim_due()
        await self.db.enqueue('new', None, 'notify.example', 'warning', 0,
                              'window', 'replace', 100)
        self.assertEqual(await self.db.count(), 2)
        self.assertEqual(await self.db.cancel('window'), 1)
        self.assertEqual(await self.db.count(), 1)
        await self.db.succeeded(job)
        self.assertEqual(await self.db.count(), 0)

    async def test_schema_migration(self):
        import sqlite3
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('''CREATE TABLE messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT NOT NULL,
              title TEXT, target TEXT NOT NULL, priority TEXT NOT NULL,
              dedup_key TEXT, expires_at REAL, attempts INTEGER NOT NULL DEFAULT 0,
              next_attempt REAL NOT NULL, created_at REAL NOT NULL, last_error TEXT)''')
        job = await self.add('migrated')
        row = await self.db.next_due()
        self.assertEqual(row['id'], job)
        self.assertEqual(row['action'], 'notify.send_message')