from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import InscriptionViewSet, EvenementViewSet, RegisterView, InscriptionPublicViewSet
from . import views

router = DefaultRouter()
router.register(r'inscriptions', InscriptionPublicViewSet, basename='inscription')
router.register(r'evenements', EvenementViewSet, basename='evenement')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('', include(router.urls)),
    path(
        "admin/inscriptions/<int:pk>/validate/",
        views.validate_inscription,
        name="inscription-validate",
    ),
    path(
        "admin/inscriptions/<int:pk>/refuse/",
        views.refuse_inscription,
        name="inscription-refuse",
    ),
    path(
        "admin/inscriptions/<int:pk>/badge/",
        views.get_badge_url,
        name="inscription-badge",
    ),
    path(
        "admin/inscriptions/<int:pk>/pieces/",
        views.get_pieces_urls,
        name="inscription-pieces",
    ),
]
