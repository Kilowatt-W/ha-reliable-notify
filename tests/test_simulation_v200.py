"""Pure dry run never persists or delivers messages."""
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
PKG="rn_test_simulation"
if PKG not in sys.modules:
    package=types.ModuleType(PKG)
    package.__path__=[str(ROOT)]
    sys.modules[PKG]=package
spec=importlib.util.spec_from_file_location(PKG+".simulation",ROOT/"simulation.py")
simulation=importlib.util.module_from_spec(spec)
sys.modules[PKG+".simulation"]=simulation
spec.loader.exec_module(simulation)


class SimulationTests(unittest.TestCase):
    def test_quiet_hours_and_retention(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now=datetime(2026,11,4,23,0,tzinfo=ZoneInfo("Europe/Vienna")).timestamp()
        settings={
            "quiet_hours":{"enabled":True,"start":"22:00","end":"07:00","allow_priorities":["critical"]},
            "archive_retention":{"windows":2},
        }
        routes={"recipients":{"phone":{"action":"notify.mobile_app_test"}}}
        result=simulation.simulate(settings,routes,{"recipients":["phone"],
            "priority":"warning","message_type":"windows","message":"test"},
            now=now,timezone="Europe/Vienna")
        self.assertTrue(result["scheduled"])
        self.assertEqual(result["archive_days"],2)
        self.assertEqual(result["would_enqueue"],1)
        self.assertFalse(result["would_send"])

    def test_unknown_recipient_rejected(self):
        with self.assertRaises(ValueError):
            simulation.simulate({},{"recipients":{}},{"recipients":["missing"]},
                                now=1000,timezone="Europe/Vienna")


if __name__=="__main__":
    unittest.main()
