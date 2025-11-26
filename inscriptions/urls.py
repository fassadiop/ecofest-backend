from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# Tu n'as plus de ViewSet pour inscriptions ou événements
# On laisse le router vide mais il peut être utilisé plus tard

urlpatterns = [
    # --- Endpoints publics ou d’inscription ---
    # Aucun RegisterView dans ton views.py → on le supprime
    # path('auth/register/', views.RegisterView.as_view(), name='auth-register'),

    path('', include(router.urls)),

    # --- Endpoints Admin ---
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
