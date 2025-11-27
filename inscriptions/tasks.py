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
    inscription = Inscription.objects.select_related("participant").get(id=inscription_id)

    # 1) Générer badge (basé sur inscription)
    badge_path = generate_badge(inscription)

    # 2) Générer lettre PDF
    letter_path = generate_invitation_letter_pdf(inscription)

    # 3) Envoi email
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    with open(badge_path, "rb") as f:
        badge_data = base64.b64encode(f.read()).decode()

    with open(letter_path, "rb") as f:
        letter_data = base64.b64encode(f.read()).decode()

    # ---------------------------
    # EMAIL — avec REPLY-TO
    # ---------------------------
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,  # inscription@ecofest.app
        to_emails=inscription.email,
        subject="ECOFEST 2025 — Votre accréditation est confirmée !",
        plain_text_content=(
            f"Bonjour {inscription.prenom},\n\n"
            "Veuillez trouver ci-joint votre badge et votre lettre d'invitation."
        )
    )

    # ICI : on ajoute Reply-To
    message.reply_to = settings.DEFAULT_FROM_EMAIL
    # ou explicitement :
    # message.reply_to = "inscription@ecofest.app"

    # ---------------------------
    # ATTACHMENTS
    # ---------------------------
    message.add_attachment(
        Attachment(
            FileContent(badge_data),
            FileName(f"badge_{inscription.id}.png"),
            FileType("image/png"),
            Disposition("attachment")
        )
    )

    message.add_attachment(
        Attachment(
            FileContent(letter_data),
            FileName(f"invitation_{inscription.id}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
    )

    # Envoi SendGrid
    sg.send(message)


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
