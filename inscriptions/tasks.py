# inscriptions/tasks.py

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import Inscription, Participant
import base64
import os
from .utils_badges import generate_badge
from .utils_letters import generate_invitation_letter_pdf


# ---------------------------------------------------------
# 1) PACKAGE ACCRÉDITATION (badge + lettre + email)
# ---------------------------------------------------------
def send_invitation_package(participant_id):
    participant = Participant.objects.get(id=participant_id)

    # Générer badge PNG
    badge_path = generate_badge(participant)

    # Générer lettre PDF
    letter_path = generate_invitation_letter_pdf(participant)

    # Préparer email
    subject = "ECOFEST 2025 — Votre accréditation est confirmée !"
    body = f"""
Cher/Chère {participant.prenom},

Votre accréditation ECOFEST est validée !
Veuillez trouver en pièce jointe votre badge et votre lettre d'invitation officielle.

Cordialement,
L'équipe ECOFEST 2025.
"""

    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [participant.email],
    )

    email.attach_file(badge_path)
    email.attach_file(letter_path)

    # Envoyer l'email
    email.send(fail_silently=False)

    return {"ok": True}


# ---------------------------------------------------------
# 2) EMAIL CONFIRMATION INITIAL
# ---------------------------------------------------------
def send_confirmation_email(inscription_id):
    """
    Version synchrone : PAS de Celery.
    """
    try:
        ins = Inscription.objects.select_related('participant').get(pk=inscription_id)
    except Inscription.DoesNotExist:
        return {"ok": False, "reason": "missing"}

    ctx = {
        "inscription": ins,
        "participant": getattr(ins, "participant", None),
        "event": getattr(ins, "evenement", None),
        "site_url": getattr(settings, "SITE_URL", "https://ecofest.app"),
    }

    subject = "Réception de votre inscription – ECOFEST"
    text_body = render_to_string("emails/confirmation_full.txt", ctx)
    html_body = render_to_string("emails/confirmation_full.html", ctx)

    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [ins.email])
    msg.attach_alternative(html_body, "text/html")

    # joindre PDF invitation si disponible
    invitation_file = getattr(ins, "invitation_file", None)

    if invitation_file:
        try:
            with invitation_file.open("rb") as f:
                msg.attach(f"invitation_{ins.id}.pdf", f.read(), "application/pdf")
        except Exception:
            pass

    msg.send(fail_silently=False)
    return {"ok": True}
