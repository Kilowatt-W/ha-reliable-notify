"""Opt-in migration patch tests. Never writes the user's HA files."""
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
PKG="rn_test_migration_v3"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package

def load(name):
    spec=importlib.util.spec_from_file_location(PKG+"."+name,ROOT/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module
load("migration_advisor")

home=types.ModuleType("homeassistant")
home.__path__=[]
util=types.ModuleType("homeassistant.util")
util.__path__=[]
yaml_mod=types.ModuleType("homeassistant.util.yaml")
yaml_mod.load_yaml=lambda path:yaml.safe_load(Path(path).read_text())
sys.modules.setdefault("homeassistant",home)
sys.modules.setdefault("homeassistant.util",util)
sys.modules.setdefault("homeassistant.util.yaml",yaml_mod)
apply=load("migration_apply")


class MigrationApplyTests(unittest.TestCase):
    ROUTES={"recipients":{"wolfgang":{"action":"telegram_bot.send_message",
                                     "data":{"chat_id":1234}}}}

    def _file(self,td):
        folder=Path(td)/"packages"
        folder.mkdir(exist_ok=True)
        path=folder/"windows.yaml"
        source='''automation:
  - alias: "Fenster"
    triggers: []
    actions:
      - action: telegram_bot.send_message
        data:
          chat_id: 1234
          message: Fenster offen
'''
        path.write_text(source)
        return path

    def test_approved_package_change_with_backup(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            path=self._file(td)
            old=path.read_bytes()
            digest=hashlib.sha256(old).hexdigest()
            report=apply.analyze(yaml.safe_load(old),self.ROUTES)
            entry=report[0]
            result=apply._apply_sync(td,"packages/windows.yaml",digest,
                                    entry["path"],self.ROUTES,"APPLY_SINGLE_CHANGE")
            self.assertTrue(result["changed"])
            self.assertIn("notify.reliable_wolfgang",path.read_text())
            self.assertEqual(Path(result["backup"]).read_bytes(),old)
            self.assertEqual(yaml.safe_load(path.read_text())["automation"][0]["alias"],"Fenster")
            with self.assertRaises(ValueError):
                apply._apply_sync(td,"packages/windows.yaml",digest,
                                  entry["path"],self.ROUTES,"APPLY_SINGLE_CHANGE")

    def test_refuse_ui_managed_and_missing_consent(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            path=self._file(td)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                apply._apply_sync(td,"packages/windows.yaml",digest,
                    "root.automation[0].actions[0]",self.ROUTES,"NOT_APPROVED")
            with self.assertRaises(ValueError):
                apply._apply_sync(td,"automations.yaml",digest,
                    "root[0].actions[0]",self.ROUTES,"APPLY_SINGLE_CHANGE")

    def test_comments_rejected(self):
        value='''automation:
  - actions:
      - action: telegram_bot.send_message # do not lose comment
        data:
          chat_id: 1234
          message: Test
'''
        proposal={"action":"notify.reliable_wolfgang","data":{"message":"Test"}}
        with self.assertRaises(ValueError):
            apply._patch(value,"root.automation[0].actions[0]",proposal)


if __name__=="__main__":
    unittest.main()
