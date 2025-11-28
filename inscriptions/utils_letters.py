# # inscriptions/utils_letters.py
# import os
# from django.conf import settings
# from django.template.loader import render_to_string
# from weasyprint import HTML


# def generate_invitation_letter_pdf(inscription):
#     """
#     Génère la lettre d’invitation PDF depuis templates/inscriptions/letters/invitation.html
#     et retourne le chemin du fichier généré.
#     """

#     output_dir = os.path.join(settings.MEDIA_ROOT, "letters")
#     os.makedirs(output_dir, exist_ok=True)

#     context = {
#         "nom": inscription.nom,
#         "prenom": inscription.prenom,
#         "nationalite": inscription.nationalite,
#         "provenance": inscription.provenance,
#         "role": inscription.type_profil,
#     }

#     html_string = render_to_string("letters/invitation.html", context)

#     output_path = os.path.join(output_dir, f"invitation_{inscription.id}.pdf")

#     HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(output_path)

#     return output_path

# inscriptions/utils_letters.py
import logging
import os
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Lazy import WeasyPrint so that manage.py doesn't fail on machines without system libs
try:
    from weasyprint import HTML  # type: ignore
    WEASY_AVAILABLE = True
except Exception as exc:
    WEASY_AVAILABLE = False
    logger.warning("WeasyPrint not available in this environment: %s. PDF generation will be skipped.", exc)


def generate_invitation_letter_pdf(inscription, output_path=None, template_name="letters/invitation.html"):
    """
    Generate invitation PDF for a given inscription.
    Returns:
      - path to saved PDF if output_path is provided,
      - bytes if output_path is None and PDF could be generated,
      - None if WeasyPrint is not available or generation failed.
    """
    if not WEASY_AVAILABLE:
        logger.info("Skipping PDF generation for inscription %s: WeasyPrint not available.", getattr(inscription, "id", None))
        return None

    try:
        # prepare output directory if saving to disk
        if output_path is None:
            output_dir = os.path.join(settings.MEDIA_ROOT, "letters")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"invitation_{inscription.id}.pdf")
            save_to_disk = True
        else:
            save_to_disk = True

        context = {
            "nom": getattr(inscription, "nom", ""),
            "prenom": getattr(inscription, "prenom", ""),
            "nationalite": getattr(inscription, "nationalite", ""),
            "provenance": getattr(inscription, "provenance", ""),
            "role": getattr(inscription, "type_profil", ""),
        }

        html_string = render_to_string(template_name, context)

        html = HTML(string=html_string, base_url=str(settings.BASE_DIR))
        if save_to_disk:
            html.write_pdf(target=output_path)
            logger.info("Invitation PDF written to %s for inscription %s", output_path, getattr(inscription, "id", None))
            return output_path
        else:
            pdf_bytes = html.write_pdf()
            logger.info("Invitation PDF generated in-memory for inscription %s", getattr(inscription, "id", None))
            return pdf_bytes
    except Exception as exc:
        logger.exception("Error generating invitation PDF for inscription %s: %s", getattr(inscription, "id", None), exc)
        return None
