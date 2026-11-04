"""Synthetic v3 queue durability/load checks.

Real seven-day HA OS soak tests remain an operator acceptance task.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_v300_load",ROOT/"store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SoakSimulation(unittest.IsolatedAsyncioTestCase):
    async def test_burst_persists_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"reliable.db"
            sender=module.QueueStore(db)
            batch=[{
                "message":"test event "+str(i),
                "title":"Load test",
                "target":"notify.phone",
                "action":"notify.send_message",
                "priority":"info",
                "payload":{},
                "ttl":0,
                "dedup_key":"burst_"+str(i),
                "archive_days":1,
            } for i in range(250)]
            ids=await sender.enqueue_many(batch,1000)
            self.assertEqual(len(set(ids)),250)
            sender=module.QueueStore(db)
            self.assertEqual(await sender.count(),250)
            report=await sender.maintenance(30)
            self.assertEqual(report["integrity"],"ok")
            self.assertEqual(await sender.count(),250)

    async def test_critical_preserved_in_archive_quota(self):
        with tempfile.TemporaryDirectory() as td:
            q=module.QueueStore(Path(td)/"a.db")
            [identifier]=await q.enqueue_many([{
                "message":"Do not discard this critical alert",
                "target":"notify.phone",
                "action":"notify.send_message",
                "priority":"critical",
                "payload":{},
                "archive_days":0,
            }],100)
            await q.maintenance(1)
            self.assertEqual(await q.count(),1)
            self.assertIsNotNone(await q.archive_detail(identifier))


if __name__=="__main__":
    unittest.main()
