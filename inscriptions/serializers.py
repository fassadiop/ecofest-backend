from rest_framework import serializers
from django.contrib.auth import get_user_model

from inscriptions.tasks import send_confirmation_email
from .models import Participant, Inscription, Badge, Evenement
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


# ------------------------
# USER / PARTICIPANT
# ------------------------
class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = [
            'id',
            'user',
            'organisation',
            'created_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telephone', 'role', 'langue_pref'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'telephone', 'langue_pref'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # créer participant lié
        Participant.objects.create(user=user)

        return user


# ------------------------
# EVENEMENT
# ------------------------
class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = '__all__'


# ------------------------
# INSCRIPTION (ADMIN)
# ------------------------
class InscriptionSerializer(serializers.ModelSerializer):
    passeport_file = serializers.FileField(required=False, allow_null=True)
    badge_file = serializers.FileField(read_only=True)
    invitation_file = serializers.FileField(read_only=True)

    class Meta:
        model = Inscription
        fields = [
            'id', 'participant', 'evenement', 'nom', 'prenom', 'email',
            'telephone', 'nationalite', 'provenance', 'type_profil',
            'passeport_file', 'adresse', 'date_naissance', 'statut',
            'admin_remarque', 'badge_file', 'invitation_file',
            'created_at'
        ]
        read_only_fields = (
            'statut', 'admin_remarque', 'badge_file',
            'invitation_file', 'created_at'
        )

    def create(self, validated_data):
        return super().create(validated_data)


class AdminStatusSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=[('Validé', 'Validé'), ('Refusé', 'Refusé')])
    admin_remarque = serializers.CharField(allow_blank=True, required=False)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['png_path', 'token', 'date_issuance', 'access_level']


# ------------------------
# INSCRIPTION PUBLIQUE
# ------------------------
class PublicInscriptionSerializer(serializers.ModelSerializer):
    passeport_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Inscription
        fields = [
            'id', 'evenement', 'nom', 'prenom', 'email', 'telephone',
            'nationalite', 'provenance', 'type_profil', 'passeport_file',
            'adresse', 'date_naissance', 'statut', 'admin_remarque',
            'created_at'
        ]
        read_only_fields = ('statut', 'admin_remarque', 'created_at')

    def create(self, validated_data):
        # 1) Création participant simple
        participant = Participant.objects.create(user=None, organisation=None)

        # 2) Forcer statut
        validated_data['statut'] = 'En_attente'

        # 3) Créer inscription
        inscription = Inscription.objects.create(
            participant=participant,
            **validated_data
        )

        # 4) Email confirmation utilisateur
        try:
            subject = "Réception de votre inscription – ECOFEST"
            message = (
                f"Bonjour {inscription.prenom},\n\n"
                "Votre inscription est reçue et en attente de validation.\n"
                "Vous recevrez un email dès validation.\n\n"
                "Cordialement,\nL'équipe ECOFEST"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [inscription.email],
                fail_silently=True,
            )
        except:
            pass

        # 5) Email admin
        try:
            admin_subject = f"[ECOFEST] Nouvelle inscription : {inscription.nom} {inscription.prenom}"
            admin_message = f"Voir l'admin : /admin/inscriptions/inscription/{inscription.id}/change/"
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except:
            pass

        # 6) Tâche Celery
        try:
            send_confirmation_email.delay(inscription.id)
        except Exception as e:
            print("Celery error:", e)

        return inscription
