from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from accounts.models import CustomUser, Learner, Profile

# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        'username', 
        'first_name',
        'last_name',
        'email', 
        'is_instructor',
    ]
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('is_instructor',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('is_instructor',)}),)

class LearnerAdmin(admin.ModelAdmin):
    list_display = [
        'first_name',
        'last_name',
        'associated_with_user',
    ]

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Learner, LearnerAdmin)
admin.site.register(Profile)
    