from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User
from rest_framework_simplejwt.settings import api_settings
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS

class IsAdmin(JWTAuthentication):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.type == User.Types.ADMIN:
                return True

        return False

class IsTeacher(JWTAuthentication):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.type == User.Types.TEACHER:
                return True

        return False

class IsAdminOrTeacher(JWTAuthentication):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.type == User.Types.ADMIN or request.user.type == User.Types.TEACHER:
                return True

        return False

class IsStudent(JWTAuthentication):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.type == User.Types.STUDENT:
            return True

        return False

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in SAFE_METHODS

class StudentPkIsSameAsRequest(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in SAFE_METHODS

# class IsStudent(JWTAuthentication):
#     def has_permission(self, request, view):
#         if request.user.is_authenticated and request.user.type == User.Types.STUDENT:
#             if request.method == "GET" and request.data.:
#             return True

#         return False

# class AdminAndTeacher(JWTAuthentication):
#     def has_permission(self, request, view):
#         if request.user.is_authenticated and request.user.type == User.Types.TEACHER:
#             return True

#         return False



    # def authenticate(self, request):
    #     header = self.get_header(request)
    #     if header is None:
    #         return None

    #     raw_token = self.get_raw_token(header)
    #     if raw_token is None:
    #         return None

    #     validated_token = self.get_validated_token(raw_token)

    #     print("a", type(self.get_validated_token(raw_token)))

    #     return self.get_user(validated_token), validated_token
