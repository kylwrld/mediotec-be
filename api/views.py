from django.shortcuts import render,  get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Grade

from .serializers import *

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenObtainSerializer

from .utils import *

# class MyRefreshToken(RefreshToken):
#     @classmethod
#     def for_user(cls, user):
#         token = cls()
#         token['name'] = user.name

#         if api_settings.CHECK_REVOKE_TOKEN:
#             token[api_settings.REVOKE_TOKEN_CLAIM] = get_md5_hash_password(
#                 user.password
#             )

#         return token

# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     token_class = MyRefreshToken

#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token['name'] = user.paciente.nome

#         return token

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer


class Signup(APIView):
    def post(self, request, format=None):
        user_serializer = SignupUserSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user: User = user_serializer.save()

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

class Login(APIView):
    # email, password
    def post(self, request, format=None):
        errors = check_fields(request, ["email", "password"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user =  get_object_or_404(User, email=request.data["email"])
        correct_password = user.check_password(request.data["password"])
        if not correct_password:
            return Response({"detail":"Not found"}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

class StudentView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            user = Student.objects.filter(pk=pk)
        else:
            user = Student.objects.all()

        student_serializer = StudentSerializer(user, many=True)
        return Response({"users":student_serializer.data}, status=status.HTTP_200_OK)

class TeacherView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            user = Teacher.objects.filter(pk=pk)
        else:
            user = Teacher.objects.all()

        teacher_serializer = TeacherSerializer(user, many=True)
        return Response({"users":teacher_serializer.data}, status=status.HTTP_200_OK)

class SubjectView(APIView):
    def get(self, request, pk=None, format=None):
        pass

    # name
    def post(self, request, format=None):
        subject_serializer = SubjectSerializer(data=request.data)
        subject_serializer.is_valid(raise_exception=True)
        subject = subject_serializer.save()
        return Response({"detail":"Disciplina criada.", "subject":subject_serializer.data}, status=status.HTTP_201_CREATED)

class TeacherSubjectView(APIView):
    def post(self, request, teacher_pk, subject_pk, format=None):
        teacher_subject_serializer = TeacherSubjectSerializer(data={"teacher":teacher_pk, "subject":subject_pk})
        teacher_subject_serializer.is_valid(raise_exception=True)
        teacher_subject = teacher_subject_serializer.save()
        print(teacher_subject)
        return Response({"detail":teacher_subject_serializer.data})


class ClassView(APIView):
    def get(self, request, pk=None, format=None):
        pass

    def post(self, request, format=None):

        return


@api_view(['GET'])
def hello_world(request):
    print(Grade.get_final_grade("A", "NA"))
    return Response({"message": "W"})
