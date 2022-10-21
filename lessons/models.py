from django.conf import settings # new to get list of courses to work
from django.db import models
from django.urls import reverse
from accounts.models import CustomUser, Learner

Course = settings.AUTH_USER_MODEL # new to get list of courses to work

class Course(models.Model):
    course_instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True) # Check this: When User is deleted, also delete the Course. 
    course_title = models.CharField(max_length=100, default=None)
    course_description = models.CharField(max_length=250)
    course_age_range_min = models.IntegerField(null=True)
    course_age_range_max = models.IntegerField(null=True)
    course_location = models.CharField(max_length=100) 
    course_start_date = models.DateField(help_text="Enter the date this course will begin.")
    course_end_date = models.DateField(help_text="Enter the date this course will end.")
    course_day_of_week = models.CharField(max_length=100)
    course_start_time = models.TimeField(help_text="Enter the start time for this course (e.g., 01:00 PM)")
    course_end_time = models.TimeField(help_text="Enter the end time for this course (e.g., 02:00 PM)")
    num_spots_available = models.IntegerField()
    # learner_on_roster = models.ManyToManyField(to=Learner, related_name="learners", default=1, blank=True)
    learner_on_roster = models.ManyToManyField(to=Learner, related_name="learners", blank=True)
    def __str__(self):
        return self.course_title[:50]
    
    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"pk": self.pk})

class Waitlist(models.Model):  
    course_instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    associated_course = models.ForeignKey('Course', null=True, on_delete=models.CASCADE)
    listed_on_waitlist = models.ManyToManyField(to=Learner, related_name="waitlisted", blank=True)



