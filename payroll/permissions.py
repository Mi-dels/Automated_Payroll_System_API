from rest_framework.permissions import BasePermission


# =========================================
# ONLY HR USERS
# =========================================
class IsHR(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "HR"
        )


# =========================================
# ONLY EMPLOYEES
# =========================================
class IsEmployee(BasePermission):

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "EMPLOYEE"
        )


# =========================================
# HR OR OWNER
# =========================================
class IsHROrOwner(BasePermission):

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        # HR can access everything
        if request.user.role == "HR":
            return True

        # Employee only accesses own data
        return obj.employee == request.user








# from rest_framework.exceptions import PermissionDenied


# def is_hr(user):
#     return user.role == "HR"


# def require_hr(user):
#     if not is_hr(user):
#         raise PermissionDenied("Only HR can perform this action")