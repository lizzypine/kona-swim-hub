from django.conf import settings # new to get list of courses to work
from django.db import models

# DAYS_OF_WEEK = [
#   ('Monday'), 
#   ('Tuesday'), 
#   ('Wednesday'), 
#   ('Thursday'), 
#   ('Friday'), 
#   ('Saturday'), 
#   ('Sunday')
# ]
Course= settings.AUTH_USER_MODEL # new to get list of courses to work

class Learner(models.Model):
    associated_with_user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True, default=1) # When User is deleted, also delete the Learner.
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    birthday = models.DateField()
    # enrolled_in_course = models.ForeignKey(Course, on_delete=models.SET_NULL) # Fix Course model then try again.
    # enrolled_in_course = models.ForeignKey(Course, on_delete=models.SET_NULL)
    #on_waitlist = models.ForeignKey(Waitlist, on_delete=models.SET_NULL)

class Course(models.Model):
    course_instructor = models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE, null=True) # Check this: When User is deleted, also delete the Course. 
    course_title = models.CharField(max_length=100, default=None)
    course_description = models.CharField(max_length=250)
    course_age_range_min = models.IntegerField(null=True)
    course_age_range_max = models.IntegerField(null=True)
    course_location = models.CharField(max_length=100) 
    course_start_date = models.DateField(help_text="Enter the date this course will begin.")
    course_end_date = models.DateField(help_text="Enter the date this course will end.")
    course_day_of_week = models.CharField(max_length=100) # Later: Select day of week (e.g., Monday, Tuesday) from checkboxes.
    # course_day_of_week = models.ManyToManyField(models.self, DAY_CHOICES)
    course_start_time = models.TimeField(help_text="Enter the start time for this course (e.g., 01:00 PM)")
    course_end_time = models.TimeField(help_text="Enter the end time for this course (e.g., 02:00 PM)")
    num_spots_available = models.IntegerField()
    # learner_on_roster = models.ForeignKey(Learner, on_delete=models.SET_NULL=True)
    def __str__(self):
        return self.course_title[:50]

class Waitlist(models.Model):  
    course_instructor = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True)
    associated_course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)



