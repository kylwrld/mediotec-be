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
from django.utils import timezone

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

class SignupStudent(APIView):
    # name, email, password, parents
    def post(self, request, format=None):
        student_serializer = SignupStudentSerializer(data=request.data)
        student_serializer.is_valid(raise_exception=True)
        student: Student = student_serializer.save()

        refresh = RefreshToken.for_user(student)
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
            student = get_object_or_404(Student, pk=pk)
            student_serializer = StudentSerializer(student)
            return Response({"users":student_serializer.data}, status=status.HTTP_200_OK)

        student = Student.objects.all()
        student_serializer = StudentSerializer(student, many=True)
        return Response({"users":student_serializer.data}, status=status.HTTP_200_OK)


class StudentClassView(APIView):
    # pass class_year or class + year
    def get(self, request, class_pk=None, year=timezone.now().year, format=None):
        class_year = get_object_or_404(ClassYear, _class_id=class_pk, year=year)
        class_year_serializer = ClassYearSerializerAllStudents(class_year)
        return Response(class_year_serializer.data, status=status.HTTP_200_OK)

    # student, _class
    def post(self, request, class_pk=None, year=timezone.now().year, format=None):
        if year < timezone.now().year:
            return Response({"detail":"Você não pode criar uma turma no passado."}, status=status.HTTP_400_BAD_REQUEST)

        request.data["year"] = year
        _class = get_object_or_404(Class, pk=request.data["_class"])
        class_year, _ = ClassYear.objects.get_or_create(_class=_class, year=year)
        request.data["class_year"] = class_year.id
        student_class_serializer = StudentClassSerializer(data=request.data)
        student_class_serializer.is_valid(raise_exception=True)
        student_class_serializer.save()
        return Response({"detail":"Aluno atribuído a turma", "student_class":student_class_serializer.data}, status=status.HTTP_201_CREATED)


class TeacherView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            teacher = get_object_or_404(Teacher, pk=pk)
            teacher_serializer = TeacherSerializer(teacher)
            print(teacher, teacher_serializer.data)
            return Response({"teacher":teacher_serializer.data}, status=status.HTTP_200_OK)

        teacher = Teacher.objects.all()
        teacher_serializer = TeacherSerializer(teacher, many=True)
        return Response({"teacher":teacher_serializer.data}, status=status.HTTP_200_OK)


class SubjectView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            subject = get_object_or_404(Subject, pk=pk)
            subject_serializer = SubjectSerializer(subject)
            return Response({"disciplina":subject_serializer.data}, status=status.HTTP_200_OK)

        subject = Subject.objects.all()
        subject_serializer = SubjectSerializer(subject, many=True)
        return Response({"disciplina":subject_serializer.data}, status=status.HTTP_200_OK)

    # name
    def post(self, request, format=None):
        subject_serializer = SubjectSerializer(data=request.data)
        subject_serializer.is_valid(raise_exception=True)
        subject_serializer.save()
        return Response({"detail":"Disciplina criada.", "subject":subject_serializer.data}, status=status.HTTP_201_CREATED)


class TeacherSubjectView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            teacher_subject = get_object_or_404(TeacherSubject, pk=pk)
            teacher_subject_serializer = TeacherSubjectSerializer(teacher_subject)
            return Response({"teacher_subject":teacher_subject_serializer.data}, status=status.HTTP_200_OK)

        teacher_subject = TeacherSubject.objects.all()
        teacher_subject_serializer = TeacherSubjectSerializer(teacher_subject, many=True)
        return Response({"teacher_subject":teacher_subject_serializer.data}, status=status.HTTP_200_OK)

    # teacher, subject
    def post(self, request, format=None):
        teacher_subject_serializer = TeacherSubjectSerializer(data=request.data)
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



class ClassYearTeacherSubjectView(APIView):
    def get(self, request, class_pk=None, year=timezone.now().year, format=None):
        class_year = get_object_or_404(ClassYear, _class_id=class_pk, year=year)
        class_year_serializer = ClassYearSerializerAllTeachers(class_year)
        return Response(class_year_serializer.data, status=status.HTTP_200_OK)

    # _class, teacher_subject
    def post(self, request, class_pk=None, year=timezone.now().year, format=None):
        # errors = check_fields(request, ["_class", "teacher_subject"])
        # if errors:
        #     return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        class_year = get_object_or_404(ClassYear, _class_id=request.data["_class"], year=timezone.now().year)
        request.data["class_year"] = class_year.id
        class_teacher_subject_serialializer = ClassYearTeacherSubjectSerializer(data=request.data)
        class_teacher_subject_serialializer.is_valid(raise_exception=True)
        class_teacher_subject_serialializer.save()
        return Response({"detail":"Turma atribuída ao professor.", "turma":class_teacher_subject_serialializer.data})


class AnnouncementView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            announcement = get_object_or_404(Announcement, pk=pk)
            announcement_serializer = AnnouncementSerializer(announcement)
            return Response({"comunicado":announcement_serializer.data}, status=status.HTTP_200_OK)

        announcement = Announcement.objects.all()
        announcement_serializer = AnnouncementSerializer(announcement, many=True)

        return Response({"comunicado":announcement_serializer.data}, status=status.HTTP_200_OK)

    # title, body, fixed, user TODO: get user from authenticated request
    def post(self, request, pk=None, format=None):
        errors = check_fields(request, ["title", "body"])
        #TODO: GET USER REQUEST.USER
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        announcement_serializer = AnnouncementSerializer(data=request.data)
        announcement_serializer.is_valid(raise_exception=True)
        announcement_serializer.save()
        return Response({"detail":"Comunicado criado.", "comunicado":announcement_serializer.data})


class CommentView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            comment = get_object_or_404(Comment, pk=pk)
            comment_serializer = CommentSerializer(comment)
            return Response({"comentario":comment_serializer.data}, status=status.HTTP_200_OK)

        comment = Comment.objects.all()
        comment_serializer = CommentSerializer(comment, many=True)

        return Response({"comentario":comment_serializer.data}, status=status.HTTP_200_OK)

    # body, announcement, user TODO: get user from authenticated request
    def post(self, request, pk=None, format=None):
        errors = check_fields(request, ["body", "announcement"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        comment_serializer = CommentSerializer(data=request.data)
        comment_serializer.is_valid(raise_exception=True)
        comment_serializer.save()
        return Response({"detail":"Comentário criado.", "comentario":comment_serializer.data})





















@api_view(['GET'])
def hello_world(request):
    print(NotStudent.objects.all())
    return Response({"message": "W"})
