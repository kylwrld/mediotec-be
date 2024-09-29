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
from django.db import transaction, connection, reset_queries
from django.db.utils import IntegrityError
from itertools import islice

class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = cls()
        token['name'] = user.name
        token['type'] = user.type

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
        token['name'] = user.name
        token['type'] = user.type

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# TODO: Mudar rota para user/student/ user/teacher/ user/admin/
# name, email, type, password
class Signup(APIView):
    def post(self, request, format=None):
        user_serializer = SignupUserSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user: User = user_serializer.save()

        refresh = CustomRefreshToken.for_user(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)


class SignupStudent(APIView):
    # name, email, password,
    # parent {name, cpf}
    # phone [{ddd, number}, ...]
    def post(self, request, format=None):
        parent_data = request.data.pop("parent", False)
        phone_data = request.data.pop("phone", False)
        if not parent_data:
            return Response({"detail":"Campo parent é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not phone_data:
            return Response({"detail":"Campo phone é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

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

        refresh = CustomRefreshToken.for_user(student)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }

        return Response(data=data, status=status.HTTP_201_CREATED)

class SignupNotStudent(APIView):
    # name, email, password
    def post(self, request, format=None):
        student_serializer = SignupStudentSerializer(data=request.data)
        student_serializer.is_valid(raise_exception=True)
        student: Student = student_serializer.save()

        refresh = CustomRefreshToken.for_user(student)
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

        refresh = CustomRefreshToken.for_user(user)
        data = {
            "refresh":str(refresh),
            "access":str(refresh.access_token),
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

class ParentView(APIView):
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

class StudentView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            student = get_object_or_404(Student, pk=pk)
            student_serializer = StudentParentSerializer(student)
            return Response(student_serializer.data, status=status.HTTP_200_OK)

        student = Student.objects.all()
        student_serializer = StudentSerializer(student, many=True)
        return Response({"students":student_serializer.data}, status=status.HTTP_200_OK)


class StudentClassView(APIView):
    # pass class_year or class + year
    def get(self, request, class_pk=None, year=timezone.now().year, format=None):
        class_year = get_object_or_404(ClassYear, _class_id=class_pk, year=year)
        class_year_serializer = ClassYearSerializerAllStudents(class_year)
        return Response(class_year_serializer.data, status=status.HTTP_200_OK)

    # student, _class
    def post(self, request, class_pk=None, year=timezone.now().year, format=None):
        errors = check_fields(request, ["student", "_class"])
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(teacher_serializer.data, status=status.HTTP_200_OK)

        teacher = Teacher.objects.all()
        teacher_serializer = TeacherSerializer(teacher, many=True)
        return Response({"teachers":teacher_serializer.data}, status=status.HTTP_200_OK)


class SubjectView(APIView):
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


class TeacherSubjectView(APIView):
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
        teacher_subject_serializer = TeacherSubjectSerializer(data=request.data)
        teacher_subject_serializer.is_valid(raise_exception=True)
        teacher_subject_serializer.save()
        return Response({"detail":"Professor atribuído a disciplina", "teacher_disciplina":teacher_subject_serializer.data}, status=status.HTTP_201_CREATED)


class ClassView(APIView):
    def get(self, request, pk=None, format=None):
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
            class_year_serializer.save()


        return Response({"detail":"Turma criada.", "class":class_year_serializer.data}, status=status.HTTP_201_CREATED)

class ClassYearView(APIView):
    def get(self, request, pk=None, format=None):
        class_year = ClassYear.objects.filter(year=timezone.now().year)
        class_year_serializer = ClassYearSerializerReadOnly(class_year, many=True)
        return Response({"class_years": class_year_serializer.data}, status=status.HTTP_200_OK)

class ClassYearTeacherSubjectView(APIView):
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


class AnnouncementView(APIView):
    def get(self, request, pk=None, format=None):
        if pk:
            announcement = get_object_or_404(Announcement, pk=pk)
            announcement_serializer = AnnouncementSerializerReadOnly(announcement)
            return Response(announcement_serializer.data, status=status.HTTP_200_OK)

        announcement = Announcement.objects.all().order_by("-created_at", '-fixed')
        announcement_serializer = AnnouncementSerializerReadOnly(announcement, many=True)

        return Response({"announcements":announcement_serializer.data}, status=status.HTTP_200_OK)

    # title, body, fixed TODO: get user from authenticated request
    def post(self, request, pk=None, format=None):
        errors = check_fields(request, ["title", "body"])
        #TODO: GET USER REQUEST.USER
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # if request.data.get("_class", None):
        #     class_year = get_object_or_404(ClassYear, _class=request.data[])
        announcement_serializer = AnnouncementSerializer(data=request.data)
        announcement_serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=30)
        announcement_serializer.save(user=user)
        return Response({"detail":"Comunicado criado.", "comunicado":announcement_serializer.data})


class CommentView(APIView):
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
        comment_serializer.save()
        return Response({"detail":"Comentário criado.", "comentario":comment_serializer.data})


class GradeView(APIView):
    # TODO: Please change
    def get(self, request, student_pk=None, year=timezone.now().year, format=None):
            grades = Grade.objects.filter(student=student_pk, year=year)
            grades_serializer = AllGradesTableSerializer(grades, many=True)
            data = [{"unit":1, "grades":{"AV1":"", "AV2":"", "NOA":""}, "subject":""},
                    {"unit":2, "grades":{"AV1":"", "AV2":"", "NOA":""}, "subject":""},
                    {"unit":3, "grades":{"AV1":"", "AV2":"", "NOA":""}, "subject":""}]
            for grade in grades_serializer.data:
                if grade["unit"] == 1:
                    data[0]["grades"][grade["type"]] = grade["grade"]
                    data[0]["subject"] = grade["subject"]
                if grade["unit"] == 2:
                    data[1]["grades"][grade["type"]] = grade["grade"]
                    data[1]["subject"] = grade["subject"]
                if grade["unit"] == 3:
                    data[2]["grades"][grade["type"]] = grade["grade"]
                    data[2]["subject"] = grade["subject"]
            # unit_1 = Grade.objects.filter(student=student_pk, year=year, unit=1)
            # unit_2 = Grade.objects.filter(student=student_pk, year=year, unit=2)
            # unit_3 = Grade.objects.filter(student=student_pk, year=year, unit=3)
            # unit_1_serializer = AllGradesTableSerializer(unit_1, many=True)
            # unit_2_serializer = AllGradesTableSerializer(unit_2, many=True)
            # unit_3_serializer = AllGradesTableSerializer(unit_3, many=True)
            # data = [{"unit":1, "grades":unit_1_serializer.data}, {"unit":2, "grades":unit_2_serializer.data}, {"unit":3, "grades":unit_3_serializer.data}]
            return Response({"grades":data, "test":grades_serializer.data}, status=status.HTTP_200_OK)

    # grade, type, year, degree, unit, student, teacher_subject
    def post(self, request, student_pk=None, year=timezone.now().year, format=None):
        request.data["year"] = timezone.now().year
        grade_serializer = GradeSerializer(data=request.data)
        grade_serializer.is_valid(raise_exception=True)
        grade_serializer.save()
        return Response({"detail":"Nota atribuída.", "grade":grade_serializer.data}, status=status.HTTP_201_CREATED)


















@api_view(['GET'])
def hello_world(request):
    test = {}
    names = TimeSchedule.Hours.names
    values = TimeSchedule.Hours.values
    for i in range(len(names)):
        test[names[i]] = values[i]

    return Response({"message": test})
