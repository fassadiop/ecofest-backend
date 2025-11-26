from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InscriptionPublicViewSet
from . import views

router = DefaultRouter()
router.register(r'inscriptions', InscriptionPublicViewSet, basename='inscriptions')

urlpatterns = [
    path('', include(router.urls)),

    # Admin-only actions
    path("admin/inscriptions/<int:pk>/validate/", views.validate_inscription),
    path("admin/inscriptions/<int:pk>/refuse/", views.refuse_inscription),
    path("admin/inscriptions/<int:pk>/badge/", views.get_badge_url),
    path("admin/inscriptions/<int:pk>/pieces/", views.get_pieces_urls),
]
