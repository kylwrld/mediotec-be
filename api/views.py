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

# TODO: Mudar rota para user/student/ user/teacher/ user/admin/
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

class StudentClassView(APIView):
    def get(self, request, class_pk=None, format=None):
        student_class = get_object_or_404(Class, pk=class_pk)
        student_class_serializer = ClassSerializerAllStudents(student_class)
        return Response(student_class_serializer.data, status=status.HTTP_200_OK)

    def post(self, request, student_pk=None, class_pk=None, format=None):
        if not student_pk:
            return Response({"detail":"O id do estudante é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        if not class_pk:
            return Response({"detail":"O id da turma é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        student_class_serializer = StudentClassSerializer(data={"student":student_pk, "_class":class_pk})
        student_class_serializer.is_valid(raise_exception=True)
        student_class_serializer.save()
        return Response({"detail":"Aluno atribuído a turma", "student_class":student_class_serializer.data}, status=status.HTTP_201_CREATED)

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
        subject_serializer.save()
        return Response({"detail":"Disciplina criada.", "subject":subject_serializer.data}, status=status.HTTP_201_CREATED)

class TeacherSubjectView(APIView):
    def post(self, request, teacher_pk, subject_pk, format=None):
        teacher_subject_serializer = TeacherSubjectSerializer(data={"teacher":teacher_pk, "subject":subject_pk})
        teacher_subject_serializer.is_valid(raise_exception=True)
        teacher_subject_serializer.save()
        return Response({"detail":"Professor atribuído a disciplina", "teacher_disciplina":teacher_subject_serializer.data}, status=status.HTTP_201_CREATED)

class ClassView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            _class =  get_object_or_404(Class, pk=pk)
            class_serializer = ClassSerializer(_class)
            return Response({"turma":class_serializer.data}, status=status.HTTP_200_OK)

        _class = Class.objects.all()
        class_serializer = ClassSerializer(_class, many=True)
        return Response({"turma":class_serializer.data}, status=status.HTTP_200_OK)


    def post(self, request, format=None):
        class_serializer = ClassSerializer(data=request.data)
        class_serializer.is_valid(raise_exception=True)
        class_serializer.save()
        return Response({"detail":"Turma criada.", "turma":class_serializer.data})
































@api_view(['GET'])
def hello_world(request):
    print(Grade.get_final_grade("A", "NA"))
    return Response({"message": "W"})
