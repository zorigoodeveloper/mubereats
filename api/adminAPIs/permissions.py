from rest_framework.permissions import BasePermission

class IsAdminUserCustom(BasePermission):
    """Зөвхөн admin / superuser-д зөвшөөрөх permission"""
    def has_permission(self, request, view):
        # auth_user хүснэгтэд байгаа бүх хэрэглэгч admin гэж үзнэ
        return request.user is not None