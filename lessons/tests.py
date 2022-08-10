# Is get_user_model correct here?
from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from .models import User
from .models import Learner
from .models import Course
from .models import Waitlist

class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            email="test@gmail.com", password="secret", first_name="testuserfirst", last_name="testuserlast", is_instructor="false"
        )

        # cls.user = User.objects.create(
        #     title="A good title",
        #     body="Nice body content",
        #     author=cls.user,
        # )

    # def test_post_model(self):
    #     self.assertEqual(self.post.title, "A good title")
    #     self.assertEqual(self.post.body, "Nice body content")
    #     self.assertEqual(self.post.author.username, "testuser")
    #     self.assertEqual(str(self.post), "A good title")
    #     self.assertEqual(self.post.get_absolute_url(), "/post/1/")

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