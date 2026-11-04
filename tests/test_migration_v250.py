"""Non-destructive migration adviser regression tests.

The tests never access Home Assistant configuration files.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_migration_advisor",ROOT/"migration_advisor.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ROUTES={
    "recipients":{
        "telegram_wolfgang":{"action":"telegram_bot.send_message",
                             "data":{"chat_id":12345}},
        "phone":{"action":"notify.mobile_app_phone"},
        "mail":{"action":"notify.send_message","target_entity":"notify.email"},
    },
    "groups":{"family":["phone","telegram_wolfgang"]},
}


class AdvisoryTests(unittest.TestCase):
    def test_simple_telegram_static_destination(self):
        automation=[{"id":"bedroom","alias":"Fenster","actions":[
            {"action":"telegram_bot.send_message",
             "data":{"chat_id":12345,"message":"Fenster ist offen"}}]}]
        old=str(automation)
        report=module.analyze(automation,ROUTES)
        self.assertEqual(len(report),1)
        self.assertEqual(report[0]["status"],"proposed")
        self.assertEqual(report[0]["replacement"]["action"],
                         "notify.reliable_telegram_wolfgang")
        self.assertEqual(str(automation),old)

    def test_recurses_choices_and_scripts(self):
        block={"sequence":[{"choose":[{"sequence":[
            {"action":"notify.mobile_app_phone","data":{"message":"Alert"}},
        ]}]}]}
        report=module.analyze(block,ROUTES)
        self.assertEqual(report[0]["route"],"phone")

    def test_target_modern_notify_entity(self):
        report=module.analyze([
            {"action":"notify.send_message",
             "target":{"entity_id":"notify.email"},
             "data":{"title":"x","message":"y"}}],ROUTES)
        self.assertEqual(report[0]["route"],"mail")

    def test_dynamic_and_ambiguous_routes_not_rewritten(self):
        dup={**ROUTES,"recipients":{
            **ROUTES["recipients"],
            "telegram_second":{"action":"telegram_bot.send_message",
                               "data":{"chat_id":12345}}
        }}
        for data in (
            {"chat_id":"{{ states('input_text.chat') }}","message":"hello"},
            {"chat_id":12345,"message":"hello","inline_keyboard":[["OK"]]},
        ):
            report=module.analyze([{"action":"telegram_bot.send_message","data":data}],ROUTES)
            self.assertEqual(report[0]["status"],"manual")
        report=module.analyze([{"action":"telegram_bot.send_message",
                 "data":{"chat_id":12345,"message":"hi"}}],dup)
        self.assertEqual(report[0]["status"],"manual")

    def test_missing_notify_and_special_target(self):
        report=module.analyze([
            {"action":"notify.notify","data":{"message":"hello"}},
            {"action":"notify.send_message","target":{"area_id":"kitchen"},
             "data":{"message":"hi"}}],ROUTES)
        self.assertEqual([x["status"] for x in report],["manual","manual"])

    def test_limits(self):
        with self.assertRaises(ValueError):
            module.analyze([],ROUTES,limit=0)


if __name__=="__main__":
    unittest.main()
