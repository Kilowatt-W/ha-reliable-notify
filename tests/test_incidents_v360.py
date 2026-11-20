"""v3.6.0 alarm window: incident lifecycle, reminders, entities data, permissions."""
import importlib.util
import json
import sqlite3
import sys
import tempfile
import time
import types
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_v360"
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


def job(key, incident=None, priority="critical", steps=None, title="Brenner"):
    return {"message": "Der Brenner hat auf Störung geschaltet.", "title": title, "target": "tg",
            "priority": priority, "ttl": 0, "dedup_key": key, "strategy": "always",
            "action": "telegram_bot.send_message", "payload": {"chat_id": 1},
            "ack_plan": {"key": key, "steps": steps if steps is not None else [{"after": 60, "recipients": ["tg"]}],
                         "incident": incident, "message_type": "heizraum"}}


INCIDENT = {"display_text": "An der Ecomatic entstören.", "area": "heizraum", "escalate_while_resolved": True}


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "q.db"
        self.db = store_module.QueueStore(self.path)

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def state(self, key):
        records = {r["dedup_key"]: r for r in await self.db.incidents(include_closed=True)}
        return records[key]

    async def test_resolved_but_unacknowledged_stays_open_until_acknowledged(self):
        await self.db.enqueue_many([job("brenner", INCIDENT)], 100)
        record = await self.state("brenner")
        self.assertEqual((record["state"], record["area"], record["display_text"], record["message_type"]),
                         ("active", "heizraum", "An der Ecomatic entstören.", "heizraum"))
        resolved = await self.db.act_on_incident("brenner", "resolve", "automation")
        self.assertEqual((resolved["state"], resolved["resolved_by"]), ("resolved", "automation"))
        self.assertIsNone(await self.db.act_on_incident("brenner", "resolve", "again"))
        closed = await self.db.act_on_incident("brenner", "ack", "Anna")
        self.assertEqual(closed["state"], "closed")
        self.assertEqual(await self.db.incidents(), [])

    async def test_acknowledged_while_cause_persists_then_resolved(self):
        await self.db.enqueue_many([job("fuehler", INCIDENT)], 100)
        acked = await self.db.act_on_incident("fuehler", "ack", "Anna")
        self.assertEqual((acked["state"], acked["acknowledged_by"]), ("acknowledged", "Anna"))
        self.assertIsNone(await self.db.act_on_incident("fuehler", "snooze", "x"))
        self.assertEqual((await self.db.act_on_incident("fuehler", "resolve", "auto"))["state"], "closed")

    async def test_plain_acknowledgement_closes_as_before(self):
        await self.db.enqueue_many([job("plain", None)], 100)
        self.assertEqual((await self.db.act_on_incident("plain", "ack", "x"))["state"], "closed")
        self.assertEqual(await self.db.acknowledgement("plain"), 0)

    async def test_snooze_pauses_reminders_but_keeps_since(self):
        await self.db.enqueue_many([job("oel", INCIDENT)], 100)
        opened = (await self.state("oel"))["opened_at"]
        snoozed = await self.db.act_on_incident("oel", "snooze", "Anna", minutes=60)
        self.assertEqual(snoozed["opened_at"], opened)
        self.assertAlmostEqual(snoozed["snoozed_until"], time.time() + 3600, delta=5)
        self.assertEqual(await self.db.due_escalations(now=time.time() + 120), [])
        self.assertEqual(len(await self.db.due_escalations(now=time.time() + 3700)), 1)
        with self.assertRaises(ValueError):
            await self.db.act_on_incident("oel", "snooze", "x", minutes=0)

    async def test_reminders_after_resolve_follow_the_option(self):
        await self.db.enqueue_many([job("a", INCIDENT), job("b", {**INCIDENT, "escalate_while_resolved": False})], 100)
        await self.db.act_on_incident("a", "resolve", "x")
        await self.db.act_on_incident("b", "resolve", "x")
        due = {d["ack_key"] for d in await self.db.due_escalations(now=time.time() + 120)}
        self.assertEqual(due, {"a"})
        await self.db.enqueue_many([job("c", INCIDENT)], 100)
        await self.db.act_on_incident("c", "resolve", "x", stop_escalation=True)
        self.assertNotIn("c", {d["ack_key"] for d in await self.db.due_escalations(now=time.time() + 120)})

    async def test_reopen_and_re_report_episodes(self):
        await self.db.enqueue_many([job("ueber", INCIDENT)], 100)
        first = (await self.state("ueber"))["opened_at"]
        with patch.object(store_module.time, "time", return_value=time.time() + 100):
            await self.db.enqueue_many([job("ueber", INCIDENT)], 100)   # still open: same episode
        self.assertEqual((await self.state("ueber"))["opened_at"], first)
        await self.db.act_on_incident("ueber", "ack", "x")
        await self.db.act_on_incident("ueber", "resolve", "x")
        self.assertIsNone(await self.db.act_on_incident("ueber", "ack", "x"))
        with patch.object(store_module.time, "time", return_value=time.time() + 200):
            reopened = await self.db.act_on_incident("ueber", "reopen", "Anna")
        self.assertEqual((reopened["state"], reopened["escalation_step"]), ("active", 0))
        self.assertGreater(reopened["opened_at"], first)
        self.assertIsNone(await self.db.act_on_incident("ueber", "reopen", "x"))  # already open
        await self.db.act_on_incident("ueber", "ack", "x")
        with patch.object(store_module.time, "time", return_value=time.time() + 300):
            await self.db.enqueue_many([job("ueber", INCIDENT)], 100)   # after acknowledgement: new episode
        self.assertEqual((await self.state("ueber"))["state"], "active")
        self.assertGreater((await self.state("ueber"))["opened_at"], reopened["opened_at"])

    async def test_old_acknowledgements_are_migrated_without_losing_open_ones(self):
        await self.db.count()
        with closing(sqlite3.connect(self.path)) as con, con:
            con.execute("DROP TABLE acknowledgements")
            con.execute("""CREATE TABLE acknowledgements (ack_key TEXT PRIMARY KEY, message_id INTEGER NOT NULL,
                title TEXT, message TEXT NOT NULL, priority TEXT NOT NULL, created_at REAL NOT NULL,
                steps_json TEXT NOT NULL, next_step INTEGER NOT NULL DEFAULT 0, acknowledged_at REAL,
                acknowledged_by TEXT, action_id TEXT)""")
            con.execute("INSERT INTO acknowledgements VALUES('open',1,'Open','m','warning',100,'[]',0,NULL,NULL,'a')")
            con.execute("INSERT INTO acknowledgements VALUES('done',2,'Done','m','info',100,'[]',0,200,'x','b')")
        records = {r["dedup_key"]: r for r in await self.db.incidents(include_closed=True)}
        self.assertEqual((records["open"]["state"], records["open"]["opened_at"]), ("active", 100))
        self.assertEqual(records["done"]["state"], "closed")


class ViewTests(unittest.TestCase):
    RECORDS = [
        {"dedup_key": "a", "priority": "warning", "state": "active", "area": "heizraum", "message_type": "heizraum",
         "opened_at": 10, "message": "secret", "display_text": None, "title": "A"},
        {"dedup_key": "b", "priority": "critical", "state": "resolved", "area": "bad", "message_type": "wasser",
         "opened_at": 5, "message": "m", "display_text": "Wasser abdrehen", "title": "B"},
        {"dedup_key": "c", "priority": "info", "state": "acknowledged", "area": "heizraum", "message_type": "x",
         "opened_at": 20, "message": "m", "display_text": None, "title": "C"},
        {"dedup_key": "d", "priority": "critical", "state": "closed", "area": "heizraum", "message_type": "x",
         "opened_at": 30, "message": "m", "display_text": None, "title": "D"},
    ]

    def test_filtering_and_sorting(self):
        keys = lambda rows: [r["dedup_key"] for r in rows]
        self.assertEqual(keys(incidents.visible_incidents(self.RECORDS)), ["b", "a"])
        self.assertEqual(keys(incidents.visible_incidents(self.RECORDS, include_acknowledged=True)), ["b", "a", "c"])
        self.assertEqual(keys(incidents.visible_incidents(self.RECORDS, areas=["heizraum"])), ["a"])
        self.assertEqual(keys(incidents.visible_incidents(self.RECORDS, min_priority="critical")), ["b"])
        self.assertEqual(keys(incidents.visible_incidents(self.RECORDS, message_types=["wasser"])), ["b"])

    def test_resident_view_permissions_and_summary(self):
        resident = incidents.public_incident(self.RECORDS[0])
        self.assertEqual(resident["text"], "secret")   # fallback when no display text
        self.assertNotIn("message", resident)
        self.assertEqual(incidents.public_incident(self.RECORDS[1])["text"], "Wasser abdrehen")
        self.assertIn("message", incidents.public_incident(self.RECORDS[1], is_admin=True))
        self.assertTrue(incidents.may_act("ack", False))
        self.assertTrue(incidents.may_act("snooze", False))
        self.assertFalse(incidents.may_act("escalate", False))
        self.assertFalse(incidents.may_act("ack", False, admin_only=True))
        self.assertTrue(incidents.may_act("reopen", True, admin_only=True))
        data = incidents.summary(self.RECORDS)
        self.assertEqual((data["count"], data["critical_unacknowledged"]), (3, 1))
        self.assertEqual([i["dedup_key"] for i in data["incidents"]], ["b", "a", "c"])

    def test_incident_field_validation(self):
        self.assertEqual(ack_module.validate_incident({"area": "heizraum"}),
                         {"display_text": None, "area": "heizraum", "escalate_while_resolved": True})
        for bad in ({"source_entity": "binary_sensor.x"}, {"area": "Heizraum"}, {"display_text": "x" * 501},
                    {"escalate_while_resolved": "yes"}, "text"):
            with self.assertRaises(ValueError):
                ack_module.validate_incident(bad)


class WebSocketTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        callbacks = {}

        def command(schema):
            name = next(value for key, value in schema.items() if key.schema == "type")
            def decorate(fn):
                callbacks[name] = fn
                return fn
            return decorate
        components = types.ModuleType("homeassistant.components")
        components.websocket_api = types.SimpleNamespace(
            websocket_command=command, async_response=lambda fn: fn, async_register_command=lambda *a: None,
            event_message=lambda ident, payload: {"id": ident, "event": payload})
        with patch.dict(sys.modules, {"homeassistant": types.ModuleType("homeassistant"),
                                      "homeassistant.components": components}):
            dashboard = load("dashboard")
        record = {"dedup_key": "brenner", "priority": "critical", "state": "active", "area": "heizraum",
                  "message_type": "heizraum", "opened_at": 1, "message": "m", "display_text": "Entstören", "title": "B"}
        self.actions = []

        async def incident_action(key, action, by, **options):
            self.actions.append((key, action, by, options))
            return record

        async def all_incidents():
            return [record]
        self.settings = {}
        self.manager = types.SimpleNamespace(settings=self.settings, incident_action=incident_action,
                                             store=types.SimpleNamespace(incidents=all_incidents))
        self.listeners = []
        self.hass = types.SimpleNamespace(data={"reliable_notify": {"x": self.manager}},
            bus=types.SimpleNamespace(async_listen=lambda event, cb: self.listeners.append(event) or (lambda: None)),
            async_create_task=lambda coro: coro.close())
        dashboard.register_dashboard(self.hass)
        self.callbacks = callbacks

    def connection(self, admin):
        sent = {"errors": [], "results": [], "messages": []}
        conn = types.SimpleNamespace(user=types.SimpleNamespace(is_admin=admin, name="Anna"), subscriptions={},
                                     send_error=lambda *a: sent["errors"].append(a),
                                     send_result=lambda *a: sent["results"].append(a),
                                     send_message=lambda m: sent["messages"].append(m))
        return conn, sent

    async def test_residents_can_acknowledge_and_snooze_but_not_escalate(self):
        action = self.callbacks["reliable_notify/incident_action"]
        conn, sent = self.connection(False)
        await action(self.hass, conn, {"id": 1, "key": "brenner", "action": "snooze", "minutes": 60})
        self.assertEqual(self.actions[-1], ("brenner", "snooze", "Anna", {"minutes": 60}))
        await action(self.hass, conn, {"id": 2, "key": "brenner", "action": "escalate", "minutes": 15})
        self.assertEqual(sent["errors"][-1][1], "unauthorized")
        self.settings["incident_admin_only"] = True
        await action(self.hass, conn, {"id": 3, "key": "brenner", "action": "ack", "minutes": 15})
        self.assertEqual(sent["errors"][-1][1], "unauthorized")
        admin, _ = self.connection(True)
        await action(self.hass, admin, {"id": 4, "key": "brenner", "action": "resolve", "minutes": 15})
        self.assertEqual(self.actions[-1][:2], ("brenner", "resolve"))

    async def test_list_and_subscription_for_residents(self):
        conn, sent = self.connection(False)
        await self.callbacks["reliable_notify/incidents"](self.hass, conn, {"id": 5, "min_priority": "info"})
        payload = sent["results"][-1][1]
        self.assertEqual(payload["incidents"][0]["text"], "Entstören")
        self.assertNotIn("message", payload["incidents"][0])
        self.assertEqual(payload["permissions"], {"ack": True, "snooze": True, "escalate": False,
                                                  "resolve": False, "reopen": False})
        await self.callbacks["reliable_notify/subscribe_incidents"](self.hass, conn, {"id": 6, "min_priority": "info"})
        self.assertIn(6, conn.subscriptions)
        self.assertEqual(self.listeners, ["reliable_notify_incident"])
        self.assertEqual(sent["messages"][-1]["event"]["incidents"][0]["dedup_key"], "brenner")


class WiringTests(unittest.TestCase):
    def test_services_entities_and_card_are_registered(self):
        import yaml
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for snippet in ('PLATFORMS = ["sensor", "binary_sensor", "button", "notify"]',
                        "frontend.add_extra_js_url(hass, ALARM_CARD_URL)", '("resolve", resolve_incident, RESOLVE_SCHEMA)',
                        '"reliable_notify_incident"', 'vol.Optional("incident"): dict'):
            self.assertIn(snippet, source)
        services = yaml.safe_load((ROOT / "services.yaml").read_text(encoding="utf-8"))
        self.assertTrue({"resolve", "snooze", "reopen"} <= set(services))
        for name in ("strings.json", "translations/en.json", "translations/de.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertTrue(data["entity"]["sensor"]["open_incidents"]["name"])
            self.assertTrue(data["entity"]["binary_sensor"]["critical_open"]["name"])
            self.assertIn("incident", data["services"]["enqueue"]["fields"])
        self.assertTrue((ROOT / "reliable-notify-alarm-card.js").is_file())


if __name__ == "__main__":
    unittest.main()
