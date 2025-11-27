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
    """
    Génère:
    - badge PNG
    - lettre d'invitation PDF
    - envoie un email via SendGrid avec les deux pièces jointes
    """
    try:
        inscription = Inscription.objects.select_related("participant").get(id=inscription_id)
    except Inscription.DoesNotExist:
        return {"ok": False, "reason": "inscription_not_found"}

    participant = inscription.participant

    # 1) Générer badge
    badge_path = generate_badge(inscription)

    # 2) Générer lettre PDF
    letter_path = generate_invitation_letter_pdf(inscription)

    # 3) Charger les fichiers en base64
    with open(badge_path, "rb") as f:
        badge_data = base64.b64encode(f.read()).decode()

    with open(letter_path, "rb") as f:
        letter_data = base64.b64encode(f.read()).decode()

    # 4) Préparer email
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=inscription.email,
        subject="ECOFEST 2025 — Votre accréditation est confirmée !",
        plain_text_content=(
            f"Bonjour {inscription.prenom},\n\n"
            f"Veuillez trouver votre badge et votre lettre d'invitation en pièces jointes.\n\n"
            "Cordialement,\nL'équipe ECOFEST 2025."
        ),
    )

    # Ajouter badge
    message.add_attachment(
        Attachment(
            FileContent(badge_data),
            FileName(f"badge_{participant.id}.png"),
            FileType("image/png"),
            Disposition("attachment"),
        )
    )

    # Ajouter la lettre PDF
    message.add_attachment(
        Attachment(
            FileContent(letter_data),
            FileName(f"invitation_{participant.id}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
    )

    # 5) Envoyer via SendGrid
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
        return {"ok": True}
    except Exception as e:
        print("SendGrid error:", e)
        return {"ok": False, "reason": str(e)}



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
