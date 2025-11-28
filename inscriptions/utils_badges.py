import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


# ---------------------------------------------------------
#  FONCTION DÉCOUPAGE : max 17 caractères, sans couper les mots
# ---------------------------------------------------------
def split_name_by_width(prenom, nom, font, max_width_px):
    """
    Découpe automatiquement le nom pour ne jamais dépasser max_width_px.
    Retourne 1 ou 2 lignes max.
    """

    full = (prenom or "").strip() + " " + (nom or "").strip()
    words = full.split()

    line1 = ""
    line2 = ""

    # Remplir ligne 1
    for w in words:
        test = (line1 + " " + w).strip()
        if font.getlength(test) <= max_width_px:
            line1 = test
        else:
            # Ce mot doit aller sur la ligne 2
            if not line2:
                line2 = w
            else:
                test2 = (line2 + " " + w).strip()
                if font.getlength(test2) <= max_width_px:
                    line2 = test2
                else:
                    # Trop long — on tronque
                    break

    return [line1, line2] if line2 else [line1]

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

    font_bold = ImageFont.truetype(font_path_bold, 55)
    font_normal = ImageFont.truetype(font_path, 45)

    draw = ImageDraw.Draw(base)

    # ------------ TEXTES ------------
    prenom = inscription.prenom or ""
    nom = inscription.nom or ""

    # max largeur autorisée = largeur dispo sur ton badge
    MAX_NAME_WIDTH = 300  # ajuste si nécessaire !
    name_lines = split_name_by_width(prenom, nom, font_bold, MAX_NAME_WIDTH)

    nat_text = inscription.nationalite or ""
    prov_text = inscription.provenance or ""

    # positions de base (ajuste si besoin)
    NAME_Y = 600
    LINE_SPACING = 60
    NAT_Y = 700
    PROV_Y = 780
    TEXT_X = 400  # alignement horizontal (gauche du bloc texte)

    # --------- NOM : 1 ou 2 lignes ---------
    # Ligne 1 (toujours présente)
    draw.text((TEXT_X, NAME_Y), name_lines[0], fill="black", font=font_bold)

    # Ligne 2 pour le nom si besoin
    extra_offset = 0
    if len(name_lines) > 1:
        draw.text(
            (TEXT_X, NAME_Y + LINE_SPACING),
            name_lines[1],
            fill="black",
            font=font_bold,
        )
        extra_offset = LINE_SPACING  # on décale les autres infos vers le bas

    # --------- NATIONALITÉ ---------
    if nat_text:
        draw.text(
            (TEXT_X, NAT_Y + extra_offset),
            nat_text,
            fill="black",
            font=font_normal,
        )

    # --------- PROVENANCE ---------
    if prov_text:
        draw.text(
            (TEXT_X, PROV_Y + extra_offset),
            prov_text,
            fill="black",
            font=font_normal,
        )

    # ------------ SAVE ------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path
