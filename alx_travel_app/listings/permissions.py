from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Anyone may read; only the object's owner (or staff) may change it.

    The owner field is named by ``owner_field`` on the view (default ``user``).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "user")
        return request.user.is_staff or getattr(obj, owner_field) == request.user
