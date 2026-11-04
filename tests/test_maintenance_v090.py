"""Maintenance checks: noncritical expiry, critical preservation and DB probes."""
import importlib.util
import tempfile
import unittest
import sqlite3
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_maintenance_store",ROOT/"store.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
QueueStore=mod.QueueStore

class MaintenanceTest(unittest.IsolatedAsyncioTestCase):
    async def test_noncritical_expiry_keeps_critical_failures(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            ids=[]
            for priority in ("info","warning","critical"):
                [ident]=await q.enqueue_many([dict(message="alert",title=priority,
                    target="notify.test",action="notify.send_message",
                    priority=priority,ttl=0,payload={})],100)
                await q.failed(ident,1,"authentication",10,permanent=True)
                ids.append(ident)
            with sqlite3.connect(q.path) as con:
                con.execute("UPDATE dead_letters SET failed_at=?",(time.time()-45*86400,))
            result=await q.maintenance(30)
            self.assertEqual(result["removed_dead_letters"],2)
            self.assertEqual(result["critical_dead_letters"],1)
            self.assertEqual(await q.dead_count(),1)
            self.assertEqual(result["integrity"],"ok")
            self.assertGreater(result["database_bytes"],0)

    async def test_invalid_retention_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueueStore(Path(td)/"q.db")
            with self.assertRaises(ValueError):
                await q.maintenance(0)

if __name__=="__main__":
    unittest.main()
