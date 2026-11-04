"""State-condition suppression keeps archived audit without delivery failures."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_cond_store",ROOT/"store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SuppressTests(unittest.IsolatedAsyncioTestCase):
    async def test_suppressed_archive_and_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=module.QueueStore(Path(tmp)/"q.db")
            [ident]=await q.enqueue_many([{
                "message":"stale alert","target":"phone","priority":"warning",
                "action":"notify.mobile_app_phone",
                "payload":{"__rn_condition":{"entity_id":"binary_sensor.window","state":"on"}},
                "ttl":0,"archive_days":7}],100)
            self.assertEqual(await q.suppress(ident),1)
            self.assertEqual(await q.count(),0)
            self.assertEqual((await q.archive_detail(ident))["status"],"suppressed")
            self.assertEqual(await q.suppress(ident),0)

    async def test_zero_retention_suppresses_without_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=module.QueueStore(Path(tmp)/"q.db")
            [ident]=await q.enqueue_many([{
                "message":"stale alert","target":"phone","priority":"info",
                "action":"notify.mobile_app_phone","payload":{},
                "ttl":0,"archive_days":0}],100)
            await q.suppress(ident)
            self.assertIsNone(await q.archive_detail(ident))


if __name__=="__main__":
    unittest.main()
