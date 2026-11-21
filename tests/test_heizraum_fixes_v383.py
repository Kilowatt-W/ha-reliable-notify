"""v3.8.3 fixes reported by the Heizraum migration on the live installation.

1. Telegram acknowledgement buttons failed with Button_data_invalid: HA's telegram_bot
   only splits "Title:/cmd" text buttons, so "Title:RN2..." became the callback_data.
2. persistent_notification.dismiss_all (start-up automation) acknowledged every open
   incident mirrored to the bell.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"


def load(name):
    spec = importlib.util.spec_from_file_location("rn_v383_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


callbacks = load("callbacks")
incidents = load("incidents")


def make_row_inline_keyboard(row):
    """Copy of HA 2026.11.2 telegram_bot/bot.py _make_row_inline_keyboard (callback buttons)."""
    buttons = []
    if isinstance(row, str):
        for key in row.split(","):
            if ":/" in key:
                label = key.split(":/")[0]
                buttons.append((label, key[len(label) + 1:]))
            else:
                buttons.append((key.strip()[1:].upper(), key))
    else:
        for text, data in row:
            buttons.append((text, data))
    return buttons


class TelegramKeyboardTests(unittest.TestCase):
    secret = "s" * 32
    titles = {"ack": "Bestätigen", "snooze": "15 Min. später", "escalate": "Eskalieren"}

    def tokens(self, key="heizraum_brenner"):
        return {name: callbacks.make_token(self.secret, key, name) for name in ("ack", "snooze", "escalate")}

    def test_callback_data_is_exactly_the_signed_token(self):
        tokens = self.tokens("a" * 200)
        keyboard = json.loads(json.dumps(callbacks.telegram_keyboard(self.titles, tokens)))  # survives the queue
        buttons = [b for row in keyboard for b in make_row_inline_keyboard(row)]
        self.assertEqual([b[0] for b in buttons], ["Bestätigen", "15 Min. später", "Eskalieren"])
        for (title, data), name in zip(buttons, ("ack", "snooze", "escalate")):
            self.assertEqual(data, tokens[name])
            self.assertLessEqual(len(data.encode("utf-8")), 64)
            self.assertEqual(callbacks.read_token(self.secret, data)[1], name)

    def test_old_text_keyboard_was_invalid_and_is_repaired_on_delivery(self):
        tokens = self.tokens()
        legacy = [self.titles["ack"] + ":" + tokens["ack"] + ", " + self.titles["snooze"] + ":" + tokens["snooze"],
                  self.titles["escalate"] + ":" + tokens["escalate"]]
        broken = make_row_inline_keyboard(legacy[0])
        self.assertTrue(all(len(data.encode("utf-8")) > 64 or data != tokens["ack"] for _, data in broken))
        self.assertEqual(callbacks.repair_keyboard(legacy), callbacks.telegram_keyboard(self.titles, tokens))
        # Keyboards of the caller stay untouched.
        own = ["OK:/ok, Später:/later", [["Öffnen", "/open"]], "/plain"]
        self.assertEqual(callbacks.repair_keyboard(own), own)
        mixed = [legacy[1], "Tür:/door"]
        self.assertEqual(callbacks.repair_keyboard(mixed), [[["Eskalieren", tokens["escalate"]]], "Tür:/door"])
        self.assertEqual(callbacks.repair_keyboard("Eskalieren:/x"), "Eskalieren:/x")

    def test_manager_wiring(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('prepared.setdefault("inline_keyboard",telegram_keyboard(titles,tokens))', source)
        self.assertIn('payload["inline_keyboard"]=repair_keyboard(payload["inline_keyboard"])', source)
        self.assertNotIn('titles["ack"]+":"+tokens["ack"]', source)


class DismissAllTests(unittest.TestCase):
    def test_single_dismiss_acknowledges_but_dismiss_all_restores(self):
        self.assertEqual(incidents.dismissed_incidents("removed", {"rn_brenner": 1}), ["brenner"])
        everything = {"rn_brenner": 1, "rn_oel": 2, "zigbee_neustart": 3}
        self.assertEqual(incidents.dismissed_incidents("removed", everything), [])
        self.assertEqual(incidents.bulk_removed_incidents("removed", everything), ["brenner", "oel"])
        self.assertEqual(incidents.bulk_removed_incidents("removed", {"rn_brenner": 1}), [])
        self.assertEqual(incidents.bulk_removed_incidents("added", everything), [])
        self.assertEqual(incidents.bulk_removed_incidents("removed", everything, {"oel"}), ["brenner"])

    def test_manager_restores_mirrors_after_bulk_removal(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("bulk_removed_incidents(update_type, notifications, self._mirror_dismissing)", source)
        self.assertIn("self.hass.async_create_task(self._restore_mirrors(restore))", source)
        restore = source.split("async def _restore_mirrors(self, keys):")[1][:400]
        self.assertIn("self.sync_mirror(record)", restore)


if __name__ == "__main__":
    unittest.main()
