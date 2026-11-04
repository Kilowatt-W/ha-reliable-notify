"""V2.0 native outbound transports and secret-handling regression tests."""
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_native_v2",ROOT/"native_transport.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeTransportTest(unittest.TestCase):
    def test_ntfy(self):
        opts={"base_url":"https://ntfy.example.org","topic":"alerts",
              "token":"SENSITIVE_BEARER"}
        queued=module.native_public_payload("reliable_notify.ntfy",opts,{})
        self.assertNotIn("SENSITIVE_BEARER",str(queued))
        self.assertNotIn("ntfy.example.org",str(queued))
        self.assertEqual(len(queued["endpoint_hash"]),32)

    def test_gotify(self):
        opts={"base_url":"https://gotify.example.com","token":"GOTIFY_SECRET"}
        queued=module.native_public_payload("reliable_notify.gotify",opts,{})
        self.assertNotIn("GOTIFY_SECRET",str(queued))

    def test_webhook(self):
        config={"base_url":"https://hooks.example.org/receive","token":"TOKEN"}
        queued=module.native_public_payload("reliable_notify.webhook",config,{"extra":"value"})
        self.assertEqual(queued["extra"],{"extra":"value"})
        with self.assertRaises(ValueError):
            module.native_public_payload("reliable_notify.webhook",config,{"token":"BAD"})

    def test_reject_unsafe_url(self):
        for host in ("http://example.org","https://127.0.0.1","https://192.168.1.2",
                     "https://user:pass@example.org","file:///etc/shadow",
                     "https://localhost"):
            with self.subTest(host=host),self.assertRaises(ValueError):
                module.checked_endpoint(host)
        self.assertEqual(module.checked_endpoint("https://127.0.0.1",allow_private=True),
                         "https://127.0.0.1")

    def test_reject_unrecognized_native_actions(self):
        with self.assertRaises(ValueError):
            module.validate_native_route("reliable_notify.unknown",{"base_url":"https://example.org"})

    def test_gotify_requires_token(self):
        with self.assertRaises(ValueError):
            module.validate_native_route("reliable_notify.gotify",{"base_url":"https://example.org"})

    def test_ntfy_topic_restrictions(self):
        for topic in ("bad topic","../token","","@bad"):
            with self.subTest(topic=topic),self.assertRaises(ValueError):
                module.validate_native_route("reliable_notify.ntfy",{
                    "base_url":"https://ntfy.sh","topic":topic})

    def test_endpoint_pinning(self):
        a=module.endpoint_hash("https://ntfy.sh")
        b=module.endpoint_hash("https://ntfy2.sh")
        self.assertNotEqual(a,b)
        self.assertEqual(a,module.endpoint_hash("https://ntfy.sh"))

    def test_native_rejects_url_query(self):
        with self.assertRaises(ValueError):
            module.validate_native_route("reliable_notify.gotify",{
                "base_url":"https://gotify.example.org?token=secret","token":"a"})


if __name__=="__main__":
    unittest.main()
