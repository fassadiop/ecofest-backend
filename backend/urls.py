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
    download_badges_zip,
    AdminInscriptionListView,
)

from backend.api_views import me, admin_users


urlpatterns = [
    path("api/auth/me/", me, name="api-auth-me"),
    path("api/admin/users/", admin_users, name="api-admin-users"),
    path('admin/', admin.site.urls),
    path('api/admin/', include('users.urls')),
    # JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Module inscriptions
    path('api/', include('inscriptions.urls')),

    # Admin actions (validate/refuse etc)
    path("api/admin/inscriptions/<int:pk>/validate/", validate_inscription),
    path("api/admin/inscriptions/<int:pk>/refuse/", refuse_inscription),
    path("api/admin/inscriptions/<int:pk>/badge/", get_badge_url),
    path("api/admin/inscriptions/<int:pk>/pieces/", get_pieces_urls),

    # Liste admin (tableau back-office)
    path("api/admin/inscriptions/", AdminInscriptionListView.as_view(), name="admin-inscriptions"),
    path("api/admin/badges/download/", download_badges_zip, name="download-badges"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
