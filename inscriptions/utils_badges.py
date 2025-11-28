# import qrcode
# from PIL import Image, ImageDraw, ImageFont
# import os
# from django.conf import settings

# def generate_badge(inscription):

#     # ------------ BACKGROUND ------------
#     role = (inscription.type_profil or "").strip().upper()

#     backgrounds = {
#         "PRESSE": "Presse.png",
#         "PRESS": "Presse.png",
#         "FESTIVALIERS": "Festivaliers.png",
#         "FESTIVALIER": "Festivaliers.png",
#         "ARTISTES PROFESSIONNELS": "Artistes.png",
#         "ARTISTE PROFESSIONNELS": "Artistes.png",
#         "ARTISTE PROFESSIONNEL": "Artistes.png",
#     }

#     filename = backgrounds.get(role, "Festivaliers.png")
#     background_path = os.path.join(settings.BASE_DIR, "static", "badges", filename)
#     base = Image.open(background_path).convert("RGBA")

#     # ------------ QR CODE 170px ------------
#     qr_data = f"ECOFEST2025-{inscription.id}-{inscription.email}"
#     qr = qrcode.make(qr_data)
#     qr = qr.resize((170, 170))
#     base.paste(qr, (80, 80))

#     # ------------ FONTS ------------
#     font_path_bold = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")
#     font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans.ttf")

#     font_bold = ImageFont.truetype(font_path_bold, 55)
#     font_normal = ImageFont.truetype(font_path, 45)

#     draw = ImageDraw.Draw(base)

#     # ------------ TEXTES ------------
#     name_text = f"{inscription.prenom} {inscription.nom}"
#     nat_text = inscription.nationalite or ""
#     prov_text = inscription.provenance or ""
    
#     NAME_Y = 600
#     NAT_Y = 700
#     PROV_Y = 780

#     draw.text((400, NAME_Y), name_text, fill="black", font=font_bold)
#     draw.text((400, NAT_Y), nat_text, fill="black", font=font_normal)
#     draw.text((400, PROV_Y), prov_text, fill="black", font=font_normal)

#     # ------------ SAVE ------------
#     output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
#     os.makedirs(output_dir, exist_ok=True)

#     output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
#     base.save(output_path, dpi=(300, 300))

#     return output_path

import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


# ---------------------------------------------------------
#  FONCTION DÉCOUPAGE : max 17 caractères, sans couper les mots
# ---------------------------------------------------------
def split_name_safely(prenom, nom, max_len=17):
    """
    Découpe (prenom + nom) en 1 ou 2 lignes max, sans couper les mots.
    - Chaque ligne ≤ max_len caractères
    - On remplit la ligne 1 autant que possible
    - Le reste va sur la ligne 2
    """

    full = (prenom or "").strip() + " " + (nom or "").strip()
    full = full.strip()
    if not full:
        return [""]

    words = full.split()
    lines = []
    current = ""

    for word in words:
        if not current:
            # première insertion
            if len(word) <= max_len:
                current = word
            else:
                # mot seul plus long que max_len => on tronque
                lines.append(word[:max_len])
                current = ""
        else:
            candidate = current + " " + word
            if len(candidate) <= max_len:
                current = candidate
            else:
                lines.append(current)
                current = word if len(word) <= max_len else word[:max_len]

        # si on a déjà 2 lignes pleines, on arrête
        if len(lines) == 2:
            break

    # ajouter le reste si possible
    if current and len(lines) < 2:
        lines.append(current)

    # sécurité : max 2 lignes
    if len(lines) > 2:
        lines = lines[:2]

    # re-troncation de sécurité au cas où
    lines = [l[:max_len] for l in lines]

    return lines


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

    # ⚠️ ICI : on force le passage par la fonction de découpage
    name_lines = split_name_safely(prenom, nom, max_len=17)

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
