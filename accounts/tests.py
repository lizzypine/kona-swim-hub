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
    def test_is_invalid(self):
        form = ContactForm(data={'from_email': 'not an email', 'subject': 'This is the subject', 'message': 'This is the message.'})
        self.assertFalse(form.is_valid())

    def test_form_is_valid(self):
        form = ContactForm(data={'from_email': 'test@gmail.com', 'subject': 'This is the subject', 'message': 'This is the message.'})
        self.assertTrue(form.is_valid())