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
#  FONCTION DÉCOUPAGE : jamais > 17 chars, pas de mot coupé
# ---------------------------------------------------------
def split_name_safely(prenom, nom, max_len=17):
    """
    Découpe prenom + nom en max 2 lignes.
    
    - Aucun mot dépassé
    - On remplit la LINE 1 avec le plus de mots possible (≤ 17 chars)
    - Le reste va en LINE 2 (≤ 17 chars)
    - Si le nom peut entrer dans la 2e ligne, il est groupé proprement
    """

    words = (prenom.strip() + " " + nom.strip()).split()
    lines = []
    current = ""

    for word in words:
        if not current:
            current = word
        else:
            if len(current) + 1 + len(word) <= max_len:
                current += " " + word
            else:
                lines.append(current)
                current = word

    if current:
        lines.append(current)

    # Garantir maximum 2 lignes (sécurité pour badge)
    if len(lines) > 2:
        # Ligne 1 = premier bloc
        line1 = lines[0]
        # Ligne 2 = tout le reste concaténé
        line2 = " ".join(lines[1:])
        # Si ligne 2 dépasse 17 chars, on laisse quand même (cas ultra rare)
        return [line1[:max_len], line2[:max_len]]

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

    name_lines = split_name_safely(prenom, nom, max_len=17)

    nat_text = inscription.nationalite or ""
    prov_text = inscription.provenance or ""
    
    NAME_Y = 600
    NAT_Y = 700
    PROV_Y = 780

    # -- NOM sur 1 ou 2 lignes
    draw.text((400, NAME_Y), name_lines[0], fill="black", font=font_bold)

    if len(name_lines) > 1:
        draw.text((400, NAME_Y + 60), name_lines[1], fill="black", font=font_bold)
        nat_y = NAT_Y + 60
        prov_y = PROV_Y + 60
    else:
        nat_y = NAT_Y
        prov_y = PROV_Y

    # -- NATIONALITE
    if nat_text:
        draw.text((400, nat_y), nat_text, fill="black", font=font_normal)

    # -- PROVENANCE
    if prov_text:
        draw.text((400, prov_y), prov_text, fill="black", font=font_normal)

    # ------------ SAVE ------------
    output_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"badge_{inscription.id}.png")
    base.save(output_path, dpi=(300, 300))

    return output_path
