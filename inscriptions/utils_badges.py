import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


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
