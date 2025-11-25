from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from inscriptions.views import AdminInscriptionListView, ResendConfirmationAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT endpoints (accessible at /api/token/ and /api/token/refresh/)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Ton API - inclusion des routes définies dans inscriptions/urls.py
    path('api/', include('inscriptions.urls')),
    path('api/admin/inscriptions/', AdminInscriptionListView.as_view(), name='admin-inscriptions'),
    path("api/inscriptions/<int:pk>/resend_confirmation/", ResendConfirmationAPIView.as_view(), name="inscription-resend"),
]

# servir les médias en dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
