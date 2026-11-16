import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.test import SimpleTestCase

from inbound.client import ForwardingError, ResendClient
from .test_webhook import ATTACHMENT_ID, EMAIL_ID


class ResendClientTests(SimpleTestCase):
    def setUp(self):
        self.patcher = patch("inbound.client.build_opener")
        self.opener = self.patcher.start().return_value
        self.addCleanup(self.patcher.stop)
        self.client = ResendClient("re_fake_api_key")

    def respond(self, value):
        self.opener.open.return_value = BytesIO(json.dumps(value).encode())

    def test_receiving_api_uses_cid_format_and_bearer_auth(self):
        self.respond({"id": EMAIL_ID})
        self.assertEqual(self.client.get_received(EMAIL_ID), {"id": EMAIL_ID})
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, f"https://api.resend.com/emails/receiving/{EMAIL_ID}?html_format=cid")
        self.assertEqual(request.get_header("Authorization"), "Bearer re_fake_api_key")
        self.assertLessEqual(self.opener.open.call_args.kwargs["timeout"], 8)

    def test_send_uses_idempotency_header_and_json_body(self):
        self.respond({"id": EMAIL_ID})
        payload = {"from": "sender@example.com", "to": ["target@example.com"], "text": "Body"}
        self.client.send(payload, "stable-key")
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Idempotency-key"), "stable-key")
        self.assertEqual(json.loads(request.data), payload)

    def test_attachment_metadata_uses_receiving_endpoint(self):
        self.respond({"id": ATTACHMENT_ID})
        self.client.get_attachment(EMAIL_ID, ATTACHMENT_ID)
        self.assertEqual(self.opener.open.call_args.args[0].full_url,
                         f"https://api.resend.com/emails/receiving/{EMAIL_ID}/attachments/{ATTACHMENT_ID}")

    def test_download_does_not_send_api_credentials(self):
        self.opener.open.return_value = BytesIO(b"attachment-content")
        self.assertEqual(self.client.download_attachment(
            "https://inbound-cdn.resend.com/file?signature=private"
        ), b"attachment-content")
        request = self.opener.open.call_args.args[0]
        self.assertIsNone(request.get_header("Authorization"))
        self.assertIsNone(request.get_header("Idempotency-key"))

    def test_untrusted_attachment_urls_never_make_a_request(self):
        for url in (
            "http://inbound-cdn.resend.com/file", "file:///etc/passwd",
            "https://127.0.0.1/file", "https://169.254.169.254/latest/meta-data/",
            "https://inbound-cdn.resend.com.attacker.example/file",
            "https://inbound-cdn.resend.com@attacker.example/file",
            "https://user:password@inbound-cdn.resend.com/file",
            "https://inbound-cdn.resend.com:8443/file", None,
        ):
            with self.subTest(url=url), self.assertRaises(ForwardingError) as caught:
                self.client.download_attachment(url)
            self.assertEqual(caught.exception.code, "unsafe_attachment_url")
        self.opener.open.assert_not_called()

    def test_redirect_is_an_error_instead_of_following_to_another_host(self):
        self.opener.open.side_effect = HTTPError(
            "https://inbound-cdn.resend.com/file", 302, "redirect", {}, BytesIO(b"private")
        )
        with self.assertRaises(ForwardingError) as caught:
            self.client.download_attachment("https://inbound-cdn.resend.com/file")
        self.assertEqual(caught.exception.code, "http_302")
        self.opener.open.assert_called_once()

    def test_transport_and_http_errors_do_not_expose_exception_or_response_contents(self):
        private = "re_fake_api_key private-email-body"
        failures = (
            OSError(private), URLError(private),
            HTTPError("https://api.resend.com", 429, private, {}, BytesIO(private.encode())),
            HTTPError("https://api.resend.com", 503, private, {}, BytesIO(private.encode())),
        )
        for failure in failures:
            with self.subTest(kind=type(failure)), self.assertRaises(ForwardingError) as caught:
                self.opener.open.side_effect = failure
                self.client.get_received(EMAIL_ID)
            self.assertNotIn(private, str(caught.exception))
            self.assertNotIn("re_fake_api_key", str(caught.exception))

    def test_malformed_api_json_is_retryable(self):
        for body in (b"not-json", b"[]", b"null", b"\xff"):
            with self.subTest(body=body), self.assertRaises(ForwardingError) as caught:
                self.opener.open.return_value = BytesIO(body)
                self.client.get_received(EMAIL_ID)
            self.assertEqual(caught.exception.code, "invalid_api_response")

    def test_download_size_is_bounded_even_when_server_does_not_advertise_size(self):
        self.opener.open.return_value = BytesIO(b"12345")
        with patch("inbound.client.MAX_ATTACHMENT_BYTES", 4):
            with self.assertRaises(ForwardingError) as caught:
                self.client.download_attachment("https://inbound-cdn.resend.com/file")
        self.assertTrue(caught.exception.needs_review)
        self.assertEqual(caught.exception.code, "size_limit_exceeded")

    def test_overall_budget_prevents_starting_another_request(self):
        self.client.deadline = 0
        with self.assertRaises(ForwardingError) as caught:
            self.client.get_received(EMAIL_ID)
        self.assertEqual(caught.exception.code, "time_budget_exceeded")
        self.opener.open.assert_not_called()
