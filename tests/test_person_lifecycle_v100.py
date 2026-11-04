"""Version 1.0 person routing and Companion lifecycle tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(name):
    spec=importlib.util.spec_from_file_location("rn_v1_"+name,ROOT/(name+".py"))
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
routing=load("routing")
lifecycle=load("lifecycle")
store=load("store")


class PersonTest(unittest.TestCase):
    def test_person_priority_channels(self):
        config={"recipients":{
            "phone":{"action":"notify.mobile_app_phone"},
            "telegram":{"action":"telegram_bot.send_message","data":{"chat_id":123}},
        },"persons":{"wolfgang":{"entity":"person.wolfgang",
            "channels":{"mobile":"phone","telegram":"telegram"},
            "preferred":{"info":"mobile","warning":"telegram","critical":["mobile","telegram"]}}},
            "groups":{"family":["wolfgang"]}}
        routing.validate_config(config)
        self.assertEqual([name for name,_ in routing.resolve(config,["wolfgang"],"info")],["phone"])
        self.assertEqual([name for name,_ in routing.resolve(config,["family"],"warning")],["telegram"])
        self.assertEqual(len(routing.resolve(config,["family"],"critical")),2)

    def test_invalid_person_reference(self):
        config={"recipients":{},"persons":{"tester":{"channels":{"mobile":"missing"}}}}
        with self.assertRaises(ValueError):
            routing.validate_config(config)

    def test_tag_deterministic(self):
        tag=lifecycle.notification_tag("window_bedroom")
        self.assertEqual(tag,lifecycle.notification_tag("window_bedroom"))
        self.assertTrue(tag.startswith("rn_"))
        self.assertLess(len(tag),65)


class MobileLifecycleTest(unittest.IsolatedAsyncioTestCase):
    async def test_auto_tag_and_manual_tag_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=store.QueueStore(Path(tmp)/"queue.db")
            [ident]=await q.enqueue_many([{
                "message":"Open","target":"phone","priority":"warning",
                "action":"notify.mobile_app_phone",
                "dedup_key":"window_bedroom","payload":{},
            }],100)
            record=await q.claim_due(lane="notify")
            self.assertEqual(json.loads(record["payload_json"])["data"]["tag"],
                             lifecycle.notification_tag("window_bedroom"))
            await q.succeeded(ident)
            await q.enqueue_many([{
                "message":"Open","target":"phone","priority":"warning",
                "action":"notify.mobile_app_phone",
                "dedup_key":"window_bedroom",
                "payload":{"data":{"tag":"custom"}},
            }],100)
            other=await q.claim_due(lane="notify")
            self.assertEqual(json.loads(other["payload_json"])["data"]["tag"],"custom")

if __name__=="__main__":
    unittest.main()
