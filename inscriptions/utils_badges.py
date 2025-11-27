import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings

def generate_badge(inscription):

    # ------------ BACKGROUND ------------
    role = (inscription.type_profil or "").strip().upper()

    backgrounds = {
        "PRESSE": "Presse.png",
        "PRESS": "Presse.png",
        "FESTIVALIERS": "Festivaliers.png",
        "FESTIVALIER": "Festivaliers.png",
        "ARTISTES PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNELS": "Artistes.png",
        "ARTISTE PROFESSIONNEL": "Artistes.png",
    }

    filename = backgrounds.get(role, "Festivaliers.png")
    background_path = os.path.join(settings.BASE_DIR, "static", "badges", filename)
    base = Image.open(background_path).convert("RGBA")

    # ------------ QR CODE (170 px exacts) ------------
    qr_data = f"ECOFEST2025-{inscription.id}-{inscription.email}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((170, 170))  # <== EXACT comme ton exemple parfait
    base.paste(qr, (80, 80))    # position calibrée

    # ------------ TEXTES ------------
    draw = ImageDraw.Draw(base)

    # Police — Arial remplaçable par ta police custom si besoin
    font_bold = ImageFont.truetype("arial.ttf", 70)
    font_normal = ImageFont.truetype("arial.ttf", 55)

    # Nom + Prénom (en gras)
    name_text = f"{inscription.prenom} {inscription.nom}"

    # Nationalité + provenance (normal)
    nat_text = inscription.nationalite or ""
    prov_text = inscription.provenance or ""

    # Positions calibrées pour éviter les débordements
    NAME_Y = 600
    NAT_Y = 700
    PROV_Y = 780

    # NOM PRÉNOM — GROS, EN GRAS
    draw.text((750, NAME_Y), name_text, fill="black", font=font_bold)

    # NATIONALITÉ — NORMAL
    draw.text((750, NAT_Y), nat_text, fill="black", font=font_normal)

    # PROVENANCE — NORMAL
    draw.text((750, PROV_Y), prov_text, fill="black", font=font_normal)

    # ------------ SAVE ------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path
