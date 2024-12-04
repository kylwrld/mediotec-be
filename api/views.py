from django.http import QueryDict
# from django.shortcuts import render,  get_object_or_404
from .utils import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Grade
from .permissions import *

from .serializers import *
import os

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenObtainSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser



import json
from .utils import *
from django.db.models import Q
from django.utils import timezone
from django.db import transaction, connection, reset_queries
from django.db.utils import IntegrityError
from django.conf import settings
from itertools import islice

import pytz
import datetime
from datetime import timedelta

# datetime.datetime.now(datetime.timezone.utc)

class CustomAPIView(APIView):
    def get_permissions(self):
        # Instances and returns the dict of permissions that the view requires.
        return {key: [permission() for permission in permissions] for key, permissions in self.permission_classes.items()}

    def check_permissions(self, request):
        # Gets the request method and the permissions dict, and checks the permissions defined in the key matching
        # the method.
        method = request.method.lower()
        for permission in self.get_permissions()[method]:
            if not permission.has_permission(request, self):
                self.permission_denied(request, message=getattr(permission, 'message', None))

class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        user_id = getattr(user, api_settings.USER_ID_FIELD)
        if not isinstance(user_id, int):
            user_id = str(user_id)

        token = cls()
        token[api_settings.USER_ID_CLAIM] = user_id
        token['id'] = user.id
        token['name'] = user.name
        token['type'] = user.type

        if user.type == User.Types.STUDENT:
            _class = StudentClass.objects.filter(student=user.id).last()
            if _class is not None:
                token["class_id"] = _class.class_year._class_id

        if api_settings.CHECK_REVOKE_TOKEN:
            token[api_settings.REVOKE_TOKEN_CLAIM] = get_md5_hash_password(
                user.password
            )

        return token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    token_class = CustomRefreshToken

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['id'] = user.id
        token['name'] = user.name
        token['type'] = user.type
        if user.type == User.Types.STUDENT:
            _class = StudentClass.objects.filter(student=user.id).last()
            if _class is not None:
                token["class_id"] = _class.class_year._class_id

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AdminView(CustomAPIView):
    parser_classes = (JSONParser, MultiPartParser)
    permission_classes = {"get":[IsAdmin], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}

    def get(self, request, pk=None):
        if pk:
            admin = get_object_or_404(Admin, pk=pk)
            admin_serializer = UserSerializerReadOnly(admin)
            return Response(admin_serializer.data, status=status.HTTP_200_OK)

        admin = Admin.objects.all()
        admin_serializer = UserSerializerReadOnly(admin, many=True)
        return Response({"admins":admin_serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk=None, format=None):
        admin = get_object_or_404(Admin, pk=pk)
        serializer = AdminSerializerWrite(admin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"admin":serializer.data}, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk=None, format=None):
        if request.user.id == pk:
            return Response({"detail":"Você não pode se deletar"}, status=status.HTTP_400_BAD_REQUEST)

        admin = get_object_or_404(Admin, pk=pk)
        admin.delete()
        return Response({"admin": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)


# TODO: Mudar rota para user/student/ user/teacher/ user/admin/
# name, email, type, password
class Signup(CustomAPIView):
    parser_classes = (JSONParser, MultiPartParser)
    permission_classes = {"post":[IsAdmin]}

    def post(self, request, format=None):
        user_serializer = SignupUserSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user: User = user_serializer.save()
        serializer = UserSerializerReadOnly(user)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class SignupStudent(CustomAPIView):
    parser_classes = (JSONParser, MultiPartParser)
    permission_classes = {"post":[IsAdmin]}
    # name, email, password,
    # parent {name, cpf}
    # phone [{ddd, number}, ...]
    def post(self, request, format=None):
        data = request.data.dict()

        parent_data = data.pop("parent", False)
        phone_data = data.pop("phone", False)
        if not parent_data:
            return Response({"detail":"Campo parent é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not phone_data:
            return Response({"detail":"Campo phone é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(request.data, QueryDict):
            parent_data = json.loads(parent_data)
            phone_data = json.loads(phone_data)

        student_serializer = SignupStudentSerializer(data=request.data)
        parent_serializer = ParentSerializer(data=parent_data)
        phone_serializer = PhoneSerializer(data=phone_data, many=True)
        student_serializer.is_valid(raise_exception=True)
        parent_serializer.is_valid(raise_exception=True)
        phone_serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                student: Student = student_serializer.save()
                parent: Parent = parent_serializer.save(student=student)
                objs = (Phone(ddd=p["ddd"], number=p["number"], parent=parent) for p in phone_serializer.data)
                batch_size = len(phone_serializer.data)
                batch = list(islice(objs, batch_size))
                Phone.objects.bulk_create(batch, batch_size)

        except:
            return Response({"detail":"Erro ao persistir no banco de dados."}, status=status.HTTP_400_BAD_REQUEST)

        student_serializer_readonly = StudentSerializerReadOnly(student)
        # refresh = CustomTokenObtainPairSerializer.get_token(student)
        # data = {
        #     "refresh":str(refresh),
        #     "access":str(refresh.access_token),
        # }

        return Response(data=student_serializer_readonly.data, status=status.HTTP_201_CREATED)

# class SignupNotStudent(CustomAPIView):
#     # name, email, password
#     def post(self, request, format=None):
#         student_serializer = SignupStudentSerializer(data=request.data)
#         student_serializer.is_valid(raise_exception=True)
#         student: Student = student_serializer.save()

#         refresh = CustomTokenObtainPairSerializer.get_token(student)
#         data = {
#             "refresh":str(refresh),
#             "access":str(refresh.access_token),
#         }
#         return Response(data=data, status=status.HTTP_201_CREATED)


class Login(CustomAPIView):
    permission_classes = {"post":[]}

    # email, password
    def post(self, request, format=None):
        errors = check_fields(request, ["email", "password"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user =  get_object_or_404(User, email=request.data["email"])
        correct_password = user.check_password(request.data["password"])
        if not correct_password:
            return Response({"detail":"Senha incorreta."}, status=status.HTTP_404_NOT_FOUND)

        refresh = CustomTokenObtainPairSerializer.get_token(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

class LoginStudent(CustomAPIView):
    permission_classes = {"post":[]}

    # email, password
    def post(self, request, format=None):
        errors = check_fields(request, ["email", "password"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user =  get_object_or_404(User, email=request.data["email"])
        if user.type == User.Types.ADMIN or user.type == User.Types.TEACHER:
            return Response({"detail":"Somente estudantes podem fazer login."}, status=status.HTTP_400_BAD_REQUEST)

        correct_password = user.check_password(request.data["password"])
        if not correct_password:
            return Response({"detail":"Senha incorreta."}, status=status.HTTP_404_NOT_FOUND)

        refresh = CustomTokenObtainPairSerializer.get_token(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

class ParentView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "delete":[IsAdmin], "put":[IsAdmin]}

    def get(self, request, student_pk=None, format=None):
        parents = get_object_or_404(Student, pk=student_pk).parents.all()
        parents_serializer = ParentSerializer(parents, many=True)
        return Response(parents_serializer.data)

    # name, cpf, student
    def post(self, request, student_pk=None, format=None):
        student_pk = request.data.pop("student", False)
        if not student_pk:
            return Response({"detail":"O campo student é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        parent_serializer = ParentSerializer(data=request.data)
        parent_serializer.is_valid(raise_exception=True)
        student = get_object_or_404(Student, pk=student_pk)
        parent_serializer.save(student=student)
        return Response({"detail":"Parent criado e atribuído."}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None, format=None):
        parent = get_object_or_404(Parent, pk=pk)
        parent.delete()
        return Response({"parent": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        parent = get_object_or_404(Parent, pk=pk)
        serializer = ParentSerializer(parent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response({"parent":serializer.data}, status=status.HTTP_204_NO_CONTENT)


class StudentView(CustomAPIView):
    parser_classes = (JSONParser, MultiPartParser)
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "delete":[IsAdmin], "put":[IsAdmin]}
    def get(self, request, pk=None, format=None):
        if pk:
            student = get_object_or_404(Student, pk=pk)
            student_serializer = StudentParentSerializer(student)
            return Response(student_serializer.data, status=status.HTTP_200_OK)

        student = Student.objects.all()
        student_serializer = StudentSerializerReadOnly(student, many=True)
        return Response({"students":student_serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None, format=None):
        student = get_object_or_404(Student, pk=pk)
        student.delete()
        return Response({"student": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        student = get_object_or_404(Student, pk=pk)
        serializer = StudentSerializerWrite(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"student":serializer.data}, status=status.HTTP_204_NO_CONTENT)

class StudentClassView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "delete":[IsAdmin]}
    # class + year
    def get(self, request, class_pk=None, year=timezone.now().year, format=None):
        _class = get_object_or_404(Class, pk=class_pk)
        class_serializer = ClassSerializer(_class)
        class_years = ClassYear.objects.filter(_class=_class)
        years = list(map(lambda cy: cy.year, class_years))
        try:
            class_year = ClassYear.objects.get(_class=_class, year=year)
        except:
            return Response({"detail":f"Turma não tem registros de {year}", "_class":class_serializer.data, "years": years})
        class_year_serializer = ClassYearSerializerAllStudents(class_year)
        return Response({"_class": class_serializer.data, "class_year": class_year_serializer.data, "years": years}, status=status.HTTP_200_OK)

    # student, _class
    def post(self, request, class_pk=None, year=timezone.now().year, format=None):
        errors = check_fields(request, ["student", "_class"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        if year < timezone.now().year:
            return Response({"detail":"Você não pode criar uma turma no passado."}, status=status.HTTP_400_BAD_REQUEST)

        _class = get_object_or_404(Class, pk=request.data["_class"])
        class_year, _ = ClassYear.objects.get_or_create(_class=_class, year=year)

        if isinstance(request.data["student"], int):
            request.data["year"] = year
            request.data["class_year"] = class_year.id
            student_class_serializer = StudentClassSerializer(data=request.data)
            student_class_serializer.is_valid(raise_exception=True)
            student_class_serializer.save()
            return Response({"detail":"Aluno atribuído a turma.", "student_class":student_class_serializer.data}, status=status.HTTP_201_CREATED)

        if isinstance(request.data["student"], list):
            students = request.data["student"]
            try:
                with transaction.atomic():
                    objs = (StudentClass(student_id=student, class_year=class_year) for student in students)
                    batch_size = len(students)
                    batch = list(islice(objs, batch_size))
                    student_class = StudentClass.objects.bulk_create(batch, batch_size)
                    student_class_serializer = StudentClassSerializer(student_class, many=True)
                    return Response({"detail":"Alunos atribuídos a turma.", "student_class":student_class_serializer.data}, status=status.HTTP_201_CREATED)
            except:
                return Response({"detail":"Erro ao persistir no banco de dados. Tenha certeza de que os ID's são válidos."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail":"ID do estudante inválido."}, status=status.HTTP_400_BAD_REQUEST)

    # /student_class_/<class_pk>/<year>/<student_pk>/
    def delete(self, request, class_pk=None, year=timezone.now().year, student_pk=None, format=None):
        class_year = get_object_or_404(ClassYear, _class_id=class_pk, year=year)
        student_class = get_object_or_404(StudentClass, class_year=class_year, student_id=student_pk)
        student_class.delete()
        return Response({"student_class": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

class TeacherView(CustomAPIView):
    parser_classes = (JSONParser, MultiPartParser)
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}

    def get(self, request, pk=None, format=None):
        if pk:
            teacher = get_object_or_404(Teacher, pk=pk)
            teacher_serializer = TeacherSerializer(teacher)
            return Response(teacher_serializer.data, status=status.HTTP_200_OK)

        teacher = Teacher.objects.all()
        teacher_serializer = TeacherSerializer(teacher, many=True)
        return Response({"teachers":teacher_serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None, format=None):
        teacher = get_object_or_404(Teacher, pk=pk)
        teacher.delete()
        return Response({"teacher": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        teacher = get_object_or_404(Teacher, pk=pk)
        serializer = TeacherSerializerWrite(teacher, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"teacher":serializer.data}, status=status.HTTP_204_NO_CONTENT)


class SubjectView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}
    def get(self, request, pk=None, format=None):
        if pk:
            subject = get_object_or_404(Subject, pk=pk)
            subject_serializer = SubjectSerializer(subject)
            return Response(subject_serializer.data, status=status.HTTP_200_OK)

        subject = Subject.objects.all()
        subject_serializer = SubjectSerializer(subject, many=True)
        return Response({"subjects":subject_serializer.data}, status=status.HTTP_200_OK)

    # name
    def post(self, request, format=None):
        subject_serializer = SubjectSerializer(data=request.data)
        subject_serializer.is_valid(raise_exception=True)
        subject_serializer.save()
        return Response({"detail":"Disciplina criada.", "subject":subject_serializer.data}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None, format=None):
        subject = get_object_or_404(Subject, pk=pk)
        subject.delete()
        return Response({"subject": "Disciplina deletada com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        subject = get_object_or_404(Subject, pk=pk)
        serializer = SubjectSerializer(subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"subject":serializer.data}, status=status.HTTP_204_NO_CONTENT)

class TeacherSubjectView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}
    def get(self, request, pk=None, format=None):
        if pk:
            teacher_subject = get_object_or_404(TeacherSubject, pk=pk)
            teacher_subject_serializer = TeacherSubjectSerializer(teacher_subject)
            return Response(teacher_subject_serializer.data, status=status.HTTP_200_OK)

        teacher_subject = TeacherSubject.objects.all()
        teacher_subject_serializer = TeacherSubjectSerializer(teacher_subject, many=True)
        return Response({"teacher_subjects":teacher_subject_serializer.data}, status=status.HTTP_200_OK)

    # teacher, subject
    def post(self, request, format=None):
        # teacher_subject_serializer = TeacherSubjectSerializer(data=request.data)
        # teacher_subject_serializer.is_valid(raise_exception=True)
        # teacher_subject_serializer.save()
        subjects = request.data["subject"]
        teacher = request.data["teacher"]
        try:
            with transaction.atomic():
                objs = (TeacherSubject(teacher=get_object_or_404(Teacher, pk=teacher), subject=get_object_or_404(Subject, pk=subject)) for subject in subjects)
                batch_size = len(subjects)
                batch = list(islice(objs, batch_size))
                teacher_subject = TeacherSubject.objects.bulk_create(batch, batch_size, unique_fields=["teacher", "subject"])
                teacher_subject_serializer = TeacherSubjectSerializerReadOnly(teacher_subject, many=True)
                return Response({"detail":"Professor atribuído a disciplina", "teacher_subject":teacher_subject_serializer.data}, status=status.HTTP_201_CREATED)
        except:
            return Response({"detail":"Erro ao persistir no banco de dados. Tenha certeza de que os ID's são válidos."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        teacher_subject = get_object_or_404(TeacherSubject, pk=pk)
        teacher_subject.delete()
        return Response({"teacher_subject": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        teacher_subject = get_object_or_404(TeacherSubject, pk=pk)
        serializer = TeacherSerializerWrite(teacher_subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        teacher_subject = serializer.save()
        data = TeacherSubjectSerializerReadOnly(teacher_subject)
        return Response({"teacher_subject":data.data}, status=status.HTTP_204_NO_CONTENT)

class ClassView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}
    def get(self, request, pk=None, format=None):
        degree = request.query_params.get("degree", None)
        if degree:
            _class = Class.objects.filter(degree=degree)
            class_serializer = ClassSerializer(_class, many=True)
            return Response({"classes":class_serializer.data}, status=status.HTTP_200_OK)

        if pk:
            _class =  get_object_or_404(Class, pk=pk)
            class_serializer = ClassSerializer(_class)
            return Response(class_serializer.data, status=status.HTTP_200_OK)

        _class = Class.objects.all()
        class_serializer = ClassSerializer(_class, many=True)
        return Response({"classes":class_serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        class_serializer = ClassSerializer(data=request.data)
        class_serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            _class = class_serializer.save()
            class_year_serializer = ClassYearSerializer(data={"_class":_class.pk, "year":timezone.now().year})
            class_year_serializer.is_valid(raise_exception=True)
            class_year = class_year_serializer.save()
            class_year_serializer_rd = ClassYearSerializerReadOnly(class_year)

        return Response({"detail":"Turma criada.", "class_year":class_year_serializer_rd.data}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None, format=None):
        _class = get_object_or_404(Class, pk=pk)
        _class.delete()
        return Response({"_class": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        _class = get_object_or_404(Class, pk=pk)
        serializer = ClassSerializer(_class, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"_class":serializer.data}, status=status.HTTP_204_NO_CONTENT)

class ClassYearView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin], "put":[IsAdmin], "delete":[IsAdmin]}
    def get(self, request, pk=None, class_pk=None, year=timezone.now().year, format=None):
        # TODO: Pass year in path
        if pk:
            class_year = ClassYear.objects.filter(year=timezone.now().year, pk=pk)
            class_year_serializer = ClassYearSerializerReadOnly(class_year)
            return Response({"class_year": class_year_serializer.data}, status=status.HTTP_200_OK)

        class_year = ClassYear.objects.filter(year=timezone.now().year)
        class_year_serializer = ClassYearSerializerReadOnly(class_year, many=True)
        return Response({"class_years": class_year_serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None, format=None):
        class_year = get_object_or_404(ClassYear, pk=pk)
        class_year.delete()
        return Response({"class_year": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        class_year = get_object_or_404(ClassYear, pk=pk)
        serializer = ClassYearSerializer(class_year, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"class_year":serializer.data}, status=status.HTTP_204_NO_CONTENT)



class ClassYearTeacherSubjectView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdmin]}
    def get(self, request, class_pk=None, year=timezone.now().year, format=None):
        class_year = get_object_or_404(ClassYear, _class_id=class_pk, year=year)
        class_year_serializer = ClassYearSerializerAllTeachers(class_year)
        return Response(class_year_serializer.data, status=status.HTTP_200_OK)

    # _class, teacher_subject
    def post(self, request, class_pk=None, year=timezone.now().year, format=None):
        errors = check_fields(request, ["_class", "teacher_subject"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        class_year = get_object_or_404(ClassYear, _class_id=request.data["_class"], year=timezone.now().year)
        request.data["class_year"] = class_year.id
        class_teacher_subject_serialializer = ClassYearTeacherSubjectSerializer(data=request.data)
        class_teacher_subject_serialializer.is_valid(raise_exception=True)
        class_teacher_subject_serialializer.save()
        return Response({"detail":"Turma atribuída ao professor.", "turma":class_teacher_subject_serialializer.data})

    def delete(self, request, pk=None, format=None):
        class_year_teacher_subject = get_object_or_404(ClassYearTeacherSubject, pk=pk)
        class_year_teacher_subject.delete()
        return Response({"class_year_teacher_subject": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

class AnnouncementView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAdminOrTeacher], "put":[IsAdminOrTeacher], "delete":[IsAdminOrTeacher]}

    def get(self, request, pk=None, format=None):
        if pk:
            announcement = get_object_or_404(Announcement, pk=pk)
            announcement_serializer = AnnouncementSerializerReadOnly(announcement)
            return Response(announcement_serializer.data, status=status.HTTP_200_OK)

        announcement = Announcement.objects.all().order_by("-fixed", '-created_at')
        announcement_serializer = AnnouncementSerializerReadOnly(announcement, many=True)

        return Response({"announcements":announcement_serializer.data}, status=status.HTTP_200_OK)

    # title, body, fixed
    def post(self, request, pk=None, format=None):
        errors = check_fields(request, ["title", "body"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        announcement_serializer = AnnouncementSerializer(data=request.data)
        announcement_serializer.is_valid(raise_exception=True)

        if request.data.get("_class", None):
            class_year = get_object_or_404(ClassYear, pk=request.data.get("_class", None))
            announcement_serializer.save(user=request.user, class_year=class_year)
        else:
            announcement_serializer.save(user=request.user)

        return Response({"detail":"Comunicado criado.", "announcement":announcement_serializer.data})

    def delete(self, request, pk=None, format=None):
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.delete()
        return Response({"announcement": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        announcement = get_object_or_404(Announcement, pk=pk)
        serializer = AnnouncementSerializer(announcement, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.data.get("_class", None):
            class_year = get_object_or_404(ClassYear, pk=request.data.get("_class", None))
            serializer.save(class_year=class_year)
        else:
            serializer.save()

        return Response({"announcement":serializer.data}, status=status.HTTP_204_NO_CONTENT)


class CommentView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsAuthenticated], "put":[IsAdminOrTeacher], "delete":[IsAdminOrTeacher]}
    def get(self, request, pk=None, format=None):
        if pk:
            comment = get_object_or_404(Comment, pk=pk)
            comment_serializer = CommentSerializer(comment)
            return Response(comment_serializer.data, status=status.HTTP_200_OK)

        comment = Comment.objects.all()
        comment_serializer = CommentSerializer(comment, many=True)

        return Response({"comments":comment_serializer.data}, status=status.HTTP_200_OK)

    # body, announcement, user TODO: get user from authenticated request
    def post(self, request, pk=None, format=None):
        errors = check_fields(request, ["body", "announcement"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        comment_serializer = CommentSerializer(data=request.data)
        comment_serializer.is_valid(raise_exception=True)
        comment_serializer.save(user=request.user)
        return Response({"detail":"Comentário criado.", "comment":comment_serializer.data})

    def delete(self, request, pk=None, format=None):
        comment = get_object_or_404(Comment, pk=pk)
        comment.delete()
        return Response({"comment": "Deletado com sucesso"}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None, format=None):
        comment = get_object_or_404(Comment, pk=pk)
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"comment":serializer.data}, status=status.HTTP_204_NO_CONTENT)

class GradeView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsTeacher]}

    def get(self, request, student_pk=None, year=timezone.now().year, format=None):
        if request.user == User.Types.STUDENT:
            if int(request.user.id) != int(student_pk):
                return Response({"detail":"Estudantes somente podem visualizar os próprios conceitos."}, status=status.HTTP_400_BAD_REQUEST)

        grades = Grade.objects.filter(student=student_pk, year=year)
        grades_serializer = GradeSerializer(grades, many=True)
        return Response({"grades":grades_serializer.data}, status=status.HTTP_200_OK)

    # TODO: Change to check if grade already exists before creating
    def post(self, request, student_pk=None, year=timezone.now().year, format=None):
        request.data["year"] = timezone.now().year
        grades = request.data["grade"]
        try:
            with transaction.atomic():
                objs = (Grade(student_id=grade.pop("student", None), teacher_subject_id=grade.pop("teacher_subject", None), **grade) for grade in grades)
                batch_size = len(grades)
                batch = list(islice(objs, batch_size))
                grades = Grade.objects.bulk_create(batch, batch_size, update_conflicts=True,
                        update_fields=[
                            "av1_1", "av2_1", "noa_1",
                            "av1_2", "av2_2", "noa_2",
                            "av1_3", "av2_3", "noa_3"
                            ],
                        unique_fields=["student", "teacher_subject", "year", "degree"])
                grade_serializer = GradeSerializer(grades, many=True)
                return Response({"detail":"Nota atribuída.", "grade":grade_serializer.data}, status=status.HTTP_201_CREATED)
        except:
            return Response({"detail":"Erro ao persistir no banco de dados. Tenha certeza de que os ID's são válidos."}, status=status.HTTP_400_BAD_REQUEST)

class AttendanceView(CustomAPIView):
    permission_classes = {"get":[IsAuthenticated], "post":[IsTeacher]}

    # path params: class_year, teacher_subject
    # query params: date
    def get(self, request, class_year=None, teacher_subject=None):
        today = timezone.now()
        date = request.query_params.get("date", f"{today.year}-{today.month}-{today.day}")
        class_year_teacher_subject = get_object_or_404(ClassYearTeacherSubject, class_year_id=class_year, teacher_subject_id=teacher_subject)

        if not teacher_subject:
            return Response({"detail":"Procure com uma disciplina"}, status=status.HTTP_400_BAD_REQUEST)
        date_format = '%Y-%m-%d'
        date_obj = timezone.datetime.strptime(date, date_format)
        day = date_obj.day
        attendances = Attendance.objects.filter(class_year_teacher_subject=class_year_teacher_subject, created_at__day=day)
        attendace_serializer = AttendanceSerializer(attendances, many=True)

        return Response({"attendances": attendace_serializer.data}, status=status.HTTP_200_OK)

    # attendaces = {
    #   student: {id, type}
    #   class_year
    #   teacher_subject
    # }
    def post(self, request, class_year=None, teacher_subject=None):
        attendances = request.data["attendances"]
        class_year_id = request.data["class_year"]

        class_year_teacher_subject = get_object_or_404(
        ClassYearTeacherSubject, class_year_id=class_year_id, teacher_subject_id=request.data["teacher_subject"])

        date_now = timezone.localtime(timezone.now())
        start_of_day = date_now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(hours=23, minutes=59, seconds=59)
        remaining = 15
        day = timezone.now()
        # attendances_same_day = Attendance.objects.filter(class_year_teacher_subject=class_year_teacher_subject, created_at__date=day)
        attendances_same_day = Attendance.objects.filter(class_year_teacher_subject=class_year_teacher_subject,
                                                         created_at__gte=start_of_day,
                                                         created_at__lt=end_of_day)

        if len(attendances_same_day) > 0:
            delta = (day - attendances_same_day[0].created_at)
            remaining -= int(delta.seconds / 60)

        if remaining < 0:
            return Response({"detail":"Você não pode mais atribuir presença nesse dia."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                objs = (
                    Attendance(
                        student_id=attendance.get("student", None)["id"],
                        class_year_teacher_subject=class_year_teacher_subject,
                        type=attendance["type"],
                        day=date_now.day
                    )
                    for attendance in attendances
                )
                batch_size = len(attendances)
                batch = list(islice(objs, batch_size))
                attendances_data = Attendance.objects.bulk_create(batch, batch_size, update_conflicts=True,
                                                                update_fields=["type"], unique_fields=["student", "class_year_teacher_subject", "day"])

                attendance_serializer = AttendanceSerializer(attendances_data, many=True)

                return Response({"detail":"Presença atribuída.", "attendances":attendance_serializer.data, "remaining":remaining}, status=status.HTTP_201_CREATED)
        except:
            return Response({"detail":"Erro ao persistir no banco de dados. Tenha certeza de que os ID's são válidos."}, status=status.HTTP_400_BAD_REQUEST)

        return Response()

class TimeScheduleView(APIView):
    def get(self, request, class_year=None, year=timezone.now().year):
        class_year = request.query_params.get("class_year", None)
        time_schedules = TimeSchedule.objects.filter(class_year=class_year)
        time_schedule_serializer = TimeScheduleSerializer(time_schedules, many=True)
        return Response({"time_schedules": time_schedule_serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, class_year=None, year=timezone.now().year):
        time_schedules = request.data["time_schedules"]

        # try:
        with transaction.atomic():
            objs = (
                TimeSchedule(
                    # id=time_schedule.pop("id", None),
                    class_year_id=time_schedule.pop("class_year", None),
                monday_class_year_teacher_subject_id=time_schedule.pop("monday_class_year_teacher_subject", None),
                tuesday_class_year_teacher_subject_id=time_schedule.pop("tuesday_class_year_teacher_subject", None),
                wednesday_class_year_teacher_subject_id=time_schedule.pop("wednesday_class_year_teacher_subject", None),
                thursday_class_year_teacher_subject_id=time_schedule.pop("thursday_class_year_teacher_subject", None),
                friday_class_year_teacher_subject_id=time_schedule.pop("friday_class_year_teacher_subject", None),
                    **time_schedule
                )
                for time_schedule in time_schedules
            )

            batch_size = len(time_schedules)
            batch = list(islice(objs, batch_size))
            time_schedules_data = TimeSchedule.objects.bulk_create(batch, batch_size, update_conflicts=True,
                                                            update_fields=[
                                                                "monday_class_year_teacher_subject",
                                                                "tuesday_class_year_teacher_subject",
                                                                "wednesday_class_year_teacher_subject",
                                                                "thursday_class_year_teacher_subject",
                                                                "friday_class_year_teacher_subject",
                                                            ], unique_fields=["id"])

            time_schedule_serializer = TimeScheduleSerializer(time_schedules_data, many=True)
            return Response({"detail":"Horário atribuído com sucesso.", "time_schedules":time_schedule_serializer.data}, status=status.HTTP_201_CREATED)
        # except:
        #     return Response({"detail":"Erro ao persistir no banco de dados. Tenha certeza de que os ID's são válidos."}, status=status.HTTP_400_BAD_REQUEST)


        # return Response({"detail":"Horário atribuído.", "time_schedules":None}, status=status.HTTP_201_CREATED)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherAllSubjects(request, pk=None):
    teacher_subject = TeacherSubject.objects.filter(teacher_id=pk)
    teacher_subject_serializer = TeacherSubjectSerializerReadOnly(teacher_subject, many=True)
    return Response({"teacher_subjects": teacher_subject_serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherAllSubjectsFromClass(request, _class_pk=None, year=None, teacher_pk=None):
    class_year = get_object_or_404(ClassYear, _class_id=_class_pk, year=year)
    class_year_teacher_subject_serializer = ClassYearTeacherSubjectSerializerReadOnly(
        ClassYearTeacherSubject.objects.filter(class_year_id=class_year, teacher_subject__teacher_id=teacher_pk),
        many=True
    )
    data = [dict["teacher_subject"] for dict in class_year_teacher_subject_serializer.data]
    return Response({"teacher_subject":data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def SubjectsAllTeachers(request, pk=None):
    teacher_subject = TeacherSubject.objects.filter(subject_id=pk)
    teacher_subject_serializer = TeacherSubjectSerializerReadOnly(teacher_subject, many=True)
    return Response({"teacher_subject": teacher_subject_serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherAllClasses(request, pk=None):
    teacher = get_object_or_404(Teacher, pk=pk)
    class_year_teacher_subject_serializer = ClassYearTeacherSubjectSerializerReadOnly(
        ClassYearTeacherSubject.objects.filter(teacher_subject__teacher=teacher), many=True)

    data = {}
    for cyts in class_year_teacher_subject_serializer.data:
        # if data.get("class_year"):
        #     continue
        data[cyts["class_year"]["_class"]["id"]] = cyts["class_year"]["_class"]
    response = [ value for key, value in data.items() ]

    return Response({"classes": response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AllTeacherSubjectFromClass(request, class_year):
    class_year_teacher_subjects = ClassYearTeacherSubject.objects.filter(class_year_id=class_year)
    class_year_teacher_subjects_serializer = ClassYearTeacherSubjectSerializerReadOnly(class_year_teacher_subjects, many=True)

    # data = []
    # for cyts in class_year_teacher_subjects_serializer.data:
    #     data.append(cyts["teacher_subject"])

    return Response({"detail":"Todos os professores da classe", "class_year_teacher_subjects":class_year_teacher_subjects_serializer.data}, status=status.HTTP_200_OK)


# serializer             takes ± 2.66s
# for loop               takes ± 0.11s
# filter Q()             takes ± 0.001s
# serialize functions    takes ± 2.54s
# a single time_schedule takes ± 0.91

# serializer | 10x | ± 2.6621812105178835
# for_loop   | 10x | ± 0.11226716041564941
# q          | 10x | ± 0.0011049747467041016
# maybe cache
@api_view(['GET'])
@permission_classes([IsAdminOrTeacher])
def AllTimeSchedulesFromTeacher(request, pk):
    class_year_teacher_subjects = ClassYearTeacherSubject.objects.filter(teacher_subject__teacher_id=pk)

    #                                           this looks stupid
    time_schedules = TimeSchedule.objects.filter(
        Q(monday_class_year_teacher_subject__in=class_year_teacher_subjects)
        | Q(tuesday_class_year_teacher_subject__in=class_year_teacher_subjects)
        | Q(wednesday_class_year_teacher_subject__in=class_year_teacher_subjects)
        | Q(thursday_class_year_teacher_subject__in=class_year_teacher_subjects)
        | Q(friday_class_year_teacher_subject__in=class_year_teacher_subjects)
    )

    time_schedules_serializer = TimeScheduleSerializer(time_schedules, many=True)
    return Response({"detail":"Todos os horários do professor", "time_schedules":time_schedules_serializer.data}, status=status.HTTP_200_OK)
    # return Response({"detail":"Todos os horários do professor", "time_schedules":data}, status=status.HTTP_200_OK)
    # return Response({"detail":"Todos os horários do professor"}, status=status.HTTP_200_OK)








@api_view(['GET'])
def hello_world(request):
    # teacher_subject = Teacher.objects.first().teachersubject_set.all()
    # print(teacher_subject[1].class_year_teacher_subject.all())
    # print(teacher_subject)
    # print(ClassYearTeacherSubject.objects.filter(teacher_subject__teacher_id=36))
    # print(ClassYearTeacherSubjectSerializerReadOnly(ClassYearTeacherSubject.objects.filter(teacher_subject__teacher_id=36), many=True).data)
    # print(User.objects.all())
    # print(User.objects.filter(email="admin@gmail.com"))
    # print(User.objects.get(email="admin@gmail.com"))
    # print(User.objects.get(email="admin@gmail.com"))
    # print(User.objects.all())
    # test = Student.objects.get(email="aluno1@gmail.com").class_year
    # print(test)
    # print(len(Attendance.objects.filter(student=4)))

    # print(ClassYear.objects.filter(_class_id=1).values_list("email", flat=True))
    # print(list(map(lambda class_year: class_year.year, class_years)))

    # class_years = ClassYear.objects.filter(year=timezone.now().year)
    # all_students = [class_year.students.all() for class_year in class_years]
    # flat_students = []
    # for students in all_students:
    #     for student in students:
    #         flat_students.append(student)

    # print(class_year)

    # print(settings.BASE_DIR.joinpath("api\\template\\email_template.html"))
    # class_year = ClassYear.objects.get(id=1)
    # print(class_year.students.values_list("email"))

    # class_years = ClassYear.objects.filter(year=timezone.now().year)
    # all_students = [class_year.students.values_list("email", flat=True) for class_year in class_years]

    return Response({})
