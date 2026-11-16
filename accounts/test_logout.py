from bs4 import BeautifulSoup
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class LogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="logout-parent", email="logout-parent@example.com", first_name="Parent"
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)

    def logout_form(self):
        response = self.client.get(reverse("home"), secure=True)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form", action=reverse("logout"))
        self.assertIsNotNone(form)
        return form

    def test_navigation_renders_post_logout_button_with_csrf_token(self):
        form = self.logout_form()
        self.assertEqual(form.get("method"), "post")
        self.assertEqual(form.find("button", type="submit").get_text(strip=True), "Log Out")
        self.assertTrue(form.find("input", attrs={"name": "csrfmiddlewaretoken"})["value"])

    def test_navigation_logout_ends_session_and_returns_to_home(self):
        form = self.logout_form()
        token = form.find("input", attrs={"name": "csrfmiddlewaretoken"})["value"]
        response = self.client.post(
            form["action"], {"csrfmiddlewaretoken": token}, secure=True,
            HTTP_ORIGIN="https://testserver", follow=True,
        )
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Log In")
        self.assertNotContains(response, "Log Out")

    def test_logout_without_csrf_token_preserves_session(self):
        response = self.client.post(
            reverse("logout"), secure=True, HTTP_ORIGIN="https://testserver"
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(SESSION_KEY, self.client.session)

    def test_get_request_cannot_log_user_out(self):
        response = self.client.get(reverse("logout"), secure=True)
        self.assertEqual(response.status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)
