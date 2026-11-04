"""Long term delivery series and SQLite query index tests."""
import importlib.util
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_metrics_v25",ROOT/"store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MetricTests(unittest.IsolatedAsyncioTestCase):
    async def test_daily_metrics_survive_short_term_history_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            q=module.QueueStore(Path(td)/"q.db")
            [ident]=await q.enqueue_many([{
                "message":"do not leak", "target":"notify.test",
                "action":"notify.send_message","priority":"info",
                "payload":{},"ttl":0
            }],100)
            await q.succeeded(ident)
            recent=await q.long_term_statistics()
            self.assertTrue(recent)
            self.assertEqual(recent[0]["sent"],1)
            with sqlite3.connect(q.path) as db:
                db.execute("DELETE FROM delivery_history")
            q=module.QueueStore(q.path)
            retained=await q.long_term_statistics()
            self.assertEqual(retained[0]["sent"],1)
            self.assertNotIn("do not leak",str(retained))

    async def test_indices_and_date_validation(self):
        with tempfile.TemporaryDirectory() as td:
            q=module.QueueStore(Path(td)/"q.db")
            await q.count()  # Database schema/indexes are created lazily.
            with sqlite3.connect(q.path) as db:
                names={row[1] for row in db.execute("PRAGMA index_list(messages)")}
                self.assertIn("idx_queue_dedup_route",names)
            with self.assertRaises(ValueError):
                await q.long_term_statistics(366)

if __name__=="__main__":
    unittest.main()
