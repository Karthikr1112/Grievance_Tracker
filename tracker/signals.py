from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserRole
from .models import UserProfile, Role

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = UserRole.ADMIN if instance.is_superuser else UserRole.STORE_USER
        UserProfile.objects.create(user=instance, role=role)
        admin_role = None
        if instance.is_superuser:
            admin_role = Role.objects.filter(is_admin=True).first()
            admin_role = Role.objects.filter(name__icontains='admin').first()
        UserProfile.objects.create(user=instance, role=admin_role)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            role = UserRole.ADMIN if instance.is_superuser else UserRole.STORE_USER
            UserProfile.objects.create(user=instance, role=role)

            admin_role = None
            if instance.is_superuser:
                admin_role = Role.objects.filter(is_admin=True).first()
                admin_role = Role.objects.filter(name__icontains='admin').first()
            UserProfile.objects.create(user=instance, role=admin_role)
