from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Inscription, Participant, Badge, Evenement, Inscription, Badge
from .serializers import InscriptionSerializer, RegisterSerializer, UserSerializer, AdminStatusSerializer, BadgeSerializer, EvenementSerializer, PublicInscriptionSerializer
from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .tasks import send_confirmation_email

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