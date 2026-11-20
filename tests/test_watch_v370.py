"""v3.7.0 alarm window phase 2: watched cause, resolve_after, auto_close_after, history."""
import importlib.util
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_v370"
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


def job(key, incident, priority="warning"):
    return {"message": "Brenner auf Störung", "title": "Brenner", "target": "tg", "priority": priority, "ttl": 0,
            "dedup_key": key, "strategy": "always", "action": "telegram_bot.send_message", "payload": {"chat_id": 1},
            "ack_plan": {"key": key, "steps": [{"after": 60, "recipients": ["tg"]}],
                         "incident": ack_module.validate_incident(incident), "message_type": "heizraum"}}


WATCH = {"source_entity": "binary_sensor.brenner", "problem_state": "on", "resolve_after": 120}


class ValidationTests(unittest.TestCase):
    def test_watch_fields(self):
        result = ack_module.validate_incident(WATCH)
        self.assertEqual((result["problem_states"], result["resolve_after"]), (["on"], 120))
        self.assertEqual(ack_module.validate_incident({"source_entity": "sensor.oel"})["problem_states"], ["on"])
        self.assertEqual(ack_module.validate_incident({"source_entity": "sensor.x", "problem_states": ["problem", "on"]})
                         ["problem_states"], ["problem", "on"])
        for bad in ({"problem_state": "on"}, {"resolve_after": 10}, {"source_entity": "sensor.x", "problem_state": "on",
                    "problem_states": ["on"]}, {"source_entity": "sensor.x", "problem_states": ["unavailable"]},
                    {"source_entity": "sensor.x", "resolve_after": 90000}, {"auto_close_after": -1},
                    {"source_entity": "sensor.x", "problem_states": []}, {"source_entity": "Sensor.X"}):
            with self.assertRaises(ValueError, msg=bad):
                ack_module.validate_incident(bad)


class PlanTests(unittest.TestCase):
    def test_decisions(self):
        base = {"problem_states": ["on"], "resolve_after": 120, "clear_since": None}
        plan = incidents.plan_incident
        self.assertIsNone(plan({**base, "state": "active"}, "on"))
        self.assertEqual(plan({**base, "state": "active"}, "off"), "start_wait")
        self.assertIsNone(plan({**base, "state": "active", "clear_since": 5}, "off"))
        self.assertEqual(plan({**base, "state": "active", "clear_since": 5}, "off", timer_due=True), "resolve")
        self.assertEqual(plan({**base, "state": "active", "clear_since": 5}, "on"), "reset_wait")
        self.assertEqual(plan({**base, "state": "resolved"}, "on"), "reactivate")
        self.assertEqual(plan({**base, "state": "acknowledged", "resolve_after": 0}, "off"), "resolve")
        self.assertIsNone(plan({**base, "state": "resolved"}, "off"))
        for undecided in (None, "unavailable", "unknown"):
            self.assertIsNone(plan({**base, "state": "active"}, undecided))
            self.assertIsNone(plan({**base, "state": "active", "clear_since": 5}, undecided, timer_due=True))


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = store_module.QueueStore(Path(self.tmp.name) / "q.db")

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_watch_wait_resolve_reactivate_and_history(self):
        await self.db.enqueue_many([job("brenner", WATCH), job("plain", {"area": "x"})], 100)
        watched = await self.db.watched_incidents()
        self.assertEqual([(r["dedup_key"], r["source_entity"], r["problem_states"]) for r in watched],
                         [("brenner", "binary_sensor.brenner", ["on"])])
        start = time.time()
        await self.db.set_clear_since("brenner", start)
        self.assertEqual(await self.db.due_incident_timers(now=start + 60), ([], []))
        due, _ = await self.db.due_incident_timers(now=start + 121)
        self.assertEqual([r["dedup_key"] for r in due], ["brenner"])
        resolved = await self.db.act_on_incident("brenner", "resolve", "source:binary_sensor.brenner")
        self.assertEqual((resolved["state"], resolved["clear_since"]), ("resolved", None))
        active = await self.db.act_on_incident("brenner", "reactivate", "source:binary_sensor.brenner")
        self.assertEqual(active["state"], "active")
        self.assertIsNone(await self.db.act_on_incident("brenner", "reactivate", "x"))  # not resolved
        history = [e["action"] for e in await self.db.incident_history("brenner")]
        self.assertEqual(history, ["reactivated", "resolved", "created"])

    async def test_auto_close_only_for_resolved_unacknowledged(self):
        await self.db.enqueue_many([job("oel", {"auto_close_after": 3600}), job("ack", {"auto_close_after": 3600})], 100)
        await self.db.act_on_incident("oel", "resolve", "x")
        await self.db.act_on_incident("ack", "ack", "x")
        await self.db.act_on_incident("ack", "resolve", "x")  # closes by acknowledgement
        _, close = await self.db.due_incident_timers(now=time.time() + 3601)
        self.assertEqual([r["dedup_key"] for r in close], ["oel"])
        closed = await self.db.act_on_incident("oel", "close", "auto_close")
        self.assertEqual(closed["state"], "closed")
        self.assertEqual((await self.db.incident_history("oel"))[0]["action"], "closed")
        self.assertEqual(await self.db.watched_incidents(), [])

    async def test_re_report_resets_waiting_period(self):
        await self.db.enqueue_many([job("fuehler", WATCH)], 100)
        await self.db.set_clear_since("fuehler", time.time())
        with patch.object(store_module.time, "time", return_value=time.time() + 10):
            await self.db.enqueue_many([job("fuehler", WATCH)], 100)
        self.assertIsNone((await self.db.watched_incidents())[0]["clear_since"])


class WiringTests(unittest.TestCase):
    def test_manager_watches_causes_and_handlers_run_in_the_event_loop(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for snippet in ("async_track_state_change_event(", "self.reconcile_incidents()", "self.incident_timer_loop()",
                        "plan_incident(record", "critical incidents are closed only by acknowledgement"):
            self.assertIn(snippet, source)
        for handler in ("_on_source_state", "_on_telegram_sent", "_on_telegram_action", "_on_mobile_action"):
            self.assertIn("    @callback\n    def " + handler, source)
        dashboard = (ROOT / "dashboard.py").read_text(encoding="utf-8")
        self.assertIn('hass.bus.async_listen("reliable_notify_incident", push)', dashboard)
        self.assertNotIn("lambda event: hass.async_create_task", dashboard)


if __name__ == "__main__":
    unittest.main()
