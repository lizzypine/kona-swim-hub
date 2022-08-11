from django.contrib import admin
# do we need the line below?
from django.contrib.auth.admin import UserAdmin

from accounts.models import CustomUser

from .models import Learner
from .models import Course
from .models import Waitlist

# Register your models here.


admin.site.register(Learner)
admin.site.register(Course)
admin.site.register(Waitlist)
