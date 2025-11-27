import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML


def generate_invitation_letter_pdf(inscription):
    """
    Génère la lettre d’invitation PDF depuis templates/inscriptions/letters/invitation.html
    et retourne le chemin du fichier généré.
    """

    output_dir = os.path.join(settings.MEDIA_ROOT, "letters")
    os.makedirs(output_dir, exist_ok=True)

    context = {
        "nom": inscription.nom,
        "prenom": inscription.prenom,
        "nationalite": inscription.nationalite,
        "provenance": inscription.provenance,
        "role": inscription.type_profil,
    }

    html_string = render_to_string("letters/invitation.html", context)

    output_path = os.path.join(output_dir, f"invitation_{inscription.id}.pdf")

    HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(output_path)

    return output_path
