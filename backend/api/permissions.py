from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly)


class IsAuthorStaffOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на изменение только для служебного персонала и автора.
    Остальным доступно только чтение.
    """
    def has_object_permission(self, request, view, obj):
        return(
            request.method in ('GET',)
            or (request.user == obj.author)
            or request.user.is_staff
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Разрешение на создание и изменение только для админа.
    Остальным доступно только чтение.
    """
    def has_permission(self, request, view):
        return (
            request.method in ('GET',)
            or request.user.is_authenticated
            and request.user.is_admin
        )


class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на изменение только для админа и пользователя.
    Остальным доступно только чтение.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET')
            or (request.user == obj)
            or request.user.is_admin
        )
