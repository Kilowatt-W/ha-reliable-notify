"""Reliable Notify v2.5: recipient migration templates and usage tests."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"

def load(filename):
    spec=importlib.util.spec_from_file_location("rn_test_"+filename,ROOT/(filename+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

templates=load("templates")


class TemplateTests(unittest.TestCase):
    def test_good_templates(self):
        records=templates.validate_templates({
            "window_warning":{
                "message":"Das Fenster {{ room }} ist offen",
                "title":"Fensterwarnung",
                "priority":"warning",
                "recipients":["wolfgang_phone"],
                "archive_days":2
            }})
        self.assertEqual(records["window_warning"]["archive_days"],2)

    def test_bad_templates(self):
        for invalid in (
            [],{"!name":{"message":"x"}},
            {"name":{"message":""}},
            {"name":{"message":"x","priority":"urgent"}},
            {"name":{"message":"x","unknown":"yes"}},
            {"name":{"message":"x","archive_days":-1}},
            {"name":{"message":"x","recipients":[""]}},
        ):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                templates.validate_templates(invalid)

    def test_parameter_restrictions(self):
        self.assertEqual(templates.validate_parameters({"room":"Bedroom","minutes":90}),
                         {"room":"Bedroom","minutes":90})
        for bad in ({"foo-bar":"x"},{"x":{"nested":1}},
                    {"x":"A"*2500}):
            with self.assertRaises(ValueError):
                templates.validate_parameters(bad)

if __name__=="__main__":
    unittest.main()
