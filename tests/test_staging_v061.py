"""v0.6.1 staging inbox regressions (no Home Assistant runtime required)."""
import asyncio
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
spec = importlib.util.spec_from_file_location("rn_store_stage", ROOT / "store.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
QueueStore = module.QueueStore


class StagingTest(unittest.IsolatedAsyncioTestCase):
    async def test_staging_survives_restart_and_is_never_claimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.db"
            store = QueueStore(path)
            [ident] = await store.enqueue_many([{
                "message": "Long test message", "title": "Test",
                "target": "(staged)", "priority": "info",
                "action": "reliable_notify.staged", "payload": {},
                "ttl": 0, "strategy": "always",
            }], 100)
            self.assertEqual(await store.staged_count(), 1)
            self.assertEqual((await store.staged())[0]["message"], "Long test message")
            store = QueueStore(path)
            for lane in ("notify", "smtp", "telegram"):
                self.assertIsNone(await store.claim_due(lane=lane))
            await store.retry_all()
            self.assertIsNone(await store.claim_due(lane="notify"))
            self.assertEqual(await store.retry_one(ident), 0)
            self.assertEqual(await store.assign_staged(
                ident, "notify.mobile_app_test", "mobile_test",
                {"data": {"clickAction": "/lovelace/test", "url": "/lovelace/test"}}), 1)
            claimed = await store.claim_due(lane="notify")
            self.assertEqual(claimed["id"], ident)
            self.assertEqual(claimed["action"], "notify.mobile_app_test")
            self.assertEqual(await store.staged_count(), 0)

    async def test_delete_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            [ident] = await store.enqueue_many([{
                "message": "not sent", "target": "(staged)", "priority": "info",
                "action": "reliable_notify.staged", "payload": {}, "ttl": 0,
            }], 100)
            self.assertEqual(await store.delete_one(ident), 1)
            self.assertEqual(await store.staged_count(), 0)


if __name__ == "__main__":
    unittest.main()
