import os
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView
from django.conf import settings

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

    # Mise à jour du statut
    inscription.statut = "Validé"
    inscription.save(update_fields=["statut"])

    # 👉 Corrections : on passe le PARTICIPANT
    participant = inscription.participant

    try:
        badge_path = generate_badge(inscription)
    except Exception as e:
        return Response(
            {"error": f"Erreur lors de la génération du badge : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        send_invitation_package(inscription.id)
    except Exception as e:
        return Response(
            {"error": f"Erreur lors de l’envoi de l’email : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {"message": "Inscription validée", "id": inscription.id},
        status=status.HTTP_200_OK
    )



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
