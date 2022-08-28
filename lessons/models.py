from django.db import models

# Create your models here.

class Learner(models.Model):
    associated_with_user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True, default=1) # When User is deleted, also delete the Learner.
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    birthday = models.DateField()
    # enrolled_in_course = models.ForeignKey(Course, on_delete=models.SET_NULL) # Fix Course model then try again.
    # enrolled_in_course = models.ForeignKey(Course, on_delete=models.SET_NULL)
    #on_waitlist = models.ForeignKey(Waitlist, on_delete=models.SET_NULL)

class Course(models.Model):
    course_instructor = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True) # Check this: When User is deleted, also delete the Course. 
    course_title = models.CharField(max_length=100, default=None)
    course_age_range = models.CharField(max_length=100)
    # course_age_range = IntegerRange() # Is this right?
    course_location = models.CharField(max_length=100)
    course_start_date = models.DateField()
    course_end_date = models.DateField()
    course_day_of_week = models.CharField(max_length=100) # Later: Select day of week (e.g., Monday, Tuesday) from checkboxes.
    course_time = models.TimeField()
    spots_available = models.CharField(max_length=100)
    # spots_available = models.Boolean()
    num_spots_available = models.IntegerField() # Do I need to do something else here?
    # learner_on_roster = models.ForeignKey(Learner, on_delete=models.SET_NULL=True)
    def __str__(self):
        return self.course_title[:50]

class Waitlist(models.Model):  
    course_instructor = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True)
    associated_course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)



