from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

from .models import Learner
from .models import Course
from .models import Waitlist

# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        # 'email', 
        # 'username', 
        'age', 
        # 'is_instructor'
    ]
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('age',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('age',)}),)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Learner)
admin.site.register(Course)
admin.site.register(Waitlist)
