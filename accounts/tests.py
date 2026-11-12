from io import BytesIO
from smtplib import SMTPServerDisconnected
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Learner
from .forms import ContactForm
from django.http import HttpRequest

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
    @patch("turnstile.fields.build_opener")
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

    @patch("turnstile.fields.build_opener")
    def test_form_is_valid(self, build_opener):
        build_opener.return_value.open.return_value = BytesIO(b'{"success": true}')
        form = ContactForm(data={
            "from_email": "test@gmail.com",
            "subject": "This is the subject",
            "message": "This is the message.",
            "cf-turnstile-response": "test-token",
        })
        self.assertTrue(form.is_valid())

    @patch("turnstile.fields.build_opener")
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

    @patch("turnstile.fields.build_opener")
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
    @patch("turnstile.fields.build_opener")
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