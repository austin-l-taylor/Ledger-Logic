from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

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
    suspension_start_date = models.DateField(null=True, blank=True)
    suspension_end_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.is_suspended:
            self.suspension_start_date = None
            self.suspension_end_date = None
        else:
            if self.suspension_start_date and self.suspension_end_date:
                today = timezone.now().date()
                self.is_suspended = self.suspension_start_date <= today <= self.suspension_end_date
            else:
                self.is_suspended = False
        super().save(*args, **kwargs)

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