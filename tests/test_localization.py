"""Check the integration's bilingual discovery and HA metadata contract."""
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'reliable_notify'


class LocalizationTests(unittest.TestCase):
    def test_discovery_links_and_bilingual_metadata_cover_all_services(self):
        source = json.loads((ROOT/'strings.json').read_text())
        english = json.loads((ROOT/'translations/en.json').read_text())
        german = json.loads((ROOT/'translations/de.json').read_text())
        self.assertEqual(source, english)
        services = yaml.safe_load((ROOT/'services.yaml').read_text())
        for translation in (english, german):
            self.assertIn('(/reliable-notify)', translation['config']['step']['user']['description'])
            self.assertIn('(/reliable-notify)', translation['options']['step']['init']['description'])
            self.assertEqual(set(translation['services']), set(services))
            for key, service in services.items():
                item = translation['services'][key]
                self.assertTrue(item['name'])
                self.assertEqual(set(item.get('fields', {})), set(service.get('fields', {})))
                for field in item.get('fields', {}).values():
                    self.assertTrue(field['name'])
        self.assertEqual(set(english['entity']['sensor']), set(german['entity']['sensor']))
        self.assertEqual(len(english['entity']['sensor']), 12)
        self.assertNotEqual(english['services']['enqueue']['name'], german['services']['enqueue']['name'])
