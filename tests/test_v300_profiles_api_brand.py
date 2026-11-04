"""Reliable Notify 3.0 profile, API and branding regression tests."""
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
def load(module):
    spec=importlib.util.spec_from_file_location("rn_v3_"+module,ROOT/(module+".py"))
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
profiles=load("profiles")
validator=load("api_validation")


class ProfilesTests(unittest.TestCase):
    def test_defaults_and_overrides(self):
        profile={"urgent":{"priority":"critical","recipients":["admin"],
                           "archive":"keep","archive_days":7}}
        data=profiles.resolve_profile({"profile":"urgent","message":"hello",
            "archive_days":2},profile)
        self.assertEqual(data["priority"],"critical")
        self.assertEqual(data["archive_days"],2)
        self.assertEqual(data["recipients"],["admin"])

    def test_invalid_profiles(self):
        for raw in ([],{"name":{"priority":"super"}},
                    {"a b":{"priority":"info"}},{"x":{"archive_days":900}},
                    {"x":{"invalid":True}},{"x":{"recipients":["!bad"]}}):
            with self.subTest(value=raw),self.assertRaises(ValueError):
                profiles.validate_profiles(raw)

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            profiles.resolve_profile({"profile":"missing"},profiles.DEFAULT)


class APIValidationTests(unittest.TestCase):
    ROUTES={"recipients":{"telegram_wolfgang":{"action":"telegram_bot.send_message"},
                          "notify_phone":{"action":"notify.mobile_app_my_phone"}},
            "groups":{"family":["notify_phone"]}}
    ALLOWED={"telegram_wolfgang","family"}

    def test_allowed_message(self):
        payload=validator.validate_api_message({
            "recipients":["telegram_wolfgang"],"message":"My home alarm",
            "priority":"warning","dedup_key":"security_123"
        },self.ROUTES,self.ALLOWED)
        self.assertEqual(payload["recipients"],["telegram_wolfgang"])

    def test_denied_and_unsafe(self):
        for extra in (
            {"recipients":["notify_phone"],"message":"no"},
            {"recipients":["telegram_wolfgang"],"message":"no","priority":"critical"},
            {"recipients":["telegram_wolfgang"],"message":"no","action":"os.system"},
            {"recipients":["telegram_wolfgang"],"message":"no","ttl":90000},
            {"recipients":["telegram_wolfgang"],"message":"no","archive_days":-1},
            {"recipients":["telegram_wolfgang"],"message":"no","title":"x"*260},
            {"recipients":["telegram_wolfgang"],"message":"no","profile":"invalid space"},
        ):
            with self.subTest(payload=extra),self.assertRaises(ValueError):
                validator.validate_api_message(extra,self.ROUTES,self.ALLOWED)


class BrandingTests(unittest.TestCase):
    def test_complete_brand_sizes(self):
        brand=ROOT/"brand"
        for fname,width,height in (
            ("icon.png",256,256),("icon@2x.png",512,512),
            ("dark_icon.png",256,256),("dark_icon@2x.png",512,512),
            ("logo.png",512,160),("logo@2x.png",1024,320)
        ):
            with self.subTest(file=fname):
                blob=(brand/fname).read_bytes()
                self.assertEqual(blob[:8],b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II",blob[16:24]),(width,height))
                self.assertGreater(len(blob),5000)

if __name__=="__main__":
    unittest.main()
