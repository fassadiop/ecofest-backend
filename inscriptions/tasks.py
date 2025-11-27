# inscriptions/tasks.py

import base64
import os
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)

from .models import Inscription
from .utils_badges import generate_badge
from .utils_letters import generate_invitation_letter_pdf


# ---------------------------------------------------------
# 1) PACKAGE ACCRÉDITATION (badge + lettre + email)
# ---------------------------------------------------------
def send_invitation_package(inscription_id):
    inscription = Inscription.objects.get(id=inscription_id)

    # Génération des fichiers
    badge_path = generate_badge(inscription)
    letter_path = generate_invitation_letter_pdf(inscription)

    # Lecture en base64
    with open(badge_path, "rb") as f:
        badge_data = base64.b64encode(f.read()).decode()

    with open(letter_path, "rb") as f:
        letter_data = base64.b64encode(f.read()).decode()

    # IMPORTANT : from_email doit être strictement une adresse valide
    from_email = settings.DEFAULT_FROM_EMAIL.strip()

    # Construction du JSON SendGrid API v3
    data = {
        "personalizations": [{
            "to": [{"email": inscription.email}],
            "subject": "ECOFEST 2025 — Votre accréditation"
        }],
        "from": {"email": from_email},
        "content": [{
            "type": "text/plain",
            "value": f"Bonjour {inscription.prenom},\n\nVeuillez trouver votre badge et votre lettre d’accréditation."
        }],
        "attachments": [
            {
                "content": badge_data,
                "type": "image/png",
                "filename": f"badge_{inscription.id}.png",
                "disposition": "attachment"
            },
            {
                "content": letter_data,
                "type": "application/pdf",
                "filename": f"inviation_{inscription.id}.pdf",
                "disposition": "attachment"
            }
        ]
    }

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.client.mail.send.post(request_body=data)

    return response.status_code



# ---------------------------------------------------------
# 2) EMAIL CONFIRMATION INITIAL (sans pièce jointe)
# ---------------------------------------------------------
def send_confirmation_email(inscription_id):
    """
    Envoie un email HTML+TXT en confirmation d'inscription.
    Version SYNCHRONE (pas de Celery).
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

    # Templates email
    subject = "Réception de votre inscription – ECOFEST"
    text_body = render_to_string("emails/confirmation_full.txt", ctx)
    html_body = render_to_string("emails/confirmation_full.html", ctx)

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [ins.email]
    )
    msg.attach_alternative(html_body, "text/html")

    # Jointure PDF éventuelle
    invitation_file = getattr(ins, "invitation_file", None)

    if invitation_file:
        try:
            with invitation_file.open("rb") as f:
                msg.attach(
                    f"invitation_{ins.id}.pdf",
                    f.read(),
                    "application/pdf"
                )
        except Exception:
            pass

    msg.send(fail_silently=False)

    return {"ok": True}
