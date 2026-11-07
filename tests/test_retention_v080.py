"""Archive retention v0.8.0 regression tests."""
import importlib.util
from contextlib import closing
import tempfile
import time
import unittest
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(name):
    spec=importlib.util.spec_from_file_location("rn_retention_"+name,ROOT/(name+".py"))
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
rules=load("retention")
module=load("store")
QueueStore=module.QueueStore


def item(days,kind="windows"):
    return {
        "message":"Message body", "title":"Title", "target":"notify.test",
        "priority":"warning","message_type":kind,"archive_days":days,
        "ttl":0,"strategy":"always","action":"notify.send_message","payload":{}
    }


class RetentionValidationTest(unittest.TestCase):
    def test_defaults_and_named_types(self):
        values=rules.validate_retention({"windows":2,"pvec":0,"critical":90})
        self.assertEqual(rules.retention_for_message(
            {"priority":"warning","message_type":"windows"},values),2)
        self.assertEqual(rules.retention_for_message(
            {"priority":"critical"},values),90)
        self.assertEqual(rules.retention_for_message(
            {"priority":"warning","message_type":"unknown"},values),7)
        self.assertEqual(rules.retention_for_message(
            {"priority":"critical","message_type":"windows","archive":"delete_after_send"},values),0)
        self.assertEqual(rules.retention_for_message(
            {"priority":"critical","message_type":"windows","archive_days":12},values),12)

    def test_validation(self):
        for wrong in ({"x":-1},{"x":366},{"x":True},{"BAD TYPE":2},[],None):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                rules.validate_retention(wrong)


class ArchiveStoreRetentionTests(unittest.IsolatedAsyncioTestCase):
    async def test_delete_after_success_retains_queue_until_sent(self):
        with tempfile.TemporaryDirectory() as td:
            queue=QueueStore(Path(td)/"q.db")
            [message_id]=await queue.enqueue_many([item(0)],100)
            self.assertEqual((await queue.archive_detail(message_id))["message"],"Message body")
            self.assertEqual((await queue.claim_due(lane="notify"))["id"],message_id)
            await queue.succeeded(message_id)
            self.assertIsNone(await queue.archive_detail(message_id))
            self.assertEqual(await queue.count(),0)

    async def test_failed_message_with_zero_retention_stays_visible(self):
        with tempfile.TemporaryDirectory() as td:
            queue=QueueStore(Path(td)/"q.db")
            [message_id]=await queue.enqueue_many([item(0)],100)
            await queue.failed(message_id,1,"failure",1,permanent=True)
            self.assertEqual((await queue.archive_detail(message_id))["status"],"dead")

    async def test_type_and_expiry_of_completed_message(self):
        with tempfile.TemporaryDirectory() as td:
            queue=QueueStore(Path(td)/"q.db")
            [message_id]=await queue.enqueue_many([item(2)],100)
            await queue.succeeded(message_id)
            self.assertEqual((await queue.archive_detail(message_id))["message_type"],"windows")
            self.assertEqual((await queue.archive_detail(message_id))["retention_days"],2)
            with closing(sqlite3.connect(queue.path)) as db, db:
                db.execute("UPDATE message_archive SET updated_at=? WHERE id=?",
                           (time.time()-3*86400,message_id))
                db.commit()
            self.assertIsNone(await queue.archive_detail(message_id))

    async def test_completed_archive_byte_quota(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"q.db"
            queue=QueueStore(path)
            previous=module.MAX_COMPLETED_ARCHIVE_BYTES
            module.MAX_COMPLETED_ARCHIVE_BYTES=35
            try:
                ids=[]
                for label in ("a"*24,"b"*24):
                    [ident]=await queue.enqueue_many([{
                        **item(5),"message":label,"title":""
                    }],100)
                    await queue.succeeded(ident)
                    ids.append(ident)
                # A subsequent database transaction runs cleanup.
                remaining=await queue.archive_list()
                self.assertEqual(len(remaining),1)
                self.assertEqual(remaining[0]["id"],ids[-1])
            finally:
                module.MAX_COMPLETED_ARCHIVE_BYTES=previous

    async def test_legacy_archive_migration(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"q.db"
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("""CREATE TABLE message_archive (
                    id INTEGER PRIMARY KEY,title TEXT,message TEXT,target TEXT,
                    action TEXT,priority TEXT,status TEXT,created_at REAL,
                    updated_at REAL,attempts INTEGER,last_error TEXT)""")
                db.execute("""INSERT INTO message_archive(id,title,message,target,action,priority,
                    status,created_at,updated_at,attempts) VALUES(1,'t','legacy','notify.t',
                    'notify.send_message','info','sent',?,?,0)""",
                    (time.time(),time.time()))
                db.commit()
            queue=QueueStore(path)
            entry=await queue.archive_detail(1)
            self.assertEqual(entry["retention_days"],30)
            self.assertEqual(entry["message"],"legacy")


if __name__=="__main__":
    unittest.main()
