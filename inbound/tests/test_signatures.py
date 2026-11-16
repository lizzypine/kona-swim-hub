import base64
import hashlib
import hmac
import time
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from inbound.signatures import InvalidSignature, verify_signature


TEST_SECRET = "whsec_" + base64.b64encode(b"test-signing-key-not-a-real-secret").decode()


def signed_headers(body, timestamp=None, message_id="msg_test"):
    timestamp = str(int(time.time() if timestamp is None else timestamp))
    digest = hmac.new(
        base64.b64decode(TEST_SECRET[6:]),
        f"{message_id}.{timestamp}.".encode() + body, hashlib.sha256,
    ).digest()
    return {
        "svix-id": message_id, "svix-timestamp": timestamp,
        "svix-signature": "v1," + base64.b64encode(digest).decode(),
    }


class SignatureTests(SimpleTestCase):
    def test_official_svix_test_vector(self):
        # https://docs.svix.com/receiving/verifying-payloads/how-manual
        with patch("inbound.signatures.time.time", return_value=1731705121):
            verify_signature(b'{"event_type":"ping","data":{"success":true}}', {
                "svix-id": "msg_loFOjxBNrRLzqYUf", "svix-timestamp": "1731705121",
                "svix-signature": "v1,rAvfW3dJ/X/qxhsaXPOyyCGmRKsaKWcsNccKXlIktD0=",
            }, "whsec_plJ3nmyCDGBKInavdOK15jsl")

    def test_raw_body_is_verified_without_json_normalization(self):
        body = '{ "value": "泳ぐ" }\n'.encode()
        headers = signed_headers(body)
        verify_signature(body, headers, TEST_SECRET)
        with self.assertRaises(InvalidSignature):
            verify_signature(body.rstrip(), headers, TEST_SECRET)

    def test_rotation_accepts_any_matching_v1_signature(self):
        body = b"{}"
        headers = signed_headers(body)
        headers["svix-signature"] = "v2,unknown v1,wrong " + headers["svix-signature"]
        verify_signature(body, headers, TEST_SECRET)

    def test_missing_headers_invalid_signature_and_old_or_future_timestamp(self):
        body = b"{}"
        cases = [{}, {**signed_headers(body), "svix-signature": "v1,wrong"}]
        cases.extend(signed_headers(body, time.time() + delta) for delta in (-301, 301))
        cases.append({**signed_headers(body), "svix-timestamp": "not-an-integer"})
        for headers in cases:
            with self.subTest(headers=headers), self.assertRaises(InvalidSignature):
                verify_signature(body, headers, TEST_SECRET)

    def test_malformed_configuration_is_distinct_from_invalid_signature(self):
        for secret in ("", "not-a-secret", "whsec_!", "whsec_"):
            with self.subTest(secret=secret), self.assertRaises(ImproperlyConfigured):
                verify_signature(b"{}", {}, secret)
