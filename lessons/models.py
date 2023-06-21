from django.conf import settings
from django.db import models
from django.urls import reverse
from accounts.models import CustomUser, Learner

Course = settings.AUTH_USER_MODEL


class Course(models.Model):
    course_instructor = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=True
    )
    course_title = models.CharField(max_length=100, default=None)
    course_description = models.CharField(max_length=250)
    course_age_range_min = models.CharField(max_length=50, null=True)
    course_age_range_max = models.CharField(max_length=50, null=True)
    course_location = models.CharField(max_length=100)
    course_start_date = models.DateField(
        help_text="Enter the date this course will begin.", null=True
    )
    course_end_date = models.DateField(
        help_text="Enter the date this course will end.", null=True
    )
    course_day_of_week = models.CharField(max_length=100, blank=True, null=True)
    course_start_time = models.TimeField(
        help_text="Enter the start time for this course in Hawaii Standard Time (e.g., 01:00 PM).",
        null=True,
    )
    course_end_time = models.TimeField(
        help_text="Enter the end time for this course in Hawaii Standard Time(e.g., 02:00 PM).",
        null=True,
    )
    num_spots_available = models.IntegerField(null=True)
    course_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Enter price in US dollars.",
        null=True,
    )
    learner_on_roster = models.ManyToManyField(
        to=Learner, related_name="learners", blank=True
    )
    learner_on_waitlist = learner_on_waitlist = models.ManyToManyField(
        to=Learner, related_name="waitlisted", blank=True
    )

    def __str__(self):
        return self.course_title[:50]

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"pk": self.pk})
