"""v3.3.2: Reliable Notify's own notify entities are recognised and never used as targets."""
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "reliable_notify"
PKG = "rn_test_own_v332"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package


def load(name):
    spec = importlib.util.spec_from_file_location(PKG + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


routing = load("routing")
advisor = load("migration_advisor")

ROUTES = {"recipients": {"mail": {"action": "notify.send_message", "target_entity": "notify.mail"}}}


def action(target):
    return {"action": "notify.send_message", "target": {"entity_id": target}, "data": {"message": "Hi"}}


class OwnEntityTests(unittest.TestCase):
    def test_prefix_and_registry_based_detection(self):
        self.assertTrue(routing.is_own_entity("notify.reliable_mail"))
        self.assertTrue(routing.is_own_entity("notify.renamed", {"notify.renamed"}))
        self.assertFalse(routing.is_own_entity("notify.mail", {"notify.renamed"}))
        self.assertFalse(routing.is_own_entity(None))
        self.assertFalse(routing.is_own_entity("notify.reliablex"))

    def test_migration_ignores_actions_already_delivered_by_reliable_notify(self):
        index = advisor.route_targets(ROUTES)
        own = frozenset({"notify.renamed"})
        for target in ("notify.reliable_mail", ["notify.reliable_mail"], "notify.renamed",
                       ["notify.reliable_a", "notify.renamed"]):
            self.assertIsNone(advisor.inspect_action(action(target), index, own), target)
        self.assertIsNone(advisor.inspect_action({"action": "notify.reliable_mail", "data": {"message": "x"}}, index))
        self.assertEqual(advisor.inspect_action(action("notify.mail"), index, own)["status"], "proposed")
        mixed = advisor.inspect_action(action(["notify.reliable_a", "notify.mail"]), index, own)
        self.assertEqual(mixed["reason_code"], "dynamic_destination")
        report = advisor.analyze([{"actions": [action("notify.renamed"), action("notify.mail")]}], ROUTES,
                                 own_entities=own)
        self.assertEqual([item["path"] for item in report], ["root[0].actions[1]"])

    def test_enqueue_rejects_own_entities_as_target(self):
        source = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("is_own_entity(\n                        target, self.own_notify_entities())", source)


class SetRouteOwnEntityTests(unittest.IsolatedAsyncioTestCase):
    async def test_own_entity_cannot_be_saved_as_target(self):
        callbacks = {}

        def command(schema):
            name = next(value for key, value in schema.items() if key.schema == "type")
            def decorate(fn):
                callbacks[name] = fn
                return fn
            return decorate
        components = types.ModuleType("homeassistant.components")
        components.websocket_api = types.SimpleNamespace(websocket_command=command,
            async_response=lambda fn: fn, async_register_command=lambda *args: None)
        package._load_routes = lambda path: {"recipients": {}, "groups": {}, "persons": {}, "labels": {}}
        with patch.dict(sys.modules, {"homeassistant": types.ModuleType("homeassistant"),
                                      "homeassistant.components": components}):
            dashboard = load("dashboard")
        entry = types.SimpleNamespace(options={"routes": {}})
        manager = types.SimpleNamespace(entry=entry, route_path="unused",
                                        own_notify_entities=lambda: frozenset({"notify.renamed"}))
        saved = []
        hass = types.SimpleNamespace(data={"reliable_notify": {"x": manager}},
            config_entries=types.SimpleNamespace(async_update_entry=lambda e, options: saved.append(options)))
        dashboard.register_dashboard(hass)
        errors = []
        conn = types.SimpleNamespace(user=types.SimpleNamespace(is_admin=True),
            send_error=lambda *args: errors.append(args), send_result=lambda *args: None)
        for target in ("notify.reliable_mail", "notify.renamed"):
            await callbacks["reliable_notify/set_route"](hass, conn, {
                "id": 1, "category": "recipients", "name": "loop", "delete": False,
                "definition": {"action": "notify.send_message", "target_entity": target}})
            self.assertEqual(errors[-1][1], "own_entity")
        self.assertEqual(saved, [])
        await callbacks["reliable_notify/set_route"](hass, conn, {
            "id": 1, "category": "recipients", "name": "mail", "delete": False,
            "definition": {"action": "notify.send_message", "target_entity": "notify.mail"}})
        self.assertEqual(len(saved), 1)


class OptionsDefaultTargetTests(unittest.IsolatedAsyncioTestCase):
    async def test_own_entity_is_rejected_as_default_target(self):
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            import test_options_forms as forms
        finally:
            sys.path.pop(0)
        module = forms.load_flow()
        flow = module.ReliableNotifyOptionsFlow()
        flow.config_entry = types.SimpleNamespace(data={}, options={})
        form = await flow.async_step_init()
        values = form["data_schema"]({key.schema: {} for key in form["data_schema"].schema
                                      if key.schema != "show_yaml"})
        values = copy.deepcopy(values)
        values["general"]["target_entity"] = "notify.reliable_mail"
        result = await flow.async_step_init(values)
        self.assertEqual(result["errors"], {"base": "own_entity"})
        values["general"]["target_entity"] = "notify.mail"
        self.assertEqual((await flow.async_step_init(values))["type"], "create_entry")


if __name__ == "__main__":
    unittest.main()
