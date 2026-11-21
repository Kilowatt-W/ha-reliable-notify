"""v3.8.2: reset all errors from the settings (dead letters, failure analysis, counters)."""
import importlib.util
import re
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"


def load(name):
    spec = importlib.util.spec_from_file_location("rn_v382_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


store_module = load("store")


class ResetErrorsStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "q.db"
        self.db = store_module.QueueStore(self.path)

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def add(self):
        return await self.db.enqueue("Hallo", None, "notify.phone", "info", 0, None, "always", 100)

    def rows(self, sql, *args):
        import sqlite3
        with closing(sqlite3.connect(self.path)) as con:
            return con.execute(sql, args).fetchall()

    async def test_reset_removes_failures_but_keeps_successes_and_retrying_jobs(self):
        ok = await self.add()
        await self.db.succeeded(ok)
        dead = []
        for _ in range(2):
            job = await self.add()
            await self.db.failed(job, 1, "MultipleInvalid: extra keys", 30, permanent=True, category="invalid_payload")
            dead.append(job)
        retrying = await self.add()
        await self.db.failed(retrying, 1, "OSError: down", 30, max_attempts=None, category="network")
        self.assertEqual(await self.db.dead_count(), 2)
        before = await self.db.metrics()
        self.assertEqual((before["failures"], before["dead_letters"], before["sent"]), (3, 2, 1))

        result = await self.db.reset_errors()

        self.assertEqual(result, {"dead_letters": 2, "history": 2, "daily": 1})
        self.assertEqual(await self.db.dead_count(), 0)
        after = await self.db.metrics()
        self.assertNotIn("failures", after)
        self.assertNotIn("dead_letters", after)
        self.assertEqual(after["sent"], 1)
        # Failure analysis is empty except the job that is still being retried.
        stats = await self.db.statistics(7)
        self.assertEqual([(f["status"], f["category"]) for f in stats["failures"]], [("retrying", "network")])
        self.assertEqual(stats["transports"][0]["sent"], 1)
        self.assertEqual(stats["transports"][0]["failed"], 0)
        self.assertEqual(self.rows("SELECT status FROM delivery_daily"), [("sent",)])
        # Archive keeps the text; former dead letters are marked deleted, the retrying job stays queued.
        status = dict(self.rows("SELECT id,status FROM message_archive"))
        self.assertEqual([status[j] for j in dead], ["deleted", "deleted"])
        self.assertEqual((status[ok], status[retrying]), ("sent", "retry"))
        self.assertEqual(len(self.rows("SELECT id FROM messages WHERE id=?", retrying)), 1)
        # A second reset has nothing left to do.
        self.assertEqual(await self.db.reset_errors(), {"dead_letters": 0, "history": 0, "daily": 0})


class ResetErrorsWiringTests(unittest.TestCase):
    def test_admin_service_websocket_and_settings_button(self):
        init = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('hass,DOMAIN,"reset_errors",reset_errors', init)
        self.assertIn("async_register_admin_service", init)
        self.assertIn("await self.update_dead_letter_issue()", init.split("async def reset_errors(self")[1][:400])
        dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
        handler = dash.split('"reliable_notify/reset_errors"')[1][:600]
        self.assertIn("connection.user.is_admin", handler)
        self.assertIn("websocket_api.async_register_command(hass, reset_errors)", dash)
        services = (ROOT / "services.yaml").read_text(encoding="utf-8")
        self.assertRegex(services, r"(?m)^reset_errors:\n  name: ")
        for name in ("strings.json", "translations/en.json", "translations/de.json"):
            self.assertIn('"reset_errors": {', (ROOT / name).read_text(encoding="utf-8"), name)
        panel = (ROOT / "reliable-notify-panel.js").read_text(encoding="utf-8")
        self.assertIn("this.resetErrorsSection(box);", panel)
        self.assertIn("confirm(this.t('Alle Fehler unwiderruflich löschen?'))", panel)
        self.assertIn("this.call('reset_errors')", panel)
        card = (ROOT / "reliable-notify-card.js").read_text(encoding="utf-8")
        for text in re.findall(r"this\.t\('([^']+)'", panel.split("resetErrorsSection(box){")[1].split("\n  }\n")[0]):
            self.assertIn("['" + text + "'", card, text)


if __name__ == "__main__":
    unittest.main()
