"""Persistent acknowledgement / escalation regression tests."""
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(name):
    spec=importlib.util.spec_from_file_location("rn_ack_test_"+name,ROOT/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
QueueStore=load("store").QueueStore
validate_acknowledgement=load("acknowledgement").validate_acknowledgement


class PlanTest(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(validate_acknowledgement({
            "required":True,
            "escalation":[{"after":300,"recipients":["it_team"]}]
        },"incident_1")["steps"][0]["after"],300)
        for plan,key in [
            ({"required":True,"escalation":[]},""),
            ({"required":False},"foo"),
            ({"required":True,"escalation":[{"after":10,"recipients":["a"]},
                                            {"after":5,"recipients":["b"]}]},"foo")
        ]:
            with self.assertRaises(ValueError):
                validate_acknowledgement(plan,key)


class AckStoreTest(unittest.IsolatedAsyncioTestCase):
    async def test_escalation_persists_and_stops_on_ack(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"q.db"
            q=QueueStore(path)
            plan=validate_acknowledgement({"required":True,
                "escalation":[{"after":5,"recipients":["it_team"]}]},"incident_42")
            await q.enqueue_many([{"message":"offline","priority":"critical",
                "action":"notify.send_message","target":"notify.test","payload":{},
                "ack_plan":plan}],100)
            restarted=QueueStore(path)
            self.assertEqual(await restarted.due_escalations(now=time.time()+20),[
                {**(await restarted.due_escalations(now=time.time()+20))[0]}
            ])
            self.assertEqual(await restarted.escalation_completed("incident_42",0),1)
            self.assertEqual(await restarted.due_escalations(now=time.time()+20),[])
            self.assertEqual(await restarted.acknowledgement("incident_42","tester"),1)
            self.assertEqual(await restarted.acknowledgement("incident_42","tester"),0)
            self.assertEqual(await restarted.active_acknowledgements(),[])

if __name__=="__main__":
    unittest.main()
