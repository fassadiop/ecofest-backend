# # inscriptions/tasks.py

# import base64
# import os
# from django.core.mail import EmailMultiAlternatives, EmailMessage
# from django.template.loader import render_to_string
# from django.conf import settings

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import (
#     Mail, Attachment, FileContent, FileName, FileType, Disposition
# )

# from .models import Inscription
# from .utils_badges import generate_badge
# from .utils_letters import generate_invitation_letter_pdf


# # ---------------------------------------------------------
# # 1) PACKAGE ACCRÉDITATION (badge + lettre + email)
# # ---------------------------------------------------------
# def send_invitation_package(inscription_id):
#     inscription = Inscription.objects.select_related("participant").get(id=inscription_id)

#     # 1) Générer badge (basé sur inscription)
#     badge_path = generate_badge(inscription)

#     # 2) Générer lettre PDF
#     letter_path = generate_invitation_letter_pdf(inscription)

#     # 3) Envoi email
#     sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

#     with open(badge_path, "rb") as f:
#         badge_data = base64.b64encode(f.read()).decode()

#     with open(letter_path, "rb") as f:
#         letter_data = base64.b64encode(f.read()).decode()

#     # ---------------------------
#     # EMAIL — avec REPLY-TO
#     # ---------------------------
#     message = Mail(
#         from_email=settings.DEFAULT_FROM_EMAIL,  # inscription@ecofest.app
#         to_emails=inscription.email,
#         subject="ECOFEST 2025 — Votre accréditation est confirmée !",
#         plain_text_content=(
#             f"Bonjour {inscription.prenom},\n\n"
#             "Veuillez trouver ci-joint votre badge et votre lettre d'invitation."
#         )
#     )

#     # ICI : on ajoute Reply-To
#     message.reply_to = settings.DEFAULT_FROM_EMAIL
#     # ou explicitement :
#     # message.reply_to = "inscription@ecofest.app"

#     # ---------------------------
#     # ATTACHMENTS
#     # ---------------------------
#     message.add_attachment(
#         Attachment(
#             FileContent(badge_data),
#             FileName(f"badge_{inscription.id}.png"),
#             FileType("image/png"),
#             Disposition("attachment")
#         )
#     )

#     message.add_attachment(
#         Attachment(
#             FileContent(letter_data),
#             FileName(f"invitation_{inscription.id}.pdf"),
#             FileType("application/pdf"),
#             Disposition("attachment")
#         )
#     )

#     # Envoi SendGrid
#     sg.send(message)


# # ---------------------------------------------------------
# # 2) EMAIL CONFIRMATION INITIAL (sans pièce jointe)
# # ---------------------------------------------------------
# def send_confirmation_email(inscription_id):

#     try:
#         ins = Inscription.objects.select_related('participant').get(pk=inscription_id)
#     except Inscription.DoesNotExist:
#         return {"ok": False, "reason": "missing"}

#     ctx = {
#         "inscription": ins,
#         "participant": getattr(ins, "participant", None),
#         "event": getattr(ins, "evenement", None),
#         "site_url": getattr(settings, "SITE_URL", "https://ecofest.app"),
#     }

#     # Templates email
#     subject = "Réception de votre inscription – ECOFEST"
#     text_body = render_to_string("emails/confirmation_full.txt", ctx)
#     html_body = render_to_string("emails/confirmation_full.html", ctx)

#     msg = EmailMultiAlternatives(
#         subject,
#         text_body,
#         settings.DEFAULT_FROM_EMAIL,
#         [ins.email]
#     )
#     msg.attach_alternative(html_body, "text/html")

#     # Jointure PDF éventuelle
#     invitation_file = getattr(ins, "invitation_file", None)

#     if invitation_file:
#         try:
#             with invitation_file.open("rb") as f:
#                 msg.attach(
#                     f"invitation_{ins.id}.pdf",
#                     f.read(),
#                     "application/pdf"
#                 )
#         except Exception:
#             pass

#     msg.send(fail_silently=False)

#     return {"ok": True}

# inscriptions/tasks.py
import base64
import logging
import os

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_via_sendgrid(to_email, subject, plain_text, html_body, attachments=None, reply_to=None):
    """
    Try to send email via SendGrid if available.
    attachments: list of tuples (filename, bytes, mime_type)
    Returns True on success, False otherwise.
    """
    try:
        # Lazy import SendGrid
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    except Exception as exc:
        logger.info("SendGrid client not available: %s", exc)
        return False

    api_key = getattr(settings, "SENDGRID_API_KEY", None) or os.environ.get("SENDGRID_API_KEY") or os.environ.get("SENDGRID_KEY")
    if not api_key:
        logger.info("SendGrid API key not configured, skipping SendGrid send.")
        return False

    try:
        message = Mail(
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            to_emails=to_email,
            subject=subject,
            plain_text_content=plain_text,
            html_content=html_body
        )
        if reply_to:
            try:
                # SendGrid expects an email object for reply_to in some versions, but setting attr works too
                message.reply_to = reply_to
            except Exception:
                pass

        # Attach files if provided
        if attachments:
            for filename, content_bytes, mime_type in attachments:
                try:
                    encoded = base64.b64encode(content_bytes).decode()
                    attachment = Attachment(
                        FileContent(encoded),
                        FileName(filename),
                        FileType(mime_type),
                        Disposition("attachment")
                    )
                    message.add_attachment(attachment)
                except Exception:
                    logger.exception("Failed to add attachment %s for SendGrid", filename)

        client = SendGridAPIClient(api_key)
        resp = client.send(message)
        logger.info("SendGrid send result: status=%s", getattr(resp, "status_code", None))
        return True
    except Exception as exc:
        logger.exception("SendGrid send failed: %s", exc)
        return False


def _send_via_django_backend(to_email, subject, plain_text, html_body, attachments=None, reply_to=None):
    """
    Send using Django's configured email backend (SMTP or other). attachments list: (filename, bytes, mime_type)
    Returns True on success, False otherwise.
    """
    try:
        msg = EmailMultiAlternatives(
            subject,
            plain_text,
            getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            [to_email]
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        if attachments:
            for filename, content_bytes, mime_type in attachments:
                try:
                    msg.attach(filename, content_bytes, mime_type)
                except Exception:
                    logger.exception("Failed to attach %s to django email", filename)
        if reply_to:
            try:
                msg.extra_headers = msg.extra_headers or {}
                # Some email backends respect 'Reply-To' header
                msg.extra_headers["Reply-To"] = reply_to
            except Exception:
                pass

        msg.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.exception("Django email backend send failed: %s", exc)
        return False


def send_invitation_package(inscription_id):
    """
    Generate badge + letter + email package for an inscription.
    Safe: lazy imports and fallbacks are used so this function does not raise at module import.
    """
    try:
        # lazy model import
        from .models import Inscription
        inscription = Inscription.objects.select_related("participant").get(id=inscription_id)
    except Exception as exc:
        logger.exception("Failed to load inscription %s: %s", inscription_id, exc)
        return {"ok": False, "reason": "missing"}

    # Lazy import helpers that may rely on heavy libs
    try:
        from .utils_badges import generate_badge
    except Exception as exc:
        logger.warning("Badge generator not available: %s", exc)
        generate_badge = None

    try:
        # import PDF generator lazily
        from .utils_letters import generate_invitation_letter_pdf
    except Exception as exc:
        logger.warning("Invitation letter generator not available: %s", exc)
        generate_invitation_letter_pdf = None

    # 1) Generate badge (if possible)
    badge_path = None
    if generate_badge:
        try:
            badge_path = generate_badge(inscription)
        except Exception as exc:
            logger.exception("Badge generation failed for inscription %s: %s", inscription_id, exc)
            badge_path = None

    # 2) Generate letter PDF (if possible)
    letter_path = None
    if generate_invitation_letter_pdf:
        try:
            # attempt to save to MEDIA_ROOT/letters as before
            letter_path = generate_invitation_letter_pdf(inscription)
        except Exception as exc:
            logger.exception("Invitation PDF generation failed for inscription %s: %s", inscription_id, exc)
            letter_path = None

    # Prepare attachments list (filename, bytes, mime_type)
    attachments = []
    if badge_path:
        try:
            with open(badge_path, "rb") as f:
                attachments.append((os.path.basename(badge_path), f.read(), "image/png"))
        except Exception:
            logger.exception("Failed to read badge file %s", badge_path)

    if letter_path:
        try:
            # letter_path may be bytes or a filepath
            if isinstance(letter_path, (bytes, bytearray)):
                attachments.append((f"invitation_{inscription.id}.pdf", letter_path, "application/pdf"))
            else:
                with open(letter_path, "rb") as f:
                    attachments.append((os.path.basename(letter_path), f.read(), "application/pdf"))
        except Exception:
            logger.exception("Failed to read letter file %s", letter_path)

    # 3) Try to send via SendGrid first (if available), else Django backend
    subject = "ECOFEST 2025 — Votre accréditation est confirmée !"
    plain_text = (
        f"Bonjour {inscription.prenom},\n\n"
        "Veuillez trouver ci-joint votre badge et votre lettre d'invitation."
    )
    html_body = render_to_string("emails/confirmation_full.html", {"inscription": inscription})

    reply_to = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    sent = False
    try:
        sent = _send_via_sendgrid(inscription.email, subject, plain_text, html_body, attachments=attachments, reply_to=reply_to)
    except Exception:
        sent = False

    if not sent:
        # Fallback to Django email backend
        try:
            sent = _send_via_django_backend(inscription.email, subject, plain_text, html_body, attachments=attachments, reply_to=reply_to)
        except Exception:
            sent = False

    if not sent:
        logger.warning("Failed to send invitation package for inscription %s (both SendGrid and Django backend failed or unavailable).", inscription_id)
        return {"ok": False, "reason": "send_failed"}

    logger.info("Invitation package sent for inscription %s", inscription_id)
    return {"ok": True}


def send_confirmation_email(inscription_id):
    """
    Send confirmation email for an inscription without necessarily attachments.
    Safe: lazy imports and fallbacks are used.
    """
    try:
        from .models import Inscription
        ins = Inscription.objects.select_related("participant").get(pk=inscription_id)
    except Exception as exc:
        logger.exception("Inscription not found: %s", exc)
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

    # If invitation_file present, attach its bytes
    attachments = []
    invitation_file = getattr(ins, "invitation_file", None)
    if invitation_file:
        try:
            with invitation_file.open("rb") as f:
                attachments.append((f"invitation_{ins.id}.pdf", f.read(), "application/pdf"))
        except Exception:
            logger.exception("Failed to read invitation_file for inscription %s", inscription_id)

    reply_to = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    # Try SendGrid first
    sent = False
    try:
        sent = _send_via_sendgrid(ins.email, subject, text_body, html_body, attachments=attachments, reply_to=reply_to)
    except Exception:
        sent = False

    if not sent:
        try:
            sent = _send_via_django_backend(ins.email, subject, text_body, html_body, attachments=attachments, reply_to=reply_to)
        except Exception:
            sent = False

    if not sent:
        logger.warning("Failed to send confirmation email for inscription %s", inscription_id)
        return {"ok": False, "reason": "send_failed"}

    return {"ok": True}
