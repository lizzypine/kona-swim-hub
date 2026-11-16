import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.db import OperationalError, close_old_connections, connections
from django.db.models.query import QuerySet
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from inbound.client import ForwardingError
from inbound.models import InboundEmail
from .test_signatures import TEST_SECRET, signed_headers


EMAIL_ID = "56761188-7520-42d8-8898-ff6fc54ce618"
SENT_ID = "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
ATTACHMENT_ID = "2a0c9ce0-3112-4728-976e-47ddcd16a318"
CONFIG = {
    "RESEND_WEBHOOK_SECRET": TEST_SECRET,
    "RESEND_API_KEY": "re_fake_api_key_not_a_secret",
    "EMAIL_FORWARD_TO": "forward-target@example.com",
    "RESEND_INBOUND_ADDRESS": "team@ilkaxle.resend.app",
    "DEFAULT_FROM_EMAIL": "Kona Swim Hub <team@notifications.konaswimhub.com>",
}
RECEIVED = {
    "id": EMAIL_ID, "from": "parent@example.com", "to": ["team@ilkaxle.resend.app"],
    "subject": "Swim lessons", "text": "Private message contents.",
    "html": "<p>Private message contents.</p>",
    "headers": {
        "From": 'A Parent <parent@example.com>',
        "Authentication-Results": "forged.example; dkim=pass",
        "Reply-To": "attacker@example.com",
    },
    "attachments": [],
}


def post_event(client, event=None, *, body=None, headers=None):
    if body is None:
        body = json.dumps(event or {
            "type": "email.received",
            "data": {"email_id": EMAIL_ID, "to": ["team@ilkaxle.resend.app"]},
        }).encode()
    if headers is None:
        headers = signed_headers(body)
    return client.post(
        reverse("resend_webhook"), data=body, content_type="application/json",
        **{"HTTP_" + key.upper().replace("-", "_"): value for key, value in headers.items()},
    )


@override_settings(**CONFIG)
class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.patcher = patch("inbound.forwarding.ResendClient")
        self.api = self.patcher.start().return_value
        self.addCleanup(self.patcher.stop)
        self.api.get_received.return_value = copy.deepcopy(RECEIVED)
        self.api.send.return_value = {"id": SENT_ID}

    def test_success_uses_fixed_destination_verified_sender_and_original_reply_to(self):
        with self.assertLogs("inbound", level="INFO") as logs:
            response = post_event(self.client)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "forwarded"})
        payload, key = self.api.send.call_args.args
        self.assertEqual(payload["to"], [CONFIG["EMAIL_FORWARD_TO"]])
        self.assertEqual(payload["from"], CONFIG["DEFAULT_FROM_EMAIL"])
        self.assertEqual(payload["reply_to"], "parent@example.com")
        self.assertEqual(payload["subject"], "Fwd: Swim lessons")
        self.assertIn("A Parent <parent@example.com>", payload["text"])
        self.assertIn("Private message contents.", payload["text"])
        self.assertIn("unverified", payload["text"])
        self.assertEqual(payload["headers"], {
            "X-Kona-Swim-Hub-Forwarded": "1", "Auto-Submitted": "auto-generated",
        })
        self.assertNotIn("html", payload)
        self.assertNotIn("cc", payload)
        self.assertNotIn("bcc", payload)
        self.assertEqual(key, f"kona-inbound/{EMAIL_ID}")
        row = InboundEmail.objects.get()
        self.assertEqual(str(row.forwarded_id), SENT_ID)
        self.assertIsNotNone(row.forwarded_at)
        self.assertIsNotNone(row.first_send_at)
        self.assertIsNone(row.lease_until)
        output = " ".join(logs.output)
        for sensitive in (CONFIG["RESEND_API_KEY"], TEST_SECRET, "Private message contents.", "parent@example.com"):
            self.assertNotIn(sensitive, output)

    def test_processing_state_and_send_boundary_are_persisted_before_send(self):
        def send(payload, key):
            row = InboundEmail.objects.get()
            self.assertEqual(row.status, "processing")
            self.assertIsNotNone(row.first_send_at)
            self.assertTrue(row.payload_sha256)
            self.assertIsNone(row.forwarded_at)
            return {"id": SENT_ID}
        self.api.send.side_effect = send
        self.assertEqual(post_event(self.client).status_code, 200)

    def test_failure_logs_do_not_contain_secrets_addresses_or_email_contents(self):
        self.api.send.side_effect = ForwardingError("transport_error")
        with self.assertLogs("inbound", level="ERROR") as logs:
            self.assertEqual(post_event(self.client).status_code, 503)
        output = " ".join(logs.output)
        for sensitive in (CONFIG["RESEND_API_KEY"], TEST_SECRET, CONFIG["EMAIL_FORWARD_TO"], RECEIVED["text"]):
            self.assertNotIn(sensitive, output)
        self.assertTrue(all(record.exc_info is None for record in logs.records))

    def test_invalid_or_missing_signature_does_not_touch_database_or_api(self):
        for headers in ({}, {"svix-id": "x", "svix-timestamp": "0", "svix-signature": "v1,x"}):
            with self.subTest(headers=headers):
                self.assertEqual(post_event(self.client, headers=headers).status_code, 400)
        self.assertEqual(InboundEmail.objects.count(), 0)
        self.api.get_received.assert_not_called()
        self.api.send.assert_not_called()

    def test_tampered_body_fails_signature(self):
        self.assertEqual(post_event(
            self.client, body=b'{"type":"email.received"}', headers=signed_headers(b"{}")
        ).status_code, 400)
        self.api.get_received.assert_not_called()

    def test_non_post_is_rejected(self):
        self.assertEqual(self.client.get(reverse("resend_webhook")).status_code, 405)

    @override_settings(RESEND_API_KEY="", EMAIL_FORWARD_TO="")
    def test_unrelated_signed_event_is_ignored_without_forwarding_configuration(self):
        response = post_event(self.client, {"type": "email.sent", "data": {}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ignored"})
        self.api.send.assert_not_called()

    def test_wrong_recipient_is_ignored_and_webhook_cannot_choose_forwarding_destination(self):
        response = post_event(self.client, {"type": "email.received", "data": {
            "email_id": EMAIL_ID, "to": ["elsewhere@example.com"],
            "forward_to": "attacker@example.com",
        }})
        self.assertEqual(response.status_code, 200)
        self.api.get_received.assert_not_called()
        response = post_event(self.client, {"type": "email.received", "data": {
            "email_id": EMAIL_ID, "to": ["team@ilkaxle.resend.app"],
            "forward_to": "attacker@example.com",
        }})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.api.send.call_args.args[0]["to"], [CONFIG["EMAIL_FORWARD_TO"]])

    def test_received_email_id_and_recipients_are_checked_again(self):
        self.api.get_received.return_value["id"] = str(uuid4())
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().status, "needs_review")

    def test_api_recipient_mismatch_is_ignored(self):
        self.api.get_received.return_value["to"] = ["elsewhere@example.com"]
        self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().status, "ignored")

    def test_missing_or_malformed_configuration_returns_retryable_error(self):
        for key, value in (
            ("RESEND_WEBHOOK_SECRET", ""), ("RESEND_WEBHOOK_SECRET", "whsec_bad!"),
            ("RESEND_API_KEY", ""), ("EMAIL_FORWARD_TO", ""),
            ("EMAIL_FORWARD_TO", "bad address"), ("DEFAULT_FROM_EMAIL", "bad sender"),
            ("RESEND_INBOUND_ADDRESS", "bad inbox"),
        ):
            with self.subTest(key=key), override_settings(**{key: value}):
                response = post_event(self.client)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response["Retry-After"], "30")
        self.api.get_received.assert_not_called()

    def test_malformed_signed_event_returns_400(self):
        for body in (b"not-json", b"[]", b'{}', b'{"type":"email.received","data":{"email_id":"../../bad"}}'):
            with self.subTest(body=body):
                self.assertEqual(post_event(self.client, body=body).status_code, 400)
        self.api.get_received.assert_not_called()

    def test_large_request_is_rejected(self):
        self.assertEqual(post_event(self.client, body=b"x" * (256 * 1024 + 1)).status_code, 413)

    def test_duplicate_received_id_is_forwarded_only_once_even_with_new_webhook_id(self):
        self.assertEqual(post_event(self.client).status_code, 200)
        body = json.dumps({"type": "email.received", "data": {
            "email_id": EMAIL_ID, "to": ["team@ilkaxle.resend.app"],
        }}).encode()
        self.assertEqual(post_event(self.client, body=body, headers=signed_headers(body, message_id="msg_other")).status_code, 200)
        self.api.send.assert_called_once()
        self.assertEqual(InboundEmail.objects.get().attempts, 1)

    def test_get_failure_is_retryable_and_never_marks_forwarded(self):
        self.api.get_received.side_effect = ForwardingError("http_429")
        self.assertEqual(post_event(self.client).status_code, 503)
        row = InboundEmail.objects.get()
        self.assertEqual(row.status, "pending")
        self.assertIsNone(row.forwarded_at)
        self.assertIsNone(row.first_send_at)
        self.api.send.assert_not_called()
        self.api.get_received.side_effect = None
        self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_called_once()

    def test_ambiguous_send_failure_retries_same_key_payload_and_frozen_routing(self):
        self.api.send.side_effect = ForwardingError("transport_error")
        self.assertEqual(post_event(self.client).status_code, 503)
        first_call = self.api.send.call_args
        row = InboundEmail.objects.get()
        self.assertIsNotNone(row.first_send_at)
        self.assertEqual(row.status, "pending")
        self.assertIsNone(row.forwarded_at)
        self.api.send.side_effect = None
        with override_settings(EMAIL_FORWARD_TO="different@example.com", DEFAULT_FROM_EMAIL="different@notifications.konaswimhub.com"):
            self.assertEqual(post_event(self.client).status_code, 200)
        self.assertEqual(self.api.send.call_args, first_call)

    def test_successful_send_response_missing_id_is_retryable_with_same_key(self):
        self.api.send.return_value = {}
        self.assertEqual(post_event(self.client).status_code, 503)
        self.assertEqual(InboundEmail.objects.get().error_code, "invalid_send_response")
        self.api.send.return_value = {"id": SENT_ID}
        self.assertEqual(post_event(self.client).status_code, 200)
        self.assertEqual(self.api.send.call_args_list[0], self.api.send.call_args_list[1])

    def test_expired_lease_can_retry_but_active_lease_returns_503(self):
        row = InboundEmail.objects.create(
            email_id=EMAIL_ID, forward_to=CONFIG["EMAIL_FORWARD_TO"],
            forward_from=CONFIG["DEFAULT_FROM_EMAIL"], status="processing",
            lease_id=uuid4(), lease_until=timezone.now() + timedelta(minutes=2),
        )
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.get_received.assert_not_called()
        InboundEmail.objects.filter(pk=row.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_called_once()

    def test_unresolved_send_outside_idempotency_window_requires_manual_review(self):
        InboundEmail.objects.create(
            email_id=EMAIL_ID, forward_to=CONFIG["EMAIL_FORWARD_TO"],
            forward_from=CONFIG["DEFAULT_FROM_EMAIL"],
            first_send_at=timezone.now() - timedelta(hours=23),
        )
        for _ in range(2):
            self.assertEqual(post_event(self.client).status_code, 503)
        self.api.get_received.assert_not_called()
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().error_code, "idempotency_window_expired")

    def test_payload_change_after_ambiguous_send_is_not_sent_again(self):
        self.api.send.side_effect = ForwardingError("transport_error")
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.get_received.return_value["text"] = "Unexpected changed content"
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.send.assert_called_once()
        self.assertEqual(InboundEmail.objects.get().error_code, "payload_changed")

    def test_database_failure_after_success_does_not_allow_unprotected_resend(self):
        # Simulate losing the database after Resend has accepted the message.
        original_update = QuerySet.update
        def fail_final_update(queryset, **kwargs):
            if kwargs.get("status") == "forwarded":
                raise OperationalError("not logged: private connection details")
            return original_update(queryset, **kwargs)
        with patch("django.db.models.query.QuerySet.update", new=fail_final_update):
            self.assertEqual(post_event(self.client).status_code, 503)
        row = InboundEmail.objects.get()
        self.assertIsNotNone(row.first_send_at)
        self.assertEqual(row.status, "processing")
        InboundEmail.objects.filter(pk=row.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(post_event(self.client).status_code, 200)
        self.assertEqual(self.api.send.call_args_list[0], self.api.send.call_args_list[1])

    def test_loops_are_ignored_and_duplicate_ignored_delivery_stays_ignored(self):
        for sender in (CONFIG["EMAIL_FORWARD_TO"], CONFIG["DEFAULT_FROM_EMAIL"], "team@ilkaxle.resend.app"):
            with self.subTest(sender=sender):
                InboundEmail.objects.all().delete()
                self.api.get_received.return_value["from"] = sender
                self.assertEqual(post_event(self.client).status_code, 200)
                self.assertEqual(InboundEmail.objects.get().status, "ignored")
                self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_not_called()

    @override_settings(EMAIL_FORWARD_TO="example.test@gmail.com")
    def test_gmail_plus_dot_and_googlemail_aliases_are_loop_senders(self):
        self.api.get_received.return_value["from"] = "ExampleTest+loop@googlemail.com"
        self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_not_called()

    def test_our_loop_marker_is_not_reforwarded(self):
        self.api.get_received.return_value["headers"]["X-Kona-Swim-Hub-Forwarded"] = "1"
        self.assertEqual(post_event(self.client).status_code, 200)
        self.api.send.assert_not_called()

    def test_html_only_email_becomes_safe_plain_text(self):
        self.api.get_received.return_value.update(
            text=None, subject="Fwd: Existing subject",
            html='<style>hidden-style</style><script>bad-script()</script><p>Hello <b>Parent</b></p><img src="https://tracking.example/">',
        )
        self.assertEqual(post_event(self.client).status_code, 200)
        payload = self.api.send.call_args.args[0]
        self.assertEqual(payload["subject"], "Fwd: Existing subject")
        self.assertIn("Hello", payload["text"])
        self.assertNotIn("bad-script", payload["text"])
        self.assertNotIn("hidden-style", payload["text"])
        self.assertNotIn("tracking.example", payload["text"])
        self.assertNotIn("html", payload)

    def test_attachments_are_downloaded_and_sent_as_base64(self):
        self.api.get_received.return_value["attachments"] = [{"id": ATTACHMENT_ID}]
        self.api.get_attachment.return_value = {
            "id": ATTACHMENT_ID, "filename": "photo.png", "size": 3,
            "download_url": "https://inbound-cdn.resend.com/attachment?signature=private",
        }
        self.api.download_attachment.return_value = b"abc"
        self.assertEqual(post_event(self.client).status_code, 200)
        payload = self.api.send.call_args.args[0]
        self.assertEqual(payload["attachments"], [{"filename": "photo.png", "content": "YWJj"}])
        self.assertNotIn("download_url", json.dumps(payload))

    def test_attachment_download_failure_does_not_send_partial_message(self):
        self.api.get_received.return_value["attachments"] = [{"id": ATTACHMENT_ID}]
        self.api.get_attachment.side_effect = ForwardingError("http_503")
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().status, "pending")

    def test_large_attachment_requires_review_without_sending_or_downloading(self):
        self.api.get_received.return_value["attachments"] = [{"id": ATTACHMENT_ID}]
        self.api.get_attachment.return_value = {
            "id": ATTACHMENT_ID, "filename": "large.pdf", "size": 6 * 1024 * 1024,
        }
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.download_attachment.assert_not_called()
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().error_code, "attachment_size_limit")

    def test_too_many_attachments_are_not_silently_dropped(self):
        self.api.get_received.return_value["attachments"] = [{"id": str(uuid4())} for _ in range(11)]
        self.assertEqual(post_event(self.client).status_code, 503)
        self.api.get_attachment.assert_not_called()
        self.api.send.assert_not_called()
        self.assertEqual(InboundEmail.objects.get().error_code, "attachment_count_limit")

    def test_cumulative_attachment_size_is_bounded(self):
        self.api.get_received.return_value["attachments"] = [{"id": ATTACHMENT_ID}]
        self.api.get_attachment.return_value = {
            "id": ATTACHMENT_ID, "filename": "photo.png", "size": 3,
            "download_url": "https://inbound-cdn.resend.com/file",
        }
        with patch("inbound.forwarding.MAX_TOTAL_ATTACHMENT_BYTES", 2):
            self.assertEqual(post_event(self.client).status_code, 503)
        self.api.download_attachment.assert_not_called()
        self.api.send.assert_not_called()


@override_settings(**CONFIG)
class ConcurrentDeliveryTests(TransactionTestCase):
    def test_concurrent_duplicate_delivery_does_not_send_twice(self):
        entered = threading.Event()
        release = threading.Event()
        def get_received(email_id):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Concurrent request never released")
            return copy.deepcopy(RECEIVED)
        def deliver():
            close_old_connections()
            try:
                return post_event(Client()).status_code
            finally:
                connections.close_all()
        with patch("inbound.forwarding.ResendClient") as client_class:
            api = client_class.return_value
            api.get_received.side_effect = get_received
            api.send.return_value = {"id": SENT_ID}
            with ThreadPoolExecutor(max_workers=1) as executor:
                first = executor.submit(deliver)
                try:
                    self.assertTrue(entered.wait(5))
                    self.assertEqual(post_event(Client()).status_code, 503)
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=5), 200)
            self.assertEqual(post_event(Client()).status_code, 200)
            api.send.assert_called_once()
