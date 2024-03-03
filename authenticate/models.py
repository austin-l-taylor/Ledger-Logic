from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    A custom user model that extends Django's built-in AbstractUser model.

    This model adds additional fields for date of birth, status, profile picture, password expiry, security questions and answers, suspension status, failed login attempts, and suspension dates.

    Attributes:
    dob (DateField): The user's date of birth. Can be null.
    status (BooleanField): The user's status. Default is True.
    profile_picture (ImageField): The user's profile picture. Can be null.
    password_expiry (DateField): The date when the user's password expires. Can be null.
    question1 (CharField): The first security question. Can be null.
    answer1 (CharField): The answer to the first security question. Can be null.
    question2 (CharField): The second security question. Can be null.
    answer2 (CharField): The answer to the second security question. Can be null.
    is_suspended (BooleanField): Whether the user is suspended. Default is False.
    failed_login_attempts (IntegerField): The number of failed login attempts. Default is 0.
    suspension_start_date (DateField): The start date of the suspension. Can be null.
    suspension_end_date (DateField): The end date of the suspension. Can be null.
    """

    dob = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
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
        # Resets suspension dates if user is not suspended. Checks if the current date falls between suspension start and end dates.
        if not self.is_suspended:
            self.suspension_start_date = None
            self.suspension_end_date = None
        else:
            # Auto-lift suspension if current date is outside suspension period
            if self.suspension_start_date and self.suspension_end_date:
                today = timezone.now().date()
                self.is_suspended = (
                    self.suspension_start_date <= today <= self.suspension_end_date
                )
            else:
                self.is_suspended = False
        super().save(*args, **kwargs)


class PasswordHistory(models.Model):
    """
    A model for storing password history.

    This model includes fields for the user, password, and the date when the password was set.

    Attributes:
    user (ForeignKey): The user who owns the password. On user deletion, the password history will be deleted as well.
    password (CharField): The password.
    date_set (DateTimeField): The date and time when the password was set. Set automatically when the object is created.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    password = models.CharField(max_length=255)
    date_set = models.DateTimeField(auto_now_add=True)
    # auto_now_add sets the date/time when the object is created


class EmailNotification(models.Model):
    """
    A model for storing email notifications.

    This model includes fields for the user, notification type, and the date when the notification was sent.

    Attributes:
    user (ForeignKey): The user who received the notification. On user deletion, the email notification will be deleted as well.
    notification_type (CharField): The type of the notification.
    sent_date (DateTimeField): The date and time when the notification was sent. Set automatically when the object is created.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=255)
    sent_date = models.DateTimeField(auto_now_add=True)
    # auto_now_add sets the date/time when the object is created

    def __str__(self):
        # String representation includes notification type, user, and sent date
        return f"{self.notification_type} notification for {self.user.username} sent on {self.sent_date}"


class ChartOfAccounts(models.Model):
    """
    A model for storing chart of accounts in the database.
    This is the main database to be used in Sprint 2.
    """
    account_name = models.CharField(max_length=255)
    account_number = models.PositiveIntegerField()
    account_description = models.TextField()
    is_active = models.BooleanField(default=True)
    normal_side = models.CharField(max_length=255)
    account_category = models.CharField(max_length=255)
    account_subcategory = models.CharField(max_length=255)
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2)
    debit = models.DecimalField(max_digits=10, decimal_places=2)
    credit = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    date_time_account_added = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.CharField(max_length=255)
    statement = models.CharField(max_length=255)
    comment = models.TextField()

    def __str__(self):
        return self.account_name