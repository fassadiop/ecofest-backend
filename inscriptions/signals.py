from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Inscription
from .tasks import send_invitation_package

@receiver(post_save, sender=Inscription)
def trigger_invitation_generation(sender, instance, created, **kwargs):
    """
    Déclenche automatiquement la génération du badge + invitation PDF
    lorsque l'INSCRIPTION passe en statut 'Validé'.
    """

    # On ignore la création initiale (statut = En_attente)
    if created:
        return

    # On ne réagit que lorsque le statut devient Validé
    if instance.statut == "Validé":
        send_invitation_package.delay(instance.id)
