"""v3.4.0: diagnosable failures, time-based give-up, transport-aware data, fallback."""
import importlib.util
import json
import re
import sys
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"


def load(name):
    spec = importlib.util.spec_from_file_location("rn_v340_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


retry = load("retry")
store_module = load("store")
routing = load("routing")


class Invalid(Exception):
    pass


class MultipleInvalid(Invalid):
    pass


class HomeAssistantError(Exception):
    pass


class ServiceValidationError(HomeAssistantError):
    def __init__(self, message="", translation_key=None):
        super().__init__(message)
        self.translation_key = translation_key


class ClassificationTests(unittest.TestCase):
    def test_validation_errors_are_permanent_instead_of_retried(self):
        for err in (MultipleInvalid("extra keys not allowed @ data['file']"),
                    ServiceValidationError("Multiple config entries", "multiple_config_entry")):
            failure = retry.classify_error(err)
            self.assertEqual((failure.kind, failure.retryable), ("invalid_payload", False))

    def test_waiting_for_ha_does_not_use_attempts_and_missing_entity_is_retryable(self):
        loading = retry.classify_error(retry.ServiceNotLoaded("telegram_bot.send_message is not loaded"))
        self.assertEqual((loading.kind, loading.retryable, loading.counts, loading.retry_after),
                         ("service_not_loaded", True, False, 60))
        missing = retry.classify_error(retry.TargetUnavailable("notify.phone is unavailable"))
        self.assertEqual((missing.kind, missing.retryable, missing.counts), ("target_unavailable", True, True))
        self.assertTrue(retry.classify_error(OSError("network down")).counts)

    def test_error_text_is_kept_but_secrets_and_ids_are_masked(self):
        text = retry.sanitize_error(HomeAssistantError(
            "Bad Request: chat not found chat_id=-1001234567890 https://api.telegram.org/bot123:ABC/send "
            "token=abc123 for me@example.com key " + "x" * 40))
        self.assertTrue(text.startswith("HomeAssistantError: Bad Request: chat not found"))
        for secret in ("1001234567890", "api.telegram.org", "abc123", "me@example.com", "x" * 40):
            self.assertNotIn(secret, text)
        self.assertIn("<id>", text)
        self.assertIn("(multiple_config_entry)",
                      retry.sanitize_error(ServiceValidationError("Choose a bot", "multiple_config_entry")))
        self.assertLessEqual(len(retry.sanitize_error(Exception("y " * 500))), 240)


class PolicyTests(unittest.TestCase):
    def test_new_time_based_defaults_and_migration_of_untouched_old_defaults(self):
        policies = retry.validate_policies({})
        self.assertEqual([policies[p]["max_hours"] for p in ("info", "warning", "critical")], [6, 24, 0])
        self.assertTrue(all(policies[p]["max_attempts"] == 0 for p in policies))
        old = {"info": {"max_attempts": 8, "base_seconds": 30, "max_delay": 1800},
               "warning": {"max_attempts": 20, "base_seconds": 30, "max_delay": 3600},
               "critical": {"max_attempts": 0, "base_seconds": 15, "max_delay": 3600}}
        migrated = retry.validate_policies(retry.migrate_policies(old))
        self.assertEqual((migrated["info"]["max_attempts"], migrated["info"]["max_hours"]), (0, 6))
        custom = {"info": {"max_attempts": 5, "base_seconds": 30, "max_delay": 1800}}
        self.assertEqual(retry.validate_policies(retry.migrate_policies(custom))["info"]["max_attempts"], 5)
        with self.assertRaises(ValueError):
            retry.validate_policies({"info": {"max_hours": 721}})


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "q.db"
        self.db = store_module.QueueStore(self.path)

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def add(self, ttl=0, priority="info"):
        return await self.db.enqueue("Hallo", None, "notify.phone", priority, ttl, None, "always", 100)

    def column(self, sql, *args):
        import sqlite3
        with closing(sqlite3.connect(self.path)) as con:
            return con.execute(sql, args).fetchone()

    async def test_gives_up_after_max_hours_of_failures_not_after_attempts(self):
        job = await self.add()
        self.assertEqual(await self.db.failed(job, 1, "OSError: down", 30, max_attempts=None,
                                              category="network", max_hours=6), "retry")
        first = self.column("SELECT first_failed_at FROM messages WHERE id=?", job)[0]
        self.assertIsNotNone(first)
        # Many attempts are fine while inside the time window.
        self.assertEqual(await self.db.failed(job, 50, "OSError: down", 30, max_attempts=None,
                                              category="network", max_hours=6), "retry")
        with patch.object(store_module.time, "time", return_value=first + 6 * 3600 + 1):
            self.assertEqual(await self.db.failed(job, 51, "OSError: down", 30, max_attempts=None,
                                                  category="network", max_hours=6), "dead")
        error = self.column("SELECT last_error FROM dead_letters WHERE id=?", job)[0]
        self.assertTrue(error.startswith("[network] OSError: down (gave up after 6 h)"))
        archive = self.column("SELECT status,last_error FROM message_archive WHERE id=?", job)
        self.assertEqual(archive[0], "dead")
        self.assertIn("OSError: down", archive[1])

    async def test_manual_retry_starts_a_fresh_failure_window(self):
        job = await self.add()
        await self.db.failed(job, 1, "OSError: down", 30, max_attempts=None, category="network", max_hours=6)
        await self.db.retry_all()
        self.assertIsNone(self.column("SELECT first_failed_at FROM messages WHERE id=?", job)[0])

    async def test_expired_messages_are_recorded_and_analysed(self):
        job = await self.add(ttl=1)
        await self.db.failed(job, 1, "TargetUnavailable: notify.phone is unavailable", 30,
                             max_attempts=None, category="target_unavailable")
        with patch.object(store_module.time, "time", return_value=time.time() + 5):
            self.assertIsNone(await self.db.claim_due(lane="notify"))
        self.assertEqual(self.column("SELECT status FROM delivery_history WHERE message_id=?", job)[0], "expired")
        self.assertEqual(self.column("SELECT status FROM message_archive WHERE id=?", job)[0], "expired")
        stats = await self.db.statistics(7)
        self.assertEqual(stats["transports"][0]["expired"], 1)
        entry = stats["failures"][0]
        self.assertEqual((entry["category"], entry["status"], entry["target"], entry["count"]),
                         ("target_unavailable", "expired", "notify.phone", 1))
        # TTL expiry without any attempt gets its own category.
        silent = await self.add(ttl=1)
        with patch.object(store_module.time, "time", return_value=time.time() + 5):
            await self.db.claim_due(lane="notify")
        categories = {e["category"] for e in (await self.db.statistics(7))["failures"]}
        self.assertIn("ttl_expired", categories)
        self.assertIsNotNone(silent)

    async def test_failure_analysis_groups_dead_and_retrying_jobs(self):
        for _ in range(2):
            job = await self.add()
            await self.db.failed(job, 1, "MultipleInvalid: extra keys not allowed", 30,
                                 permanent=True, category="invalid_payload")
        retrying = await self.add()
        await self.db.failed(retrying, 1, "OSError: down", 30, max_attempts=None, category="network")
        failures = (await self.db.statistics(7))["failures"]
        self.assertEqual((failures[0]["category"], failures[0]["status"], failures[0]["count"]),
                         ("invalid_payload", "dead", 2))
        self.assertIn("extra keys not allowed", failures[0]["detail"])
        self.assertIn(("network", "retrying"), {(f["category"], f["status"]) for f in failures})
        json.dumps(failures)

    def test_failure_category_reads_new_and_legacy_texts(self):
        category = store_module.failure_category
        self.assertEqual(category("[rate_limit] HTTPError: 429"), "rate_limit")
        self.assertEqual(category("HomeAssistantError: unknown"), "unknown")
        self.assertEqual(category("OSError: network"), "network")
        self.assertEqual(category(None, "expired"), "ttl_expired")
        self.assertEqual(category("weird text", "dead"), "unknown")


class TransportDataTests(unittest.TestCase):
    def test_extra_data_is_filtered_per_transport(self):
        extra = {"data": {"actions": []}, "file": "/media/a.jpg", "inline_keyboard": ["Ok:/ok"], "target": ["x"]}
        self.assertEqual(routing.filter_extras("notify.send_message", extra),
                         ({}, ["data", "file", "inline_keyboard", "target"]))
        kept, dropped = routing.filter_extras("notify.mobile_app_phone", extra)
        self.assertEqual((sorted(kept), dropped), (["data", "target"], ["file", "inline_keyboard"]))
        kept, dropped = routing.filter_extras("telegram_bot.send_message", extra)
        self.assertEqual((sorted(kept), dropped), (["inline_keyboard", "target"], ["data", "file"]))
        kept, dropped = routing.filter_extras("telegram_bot.send_photo", extra)
        self.assertEqual(dropped, ["data"])
        self.assertIn("file", kept)
        self.assertEqual(routing.filter_extras("rest_command.push", extra), (extra, []))
        self.assertEqual(routing.filter_extras("notify.send_message", {}), ({}, []))


class FallbackConfigTests(unittest.TestCase):
    ROUTES = {"recipients": {"tg": {"action": "telegram_bot.send_message", "data": {"chat_id": 1}, "fallback": "phone"},
                             "phone": {"action": "notify.mobile_app_phone"}},
              "groups": {"family": ["tg", "phone"]}, "persons": {}}

    def test_fallback_must_name_another_existing_route(self):
        routing.validate_config(self.ROUTES)
        for bad in ("tg", "missing", 5):
            routes = json.loads(json.dumps(self.ROUTES))
            routes["recipients"]["tg"]["fallback"] = bad
            with self.assertRaises(ValueError):
                routing.validate_config(routes)
        routes = json.loads(json.dumps(self.ROUTES))
        routes["recipients"]["tg"]["fallback"] = "family"
        routing.validate_config(routes)
        routes["recipients"]["tg"]["fallback"] = ""
        routing.validate_config(routes)


class WiringTests(unittest.TestCase):
    def test_manager_uses_new_failure_handling(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for snippet in ("sanitize_error(err)", "max_hours=policy.get('max_hours', 0)",
                        "1 if classification.counts else 0", "raise ServiceNotLoaded(",
                        "raise TargetUnavailable(", '"reliable_notify_dead_letter"',
                        'payload.get("__rn_fallback")', 'saved_payload.pop("__rn_route",None)',
                        "filter_extras(action, extra)"):
            self.assertIn(snippet, source)

    def test_panel_explains_every_failure_category(self):
        kinds = set(re.findall(r'Failure\("([a-z_]+)"', (ROOT / "retry.py").read_text(encoding="utf-8")))
        kinds |= {"ttl_expired", "unknown"}
        panel = (ROOT / "reliable-notify-panel.js").read_text(encoding="utf-8")
        body = panel[panel.index("  failureText(kind,code){"):panel.index("  renderFailures(box,data){")]
        for table in ("category", "advice"):
            listed = set(re.findall(r"([a-z_]+):'", re.search(table + r":\{(.*?)\}", body, re.S).group(1)))
            self.assertEqual(listed, kinds, table)

    def test_repair_issue_and_option_texts_exist_in_both_languages(self):
        for name in ("strings.json", "translations/en.json", "translations/de.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            issue = data["issues"]["dead_letters"]
            self.assertIn("{count}", issue["title"])
            self.assertIn("(/reliable-notify)", issue["description"])
            for priority in ("info", "warning", "critical"):
                self.assertIn("max_hours", data["options"]["step"]["init"]["sections"]["retry_" + priority]["data"])


if __name__ == "__main__":
    unittest.main()
