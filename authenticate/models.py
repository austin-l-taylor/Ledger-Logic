from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    dob = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    password_expiry = models.DateField(null=True, blank=True)
    question1 = models.CharField(max_length=255, null=True, blank=True)
    answer1 = models.CharField(max_length=255, null=True, blank=True)
    question2 = models.CharField(max_length=255, null=True, blank=True)
    answer2 = models.CharField(max_length=255, null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)

class PasswordHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    password = models.CharField(max_length=255) 
    date_set = models.DateTimeField(auto_now_add=True)

class EmailNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=255)
    sent_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username} sent on {self.sent_date}"