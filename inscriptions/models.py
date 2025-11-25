from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import os

# ---------- Custom User ----------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Opérateur', 'Opérateur'),
        ('Vérificateur', 'Vérificateur'),
        ('Participant', 'Participant'),
    ]
    telephone = models.CharField(max_length=30, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Participant')
    langue_pref = models.CharField(max_length=2, choices=[('FR','FR'),('EN','EN'),('PT','PT')], default='FR')

    def __str__(self):
        return f"{self.username} ({self.email})"


# ---------- Evenement ----------
class Evenement(models.Model):
    nom = models.CharField(max_length=255)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    lieux = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


# ---------- Participant ----------
class Participant(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='participant_profile',
    null=True,         # autorise participant sans user (inscriptions publiques)
    blank=True
)
    organisation = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


def upload_to_passport(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"passeports/{instance.id}_{uuid.uuid4().hex}.{ext}"
    return filename


# ---------- Inscription ----------
class Inscription(models.Model):
    PROFILE_CHOICES = [
        ('All Access','All Access'),
        ('Équipe technique','Équipe technique'),
        ('Presse','Presse'),
        ('Staff','Staff'),
        ('VIP','VIP'),
    ]
    STATUS_CHOICES = [
        ('En_attente','En_attente'),
        ('Validé','Validé'),
        ('Refusé','Refusé'),
    ]

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='inscriptions')
    evenement = models.ForeignKey(Evenement, on_delete=models.SET_NULL, null=True, blank=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    email = models.EmailField()
    telephone = models.CharField(max_length=30, blank=True, null=True)
    nationalite = models.CharField(max_length=100, blank=True, null=True)
    provenance = models.CharField(max_length=255, blank=True, null=True)
    type_profil = models.CharField(max_length=30, choices=PROFILE_CHOICES)
    passeport_file = models.FileField(upload_to=upload_to_passport, null=True, blank=True)
    adresse = models.TextField(blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='En_attente')
    admin_remarque = models.TextField(blank=True, null=True)
    badge_file = models.FileField(upload_to='badges/', null=True, blank=True)
    invitation_file = models.FileField(upload_to='invitations/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.type_profil})"

    def mark_validated(self, admin_user=None, remarque=None):
        """
        Helper: mark as Validé and trigger badge/invitation generation.
        """
        self.statut = 'Validé'
        if remarque:
            self.admin_remarque = remarque
        self.save()
        # generate badge & invitation synchronously (or schedule Celery task in prod)
        from .utils import generate_badge_png_for_inscription, generate_invitation_pdf_for_inscription
        badge_path = generate_badge_png_for_inscription(self)
        invitation_path = generate_invitation_pdf_for_inscription(self)
        if badge_path:
            self.badge_file.name = badge_path
        if invitation_path:
            self.invitation_file.name = invitation_path
        self.save()


# ---------- PieceJointe ----------
class PieceJointe(models.Model):
    OWNER_CHOICES = [
        ('participant','participant'),
        ('inscription','inscription'),
    ]
    owner_type = models.CharField(max_length=20, choices=OWNER_CHOICES)
    owner_id = models.BigIntegerField()
    filename = models.CharField(max_length=500)
    filetype = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner_type','owner_id']),
        ]

    def __str__(self):
        return self.filename


# ---------- Badge ----------
class Badge(models.Model):
    inscription = models.OneToOneField(Inscription, on_delete=models.CASCADE, related_name='badge')
    png_path = models.CharField(max_length=500, blank=True, null=True)
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    date_issuance = models.DateTimeField(null=True, blank=True)
    access_level = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Badge {self.inscription} - {self.token}"
