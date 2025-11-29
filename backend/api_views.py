from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

User = get_user_model()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": getattr(u, "role", None),
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    })

@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_users(request):
    users = User.objects.all().order_by("id")
    data = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": getattr(u, "role", None),
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    } for u in users]
    return Response(data)
