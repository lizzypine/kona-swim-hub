from django.contrib import admin

from lessons.models import Course
from lessons.models import Waitlist

# Register your models here.
admin.site.register(Course)
admin.site.register(Waitlist)
