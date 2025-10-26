from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    """
    Разрешает доступ пользователям из группы 'Administrator'
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Administrator').exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

