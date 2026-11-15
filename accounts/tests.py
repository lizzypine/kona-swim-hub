import json
import re
from io import BytesIO
from urllib.parse import parse_qs, urlsplit
from smtplib import SMTPServerDisconnected
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from lessons.models import Course
from .models import CustomUser, Learner
from .forms import ContactForm, ResilientTurnstileField
from django.http import HttpRequest


@override_settings(TURNSTILE_ENABLE=True, TURNSTILE_SECRET="fake-private-secret")
class TurnstileVerificationTests(SimpleTestCase):
    token = "fake-private-token"

    def verify(self, result, remote_ip=None):
        with patch("accounts.forms.build_opener") as build_opener:
            build_opener.return_value.open.return_value = BytesIO(json.dumps(result).encode())
            ResilientTurnstileField(remote_ip=remote_ip).clean(self.token)
        return build_opener.return_value.open.call_args

    def test_success_logs_only_safe_metadata_and_omits_absent_ip(self):
        with self.assertLogs("accounts.forms", level="INFO") as logs:
            call = self.verify({
                "success": True,
                "hostname": "konaswimhub.com",
                "cdata": self.token,
                "secret": settings.TURNSTILE_SECRET,
            })
        request = call.args[0]
        self.assertEqual(request.full_url, "https://challenges.cloudflare.com/turnstile/v0/siteverify")
        self.assertEqual(parse_qs(request.data.decode()), {
            "secret": [settings.TURNSTILE_SECRET], "response": [self.token],
        })
        self.assertEqual(call.kwargs["timeout"], 5)
        self.assertIn('"success": true', logs.output[0])
        self.assertIn("konaswimhub.com", logs.output[0])
        self.assertNotIn(self.token, " ".join(logs.output))
        self.assertNotIn(settings.TURNSTILE_SECRET, " ".join(logs.output))

    def test_explicit_remote_ip_is_forwarded(self):
        call = self.verify({"success": True}, remote_ip="192.0.2.1")
        self.assertEqual(parse_qs(call.args[0].data.decode())["remoteip"], ["192.0.2.1"])

    def test_rejection_logs_cloudflare_reason_without_sensitive_data(self):
        with self.assertLogs("accounts.forms", level="WARNING") as logs:
            with self.assertRaisesMessage(ValidationError, "Turnstile could not be verified"):
                self.verify({
                    "success": False,
                    "error-codes": ["invalid-input-secret", "timeout-or-duplicate"],
                    "hostname": "konaswimhub.com",
                    "cdata": self.token,
                    "secret": settings.TURNSTILE_SECRET,
                })
        self.assertIn("invalid-input-secret", logs.output[0])
        self.assertIn("timeout-or-duplicate", logs.output[0])
        self.assertIn("konaswimhub.com", logs.output[0])
        self.assertNotIn(self.token, " ".join(logs.output))
        self.assertNotIn(settings.TURNSTILE_SECRET, " ".join(logs.output))
        self.assertIsNone(logs.records[0].exc_info)

    def test_metadata_redacts_credentials_even_if_reflected(self):
        with self.assertLogs("accounts.forms", level="WARNING") as logs:
            with self.assertRaisesMessage(ValidationError, "Turnstile could not be verified"):
                self.verify({
                    "success": False,
                    "error-codes": [settings.TURNSTILE_SECRET],
                    "hostname": self.token,
                })
        self.assertNotIn(self.token, " ".join(logs.output))
        self.assertNotIn(settings.TURNSTILE_SECRET, " ".join(logs.output))

    def test_transport_failure_does_not_log_exception_contents(self):
        with patch("accounts.forms.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = OSError(
                f"{self.token} {settings.TURNSTILE_SECRET}"
            )
            with self.assertLogs("accounts.forms", level="WARNING") as logs:
                with self.assertRaisesMessage(ValidationError, "temporarily unavailable"):
                    ResilientTurnstileField().clean(self.token)
        self.assertNotIn(self.token, " ".join(logs.output))
        self.assertNotIn(settings.TURNSTILE_SECRET, " ".join(logs.output))
        self.assertIsNone(logs.records[0].exc_info)

    def test_invalid_responses_fail_closed(self):
        for body in (b"not-json", b"[]", b"null", b'{}', b'{"success": "false"}'):
            with self.subTest(body=body), patch("accounts.forms.build_opener") as build_opener:
                build_opener.return_value.open.return_value = BytesIO(body)
                with self.assertLogs("accounts.forms", level="WARNING"):
                    with self.assertRaisesMessage(ValidationError, "temporarily unavailable"):
                        ResilientTurnstileField().clean(self.token)

    def test_missing_token_does_not_call_siteverify(self):
        with patch("accounts.forms.build_opener") as build_opener:
            with self.assertRaisesMessage(ValidationError, "Please prove you are a human"):
                ResilientTurnstileField().clean("")
        build_opener.assert_not_called()

    @override_settings(TURNSTILE_ENABLE=False)
    def test_explicitly_disabled_verification_does_not_call_siteverify(self):
        with patch("accounts.forms.build_opener") as build_opener:
            ResilientTurnstileField().clean("")
        build_opener.assert_not_called()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username="reset-parent", email="parent@example.com", password="test-password"
        )

    def post_reset(self, email):
        response = self.client.post(
            reverse("password_reset"), {"email": email},
            HTTP_HOST="konaswimhub.com", HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertRedirects(response, reverse("password_reset_done"))

    def test_active_user_receives_message_with_working_https_reset_link(self):
        self.post_reset(self.user.email)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(message.to, [self.user.email])
        link = re.search(r"https://konaswimhub\.com/accounts/reset/[^\s]+", message.body)
        self.assertIsNotNone(link)
        response = self.client.get(urlsplit(link.group()).path, follow=True)
        self.assertContains(response, 'name="new_password1"')

    def test_unknown_email_gets_confirmation_without_sending(self):
        self.post_reset("unknown@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_inactive_user_gets_confirmation_without_sending(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.post_reset(self.user.email)
        self.assertEqual(len(mail.outbox), 0)

    def test_unusable_password_gets_confirmation_without_sending(self):
        self.user.set_unusable_password()
        self.user.save(update_fields=["password"])
        self.post_reset(self.user.email)
        self.assertEqual(len(mail.outbox), 0)

    @patch("django.core.mail.EmailMultiAlternatives.send", side_effect=SMTPServerDisconnected("disconnected"))
    def test_delivery_failure_is_logged_but_still_shows_confirmation(self, send):
        with self.assertLogs("django.contrib.auth", level="ERROR") as logs:
            self.post_reset(self.user.email)
        send.assert_called_once()
        self.assertIn("Failed to send password reset email", logs.output[0])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Kona Swim Hub <team@notifications.konaswimhub.com>",
    CONTACT_EMAIL="team@konaswimhub.com",
)
class MailSenderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = CustomUser.objects.create_user(
            username="course-parent", email="parent@example.com", first_name="Parent"
        )
        cls.instructor = CustomUser.objects.create_user(
            username="course-instructor", email="instructor@example.com",
            first_name="Instructor", is_instructor=True,
        )
        cls.learner = Learner.objects.create(
            first_name="Learner", last_name="Test", birthday="2020-01-01",
            associated_with_user=cls.parent,
        )
        cls.course = Course.objects.create(
            course_title="Beginner swimming", course_instructor=cls.instructor,
            num_spots_available=2,
        )

    def test_account_registration_uses_configured_sender(self):
        response = self.client.post(reverse("register"), {
            "username": "new-parent", "email": "new-parent@example.com",
            "first_name": "New", "last_name": "Parent",
            "password1": "A-swimming-password-927!",
            "password2": "A-swimming-password-927!",
        })
        self.assertRedirects(response, reverse("register_thanks"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, ["new-parent@example.com"])

    def test_course_registration_uses_configured_sender_for_both_messages(self):
        self.client.force_login(self.parent)
        response = self.client.post(
            reverse("course_registration", args=[self.course.pk]),
            {"learner": self.learner.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            [message.from_email for message in mail.outbox],
            [settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL],
        )
        self.assertEqual(mail.outbox[0].to, [self.parent.email])
        self.assertEqual(mail.outbox[1].to, [self.instructor.email])

    def test_roster_and_waitlist_copies_go_to_contact_inbox(self):
        self.course.learner_on_roster.add(self.learner)
        self.course.learner_on_waitlist.add(self.learner)
        self.client.force_login(self.instructor)
        for view_name in ("contact_learners", "contact_waitlist"):
            with self.subTest(view=view_name):
                mail.outbox.clear()
                response = self.client.post(reverse(view_name, args=[self.course.pk]), {
                    "recipient_list": [self.learner.pk],
                    "subject": "Class update", "message": "See you at the pool.",
                })
                self.assertEqual(response.status_code, 302)
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
                self.assertEqual(mail.outbox[0].to, [settings.CONTACT_EMAIL])
                self.assertEqual(mail.outbox[0].bcc, [self.parent.email])

class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customuser = CustomUser.objects.create(
        email='test@gmail.com', password='secret', first_name='testuserfirst', last_name='testuserlast', is_instructor='False'
        )

        cls.learner = Learner.objects.create(
        first_name='test_first', last_name='test_last', birthday='2000-01-01', associated_with_user=cls.customuser
        )

    def test_model_content(self):
        self.assertEqual(self.customuser.email, 'test@gmail.com')
        self.assertEqual(self.learner.associated_with_user, self.customuser)
    
    def test_anonymous_cannot_see_course_list(self):
        response = self.client.get(reverse('course_list'))
        self.assertRedirects(response, '/accounts/login/?next=/lessons/course_list/')

    def test_authenticated_user_can_see_course_list(self):
        self.client.force_login(user=self.customuser)
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
    
class TestContactForm(TestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kona Swim Hub <team@notifications.konaswimhub.com>",
        CONTACT_EMAIL="team@konaswimhub.com",
    )
    @patch("accounts.forms.build_opener")
    def test_verified_contact_queues_email(self, build_opener):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": true}')
        response = self.client.post(reverse("contact"), {
            "from_email": "family@example.com",
            "subject": "Question about lessons",
            "message": "Please call me about swim lessons.",
            "cf-turnstile-response": "test-token",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, ["team@konaswimhub.com"])
        self.assertIn("Please call me about swim lessons.", mail.outbox[0].body)

    @patch("accounts.views.send_mail")
    @patch("accounts.forms.build_opener")
    def test_rejected_turnstile_prevents_email(self, build_opener, send_mail):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": false}')
        with self.assertLogs("accounts.forms", level="WARNING"):
            response = self.client.post(reverse("contact"), {
                "from_email": "family@example.com",
                "subject": "Question about lessons",
                "message": "Please call me about swim lessons.",
                "cf-turnstile-response": "invalid-token",
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn("turnstile", response.context["form"].errors)
        send_mail.assert_not_called()

    @patch("accounts.forms.build_opener")
    def test_is_invalid(self, build_opener):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": true}')
        form = ContactForm(data={
            "from_email": "not an email",
            "subject": "This is the subject",
            "message": "This is the message.",
            "cf-turnstile-response": "test-token",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("from_email", form.errors)

    @patch("accounts.forms.build_opener")
    def test_form_is_valid(self, build_opener):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": true}')
        form = ContactForm(data={
            "from_email": "test@gmail.com",
            "subject": "This is the subject",
            "message": "This is the message.",
            "cf-turnstile-response": "test-token",
        })
        self.assertTrue(form.is_valid())

    @patch("accounts.forms.build_opener")
    def test_invalid_turnstile_token_is_rejected(self, build_opener):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": false}')
        form = ContactForm(data={
            "from_email": "test@gmail.com",
            "subject": "This is the subject",
            "message": "This is the message.",
            "cf-turnstile-response": "invalid-token",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("turnstile", form.errors)

    @patch("accounts.forms.build_opener")
    def test_siteverify_network_failure_is_a_form_error(self, build_opener):
        build_opener.return_value.open.side_effect = OSError("network unavailable")
        form = ContactForm(data={
            "from_email": "test@gmail.com",
            "subject": "This is the subject",
            "message": "This is the message.",
            "cf-turnstile-response": "test-token",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("temporarily unavailable", str(form.errors["turnstile"]))

    @patch("accounts.views.send_mail", side_effect=SMTPServerDisconnected("disconnected"))
    @patch("accounts.forms.build_opener")
    def test_contact_email_failure_renders_retry_message(
        self, build_opener, send_mail
    ):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": true}')
        message = "Please call me about swim lessons."
        response = self.client.post(
            reverse("contact"),
            {
                "from_email": "family@example.com",
                "subject": "Question about lessons",
                "message": message,
                "cf-turnstile-response": "test-token",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Please try again later.", status_code=503)
        self.assertEqual(response.context["form"]["message"].value(), message)
        send_mail.assert_called_once()
