"""v3.5.0: scheduling, quiet hours per target/person, ntfy/Gotify extras, grouping, daily report."""
import copy
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_v350"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package


def load(name):
    spec = importlib.util.spec_from_file_location(PKG + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


smart = load("smart")
routing = load("routing")
simulation = load("simulation")
native = load("native_transport")
i18n = load("i18n")
store_module = load("store")

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=ZoneInfo("Europe/Vienna")).timestamp()
NIGHT = {"enabled": True, "start": "11:00", "end": "13:00", "allow_priorities": ["critical"]}
ROUTES = {
    "recipients": {
        "phone": {"action": "notify.mobile_app_phone"},
        "tg": {"action": "telegram_bot.send_message", "data": {"chat_id": 1}},
        "quiet_tg": {"action": "telegram_bot.send_message", "data": {"chat_id": 2},
                     "quiet_hours": {"enabled": False}},
    },
    "groups": {"family": ["anna"]},
    "persons": {"anna": {"channels": {"mobile": "phone", "telegram": "quiet_tg"}, "quiet_hours": NIGHT}},
}


class SchedulingTests(unittest.TestCase):
    def test_send_at_and_delay(self):
        self.assertEqual(smart.scheduled_timestamp(NOW), NOW)
        self.assertEqual(smart.scheduled_timestamp(NOW, delay=600), NOW + 600)
        local = smart.scheduled_timestamp(NOW, send_at="2026-11-20 19:00:00", timezone="Europe/Vienna")
        self.assertEqual(datetime.fromtimestamp(local, ZoneInfo("Europe/Vienna")).hour, 19)
        self.assertEqual(smart.scheduled_timestamp(NOW, send_at="2026-11-20T18:00:00Z"),
                         datetime(2026, 11, 20, 18, tzinfo=timezone.utc).timestamp())
        aware = datetime(2026, 11, 21, 8, tzinfo=ZoneInfo("Europe/Vienna"))
        self.assertEqual(smart.scheduled_timestamp(NOW, send_at=aware, delay=60), aware.timestamp())
        self.assertEqual(smart.scheduled_timestamp(NOW, send_at="2020-01-01 00:00"), NOW)  # past = now
        self.assertEqual(smart.scheduled_timestamp(NOW, send_at="  "), NOW)
        for kwargs in ({"delay": -1}, {"delay": 40 * 86400}, {"send_at": "morgen"},
                       {"send_at": "2027-01-30 00:00"}, {"delay": True}):
            with self.assertRaises(ValueError, msg=kwargs):
                smart.scheduled_timestamp(NOW, timezone="Europe/Vienna", **kwargs)


class QuietHoursPerRouteTests(unittest.TestCase):
    def test_person_quiet_hours_apply_directly_and_through_groups_but_own_settings_win(self):
        routing.validate_config(ROUTES)
        smart.validate_route_quiet_hours(ROUTES)
        for names in (["anna"], ["family"]):
            policies = routing.route_quiet_hours(ROUTES, names)
            self.assertEqual(policies["phone"], NIGHT)
            self.assertEqual(policies["quiet_tg"], {"enabled": False})  # own setting wins
        self.assertNotIn("tg", routing.route_quiet_hours(ROUTES, ["tg"]))
        broken = copy.deepcopy(ROUTES)
        broken["persons"]["anna"]["quiet_hours"] = {"start": "25:00"}
        with self.assertRaises(ValueError):
            smart.validate_route_quiet_hours(broken)

    def test_simulation_shows_schedule_per_target(self):
        settings = {"quiet_hours": {"enabled": False}, "archive_retention": {}, "default_notify": ""}
        result = simulation.simulate(settings, ROUTES, {"message": "x", "recipients": ["family", "tg"],
                                     "priority": "warning", "delay": 60}, now=NOW, timezone="Europe/Vienna")
        per_target = {t["recipient"]: t["not_before"] for t in result["recipients"]}
        end_of_night = datetime(2026, 11, 20, 13, 0, tzinfo=ZoneInfo("Europe/Vienna")).timestamp()
        self.assertEqual(per_target["phone"], end_of_night)       # person quiet hours
        self.assertEqual(per_target["tg"], NOW + 60)               # global policy, only the delay
        self.assertEqual(result["not_before"], end_of_night)
        self.assertTrue(result["scheduled"])


class NativeExtrasTests(unittest.TestCase):
    NTFY = {"base_url": "https://ntfy.example.org", "topic": "alerts", "token": "tk"}
    GOTIFY = {"base_url": "https://gotify.example.org", "token": "gt"}
    ITEM = {"message": "Es hat geläutet", "title": "Haustür", "priority": "warning"}

    def test_ntfy_json_with_buttons_image_and_click(self):
        extra = {"click": "https://ha.example/kamera", "attach": "https://ha.example/a.jpg", "tags": "bell",
                 "actions": [{"action": "view", "label": "Tür öffnen", "url": "https://ha.example/tuer", "clear": True}]}
        queued = native.native_public_payload("reliable_notify.ntfy", self.NTFY, extra)
        url, headers, body = native.build_native_request("reliable_notify.ntfy", self.NTFY, self.ITEM, queued["extra"])
        self.assertEqual(url, "https://ntfy.example.org")
        self.assertEqual(headers["Authorization"], "Bearer tk")
        self.assertEqual((body["topic"], body["title"], body["priority"], body["tags"]), ("alerts", "Haustür", 4, ["bell"]))
        self.assertEqual(body["actions"][0], {"action": "view", "label": "Tür öffnen", "url": "https://ha.example/tuer", "clear": True})
        self.assertNotIn("tk", json.dumps(queued))
        json.dumps(body, ensure_ascii=False)

    def test_gotify_click_and_image_and_webhook_data(self):
        url, headers, body = native.build_native_request("reliable_notify.gotify", self.GOTIFY, self.ITEM,
                                                         {"click": "https://ha.example", "image": "https://ha.example/i.png"})
        self.assertEqual(url, "https://gotify.example.org/message")
        self.assertEqual(body["extras"]["client::notification"],
                         {"click": {"url": "https://ha.example"}, "bigImageUrl": "https://ha.example/i.png"})
        _, _, hook = native.build_native_request("reliable_notify.webhook", {"base_url": "https://hook.example"},
                                                 self.ITEM, {"room": "Bad"})
        self.assertEqual(hook["data"], {"room": "Bad"})

    def test_invalid_extras_are_rejected_when_queueing_but_old_jobs_still_deliver(self):
        for bad in ({"click": "javascript:alert(1)"}, {"actions": [{"label": "x", "url": "https://a"}] * 4},
                    {"actions": [{"action": "broadcast", "label": "x", "url": "https://a"}]},
                    {"tags": "a\nb"}, {"unknown": 1}):
            with self.assertRaises(ValueError, msg=bad):
                native.native_public_payload("reliable_notify.ntfy", self.NTFY, bad)
        _, _, body = native.build_native_request("reliable_notify.ntfy", self.NTFY, self.ITEM, {"legacy": 1})
        self.assertNotIn("legacy", body)
        kept, dropped = routing.filter_extras("reliable_notify.ntfy", {"click": "https://a", "file": "/x"})
        self.assertEqual((kept, dropped), ({"click": "https://a"}, ["file"]))
        self.assertEqual(routing.filter_extras("reliable_notify.gotify", {"image": "https://a"})[1], [])


class GroupingTests(unittest.TestCase):
    def test_companion_group_and_thread_id_without_overriding_caller(self):
        grouped = routing.companion_group({"data": {"actions": []}}, "heizraum")
        self.assertEqual(grouped["data"]["group"], "heizraum")
        self.assertEqual(grouped["data"]["push"], {"thread-id": "heizraum"})
        own = routing.companion_group({"data": {"group": "mine", "push": {"sound": "x"}}}, "heizraum")
        self.assertEqual(own["data"]["group"], "mine")
        self.assertEqual(own["data"]["push"], {"sound": "x", "thread-id": "heizraum"})
        self.assertEqual(routing.companion_group({}, "info")["data"]["group"], "info")
        self.assertEqual(routing.companion_group({"data": "odd"}, "info"), {"data": "odd"})


class ReportTests(unittest.IsolatedAsyncioTestCase):
    FAILURES = [{"category": "network", "status": "dead", "target": "tg", "count": 3},
                {"category": "ttl_expired", "status": "expired", "target": "phone", "count": 1}]

    def test_report_text_in_both_languages(self):
        german = i18n.failure_report("de-AT", self.FAILURES, {"tg": "Telegram Büro"})
        self.assertIn("3 fehlgeschlagen, 1 abgelaufen, 0 in Wiederholung", german)
        self.assertIn("• Netzwerk – Telegram Büro: 3", german)
        english = i18n.failure_report("en", self.FAILURES * 4, limit=5)
        self.assertIn("12 failed, 4 expired", english)
        self.assertIn("… and 3 more", english)

    async def test_report_day_is_remembered(self):
        with tempfile.TemporaryDirectory() as td:
            store = store_module.QueueStore(Path(td) / "q.db")
            self.assertEqual(await store.metric_value("daily_report_day"), 0)
            await store.set_metric("daily_report_day", 20261120)
            self.assertEqual(await store.metric_value("daily_report_day"), 20261120)


class OptionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_report_recipient_and_time_are_validated(self):
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            import test_options_forms as forms
        finally:
            sys.path.pop(0)
        module = forms.load_flow()
        flow = module.ReliableNotifyOptionsFlow()
        flow.config_entry = types.SimpleNamespace(data={}, options={})
        form = await flow.async_step_init()
        values = form["data_schema"]({key.schema: {} for key in form["data_schema"].schema if key.schema != "show_yaml"})
        self.assertEqual((values["general"]["companion_grouping"], values["general"]["daily_report_time"]), (True, "08:00"))
        for field, bad in (("daily_report_recipient", "Telegram Admin"), ("daily_report_time", "8 Uhr")):
            broken = copy.deepcopy(values)
            broken["general"][field] = bad
            self.assertEqual((await flow.async_step_init(broken))["errors"], {"base": "invalid_options"})
        values["general"].update(daily_report_recipient=" telegram_admin ", daily_report_time="07:30")
        saved = (await flow.async_step_init(values))["data"]
        self.assertEqual((saved["daily_report_recipient"], saved["daily_report_time"]), ("telegram_admin", "07:30"))


class WiringTests(unittest.TestCase):
    def test_manager_uses_the_extensions(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for snippet in ("scheduled_timestamp(now, data.get(\"send_at\"), data.get(\"delay\")",
                        "route_quiet_hours(self.routes, names", "companion_group(payload",
                        "self.report_loop()", "validate_route_quiet_hours(validate_config(",
                        'vol.Optional("send_at"): cv.datetime'):
            self.assertIn(snippet, source)

    def test_enqueue_service_fields_are_translated(self):
        import yaml
        services = yaml.safe_load((ROOT / "services.yaml").read_text(encoding="utf-8"))
        self.assertIn("send_at", services["enqueue"]["fields"])
        for name in ("strings.json", "translations/en.json", "translations/de.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertTrue(data["services"]["enqueue"]["fields"]["delay"]["name"])
            general = data["options"]["step"]["init"]["sections"]["general"]["data"]
            self.assertIn("daily_report_recipient", general)


if __name__ == "__main__":
    unittest.main()
