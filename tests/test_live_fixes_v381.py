"""v3.8.1 fixes found on the live installation.

- 204 dead letters: status messages with ``parse_mode: HTML`` sent to a Telegram
  notify entity through notify.send_message (HA rejects parse_mode there).
- HA warned at shutdown that Reliable Notify loops were still running.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
spec = importlib.util.spec_from_file_location("rn_routing_v381", ROOT / "routing.py")
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)


class TelegramEntityTests(unittest.TestCase):
    def test_telegram_notify_entity_is_sent_through_the_bot_action(self):
        rec = {"action": "notify.send_message", "target_entity": "notify.telegram_bot_1_2", "data": {}}
        routed = routing.telegram_entity_route(rec)
        self.assertEqual(routed["action"], "telegram_bot.send_message")
        self.assertEqual(routed["data"], {"entity_id": "notify.telegram_bot_1_2"})
        self.assertEqual(rec["data"], {})  # input not mutated
        # parse_mode and keyboards are kept for the bot action instead of being rejected.
        kept, dropped = routing.filter_extras(routed["action"], {"parse_mode": "HTML", "inline_keyboard": ["A:/a"]})
        self.assertEqual((sorted(kept), dropped), (["inline_keyboard", "parse_mode"], []))
        self.assertEqual(routing.filter_extras("notify.send_message", {"parse_mode": "HTML"})[1], ["parse_mode"])
        self.assertTrue(routing.valid_action(routed["action"]))

    def test_manager_wiring(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('via_entity = action == "notify.send_message" and self._is_telegram_entity(rec.get("target_entity"))', source)
        self.assertIn("rec=telegram_entity_route(rec)", source)          # escalations too
        self.assertIn('entry.platform == "telegram_bot"', source)
        # All long-running loops are config-entry background tasks (cancelled on HA stop).
        self.assertIn("self.entry.async_create_background_task(self.hass, coro", source)
        self.assertNotIn("self.tasks.append(self.hass.async_create_task(", source)
        self.assertEqual(source.count("self.tasks.append(self._background("), 7)


if __name__ == "__main__":
    unittest.main()
