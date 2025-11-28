# users/permissions.py
from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with role 'Admin'.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # assume your User.role field stores 'Admin' for admins
        return getattr(user, 'role', '') == 'Admin'
