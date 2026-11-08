"""v3.3.1: automation check must work on real HA config files.

Regression: HA's own YAML loader returns str subclasses (NodeStrClass) that
yaml.safe_dump cannot represent, and it rejects !secret without a secrets
store. Every file with a suggestion or a secret was reported as an error.
"""
import asyncio
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_scan_v331"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package


def load(name):
    spec = importlib.util.spec_from_file_location(PKG + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


advisor = load("migration_advisor")
scan = load("migration_scan")
apply = load("migration_apply")

ROUTES = {"recipients": {
    "wolfgang": {"action": "telegram_bot.send_message", "data": {"chat_id": 1234}},
    "mail": {"action": "notify.send_message", "target_entity": "notify.mail"},
}}

AUTOMATIONS = """- id: window
  alias: Fenster offen
  triggers: []
  actions:
    - action: telegram_bot.send_message
      data:
        chat_id: 1234
        message: "Fenster offen!"
    - action: notify.send_message
      target:
        entity_id: notify.mail
      data:
        title: !secret mail_title
        message: Hallo
    - action: telegram_bot.send_message
      data:
        chat_id: !secret telegram_chat
        message: geheim
"""


class LoaderTests(unittest.TestCase):
    def test_plain_python_values_and_unresolved_tags(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "automations.yaml"
            path.write_text(AUTOMATIONS, encoding="utf-8")
            data = advisor.load_automation_yaml(path)
        self.assertIs(type(data[0]["alias"]), str)  # never a HA NodeStrClass
        title = data[0]["actions"][1]["data"]["title"]
        self.assertIsInstance(title, advisor.Tagged)
        self.assertEqual((title.tag, title.value), ("!secret", "mail_title"))
        # Proposals built from these values can always be dumped as YAML.
        yaml.safe_dump(data[0]["actions"][0], allow_unicode=True)

    def test_scanner_does_not_depend_on_home_assistant_yaml_loader(self):
        for name in ("migration_scan.py", "migration_apply.py"):
            self.assertNotIn("homeassistant.util.yaml", (ROOT / name).read_text(encoding="utf-8"))


class ScanTests(unittest.TestCase):
    def scan(self, files):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, text in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
            return asyncio.run(scan.scan_automation_files(td, ROUTES))

    def test_real_file_with_secrets_gives_suggestions_not_errors(self):
        report = self.scan({"automations.yaml": AUTOMATIONS})
        json.dumps(report)  # sent over the HA WebSocket
        files = {Path(f["file"]).name: f for f in report["files"]}
        automations = files["automations.yaml"]
        self.assertNotIn("error", automations)
        by_source = [(p["status"], p.get("reason_code")) for p in automations["proposals"]]
        self.assertEqual(by_source, [("proposed", "unambiguous"), ("manual", "yaml_tags"), ("manual", "yaml_tags")])
        self.assertIn("notify.reliable_wolfgang", automations["proposals"][0]["preview_diff"])
        self.assertNotIn("mail_title", json.dumps(automations["proposals"][1]))
        # A missing scripts.yaml is skipped, not reported as an error.
        self.assertEqual(files["scripts.yaml"], {"file": "scripts.yaml", "skipped": "not_present", "proposals": []})
        self.assertEqual((report["proposed"], report["manual"]), (1, 2))

    def test_broken_or_unusual_files_get_clear_error_codes(self):
        report = self.scan({
            "automations.yaml": "- alias: ok\n  actions: []\n",
            "packages/broken.yaml": "automation:\n  - alias: [unclosed\n",
            "packages/scalar.yaml": "just text\n",
            "packages/empty.yaml": "# only a comment\n",
        })
        files = {Path(f["file"]).name: f for f in report["files"]}
        self.assertEqual(files["broken.yaml"]["error_code"], "yaml_syntax")
        self.assertIsInstance(files["broken.yaml"]["line"], int)
        self.assertEqual(files["scalar.yaml"]["error_code"], "not_automation_yaml")
        self.assertNotIn("error", files["empty.yaml"])
        self.assertNotIn("error", files["automations.yaml"])
        for item in files.values():
            if "error_code" in item:
                self.assertEqual(item["error"], scan.ERRORS[item["error_code"]])

    def test_every_reason_code_has_english_text(self):
        report = self.scan({"automations.yaml": AUTOMATIONS})
        for proposal in report["files"][0]["proposals"]:
            self.assertEqual(proposal["reason"], advisor.REASONS[proposal["reason_code"]])


class ApplyTests(unittest.TestCase):
    def test_package_with_secret_elsewhere_can_apply_and_errors_have_codes(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / "packages"
            folder.mkdir()
            path = folder / "windows.yaml"
            path.write_text("automation:\n" + "".join("  " + line + "\n" for line in AUTOMATIONS.splitlines()),
                            encoding="utf-8")
            old = path.read_bytes()
            digest = hashlib.sha256(old).hexdigest()
            report = advisor.analyze(advisor.load_automation_yaml(path), ROUTES)
            entry = next(x for x in report if x["status"] == "proposed")
            result = apply._apply_sync(td, "packages/windows.yaml", digest, entry["path"], ROUTES,
                                       "APPLY_SINGLE_CHANGE")
            self.assertTrue(result["changed"])
            text = path.read_text(encoding="utf-8")
            self.assertIn("notify.reliable_wolfgang", text)
            self.assertIn("!secret telegram_chat", text)  # untouched
            with self.assertRaises(apply.MigrationError) as ctx:
                apply._apply_sync(td, "packages/windows.yaml", digest, entry["path"], ROUTES,
                                  "APPLY_SINGLE_CHANGE")
            self.assertEqual(ctx.exception.code, "file_changed")
            with self.assertRaises(apply.MigrationError) as ctx:
                apply._apply_sync(td, "automations.yaml", digest, entry["path"], ROUTES, "APPLY_SINGLE_CHANGE")
            self.assertEqual(ctx.exception.code, "not_eligible")


if __name__ == "__main__":
    unittest.main()
