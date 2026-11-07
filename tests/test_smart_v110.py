"""v1.1 smart notification regression tests."""
import importlib.util
from contextlib import closing
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(name):
    spec=importlib.util.spec_from_file_location("rn_smart_"+name,ROOT/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
smart=load("smart")
store=load("store")
QueueStore=store.QueueStore


def make(message, target="notify.one", strategy="always", dedup_key=None):
    return {"message":message,"priority":"info","action":"notify.send_message",
            "target":target,"payload":{},"ttl":0,"strategy":strategy,
            "dedup_key":dedup_key,"digest_window_seconds":300}


class QuietHoursTests(unittest.TestCase):
    def test_cross_midnight_and_critical_bypass(self):
        p=smart.validate_quiet_hours({"enabled":True,"start":"22:00","end":"07:00"})
        zone=ZoneInfo("Europe/Vienna")
        now=datetime(2026,11,4,23,10,tzinfo=zone).timestamp()
        deadline=smart.next_allowed_timestamp(now,"warning",p,"Europe/Vienna")
        result=datetime.fromtimestamp(deadline,zone)
        self.assertEqual((result.day,result.hour,result.minute),(5,7,0))
        self.assertEqual(smart.next_allowed_timestamp(now,"critical",p,"Europe/Vienna"),now)

    def test_invalid_quiet_hours(self):
        for p in ({"start":"25:00"},{"start":"07:00","end":"07:00"},{"enabled":"yes"}):
            with self.assertRaises(ValueError):
                smart.validate_quiet_hours(p)


class DigestTests(unittest.IsolatedAsyncioTestCase):
    async def test_digest_merges_pending_into_single_message(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            [first]=await q.enqueue_many([make("pump started",strategy="digest",dedup_key="pump")],100)
            [second]=await q.enqueue_many([make("pump stopped",strategy="digest",dedup_key="pump")],100)
            self.assertEqual(first,second)
            self.assertEqual(await q.count(),1)
            message=await q.archive_detail(first)
            self.assertIn("2 events",message["message"])
            self.assertIn("pump stopped",message["message"])
            self.assertIsNone(await q.claim_due(lane="notify"))

    async def test_digest_preserves_companion_archive_link(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            source={**make("first",strategy="digest",dedup_key="window"),
                    "action":"notify.mobile_app_my_phone",
                    "archive_url":"/lovelace/notifications"}
            [ident]=await q.enqueue_many([source],100)
            await q.enqueue_many([{**source,"message":"latest"}],100)
            import sqlite3
            with closing(sqlite3.connect(q.path)) as db, db:
                row=db.execute("SELECT payload_json FROM messages WHERE id=?",(ident,)).fetchone()
            data=json.loads(row[0])
            self.assertIn("rn_message="+str(ident),data["data"]["clickAction"])
            self.assertIn("rn_message="+str(ident),data["data"]["url"])

    async def test_per_target_limit_and_critical_bypass(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            await q.enqueue_many([make("a"),make("b"),make("third",target="notify.two")],100)
            first=await q.claim_due(lane="notify",rate_limit_per_minute=1)
            self.assertEqual(first["target"],"notify.one")
            await q.succeeded(first["id"])
            second=await q.claim_due(lane="notify",rate_limit_per_minute=1)
            self.assertEqual(second["target"],"notify.two")
            await q.succeeded(second["id"])
            self.assertIsNone(await q.claim_due(lane="notify",rate_limit_per_minute=1))
            [ident]=await q.enqueue_many([{**make("urgent"),"priority":"critical"}],100)
            urgent=await q.claim_due(lane="notify",rate_limit_per_minute=1)
            self.assertEqual(urgent["id"],ident)

if __name__=="__main__":
    unittest.main()
