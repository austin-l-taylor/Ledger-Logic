"""
This file contains the signals for the Chart of Accounts model.
This will be called before and after a ChartOfAccounts instance is saved (or deleted, for deactivation). 
These handlers will create a CoAEventLog entry.
"""

from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.core.serializers import serialize
from django.utils import timezone
from .models import ChartOfAccounts, CoAEventLog

@receiver(pre_save, sender=ChartOfAccounts)
def log_pre_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._pre_save_instance = old_instance
        except sender.DoesNotExist:
            pass  # This is an add, not an update

@receiver(post_save, sender=ChartOfAccounts)
def log_post_change(sender, instance, created, **kwargs):
    action = 'added' if created else 'modified'
    before_change = serialize('json', [instance._pre_save_instance]) if hasattr(instance, '_pre_save_instance') else None
    after_change = serialize('json', [instance])
    
    CoAEventLog.objects.create(
        user=instance.user_id, 
        action=action,
        before_change=before_change,
        after_change=after_change,
        chart_of_account=instance
    )
    
@receiver(pre_delete, sender=ChartOfAccounts)
def log_pre_delete(sender, instance, **kwargs):
    before_change = serialize('json', [instance])
    
    CoAEventLog.objects.create(
        user=instance.user_id, 
        action='deactivated',
        before_change=before_change,
        chart_of_account=instance
    )