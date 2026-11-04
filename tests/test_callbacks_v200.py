"""Reliable Notify v2.0 signed actions and crash-safe escalation tests."""
import asyncio
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"

def load(module):
    spec=importlib.util.spec_from_file_location("rn_v2_"+module,ROOT/(module+".py"))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

callbacks=load("callbacks")
QueueStore=load("store").QueueStore


def incident(key="critical_alarm",steps=None):
    return dict(message="IT outage",title="WAN failure",target="admin",
        priority="critical",action="notify.mobile_app_phone",
        payload={},archive_days=30,
        ack_plan={"key":key,"steps":steps or [{"after":15,"recipients":["fallback"]}]})


class CallbackSecurityTest(unittest.TestCase):
    def test_telegram_size(self):
        token=callbacks.make_token("a"*64,"long_key_"+"z"*90,"ack")
        self.assertLessEqual(len(token),64)
        self.assertEqual(callbacks.read_token("a"*64,token),
            (callbacks.action_id("long_key_"+"z"*90),"ack"))

    def test_tampering_and_wrong_key(self):
        good=callbacks.make_token("b"*64,"home_alarm","ack")
        self.assertIsNone(callbacks.read_token("c"*64,good))
        self.assertIsNone(callbacks.read_token("b"*64,good.replace(".ack.",".snooze.")))
        self.assertIsNone(callbacks.read_token("b"*64,"X"*100))
        self.assertIsNone(callbacks.read_token("b"*64,None))

    def test_operations_distinct(self):
        secret="secret"
        key="alarm"
        for action in ("ack","snooze","escalate"):
            value=callbacks.make_token(secret,key,action)
            self.assertEqual(callbacks.read_token(secret,value),(callbacks.action_id(key),action))
        with self.assertRaises(ValueError):
            callbacks.make_token(secret,key,"erase")


class EscalationTransactionTest(unittest.IsolatedAsyncioTestCase):
    async def test_idempotent_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"queue.db"
            store=QueueStore(path)
            await store.enqueue_many([incident()],100)
            jobs=await store.due_escalations(now=time.time()+20)
            self.assertEqual(len(jobs),1)
            # Force the time condition without waiting for 15 seconds.
            with __import__("sqlite3").connect(path) as db:
                db.execute("UPDATE acknowledgements SET created_at=created_at-60")
            store=QueueStore(path)
            prepared=[("fallback",{"action":"notify.mobile_app_phone","data":{}})]
            result=await store.enqueue_escalation_atomic("critical_alarm",0,prepared)
            self.assertEqual(len(result),1)
            count=await store.count()
            self.assertEqual(count,2)
            restarted=QueueStore(path)
            self.assertEqual(await restarted.enqueue_escalation_atomic("critical_alarm",0,prepared),[])
            self.assertEqual(await restarted.count(),count)

    async def test_ack_cancels_queued_escalation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            await store.enqueue_many([incident()],100)
            self.assertTrue(await store.act_on_incident("critical_alarm","ack","user"))
            self.assertFalse(await store.act_on_incident("critical_alarm","ack","user"))
            self.assertEqual(await store.enqueue_escalation_atomic(
                "critical_alarm",0,[("fallback",{"action":"notify.mobile_app_phone"})]),[])
            self.assertEqual(await store.active_acknowledgements(),[])

    async def test_ack_cancels_only_unleased_escalation_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"queue.db"
            q=QueueStore(path)
            await q.enqueue_many([incident()],100)
            with __import__("sqlite3").connect(path) as db:
                db.execute("UPDATE acknowledgements SET created_at=created_at-60")
            [escalation_id]=await q.enqueue_escalation_atomic(
                "critical_alarm",0,[("fallback",{"action":"notify.mobile_app_phone","data":{}})])
            self.assertEqual(await q.count(),2)
            self.assertTrue(await q.acknowledgement("critical_alarm","admin"))
            self.assertEqual(await q.count(),1)
            self.assertEqual((await q.archive_detail(escalation_id))["status"],"cancelled")
            self.assertEqual(await q.active_acknowledgements(),[])

    async def test_unknown_token_identity_does_not_ack(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            await store.enqueue_many([incident()],100)
            identity=callbacks.action_id("critical_alarm")
            self.assertEqual(await store.incident_key_from_action_id(identity),"critical_alarm")
            self.assertIsNone(await store.incident_key_from_action_id(callbacks.action_id("other")))

    async def test_snooze_and_immediate_escalate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            await store.enqueue_many([incident()],100)
            self.assertTrue(await store.act_on_incident("critical_alarm","snooze"))
            self.assertEqual(await store.due_escalations(now=time.time()+100),[])
            self.assertTrue(await store.act_on_incident("critical_alarm","escalate"))
            self.assertEqual(len(await store.due_escalations()),1)

    async def test_invalid_routing_does_not_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=QueueStore(Path(tmp)/"queue.db")
            await store.enqueue_many([incident()],100)
            with __import__("sqlite3").connect(store.path) as db:
                db.execute("UPDATE acknowledgements SET created_at=created_at-60")
            with self.assertRaises(ValueError):
                await store.enqueue_escalation_atomic("critical_alarm",0,
                    [("photo",{"action":"telegram_bot.send_photo"})])
            self.assertEqual(len(await store.due_escalations()),1)


if __name__=="__main__":
    unittest.main()
