"""v0.7 archive persistence, search, status and Companion deep links."""
import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
spec = importlib.util.spec_from_file_location("rn_archive_store", ROOT / "store.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
QueueStore = module.QueueStore


def record(message="A long message", action="notify.mobile_app_test", payload=None,
           archive_url="/lovelace/reliable-notify"):
    return dict(message=message, title="Window alert", target="phone", priority="warning",
                action=action, payload=payload or {}, ttl=0, strategy="always",
                archive_url=archive_url)


class ArchiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_archive_survives_delivery_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"queue.db"
            store=QueueStore(path)
            [ident]=await store.enqueue_many([record()],100)
            self.assertEqual((await store.archive_detail(ident))["message"],"A long message")
            queued=await store.claim_due(lane="notify")
            self.assertIn("rn_message="+str(ident),json.loads(queued["payload_json"])["data"]["clickAction"])
            await store.succeeded(ident)
            other=QueueStore(path)
            detail=await other.archive_detail(ident)
            self.assertEqual(detail["status"],"sent")
            self.assertEqual(detail["message"],"A long message")
            self.assertEqual(len(await other.archive_list(search="LONG")),1)
            self.assertEqual(await other.archive_list(search="not in message"),[])

    async def test_does_not_override_explicit_click_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            [ident]=await store.enqueue_many([record(payload={
                "data":{"clickAction":"/lovelace/windows"}})],100)
            claimed=await store.claim_due(lane="notify")
            p=json.loads(claimed["payload_json"])
            self.assertEqual(p["data"]["clickAction"],"/lovelace/windows")
            self.assertNotIn("url",p["data"])

    async def test_dead_letter_is_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            [ident]=await store.enqueue_many([record(action="notify.send_message",
                archive_url=None)],100)
            await store.failed(ident,1,"service not available",1,permanent=True,category="invalid_payload")
            self.assertEqual((await store.archive_detail(ident))["status"],"dead")


if __name__=="__main__":
    unittest.main()
