# users/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .serializers import UserListSerializer, UserCreateSerializer
from django.contrib.auth import get_user_model
from .permissions import IsAdminRole
from rest_framework.response import Response
from rest_framework.decorators import action

User = get_user_model()

class UserViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('-id')
    permission_classes = [IsAuthenticated]
    # choose serializer in get_serializer_class
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserListSerializer

    # only Admins can create
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]
