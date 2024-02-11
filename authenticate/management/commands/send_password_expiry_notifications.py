from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from authenticate.models import CustomUser, EmailNotification

#section for notifying all users whose password is about to expire in 3 days
class Command(BaseCommand):
    help = 'Notify a user about password expiry and log the notification into emailnotification table.'

    def handle(self, *args, **kwargs):
        target_date = now().date() + timedelta(days=3)
        users_to_notify = CustomUser.objects.filter(
            password_expiry=target_date
        ).exclude(
            emailnotification__notification_type='password-expiry',
            emailnotification__sent_date__date=now().date()
        )

        for user in users_to_notify:
            if not EmailNotification.objects.filter(user=user, notification_type='password-expiry', sent_date__date=now().date()).exists():
                send_mail(
                    'Password Expiry Notice',
                    f'Hi {user.username}, your password is about to expire in 3 days! Please update it as soon as possible.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                EmailNotification.objects.create(
                    user=user,
                    notification_type='password-expiry',
                    sent_date=now()
                )

                self.stdout.write(self.style.SUCCESS(f'User {user.email} has been notified via email about password expiring in 3 days.'))


#section for testing a single user already in the database: 'jonathanochoa'
"""
class Command(BaseCommand):
    help = 'Notify a user about password expiry and log the notification into emailnotification table.'

    def handle(self, *args, **kwargs):
        # Temporary filter for testing: filter by username
        users_to_notify = CustomUser.objects.filter(username='jonathanochoa')

        for user in users_to_notify:
            send_mail(
                'Password Expiry Notice',
                f'Hi {user.username}, your password is about to expire in 3 days! Please update it as soon as possible.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Log the notification in EmailNotification table
            EmailNotification.objects.create(
                user=user,
                notification_type='password-expiry',
                sent_date=now()
            )

            self.stdout.write(self.style.SUCCESS(f'User {user.email} has been notified via email about password expiring in 3 days.'))
"""