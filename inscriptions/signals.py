from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Participant
from .tasks import send_invitation_package


@receiver(post_save, sender=Participant)
def trigger_invitation_generation(sender, instance, created, **kwargs):
    """
    Quand l'admin passe une inscription en 'VALIDÉE',
    on déclenche automatiquement le task Celery
    pour générer le badge + lettre PDF + envoi email.
    """

    # Seulement si le status devient VALIDÉ
    if instance.statut == "VALIDEE":
        send_invitation_package.delay(instance.id)
