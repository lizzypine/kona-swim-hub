from django.contrib.auth.models import AbstractUser
from django.db import models
from lessons.models import Course
# from django.urls import reverse

# Create your models here.

class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200)
    password = models.CharField(max_length=200)
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    # #associated_with_learner = models.ForeignKey(Learner, on_delete=models.SET_NULL) # When Learner is deleted, don't delete the User object. Set it to null.
    is_instructor = models.BooleanField(default=False)
    course_created = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)
    # age = models.PositiveIntegerField(null=True, blank=True)
    def __str__(self):
        return self.first_name[:50] + " " + self.last_name[:50]