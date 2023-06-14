from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200)
    password = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_instructor = models.BooleanField(default=False, blank=True)
    course_created = models.ForeignKey(
        "lessons.Course", null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return self.first_name[:50] + " " + self.last_name[:50]


class Learner(models.Model):
    associated_with_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthday = models.DateField()

    def __str__(self):
        return self.first_name[:50] + " " + self.last_name[:50]


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField()

    def __str__(self):
        return self.customuser.email
