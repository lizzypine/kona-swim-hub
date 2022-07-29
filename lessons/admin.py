from django.contrib import admin

from .models import User
from .models import Learner
from .models import Course
from .models import Waitlist

# Register your models here.

admin.site.register(User)
admin.site.register(Learner)
admin.site.register(Course)
admin.site.register(Waitlist)
