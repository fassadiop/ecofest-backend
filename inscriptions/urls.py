from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import InscriptionViewSet, EvenementViewSet, RegisterView, InscriptionPublicViewSet

router = DefaultRouter()
router.register(r'inscriptions', InscriptionPublicViewSet, basename='inscription')
router.register(r'evenements', EvenementViewSet, basename='evenement')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('', include(router.urls)),
]