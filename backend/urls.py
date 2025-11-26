from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from inscriptions.views import (
    validate_inscription,
    refuse_inscription,
    get_badge_url,
    get_pieces_urls,
    AdminInscriptionListView,
    ResendConfirmationAPIView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('inscriptions.urls')),
    path('api/admin/inscriptions/', AdminInscriptionListView.as_view(), name='admin-inscriptions'),
    path("api/inscriptions/<int:pk>/resend_confirmation/", ResendConfirmationAPIView.as_view(), name="inscription-resend"),

    path("api/admin/inscriptions/<int:pk>/validate/", validate_inscription),
    path("api/admin/inscriptions/<int:pk>/refuse/", refuse_inscription),
    path("api/admin/inscriptions/<int:pk>/badge/", get_badge_url),
    path("api/admin/inscriptions/<int:pk>/pieces/", get_pieces_urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
