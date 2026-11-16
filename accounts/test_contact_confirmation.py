"""Public contact submissions must finish without requiring an account."""

from urllib.parse import parse_qs, urlsplit

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    TURNSTILE_ENABLE=False,
    DEFAULT_FROM_EMAIL="sender@example.com",
    CONTACT_EMAIL="contact@example.com",
)
class PublicContactConfirmationTests(TestCase):
    def test_anonymous_visitor_can_open_confirmation(self):
        response = self.client.get(reverse("contact_thanks"), secure=True)

        self.assertContains(response, "Thank you for your message.")
        self.assertTemplateUsed(response, "contact_thanks.html")

    def test_anonymous_submission_reaches_confirmation(self):
        response = self.client.post(
            reverse("contact"),
            {
                "from_email": "family@example.com",
                "subject": "Question about lessons",
                "message": "Please share information about swim lessons.",
            },
            follow=True,
            secure=True,
        )

        self.assertRedirects(response, reverse("contact_thanks"))
        self.assertContains(response, "Thank you for your message.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Please share information about swim lessons.", mail.outbox[0].body)

    def test_instructor_confirmation_still_requires_login(self):
        response = self.client.get(reverse("contact_instructor_thanks"), secure=True)

        self.assertEqual(response.status_code, 302)
        destination = urlsplit(response.url)
        self.assertEqual(destination.path, reverse("login"))
        self.assertEqual(
            parse_qs(destination.query)["next"],
            [reverse("contact_instructor_thanks")],
        )
