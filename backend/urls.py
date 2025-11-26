from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

from inscriptions.views import (
    validate_inscription,
    refuse_inscription,
    get_badge_url,
    get_pieces_urls,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Routes du module inscriptions
    path('api/', include('inscriptions.urls')),

    # Actions admin (validate / refuse / badge / pièces)
    path("api/admin/inscriptions/<int:pk>/validate/", validate_inscription),
    path("api/admin/inscriptions/<int:pk>/refuse/", refuse_inscription),
    path("api/admin/inscriptions/<int:pk>/badge/", get_badge_url),
    path("api/admin/inscriptions/<int:pk>/pieces/", get_pieces_urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
