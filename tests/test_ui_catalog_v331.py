"""Every German UI text in the panel's code tables has an English translation."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
CARD = (ROOT / "reliable-notify-card.js").read_text(encoding="utf-8")
PANEL = (ROOT / "reliable-notify-panel.js").read_text(encoding="utf-8")
STRING = r"""("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')"""


def literal(text):
    if text.startswith("'"):
        text = '"' + text[1:-1].replace("\\'", "'").replace('"', '\\"') + '"'
    return json.loads(text)


def catalog():
    head = CARD[:CARD.index("const RN_CATALOG")]
    pairs = re.findall(r"\[\s*" + STRING + r"\s*,\s*" + STRING + r"\s*\]", head)
    return {literal(de): literal(en) for de, en in pairs}


def method_body(name):
    start = PANEL.index("  " + name + "(")
    end = PANEL.index("\n  }\n", start)
    return PANEL[start:end]


class CatalogTests(unittest.TestCase):
    def test_all_literal_translations_and_code_tables_are_in_catalog(self):
        known = catalog()
        texts = {literal(m) for m in re.findall(r"\bt\(\s*" + STRING, PANEL + CARD[CARD.index("const RN_CATALOG"):])}
        for name in ("migrationText", "errorText"):
            body = method_body(name)
            texts |= {literal(m) for m in re.findall(r"[a-z_]+:" + STRING, body)}
        missing = sorted(text for text in texts if text not in known and text not in known.values())
        self.assertEqual(missing, [])

    def test_backend_reason_and_error_codes_are_all_translated_in_panel(self):
        import importlib.util
        import sys
        import types
        package = types.ModuleType("rn_ui_catalog")
        package.__path__ = [str(ROOT)]
        sys.modules["rn_ui_catalog"] = package
        modules = {}
        for name in ("migration_advisor", "migration_scan", "migration_apply"):
            spec = importlib.util.spec_from_file_location("rn_ui_catalog." + name, ROOT / (name + ".py"))
            modules[name] = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = modules[name]
            spec.loader.exec_module(modules[name])
        body = method_body("migrationText")
        tables = {kind: set(re.findall(r"([a-z_]+):'", re.search(kind + r":\{(.*?)\}", body, re.S).group(1)))
                  for kind in ("reason", "file", "apply")}
        self.assertEqual(set(modules["migration_advisor"].REASONS), tables["reason"])
        self.assertEqual(set(modules["migration_scan"].ERRORS), tables["file"])
        source = (ROOT / "migration_apply.py").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r'MigrationError\("([a-z_]+)"', source)), tables["apply"])

    def test_help_exists_for_every_section_in_both_languages(self):
        sections = set(re.findall(r"^  ([a-z]+):\{icon:", CARD, re.M))
        self.assertEqual(len(sections), 9)
        start = PANEL.index("const RN_HELP={")
        help_source = PANEL[start:PANEL.index("\n};\n", start)]
        for section in sections:
            self.assertRegex(help_source, r"\n  " + section + r":\{doc:'[A-Z_0-9]+\.md'", section)
            doc = re.search(r"\n  " + section + r":\{doc:'([A-Z_0-9]+\.md)'", help_source).group(1)
            self.assertTrue((ROOT.parents[1] / "docs" / doc).is_file(), doc)
        self.assertEqual(help_source.count("de:{intro:"), 9)
        self.assertEqual(help_source.count("en:{intro:"), 9)


if __name__ == "__main__":
    unittest.main()
