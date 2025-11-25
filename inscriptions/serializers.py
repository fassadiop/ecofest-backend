from rest_framework import serializers
from django.contrib.auth import get_user_model

from inscriptions.tasks import send_confirmation_email
from .models import Participant, Inscription, PieceJointe, Badge, Evenement
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','telephone','role','langue_pref']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','password','telephone','langue_pref']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # create participant profile
        Participant.objects.create(user=user)
        return user

class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = '__all__'

class InscriptionSerializer(serializers.ModelSerializer):
    passeport_file = serializers.FileField(required=False, allow_null=True)
    badge_file = serializers.FileField(read_only=True)
    invitation_file = serializers.FileField(read_only=True)

    class Meta:
        model = Inscription
        fields = [
            'id','participant_id','evenement','nom','prenom','email','telephone','nationalite',
            'provenance','type_profil','passeport_file','adresse','date_naissance','statut',
            'admin_remarque','badge_file','invitation_file','created_at'
        ]
        read_only_fields = ('statut','admin_remarque','badge_file','invitation_file','created_at')

    def create(self, validated_data):
        # validated_data contains 'participant' because of source above
        return super().create(validated_data)

class AdminStatusSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=[('Validé','Validé'),('Refusé','Refusé')])
    admin_remarque = serializers.CharField(allow_blank=True, required=False)

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['png_path','token','date_issuance','access_level']

class PublicInscriptionSerializer(serializers.ModelSerializer):
    # fichiers uploadés
    passeport_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Inscription
        fields = [
            'id','evenement','nom','prenom','email','telephone','nationalite',
            'provenance','type_profil','passeport_file','adresse','date_naissance',
            'statut','admin_remarque','created_at'
        ]
        read_only_fields = ('statut','admin_remarque','created_at')

    def validate_email(self, value):
        # Optional: stricter email/check duplicates etc.
        return value

    def create(self, validated_data):
        # Créer un participant "anonyme" lié à cette inscription (participant.user = None)
        # On ne tente pas d'associer à un User si l'inscription est publique.
        participant = Participant.objects.create(user=None, organisation=None)

        # Forcer statut En_attente pour la soumission publique
        validated_data['statut'] = 'En_attente'

        # create the inscription
        inscription = Inscription.objects.create(participant=participant, **validated_data)

        # Envoi d'un email de confirmation (console backend en dev)
        try:
            subject = "Réception de votre inscription – ECOFEST"
            message = (
                f"Bonjour {inscription.prenom},\n\n"
                "Nous avons bien reçu votre inscription. Elle est en attente de validation.\n"
                "Vous serez informé par email une fois la validation effectuée.\n\n"
                "Cordialement,\nL'équipe ECOFEST"
            )
            send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                      [inscription.email], fail_silently=True)
        except Exception:
            # fail_silently pour dev; log en prod
            pass

        # Notifier admin(s) sommairement
        try:
            admin_subject = f"[ECOFEST] Nouvelle inscription En_attente: {inscription.nom} {inscription.prenom}"
            admin_message = f"Consulter l'admin pour valider: /admin/inscriptions/inscription/{inscription.id}/change/"
            send_mail(admin_subject, admin_message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                      [getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')], fail_silently=True)
        except Exception:
            pass

        try:
            send_confirmation_email.delay(inscription.id)
        except Exception as e:
            # log erreur, mais ne bloque pas la création
            print("Celery send task error:", e)

        return inscription
    
