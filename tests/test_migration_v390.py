"""3.9.0: migration proposals for the cases that used to be "check manually"."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
spec = importlib.util.spec_from_file_location("rn_advisor_v390", ROOT / "migration_advisor.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ROUTES = {"recipients": {
    "tricorder": {"action": "notify.mobile_app_tricorder", "data": {"data": {"channel": "Störmeldung"}}},
    "tg_home": {"action": "notify.send_message", "target_entity": "notify.telegram_home"},
    "tg_chat": {"action": "telegram_bot.send_message", "data": {"chat_id": 42}},
}, "groups": {}, "persons": {}}


def one(action, **node):
    return module.analyze([{"id": "1700000000001", "alias": "Fenster", "actions": [{"action": action, **node}]}], ROUTES)[0]


class ProposalTests(unittest.TestCase):
    def test_editor_metadata_no_longer_blocks_and_is_kept(self):
        item = one("notify.send_message", metadata={}, target={"entity_id": "notify.telegram_home"},
                   data={"message": "Hallo"})
        self.assertEqual(item["status"], "proposed")
        self.assertEqual(item["replacement"], {"action": "notify.reliable_tg_home", "data": {"message": "Hallo"}, "metadata": {}})
        self.assertEqual(item["owner"], {"kind": "automation", "id": "1700000000001"})

    def test_companion_data_is_carried_over_through_the_classic_service(self):
        item = one("notify.mobile_app_tricorder", metadata={},
                   data={"title": "Fenster", "message": "offen", "data": {"tag": "fenster", "channel": "Fenster", "sticky": "true"}})
        self.assertEqual(item["reason_code"], "unambiguous_data")
        self.assertEqual(item["replacement"]["action"], "notify.reliable_tricorder")
        self.assertEqual(item["replacement"]["data"]["data"], {"tag": "fenster", "channel": "Fenster", "sticky": "true"})

    def test_companion_fields_named_like_options_use_enqueue(self):
        item = one("notify.mobile_app_tricorder", data={"message": "x", "data": {"ttl": 0, "priority": "high"}})
        self.assertEqual(item["replacement"], {"action": "reliable_notify.enqueue", "data": {
            "recipients": ["tricorder"], "message": "x", "data": {"data": {"ttl": 0, "priority": "high"}}}})

    def test_response_variable_and_device_targets(self):
        item = one("telegram_bot.send_photo", response_variable="sent", data={"chat_id": 42, "message": "x"})
        self.assertEqual((item["status"], item["reason_code"]), ("manual", "response_used"))
        node = {"action": "notify.send_message", "target": {"device_id": "dev1"}, "data": {"message": "hi"}}
        self.assertEqual(module.analyze([node], ROUTES, devices={"dev1": ["notify.telegram_home"]})[0]["route"], "tg_home")
        ambiguous = module.analyze([node], ROUTES, devices={"dev1": ["notify.a", "notify.b"]})[0]
        self.assertEqual(ambiguous["reason_code"], "complex_target")
        self.assertEqual(module.analyze([node], ROUTES)[0]["reason_code"], "complex_target")

    def test_missing_route_suggests_a_target_and_bell_entries_are_ignored(self):
        item = one("notify.send_message", target={"entity_id": "notify.echo_kueche"}, data={"message": "Essen"})
        self.assertEqual(item["reason_code"], "no_route")
        self.assertEqual(item["suggested_target"], {"action": "notify.send_message", "target_entity": "notify.echo_kueche"})
        self.assertEqual(module.analyze([{"action": "notify.persistent_notification", "data": {"message": "x"}}], ROUTES), [])

    def test_unknown_notify_service_is_reported_instead_of_a_broken_target(self):
        node = {"action": "notify.all_mobiles", "data": {"message": "x"}}
        item = module.analyze([node], ROUTES, services=frozenset({"mobile_app_tricorder", "send_message"}))[0]
        self.assertEqual((item["status"], item["reason_code"]), ("manual", "unknown_service"))
        self.assertNotIn("suggested_target", item)
        self.assertEqual(module.analyze([node], ROUTES)[0]["reason_code"], "no_route")

    def test_script_owner_is_the_script_key(self):
        report = module.analyze({"waschmaschine": {"sequence": [{"action": "notify.mobile_app_tricorder", "data": {"message": "fertig"}}]}}, ROUTES)
        self.assertEqual(report[0]["owner"], {"kind": "script", "id": "waschmaschine"})


if __name__ == "__main__":
    unittest.main()
