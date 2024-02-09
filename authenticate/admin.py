from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'dob')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_suspended', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'password_expiry')}),
        (_('Security Questions'), {'fields': ('question1', 'answer1', 'question2', 'answer2')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'dob')}),
        (_('Security Questions'), {'fields': ('question1', 'answer1', 'question2', 'answer2')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_suspended', 'dob', 'status') 
    search_fields = ('username', 'first_name', 'last_name', 'email')

admin.site.register(CustomUser, CustomUserAdmin)

