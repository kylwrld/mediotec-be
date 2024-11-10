from cloudinary.models import CloudinaryField, CloudinaryResource
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from enum import Enum
from .utils import *
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
from django.utils import timezone

# class UserManager(BaseUserManager):
#     def create_user(self, email, password=None):
#         if email is None:
#             raise TypeError('Users must have an email address.')

#         user = self.model(email=self.normalize_email(email))
#         user.set_password(password)
#         user.birth_date = timezone.now()
#         user.save()

#         return user

#     def create_superuser(self, email, password):
#         if password is None:
#             raise TypeError('Superusers must have a password.')

#         user = self.create_user(email, password)
#         user.type = User.Types.ADMIN
#         user.birth_date = timezone.now()
#         user.is_superuser = True
#         user.is_staff = True
#         user.is_active = True
#         user.save()

#         return user

class User(AbstractUser):
    name = models.CharField(max_length=70, null=False, blank=False)
    email = models.EmailField(max_length=70, unique=True, null=False, blank=False)
    birth_date = models.DateField()
    entry_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True)
    image = CloudinaryField("image", null=True, blank=True)

    # objects = UserManager()

    class Types(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    base_type = Types.STUDENT
    type = models.CharField(max_length=50, choices=Types.choices)

    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = self.base_type
        return super().save(*args, **kwargs)



class NotStudentManager(BaseUserManager):
    cr_admin = Q(type__contains="ADMIN")
    cr_teacher = Q(type__contains="TEACHER")
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(NotStudentManager.cr_admin | NotStudentManager.cr_teacher)

class NotStudent(User):
    base_type = User.Types.ADMIN
    objects = NotStudentManager()

    class Meta:
        proxy = True

# class AdminProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)


class StudentManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.STUDENT)

class Student(User):
    base_type = User.Types.STUDENT
    objects = StudentManager()

    class Meta:
        proxy = True

# class StudentProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)


class TeacherManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.TEACHER)

class Teacher(User):
    base_type = User.Types.TEACHER
    objects = TeacherManager()

    class Meta:
        proxy = True

class Subject(models.Model):
    name = models.CharField(max_length=70)
    teachers = models.ManyToManyField(Teacher, related_name="subjects", through="TeacherSubject")

# PROFESSOR + DISCIPLINA
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['teacher', 'subject']]

# class TeacherProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)


class AdminManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.ADMIN)

class Admin(User):
    base_type = User.Types.ADMIN
    objects = AdminManager()

    class Meta:
        proxy = True


class Class(models.Model):
    class Types(models.TextChoices):
        INFORMATICA = "Informática", "Informática"
        LOGISTICA = "Logística", "Logística"

    class Shifts(models.TextChoices):
        MANHA = "Manhã", "Manhã"
        TARDE = "Tarde", "Tarde"

    name = models.CharField(max_length=50)
    degree = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    type = models.CharField(max_length=11, choices=Types.choices)
    shift = models.CharField(max_length=5, choices=Shifts.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['name', 'type']]

class ClassYear(models.Model):
    _class = models.ForeignKey(Class, related_name="class_years", on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    students = models.ManyToManyField(Student, related_name="class_year", through="StudentClass")
    teacher_subject = models.ManyToManyField(TeacherSubject, related_name="class_year", through="ClassYearTeacherSubject")

    class Meta:
        unique_together = [['_class', 'year']]

class StudentClass(models.Model):
    student = models.ForeignKey(Student, related_name="student_class", on_delete=models.CASCADE)
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['student', 'class_year']]


class Announcement(models.Model):
    title = models.CharField(max_length=70)
    body = models.CharField(max_length=2000)
    fixed = models.BooleanField(default=False, null=True, blank=True)
    user = models.ForeignKey(NotStudent, related_name="announcements", on_delete=models.CASCADE, blank=True)
    class_year = models.ForeignKey(ClassYear, related_name="announcemets", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Comment(models.Model):
    body = models.CharField(max_length=1000)
    announcement = models.ForeignKey(Announcement, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# ALUNO + CONCEITO
class Grade(models.Model):
    class Grades(models.TextChoices):
        NA = "NA", "NA"
        PA = "PA", "PA"
        A  = "A", "A"

    av1_1 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    av2_1 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    noa_1 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    av1_2 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    av2_2 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    noa_2 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    av1_3 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    av2_3 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    noa_3 = models.CharField(max_length=2, choices=Grades.choices, null=True, blank=True)
    year = models.PositiveIntegerField()
    degree = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    # unit = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    student = models.ForeignKey(User, related_name="grades", on_delete=models.CASCADE)
    teacher_subject = models.ForeignKey(TeacherSubject, related_name="grades", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['student', 'year', 'degree', 'teacher_subject']]


class Parent(models.Model):
    name = models.CharField(max_length=70)
    cpf = models.CharField(max_length=14, unique=True)
    student = models.ForeignKey(User, related_name="parents", on_delete=models.CASCADE)

class Phone(models.Model):
    ddd = models.CharField(max_length=2)
    number = models.CharField(max_length=9)
    parent = models.ForeignKey(Parent, related_name="phones", on_delete=models.CASCADE)

# (TURMA + ANO) + (PROFESSOR + DISCIPLINA)
class ClassYearTeacherSubject(models.Model):
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)
    teacher_subject = models.ForeignKey(TeacherSubject, related_name="class_year_teacher_subject", on_delete=models.CASCADE)

    class Meta:
        unique_together = [['class_year', 'teacher_subject']]


# SEGUNDA | TURMA 1A | 7h | 0m  | PROFESSOR 1 | DISCIPLINA 1
# SEGUNDA | TURMA 2A | 7h | 0m  | PROFESSOR 2 | DISCIPLINA 1
# SEGUNDA | TURMA 2A | 7h | 50m | PROFESSOR 2 | DISCIPLINA 1

class TimeSchedule(models.Model):
    class Days(models.TextChoices):
        SEGUNDA = "SEGUNDA", "SEGUNDA"
        TERCA = "TERCA", "TERCA"
        QUARTA = "QUARTA", "QUARTA"
        QUINTA = "QUINTA", "QUINTA"
        SEXTA = "SEXTA", "SEXTA"
        SABADO = "SABADO", "SABADO"
        DOMINGO = "DOMINGO", "DOMINGO"

    # day = models.CharField(max_length=7, choices=Days.choices)
    hour = models.IntegerField(validators=[MinValueValidator(7), MaxValueValidator(18)])
    minute = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(59)])

    monday_class_year_teacher_subject = models.ForeignKey(
        ClassYearTeacherSubject, on_delete=models.CASCADE, null=True, blank=True, related_name="monday")
    tuesday_class_year_teacher_subject = models.ForeignKey(
        ClassYearTeacherSubject, on_delete=models.CASCADE, null=True, blank=True, related_name="tuesday")
    wednesday_class_year_teacher_subject = models.ForeignKey(
        ClassYearTeacherSubject, on_delete=models.CASCADE, null=True, blank=True, related_name="wednesday")
    thursday_class_year_teacher_subject = models.ForeignKey(
        ClassYearTeacherSubject, on_delete=models.CASCADE, null=True, blank=True, related_name="thursday")
    friday_class_year_teacher_subject = models.ForeignKey(
        ClassYearTeacherSubject, on_delete=models.CASCADE, null=True, blank=True, related_name="friday")

    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = [['hour', 'minute', 'class_year']]

class Attendance(models.Model):
    class Types(models.TextChoices):
        FALTA = "FALTA", "FALTA"
        JUSTIFICADA = "JUSTIFICADA", "JUSTIFICADA"
        PRESENTE = "PRESENTE", "PRESENTE"

    type = models.CharField(max_length=11, choices=Types.choices)
    student = models.ForeignKey(Student, related_name="attendances", on_delete=models.CASCADE)
    class_year_teacher_subject = models.ForeignKey(ClassYearTeacherSubject, on_delete=models.CASCADE)
    day = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["student", "class_year_teacher_subject", "day"]]


# class Hours(models.Choices):
#     M1 = (7, 0)
#     M2 = (7, 50)
#     M3 = (8, 40)
#     M4 = (10, 0)
#     M5 = (10, 50)
#     M6 = (11, 40)
#     M7 = (12, 30)

#     T1 = (13, 40)
#     T2 = (14, 30)
#     T3 = (15, 20)
#     T4 = (16, 40)
#     T5 = (17, 30)
#     T6 = (18, 20)
#     T7 = (19, 10)
