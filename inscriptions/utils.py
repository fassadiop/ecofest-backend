import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from weasyprint import HTML  # si tu utilises WeasyPrint


def generate_invitation_letter_pdf(participant):

    html = render_to_string("letters/invitation.html", {
        "participant": participant
    })

    output_dir = os.path.join(settings.MEDIA_ROOT, "letters")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"invitation_{participant.id}.pdf")

    HTML(string=html).write_pdf(output_path)

    return output_path

def generate_badge(participant):
    """
    Génère un badge PNG A6 (300 DPI) avec :
    - Image de fond selon rôle
    - Nom / Prénom / Nationalité / Provenance
    - QR code unique
    """

    # ---------------------------------------------------------
    # 1) Sélection du fond selon le rôle
    # ---------------------------------------------------------
    role = (participant.profil or "").strip().upper()

    backgrounds = {
        "PRESSE": "Presse.png",
        "FESTIVALIERS": "Festivaliers.png",
        "FESTIVALIERS": "Festivaliers.png",
        "FESTIVALIERS ": "Festivaliers.png",
        "ARTISTE PROFESSIONNELS": "Artistes.png",
        "ARTISTES PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNEL": "Artistes.png"
    }

    filename = backgrounds.get(role, "Festivaliers.png")  # fallback

    background_path = os.path.join(settings.BASE_DIR, "static", "badges", filename)
    base = Image.open(background_path).convert("RGBA")

    # ---------------------------------------------------------
    # 2) Fabriquer le QR code
    # ---------------------------------------------------------
    qr_data = f"ECOFEST2025-{participant.id}-{participant.email}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((600, 600))  # Taille QR en pixels

    # Position du QR sur le badge
    base.paste(qr, (80, 80))

    # ---------------------------------------------------------
    # 3) Ajouter les textes
    # ---------------------------------------------------------
    draw = ImageDraw.Draw(base)

    # Polices (tu peux ajouter ta propre police si besoin)
    font_big = ImageFont.truetype("arial.ttf", 90)
    font_medium = ImageFont.truetype("arial.ttf", 70)

    # Textes à afficher
    prenom_nom = f"{participant.prenom} {participant.nom}"
    nationalite = f"{participant.nationalite}"
    provenance = f"{participant.provenance}"

    # Emplacements (optimisés à partir du modèle)
    draw.text((750, 620), prenom_nom, fill="black", font=font_big)
    draw.text((750, 750), nationalite, fill="black", font=font_medium)
    draw.text((750, 850), provenance, fill="black", font=font_medium)

    # ---------------------------------------------------------
    # 4) Sauvegarde
    # ---------------------------------------------------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{participant.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path


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
