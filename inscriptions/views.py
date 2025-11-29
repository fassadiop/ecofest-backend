import os
import zipfile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView
from django.http import Http404, HttpResponse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

from .models import Inscription, Participant, Badge, Evenement
from .serializers import (
    InscriptionSerializer,
    RegisterSerializer,
    UserSerializer,
    AdminStatusSerializer,
    BadgeSerializer,
    EvenementSerializer,
    PublicInscriptionSerializer,
)
from .tasks import send_confirmation_email, send_invitation_package
from .utils_badges import generate_badge

User = get_user_model()

class InscriptionPublicViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all().order_by('-created_at')
    serializer_class = PublicInscriptionSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]


class InscriptionViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all().order_by('-created_at')
    serializer_class = InscriptionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class AdminInscriptionListView(ListAPIView):
    queryset = Inscription.objects.all().order_by('-created_at')
    serializer_class = InscriptionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def validate_inscription(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)

    inscription.statut = "Validé"
    inscription.save(update_fields=["statut"])

    # LOG 100% FORCE
    print("---- VALIDATE INSCRIPTION START ----")
    print("Inscription ID:", inscription.id)
    print("Email to send:", inscription.email)
    print("SendGrid Key Loaded:", settings.SENDGRID_API_KEY[:10] + "...")
    print("------------------------------------")

    try:
        send_invitation_package(inscription.id)
        print("SEND INVITATION PACKAGE: SUCCESS")
    except Exception as e:
        import traceback
        print("SEND INVITE ERROR:", str(e))
        traceback.print_exc()

        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    print("---- VALIDATE INSCRIPTION END ----")

    return Response({"message": "OK"}, status=200)


# @api_view(["POST"])
# @permission_classes([IsAuthenticated, IsAdminUser])
# def validate_inscription(request, pk):
#     inscription = get_object_or_404(Inscription, pk=pk)

#     inscription.statut = "Validé"
#     inscription.save(update_fields=["statut"])

#     try:
#         send_invitation_package(inscription.id)
#     except Exception as e:
#         import traceback
#         print("SENDGRID ERROR:", str(e))
#         traceback.print_exc()
#         return Response(
#             {"error": str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     return Response({"message": "OK"}, status=200)


# @api_view(["POST"])
# @permission_classes([IsAuthenticated, IsAdminUser])
# def validate_inscription(request, pk):
#     """
#     Passe une INSCRIPTION en 'Validé',
#     génère badge + lettre + email.
#     """
#     inscription = get_object_or_404(Inscription, pk=pk)

#     # Récupérer le participant lié
#     participant = inscription.participant

#     # Mise à jour du statut de l'inscription
#     inscription.statut = "Validé"
#     inscription.save(update_fields=["statut"])

#     # Générer badge + PDF + envoyer email
#     send_invitation_package(inscription.id)

#     return Response(
#         {"message": "Inscription validée", "id": inscription.id},
#         status=status.HTTP_200_OK,
#     )

# @api_view(["POST"])
# @permission_classes([IsAuthenticated, IsAdminUser])
# def validate_inscription(request, pk):
#     inscription = get_object_or_404(Inscription, pk=pk)

#     # Mise à jour du statut
#     inscription.statut = "Validé"
#     inscription.save(update_fields=["statut"])

#     # 👉 Corrections : on passe le PARTICIPANT
#     participant = inscription.participant

#     try:
#         badge_path = generate_badge(inscription)
#     except Exception as e:
#         return Response(
#             {"error": f"Erreur lors de la génération du badge : {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     try:
#         send_invitation_package(inscription.id)
#     except Exception as e:
#         return Response(
#             {"error": f"Erreur lors de l’envoi de l’email : {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     return Response(
#         {"message": "Inscription validée", "id": inscription.id},
#         status=status.HTTP_200_OK
#     )



@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def refuse_inscription(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    inscription.statut = "Refusé"
    inscription.save(update_fields=["statut"])
    return Response({"message": "Inscription refusée", "id": inscription.id})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_badge_url(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    participant = inscription.participant  # 🔥 correction

    try:
        badge_path = generate_badge(inscription)
    except Exception as e:
        return Response(
            {"error": f"Erreur badge : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    rel_path = os.path.relpath(badge_path, settings.MEDIA_ROOT)
    badge_url = request.build_absolute_uri(settings.MEDIA_URL + rel_path)

    return Response({"badge_url": badge_url})



@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_pieces_urls(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    data = {}
    if inscription.passeport_file:
        data["passeport_url"] = request.build_absolute_uri(inscription.passeport_file.url)
    if hasattr(inscription, "cni_file") and inscription.cni_file:
        data["cni_url"] = request.build_absolute_uri(inscription.cni_file.url)
    if hasattr(inscription, "carte_presse_file") and inscription.carte_presse_file:
        data["carte_presse_url"] = request.build_absolute_uri(inscription.carte_presse_file.url)

    return Response(data)

# @staff_member_required
# def download_badges_zip(request):
#     badges_dir = os.path.join(settings.MEDIA_ROOT, "badges")
#     zip_path = os.path.join(settings.MEDIA_ROOT, "badges.zip")

#     # Créer le ZIP
#     with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#         for root, dirs, files in os.walk(badges_dir):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 arcname = os.path.relpath(file_path, badges_dir)
#                 zipf.write(file_path, arcname)

#     # Lire le ZIP et l'envoyer
#     with open(zip_path, 'rb') as f:
#         response = HttpResponse(f.read(), content_type='application/zip')
#         response['Content-Disposition'] = 'attachment; filename="badges.zip"'
#         return response

@staff_member_required
def download_badges_zip(request):
    badges_dir = os.path.join(settings.MEDIA_ROOT, "badges")
    if not os.path.isdir(badges_dir):
        raise Http404("Badges directory not found.")

    # create an in-memory zip? For simplicity we write a temp file in MEDIA_ROOT
    zip_path = os.path.join(settings.MEDIA_ROOT, "badges_export.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(badges_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, badges_dir)
                zf.write(file_path, arcname)

    with open(zip_path, "rb") as f:
        resp = HttpResponse(f.read(), content_type="application/zip")
        resp["Content-Disposition"] = 'attachment; filename="badges_ecofest.zip"'
        return resp