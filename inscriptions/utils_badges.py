import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


# ---------------------------------------------------------
#  FONCTION DÉCOUPAGE PAR LARGEUR EN PIXELS
# ---------------------------------------------------------
def split_name_by_pixels(prenom, nom, font, draw, max_width_px):
    """
    Coupe le texte prénom + nom en 1 ou 2 lignes SANS dépasser max_width_px.
    Utilise la largeur réelle en pixels → 100% fiable.
    """
    full = (prenom or "").strip() + " " + (nom or "").strip()
    words = full.split()

    line1 = ""
    line2 = ""

    for w in words:
        test = (line1 + " " + w).strip()

        # Mesurer la largeur réelle
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width_px:
            line1 = test
        else:
            # Le mot ne rentre pas → ligne 2
            line2 = " ".join(words[words.index(w):])
            break

    return [line1] if not line2 else [line1, line2]



# ---------------------------------------------------------
#                  GÉNÉRATION DU BADGE
# ---------------------------------------------------------
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

    # ------------ QR CODE 170px ------------
    qr_data = f"ECOFEST2025-{inscription.id}-{inscription.email}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((170, 170))
    base.paste(qr, (80, 80))

    # ------------ FONTS ------------
    font_path_bold = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans.ttf")

    font_bold = ImageFont.truetype(font_path_bold, 30)
    font_normal = ImageFont.truetype(font_path, 20)

    draw = ImageDraw.Draw(base)

    # ------------ NOM : Découpage intelligent par pixels ------------
    MAX_NAME_WIDTH = 850  # largeur utile pour le texte nom/prénom

    name_lines = split_name_by_pixels(
        inscription.prenom,
        inscription.nom,
        font_bold,
        draw,
        MAX_NAME_WIDTH
    )

    # ------------ TEXTES ANNEXES ------------
    nat_text = inscription.nationalite or ""
    prov_text = inscription.provenance or ""

    TEXT_X = 400
    NAME_Y = 600
    LINE_SPACING = 60
    NAT_Y = 700
    PROV_Y = 780

    # --- Affichage du nom en 1 ou 2 lignes ---
    draw.text((TEXT_X, NAME_Y), name_lines[0], fill="black", font=font_bold)

    extra_offset = 0
    if len(name_lines) > 1:
        draw.text(
            (TEXT_X, NAME_Y + LINE_SPACING),
            name_lines[1],
            fill="black",
            font=font_bold
        )
        extra_offset = LINE_SPACING

    # --- NATIONALITÉ ---
    if nat_text:
        draw.text(
            (TEXT_X, NAT_Y + extra_offset),
            nat_text,
            fill="black",
            font=font_normal
        )

    # --- PROVENANCE ---
    if prov_text:
        draw.text(
            (TEXT_X, PROV_Y + extra_offset),
            prov_text,
            fill="black",
            font=font_normal
        )

    # ------------ SAVE ------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path
