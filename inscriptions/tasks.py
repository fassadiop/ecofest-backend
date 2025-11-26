# inscriptions/tasks.py
from celery import shared_task
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import Inscription, Participant
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import os
from .utils_badges import generate_badge
from .utils_letters import generate_invitation_letter_pdf


@shared_task
def send_invitation_package(participant_id):
    participant = Participant.objects.get(id=participant_id)

    # 1) Générer badge PNG
    badge_path = generate_badge(participant)

    # 2) Générer lettre PDF
    letter_path = generate_invitation_letter_pdf(participant)

    # 3) Préparer email
    subject = "ECOFEST 2025 — Votre accréditation est confirmée !"
    body = f"""
Cher/Chère {participant.prenom},

Votre accréditation ECOFEST est confirmée !
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

    # 4) Envoyer
    email.send(fail_silently=False)


@shared_task
def send_confirmation_email(inscription_id):
    try:
        ins = Inscription.objects.select_related('participant').get(pk=inscription_id)
    except Inscription.DoesNotExist:
        return {"ok": False, "reason": "missing"}
    ctx = {
      "inscription": ins,
      "participant": None, 
      "event": getattr(ins, "evenement", None),
      "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:3000")
    }
    subject = f"Réception de votre inscription – ECOFEST"
    text_body = render_to_string("emails/confirmation_full.txt", ctx)
    html_body = render_to_string("emails/confirmation_full.html", ctx)
    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [ins.email])
    msg.attach_alternative(html_body, "text/html")
    # attach PDF if exists (ins.invitation_file)
    if getattr(ins, "invitation_file", None):
        try:
            with ins.invitation_file.open("rb") as f:
                msg.attach(f"invitation_{ins.id}.pdf", f.read(), "application/pdf")
        except Exception:
            pass
    msg.send(fail_silently=False)
    return {"ok": True}


def send_confirmation_with_sendgrid(inscription, pdf_path=None):
    subject = f"Réception de votre inscription — ECOFEST"
    context = {"inscription": inscription, "site_url": settings.SITE_URL}
    html_body = render_to_string("emails/confirmation_full.html", context)
    text_body = render_to_string("emails/confirmation_full.txt", context)

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=inscription.email,
        subject=subject,
        plain_text_content=text_body,
        html_content=html_body
    )

    # attach PDF if exists
    if pdf_path:
        with open(pdf_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        attachedFile = Attachment(
            FileContent(data),
            FileName(f"invitation_{inscription.id}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
        message.attachment = attachedFile

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    return response.status_code, response.body


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_confirmation_email(self, inscription_id):
    """
    Envoie un email HTML+TXT via SendGrid pour une inscription.
    Exécuter en tâche Celery.
    """
    try:
        ins = Inscription.objects.select_related('participant').get(pk=inscription_id)
    except Inscription.DoesNotExist:
        return {"ok": False, "reason": "inscription_not_found"}

    # Contexte pour templates
    context = {
        "inscription": ins,
        "participant": getattr(ins, "participant", None),
        "event": getattr(ins, "evenement", None),
        "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:3000"),
    }

    subject = f"Réception de votre inscription — ECOFEST"
    plain_text = render_to_string("emails/confirmation_full.txt", context)
    html_content = render_to_string("emails/confirmation_full.html", context)

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=ins.email,
        subject=subject,
        plain_text_content=plain_text,
        html_content=html_content
    )

    # Jointure PDF si présent (champ FileField ou chemin)
    try:
        # Si vous utilisez FileField (recommended): ins.invitation_file
        invitation_file = getattr(ins, "invitation_file", None)
        if invitation_file:
            # invitation_file peut être un FileField
            with invitation_file.open("rb") as f:
                data = base64.b64encode(f.read()).decode()
            attachment = Attachment(
                FileContent(data),
                FileName(f"invitation_{ins.id}.pdf"),
                FileType("application/pdf"),
                Disposition("attachment")
            )
            message.attachment = attachment
        else:
            # fallback: chemin stocké en string (invitation_pdf_path)
            path = getattr(ins, "invitation_pdf_path", None)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                attachment = Attachment(
                    FileContent(data),
                    FileName(f"invitation_{ins.id}.pdf"),
                    FileType("application/pdf"),
                    Disposition("attachment")
                )
                message.attachment = attachment
    except Exception as e:
        # on continue l'envoi même si l'attach échoue
        # log l'erreur dans les logs (ici we just print)
        print("Attachment error:", e)

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        resp = sg.send(message)
        return {"ok": True, "status_code": resp.status_code}
    except Exception as exc:
        # retry en cas d'erreur transitoire
        try:
            self.retry(exc=exc)
        except Exception:
            # si retry échoue, log et renvoyer erreur
            print("SendGrid send error:", exc)
            return {"ok": False, "reason": str(exc)}