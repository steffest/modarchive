from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

from homepage.models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_after_activation(sender, instance, **kwargs):
    if instance.is_active and not hasattr(instance, 'profile'):
        Profile.objects.create(user = instance, display_name = instance.username)
