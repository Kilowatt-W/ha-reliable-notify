"""v3 Telegram sent-message receipt store tests, no provider calls."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_v3_telegram_store",ROOT/"store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TelegramReceipts(unittest.IsolatedAsyncioTestCase):
    async def test_store_and_remove_message_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            queue=module.QueueStore(Path(d)/"queue.db")
            [ident]=await queue.enqueue_many([{
                "message":"Pump running",
                "title":"PVEC",
                "target":"telegram_wolfgang",
                "action":"telegram_bot.send_message",
                "priority":"info",
                "dedup_key":"pvec_status",
                "payload":{"chat_id":123456},
            }],100)
            self.assertTrue(await queue.record_telegram_receipt(ident,123456,78))
            self.assertEqual(await queue.telegram_receipts("pvec_status"),
                             [{"chat_id":123456,"message_id":78}])
            await queue.succeeded(ident)
            self.assertEqual(await queue.telegram_receipts("pvec_status"),
                             [{"chat_id":123456,"message_id":78}])
            self.assertEqual(await queue.telegram_receipt_deleted(123456,78),1)
            self.assertEqual(await queue.telegram_receipts("pvec_status"),[])

    async def test_unknown_or_corrupt_references_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            q=module.QueueStore(Path(d)/"queue.db")
            self.assertFalse(await q.record_telegram_receipt(999,42,300))
            self.assertFalse(await q.record_telegram_receipt("NaN",42,100))
            with self.assertRaises(ValueError):
                await q.telegram_receipts("")

if __name__=="__main__":
    unittest.main()
