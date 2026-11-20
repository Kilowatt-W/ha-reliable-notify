"""v3.8.0 alarm window phase 3: mirror to bell/repairs, per-area sensors, card editor wiring."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_v380"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package


def load(name):
    spec = importlib.util.spec_from_file_location(PKG + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


store_module = load("store")
incidents = load("incidents")
ack_module = load("acknowledgement")


def job(key, incident, priority="critical"):
    return {"message": "Wasser im Keller", "title": "Wasseralarm", "target": "tg", "priority": priority, "ttl": 0,
            "dedup_key": key, "strategy": "always", "action": "telegram_bot.send_message", "payload": {"chat_id": 1},
            "ack_plan": {"key": key, "steps": [], "incident": ack_module.validate_incident(incident),
                         "message_type": "keller"}}


class MirrorPlanTests(unittest.TestCase):
    def record(self, **values):
        return {"state": "active", "priority": "critical", "mirror": None, **values}

    def test_where_incidents_are_mirrored(self):
        plan = incidents.mirror_plan
        self.assertEqual(plan(self.record()), {"notification": "hide", "issue": "hide"})
        self.assertEqual(plan(self.record(mirror="persistent_notification")), {"notification": "show", "issue": "hide"})
        self.assertEqual(plan(self.record(), "persistent_notification")["notification"], "show")   # global default
        self.assertEqual(plan(self.record(mirror="none"), "repairs"), {"notification": "hide", "issue": "hide"})
        self.assertEqual(plan(self.record(mirror="repairs")), {"notification": "hide", "issue": "error"})
        self.assertEqual(plan(self.record(mirror="repairs", priority="warning"))["issue"], "warning")
        self.assertEqual(plan(self.record(mirror="repairs", priority="info"))["issue"], "hide")
        self.assertEqual(plan(self.record(mirror="repairs", state="resolved"))["issue"], "error")
        for state in ("acknowledged", "closed"):
            self.assertEqual(plan(self.record(mirror="persistent_notification", state=state))["notification"], "hide")

    def test_dismissing_a_bell_entry_acknowledges_only_foreign_removals(self):
        found = incidents.dismissed_incidents
        self.assertEqual(found("removed", {"rn_wasser": 1, "other": 2}), ["wasser"])
        self.assertEqual(found("removed", ["rn_wasser"], {"wasser"}), [])        # our own removal
        self.assertEqual(found("added", ["rn_wasser"]), [])
        self.assertEqual(found("removed", ["rn_"]), [])

    def test_mirror_validation(self):
        self.assertEqual(ack_module.validate_incident({"mirror": "repairs"})["mirror"], "repairs")
        with self.assertRaises(ValueError):
            ack_module.validate_incident({"mirror": "bell"})


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_mirror_and_areas_are_stored(self):
        with tempfile.TemporaryDirectory() as td:
            db = store_module.QueueStore(Path(td) / "q.db")
            # One acknowledgement plan per enqueue call (as the manager does).
            for item in (job("wasser", {"mirror": "persistent_notification", "area": "keller"}),
                         job("oel", {"area": "heizraum"}), job("plain", None)):
                await db.enqueue_many([item], 100)
            records = {r["dedup_key"]: r for r in await db.incidents()}
            self.assertEqual((records["wasser"]["mirror"], records["oel"]["mirror"]), ("persistent_notification", None))
            self.assertEqual(await db.incident_areas(), ["heizraum", "keller"])


class WiringTests(unittest.TestCase):
    def test_manager_sensors_translations_and_card(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for snippet in ("pn.async_register_callback(self.hass, self._on_notification_update)",
                        "    @callback\n    def _on_notification_update", "self.sync_mirror(record)",
                        "self._mirror_dismissing.add(key)", 'translation_key="incident"',
                        "dismissed_incidents(update_type, notifications, self._mirror_dismissing)"):
            self.assertIn(snippet, source)
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("persistent_notification", manifest["dependencies"])
        sensor = (ROOT / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('self.entity_id = f"sensor.reliable_notify_open_incidents_{area}"', sensor)
        self.assertIn("async def new_area(event)", sensor)
        for name in ("strings.json", "translations/en.json", "translations/de.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertIn("{area}", data["entity"]["sensor"]["open_incidents_area"]["name"])
            self.assertEqual(set(data["selector"]["incident_mirror"]["options"]), {"none", "persistent_notification", "repairs"})
            self.assertIn("{key}", data["issues"]["incident"]["description"])
            self.assertIn("incident_mirror", data["options"]["step"]["init"]["sections"]["general"]["data"])
        card = (ROOT / "reliable-notify-alarm-card.js").read_text(encoding="utf-8")
        self.assertIn("static getConfigElement(){return document.createElement('reliable-notify-alarm-card-editor');}", card)


if __name__ == "__main__":
    unittest.main()
