from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        'email', 
        'username', 
        'first_name',
        'last_name',
        'is_instructor',
    ]
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('is_instructor',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('is_instructor',)}),)

    admin.site.register(CustomUser, CustomUserAdmin)