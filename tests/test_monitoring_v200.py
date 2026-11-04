"""V2.0 route and monitoring regression tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(name):
    spec=importlib.util.spec_from_file_location("rn_v2_tests_"+name,ROOT/(name+".py"))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
routing=load("routing")
logging_utils=load("logging_utils")
store=load("store")


class RouteV2Test(unittest.TestCase):
    def test_safe_rest_command(self):
        self.assertTrue(routing.valid_action("rest_command.send_ntfy"))
        self.assertFalse(routing.valid_action("rest_command.https://evil"))
        self.assertFalse(routing.valid_action("rest_command.__import__"))
        self.assertFalse(routing.valid_action("http.post"))

    def test_person_zone_preference(self):
        config={"recipients":{
            "mobile":{"action":"notify.mobile_app_abc"},
            "telegram":{"action":"telegram_bot.send_message","data":{"chat_id":12345}}},
            "groups":{},
            "persons":{"wolfgang":{
                "entity":"person.wolfgang",
                "channels":{"phone":"mobile","telegram":"telegram"},
                "preferred":{"warning":"phone"},
                "preferred_by_zone":{"driving":{"warning":"telegram"},
                                     "home":{"warning":"phone"}}
            }}}
        routing.validate_config(config)
        self.assertEqual(routing.resolve(config,["wolfgang"],"warning",{
            "person.wolfgang":"driving"})[0][0],"telegram")
        self.assertEqual(routing.resolve(config,["wolfgang"],"warning",{
            "person.wolfgang":"home"})[0][0],"mobile")
        self.assertEqual(routing.resolve(config,["wolfgang"],"warning")[0][0],"mobile")

    def test_invalid_zone_channel(self):
        config={"recipients":{"phone":{"action":"notify.mobile_app_test"}},
            "persons":{"test":{"entity":"person.test",
                "channels":{"mobile":"phone"},
                "preferred_by_zone":{"home":{"critical":"telegram"}}}}}
        with self.assertRaises(ValueError):
            routing.validate_config(config)

    def test_log_levels(self):
        settings=logging_utils.validate_transport_logging({"telegram":"debug","smtp":"off"})
        self.assertEqual(settings["telegram"],"debug")
        self.assertEqual(settings["companion"],"warning")
        with self.assertRaises(ValueError):
            logging_utils.validate_transport_logging({"telegram":"password"})


class StatisticsTest(unittest.IsolatedAsyncioTestCase):
    async def test_delivery_rate_and_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=store.QueueStore(Path(tmp)/"q.db")
            [ident]=await q.enqueue_many([{
                "message":"hello","priority":"info","target":"notify.foo",
                "action":"notify.send_message","payload":{},"ttl":0}],100)
            await q.succeeded(ident)
            result=await q.statistics(days=7)
            self.assertEqual(result["transports"][0]["sent"],1)
            self.assertIsNotNone(result["transports"][0]["avg_delivery_seconds"])
            self.assertEqual(result["queued"],0)
            self.assertEqual(result["acknowledgements"]["total"],0)

    async def test_statistics_omit_message_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=store.QueueStore(Path(tmp)/"q.db")
            await q.enqueue_many([{
                "message":"SECRET_PASSPHRASE",
                "priority":"warning","target":"notify.foo",
                "action":"notify.send_message","payload":{}}],100)
            self.assertNotIn("SECRET_PASSPHRASE",str(await q.statistics(days=7)))


if __name__=="__main__":
    unittest.main()
