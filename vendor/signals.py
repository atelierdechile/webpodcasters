from django.db.models.signals import m2m_changed
from django.contrib.auth.models import User
from django.dispatch import receiver

from vendor.models import Profile, UserPreference, Preference


@receiver(m2m_changed, sender=Profile.preferences.through)
def log_user_preference_change(sender, instance, action, pk_set, **kwargs):
    """
    Registra automáticamente cuando un usuario agrega o quita una preferencia.
    """

    user = instance.user

    if action == "post_add":
        for pk in pk_set:
            pref = Preference.objects.get(pk=pk)
            UserPreference.objects.create(
                user=user,
                preference=pref,
                action="add",
            )

    if action == "post_remove":
        for pk in pk_set:
            pref = Preference.objects.get(pk=pk)
            UserPreference.objects.create(
                user=user,
                preference=pref,
                action="remove",
            )
