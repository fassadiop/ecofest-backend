import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


def generate_badge(inscription):
    role = (inscription.type_profil or "").strip().upper()

    backgrounds = {
        "PRESSE": "Presse.png",
        "FESTIVALIERS": "Festivaliers.png",
        "ARTISTES PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNEL": "Artistes.png",
    }

    filename = backgrounds.get(role, "Festivaliers.png")

    background_path = os.path.join(settings.BASE_DIR, "static", "badges", filename)
    base = Image.open(background_path).convert("RGBA")

    # QR code
    qr_data = f"ECOFEST2025-{inscription.id}-{inscription.email}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((600, 600))
    base.paste(qr, (80, 80))

    draw = ImageDraw.Draw(base)

    # --- 🔥 FIX POLICE POUR RENDER ---
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans-Bold.ttf")
    font_big = ImageFont.truetype(font_path, 90)
    font_medium = ImageFont.truetype(font_path, 70)

    # Textes
    full_name = f"{inscription.prenom} {inscription.nom}"
    draw.text((750, 620), full_name, fill="black", font=font_big)
    draw.text((750, 750), inscription.nationalite, fill="black", font=font_medium)
    draw.text((750, 850), inscription.provenance, fill="black", font=font_medium)

    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path


