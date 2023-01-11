from django.test import TestCase

from .models import Course
from accounts.models import Learner

class TestModels(TestCase):
    def test_course_has_learners(self):
        course = Course.objects.create(course_title="Test Course")
        bob = Learner.objects.create(first_name="Bob", last_name="Boy", birthday="2000-01-01")
        jane = Learner.objects.create(first_name="Jane", last_name="Girl", birthday="2001-01-01")
        course.learner_on_roster.set([bob.pk, jane.pk])
        self.assertEqual(course.learner_on_roster.count(), 2)
    
    def test_course_has_waitlist(self):
        course = Course.objects.create(course_title="Test Course Full")
        kekoa = Learner.objects.create(first_name="Kekoa", last_name="Boy", birthday="2000-01-01")
        maile = Learner.objects.create(first_name="Maile", last_name="Girl", birthday="2001-01-01")
        course.learner_on_waitlist.set([kekoa.pk, maile.pk])
        self.assertEqual(course.learner_on_waitlist.count(), 2)