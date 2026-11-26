"""3.9.0: data of classic notify.reliable_<route> calls reaches the transport.

Before, Companion fields (channel, tag, sticky ...) of a migrated
``notify.mobile_app_*`` call became top-level transport keys and were dropped.
"""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
spec = importlib.util.spec_from_file_location("rn_routing_v390", ROOT / "routing.py")
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)


class TransportExtraTests(unittest.TestCase):
    def test_companion_fields_stay_in_the_transport_data(self):
        notify = {"channel": "Fenster", "tag": "fenster", "sticky": "true"}
        extra = routing.transport_extra("notify.mobile_app_phone", {}, notify)
        kept, dropped = routing.filter_extras("notify.mobile_app_phone", extra)
        self.assertEqual(dropped, [])
        self.assertEqual(kept, {"data": notify})

    def test_explicit_inner_data_wins_and_route_defaults_are_merged(self):
        extra = routing.transport_extra("notify.mobile_app_phone", {"data": {"tag": "explicit"}}, {"tag": "x", "group": "g"})
        self.assertEqual(extra["data"], {"tag": "explicit", "group": "g"})
        defaults = {"data": {"channel": "Störmeldung", "priority": "high", "ttl": 0}}
        payload = routing.merge_transport_payload("notify.mobile_app_phone", defaults, {"data": {"channel": "Fenster", "tag": "t"}})
        self.assertEqual(payload["data"], {"channel": "Fenster", "priority": "high", "ttl": 0, "tag": "t"})

    def test_telegram_keeps_top_level_fields_and_never_takes_a_chat_from_call_data(self):
        extra = routing.transport_extra("telegram_bot.send_message", {}, {"parse_mode": "html", "entity_id": "notify.other"})
        self.assertEqual(extra, {"parse_mode": "html"})
        self.assertEqual(routing.merge_transport_payload("telegram_bot.send_message", {"chat_id": 1}, {"parse_mode": "html"}),
                         {"chat_id": 1, "parse_mode": "html"})

    def test_entity_actions_and_plain_enqueue_are_unchanged(self):
        self.assertFalse(routing.is_classic_notify("notify.send_message"))
        self.assertTrue(routing.is_classic_notify("notify.alle_mobiles"))
        self.assertEqual(routing.transport_extra("notify.mobile_app_phone", {"data": {"a": 1}}, None), {"data": {"a": 1}})


class CompatWiringTests(unittest.TestCase):
    def test_compat_service_hands_its_data_over_as_notify_data(self):
        source = (ROOT / "notify_compat.py").read_text(encoding="utf-8")
        self.assertIn('request["_notify_data"] = opts', source)
        self.assertNotIn('request["data"] = opts', source)
        init = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('notify_data = data.get("_notify_data") or {}', init)
        self.assertIn("merge_transport_payload(action, rec.get(\"data\", {}), kept)", init)


if __name__ == "__main__":
    unittest.main()
