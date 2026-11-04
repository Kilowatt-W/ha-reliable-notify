"""Online backup integrity, WAL capture, retention tests."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_backup_v2",ROOT/"store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
QueueStore=module.QueueStore

class BackupTests(unittest.IsolatedAsyncioTestCase):
    async def test_online_snapshot_and_restore(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"queue.db"
            queue=QueueStore(path)
            [ident]=await queue.enqueue_many([{
                "message":"queued alert","title":"ALERT",
                "priority":"critical","target":"notify.foo",
                "action":"notify.send_message","payload":{},"ttl":0}],100)
            result=await queue.online_backup(Path(td)/"backups",min_free_bytes=0)
            saved=Path(td)/"backups"/result["filename"]
            self.assertTrue(saved.is_file())
            self.assertEqual(result["integrity"],"ok")
            with sqlite3.connect(saved) as db:
                self.assertEqual(db.execute("SELECT message FROM messages WHERE id=?",(ident,)).fetchone()[0],"queued alert")
                self.assertEqual(db.execute("PRAGMA quick_check(1)").fetchone()[0],"ok")

    async def test_backup_retention(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            folder=Path(td)/"backup"
            for _ in range(4):
                await q.online_backup(folder,keep=2,min_free_bytes=0)
            self.assertLessEqual(len(list(folder.glob("reliable_notify-*.sqlite3"))),2)

    async def test_invalid_backup_policy(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            with self.assertRaises(ValueError):
                await q.online_backup(Path(td)/"backup",keep=0)


if __name__=="__main__":
    unittest.main()
