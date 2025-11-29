# backend/api_views.py
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

User = get_user_model()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current authenticated user minimal profile for frontend."""
    u = request.user
    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "first_name": getattr(u, "first_name", ""),
        "last_name": getattr(u, "last_name", ""),
        "role": getattr(u, "role", None),
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_users(request):
    """
    Return a simple list of users for admin UI.
    Only accessible to staff / superusers.
    """
    qs = User.objects.all().order_by("id")
    data = []
    for u in qs:
        data.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "first_name": getattr(u, "first_name", ""),
            "last_name": getattr(u, "last_name", ""),
            "role": getattr(u, "role", None),
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
        })
    return Response(data)
