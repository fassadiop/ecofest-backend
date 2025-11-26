import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from weasyprint import HTML  # si tu utilises WeasyPrint


# def generate_badge_png_for_inscription(inscription):
#     """
#     Génère un PNG simple pour badge et renvoie le chemin relatif stocké.
#     NOTE: en production, personnaliser design, fonts, tailles.
#     """
#     # chemin local pour démonstration
#     out_dir = os.path.join(settings.MEDIA_ROOT, 'badges')
#     os.makedirs(out_dir, exist_ok=True)
#     filename = f"badge_{inscription.id}.png"
#     fullpath = os.path.join(out_dir, filename)

#     # Créer image basique
#     img = Image.new('RGB', (800, 1200), color=(255,255,255))
#     draw = ImageDraw.Draw(img)

#     # Texte (tu peux charger une font)
#     draw.text((40,40), f"{inscription.nom} {inscription.prenom}", fill=(0,0,0))
#     draw.text((40,100), f"Profil: {inscription.type_profil}", fill=(0,0,0))
#     draw.text((40,160), f"Nationalité: {inscription.nationalite or ''}", fill=(0,0,0))
#     draw.text((40,220), f"Provenance: {inscription.provenance or ''}", fill=(0,0,0))

#     # Generate QR
#     token = f"{inscription.id}-{os.urandom(6).hex()}"
#     qr = qrcode.make(token)
#     qr = qr.resize((300,300))
#     img.paste(qr, (40,300))

#     # Save
#     img.save(fullpath, format='PNG')

#     # Create or update Badge model
#     from .models import Badge
#     badge, _ = Badge.objects.get_or_create(inscription=inscription)
#     badge.png_path = f"badges/{filename}"
#     badge.token = token
#     badge.save()

#     return f"badges/{filename}"


def generate_invitation_pdf_for_inscription(inscription):
    """
    Génère une lettre d'invitation PDF basique et renvoie chemin relatif.
    Utilise un template HTML + WeasyPrint pour la conversion.
    """
    out_dir = os.path.join(settings.MEDIA_ROOT, 'invitations')
    os.makedirs(out_dir, exist_ok=True)
    filename = f"invitation_{inscription.id}.pdf"
    fullpath = os.path.join(out_dir, filename)

    context = {
        "inscription": inscription,
        "evenement": inscription.evenement,
    }
    html_string = render_to_string('invitations/invitation_template.html', context)
    HTML(string=html_string).write_pdf(fullpath)

    return f"invitations/{filename}"
