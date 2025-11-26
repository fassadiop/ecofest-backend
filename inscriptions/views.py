import os
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Inscription, Participant, Badge, Evenement, Inscription, Badge
from .serializers import ParticipantSerializer, InscriptionSerializer, RegisterSerializer, UserSerializer, AdminStatusSerializer, BadgeSerializer, EvenementSerializer, PublicInscriptionSerializer
from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .tasks import send_confirmation_email, send_invitation_package
from django.conf import settings
from .utils_badges import generate_badge


User = get_user_model()

# Registration endpoint (simple)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# Inscription ViewSet
class InscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Inscription.objects.select_related('participant','evenement').all().order_by('-created_at')
    serializer_class = InscriptionSerializer

    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            return [permissions.IsAuthenticated(), ]  # adjust per your rules
        if self.action in ['change_status','admin_list']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        # expected participant is provided; if user is authenticated and has profile use it
        serializer.save()

    @action(detail=True, methods=['post'], url_path='change-status', permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def change_status(self, request, pk=None):
        """
        Admin action to change statut to Validé or Refusé.
        If Validé -> generate badge & invitation and send email (sync or schedule).
        """
        inscription = self.get_object()
        serializer = AdminStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        statut = serializer.validated_data['statut']
        admin_remarque = serializer.validated_data.get('admin_remarque','')
        inscription.admin_remarque = admin_remarque

        if statut == 'Validé':
            inscription.mark_validated()
            # Optionally send email here or schedule task
        else:
            inscription.statut = 'Refusé'
            inscription.save()
            # send refusal email (left as exercise)
        return Response(InscriptionSerializer(inscription, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='badge', permission_classes=[permissions.IsAuthenticated])
    def badge(self, request, pk=None):
        inscription = self.get_object()
        try:
            badge = inscription.badge
        except Badge.DoesNotExist:
            return Response({'detail':'Badge not generated'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BadgeSerializer(badge).data)

# Minimal Evenement ViewSet
class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class InscriptionPublicViewSet(viewsets.ModelViewSet):
    """
    - create: accessible au public (AllowAny)
    - list/retrieve: public read? (IsAuthenticatedOrReadOnly) — adapte selon besoin
    - update/partial_update/destroy: restreint aux admins
    """
    queryset = Inscription.objects.all().order_by('-created_at')
    serializer_class = PublicInscriptionSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        if self.action in ['update','partial_update','destroy','change_status','admin_list']:
            return [IsAdminUser()]
        # lecture ouverte (ou restreindre selon besoin)
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_status(self, request, pk=None):
        ins = self.get_object()
        statut = request.data.get('statut')
        if statut not in ['Validé','Refusé']:
            return Response({'detail':'statut invalide'}, status=status.HTTP_400_BAD_REQUEST)
        ins.statut = statut
        ins.admin_remarque = request.data.get('admin_remarque','')
        ins.save()
        # Si Validé -> génération badge/pdf + envoi mail (prévoir Celery en prod)
        if statut == 'Validé':
            ins.mark_validated(admin_user=request.user, remarque=ins.admin_remarque)
            # envoyer email info (tu peux appeler util send_mail ici)
        return Response({'ok':'statut mis à jour'})
    
class AdminInscriptionListView(ListAPIView):
    queryset = Inscription.objects.all().order_by('-id')
    serializer_class = InscriptionSerializer
    permission_classes = [IsAdminUser]

class ResendConfirmationAPIView(APIView):
    permission_classes = [permissions.AllowAny]  # ou IsAuthenticated selon logique

    def post(self, request, pk):
        send_confirmation_email.delay(pk)  # si Celery async
        return Response({"ok": True, "message": "E-mail programmé"}, status=status.HTTP_200_OK)
    
class ResendConfirmationAPIView(APIView):
    # AllowAny si tu veux qu'un client public l'appelle juste après POST /inscriptions/
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        send_confirmation_email.delay(pk)
        return Response({"ok": True, "message": "E-mail programmé"}, status=status.HTTP_200_OK)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def validate_inscription(request, pk):
    """
    Passe une inscription en VALIDEE + déclenche envoi badge + lettre.
    """
    participant = get_object_or_404(Participant, pk=pk)
    participant.statut = "VALIDEE"
    participant.save(update_fields=["statut"])

    # envoi automatique (badge + PDF)
    send_invitation_package.delay(participant.id)

    serializer = ParticipantSerializer(participant)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refuse_inscription(request, pk):
    """
    Passe une inscription en REFUSEE (sans envoi d’email).
    """
    participant = get_object_or_404(Participant, pk=pk)
    participant.statut = "REFUSEE"
    participant.save(update_fields=["statut"])

    serializer = ParticipantSerializer(participant)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_badge_url(request, pk):
    """
    Génère le badge si besoin puis renvoie l’URL pour téléchargement/affichage.
    """
    participant = get_object_or_404(Participant, pk=pk)
    badge_path = generate_badge(participant)  # crée /media/badges/badge_<id>.png

    rel_path = os.path.relpath(badge_path, settings.MEDIA_ROOT)
    badge_url = request.build_absolute_uri(settings.MEDIA_URL + rel_path)

    return Response({"badge_url": badge_url})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pieces_urls(request, pk):
    """
    Renvoie les URLs des pièces jointes : passeport, CNI, carte presse.
    Adapte les noms de champs à ton modèle.
    """
    participant = get_object_or_404(Participant, pk=pk)

    data = {}
    # ⚠️ adapte ces noms de champs à ton models.py
    if getattr(participant, "passeport", None):
        data["passeport_url"] = request.build_absolute_uri(participant.passeport.url)
    if getattr(participant, "cni", None):
        data["cni_url"] = request.build_absolute_uri(participant.cni.url)
    if getattr(participant, "carte_presse", None):
        data["carte_presse_url"] = request.build_absolute_uri(participant.carte_presse.url)

    return Response(data)