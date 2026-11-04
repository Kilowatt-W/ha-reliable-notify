import asyncio
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/f'{name}.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
store=module('store')
media=module('media')

class QueueV05Tests(unittest.TestCase):
    def test_history_per_id_retry_and_delete(self):
        async def run():
            with tempfile.TemporaryDirectory() as td:
                q=store.QueueStore(Path(td)/'db.sqlite')
                a=await q.enqueue('hello',None,'notify.a','info',0,None,'always',100)
                b=await q.enqueue('other',None,'notify.b','critical',0,None,'always',100)
                self.assertEqual(await q.retry_one(a),1)
                self.assertEqual(await q.delete_one(b),1)
                self.assertEqual(await q.delete_one(b),0)
                await q.succeeded(a)
                history=await q.history()
                self.assertEqual([x['status'] for x in history],['sent','deleted'])
                self.assertNotIn('hello',str(history))
                self.assertEqual(await q.count(),0)
        asyncio.run(run())

    def test_retry_dead_one_and_reject_active_lease(self):
        async def run():
            with tempfile.TemporaryDirectory() as td:
                q=store.QueueStore(Path(td)/'db.sqlite')
                a=await q.enqueue('a',None,'notify.a','warning',0,None,'always',100)
                self.assertEqual((await q.claim_due())['id'],a)
                self.assertEqual(await q.delete_one(a),0)
                self.assertEqual(await q.retry_one(a),0)
                await q.failed(a,12,'network',10,max_attempts=12)
                self.assertEqual(await q.retry_one(a,True),1)
                self.assertEqual(await q.dead_count(),0)
                self.assertEqual(await q.count(),1)
        asyncio.run(run())

    def test_media_quota(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/'source.png'; source.write_bytes(b'12345')
            path=media.snapshot_file(str(source),str(root/'spool'),quota_bytes=5)
            self.assertEqual(Path(path).read_bytes(),b'12345')
            with self.assertRaises(OverflowError):
                media.snapshot_file(str(source),str(root/'spool'),quota_bytes=9)

    def test_smtp_separate_delivery_lane(self):
        async def run():
            with tempfile.TemporaryDirectory() as td:
                q=store.QueueStore(Path(td)/'db.sqlite')
                await q.enqueue('a',None,'notify.a','info',0,None,'always',100,action='smtp.send_message')
                await q.enqueue('b',None,'notify.b','info',0,None,'always',100)
                smtp=await q.claim_due(lane='smtp')
                notify=await q.claim_due(lane='notify')
                self.assertEqual(smtp['action'],'smtp.send_message')
                self.assertEqual(notify['action'],'notify.send_message')
        asyncio.run(run())

if __name__=='__main__': unittest.main()