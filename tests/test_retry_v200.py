"""Provider classification on TLS, SMTP, HTTP rate limit and payload errors."""
import importlib.util
import smtplib
import ssl
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"
spec=importlib.util.spec_from_file_location("rn_retry_v2",ROOT/"retry.py")
module=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=module
spec.loader.exec_module(module)


class ResponseError(Exception):
    def __init__(self,status,headers=None):
        self.status=status
        self.headers=headers or {}
        super().__init__("Request failed")


class FailureClassificationTest(unittest.TestCase):
    def test_rate_limit_retry_after_seconds(self):
        failure=module.classify_error(ResponseError(429,{"Retry-After":"180"}))
        self.assertEqual(failure.kind,"rate_limit")
        self.assertTrue(failure.retryable)
        self.assertEqual(failure.retry_after,180)

    def test_invalid_payload_permanent(self):
        self.assertFalse(module.classify_error(ResponseError(413)).retryable)
        self.assertFalse(module.classify_error(ValueError("bad route")).retryable)

    def test_tls_certificate_permanent(self):
        cert=ssl.SSLCertVerificationError(1,"certificate verify failed")
        self.assertEqual(module.classify_error(cert).kind,"tls_certificate")
        self.assertFalse(module.classify_error(cert).retryable)

    def test_smtp_auth_and_recipient(self):
        auth=smtplib.SMTPAuthenticationError(535,b"bad login")
        self.assertEqual(module.classify_error(auth).kind,"authentication")
        target=smtplib.SMTPRecipientsRefused({"bad@example.test":(550,b"No such user")})
        self.assertEqual(module.classify_error(target).kind,"invalid_recipient")

    def test_http_503_retry(self):
        self.assertTrue(module.classify_error(ResponseError(503)).retryable)


if __name__=="__main__":
    unittest.main()
