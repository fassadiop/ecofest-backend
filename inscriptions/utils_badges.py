import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


def generate_badge(inscription):
    """
    Génère un badge pour une inscription ECOFEST.
    Paramètre : inscription (pas participant)
    """

    # Récupération du rôle
    role = (inscription.type_profil or "").strip().upper()

    backgrounds = {
        "PRESSE": "Presse.png",
        "FESTIVALIERS": "Festivaliers.png",
        "ARTISTES PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNEL": "Artistes.png",
        "ARTISTE PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNELLE": "Artistes.png",
    }

    filename = backgrounds.get(role, "Festivaliers.png")

    # Chemin vers /static/badges/*
    background_path = os.path.join(settings.BASE_DIR, "static", "badges", filename)
    base = Image.open(background_path).convert("RGBA")

    # ---------------------------------------------------------
    # QR CODE
    # ---------------------------------------------------------
    qr_data = f"ECOFEST2025-{inscription.id}-{inscription.email}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((600, 600))
    base.paste(qr, (80, 80))

    # ---------------------------------------------------------
    # TEXTES
    # ---------------------------------------------------------
    draw = ImageDraw.Draw(base)

    try:
        font_big = ImageFont.truetype("arial.ttf", 90)
        font_medium = ImageFont.truetype("arial.ttf", 70)
    except:
        font_big = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    full_name = f"{inscription.prenom} {inscription.nom}"
    nationalite = inscription.nationalite or ""
    provenance = inscription.provenance or ""

    draw.text((750, 620), full_name, fill="black", font=font_big)
    draw.text((750, 750), nationalite, fill="black", font=font_medium)
    draw.text((750, 850), provenance, fill="black", font=font_medium)

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path
