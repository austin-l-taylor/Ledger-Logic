from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from django.shortcuts import redirect
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'dob')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_suspended', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'password_expiry', 'suspension_start_date', 'suspension_end_date')}),
        (_('Security Questions'), {'fields': ('question1', 'answer1', 'question2', 'answer2')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'dob')}),
        (_('Security Questions'), {'fields': ('question1', 'answer1', 'question2', 'answer2')}),
        (_('Suspension Info'), {'fields': ('suspension_start_date', 'suspension_end_date')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_suspended', 'suspension_start_date', 'suspension_end_date', 'dob', 'status', 'send_email_link', 'password_expiry_status')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def send_email_link(self, obj):
        return format_html('<a href="{}">Send Email</a>', reverse('send_email', args=[obj.pk]))
    send_email_link.short_description = 'Send Email'

    def password_expiry_status(self, obj):
        if obj.password_expiry and obj.password_expiry <= timezone.now().date():
            return "Expired"
        else:
            return "Valid"
    
    password_expiry_status.short_description = 'Password Status'

    actions = None

admin.site.register(CustomUser, CustomUserAdmin)