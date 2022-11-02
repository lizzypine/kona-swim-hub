from django.test import TestCase
from django.urls import reverse

from lessons.lessons.models import User

class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            email="test@gmail.com", password="secret", first_name="testuserfirst", last_name="testuserlast", is_instructor="false"
        )

    def test_model_content(self):
        self.assertEqual(self.user.email, "test@email.com")

    def test_url_exists_at_correct_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code,200)

    def test_url_available_by_name(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_template_name_correct(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")

    def test_template_content(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "<h1>Homepage</h1>")