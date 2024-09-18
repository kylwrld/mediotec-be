from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from enum import Enum
from .utils import *
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q

class User(AbstractUser):
    name = models.CharField(max_length=70, null=False, blank=False)
    email = models.EmailField(max_length=70, unique=True, null=False, blank=False)

    class Types(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    base_type = Types.STUDENT
    type = models.CharField(max_length=50, choices=Types.choices)

    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

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

class Subject(models.Model):
    name = models.CharField(max_length=70)

class TeacherManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.TEACHER)

class Teacher(User):
    base_type = User.Types.TEACHER
    objects = TeacherManager()

    class Meta:
        proxy = True

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
    name = models.CharField(max_length=50)
    degree = models.IntegerField(validators=[validate_range(1, 3)])

class ClassYear(models.Model):
    _class = models.ForeignKey(Class, related_name="class_years", on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    students = models.ManyToManyField(Student, related_name="class_year", through="StudentClass")
    teacher_subject = models.ManyToManyField(TeacherSubject, related_name="class_year", through="ClassYearTeacherSubject")

    class Meta:
        unique_together = [['_class', 'year']]

class StudentClass(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['student', 'class_year']]



class Announcement(models.Model):
    title = models.CharField(max_length=70)
    body = models.CharField(max_length=2000)
    fixed = models.BooleanField(null=True, blank=True)
    user = models.ForeignKey(NotStudent, related_name="announcements", on_delete=models.DO_NOTHING)
    class_year = models.ForeignKey(ClassYear, related_name="announcemets", on_delete=models.CASCADE, null=True)


class Comment(models.Model):
    body = models.CharField(max_length=1000)
    announcement = models.ForeignKey(Announcement, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="comments", on_delete=models.DO_NOTHING)


# ALUNO + CONCEITO
class Grade(models.Model):
    class Grades(models.TextChoices):
        NA = "NA", "NA"
        PA = "PA", "PA"
        A  = "A", "A"

    class Types(models.TextChoices):
        AV1 = "AV1", "AV1"
        AV2 = "AV2", "AV2"
        NOA  = "NOA", "NOA"
        NOA_FINAL = "NOA_FINAL", "NOA_FINAL"

    @classmethod
    def get_final_grade(cls, av1: str, av2: str, default=None):
        final = av1 + av2
        try:
            return EGrade[final].value
        except:
            return default

    grade = models.CharField(max_length=2, choices=Grades.choices)
    type = models.CharField(max_length=9, choices=Types.choices)
    year = models.PositiveIntegerField()
    degree = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    unit = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    student = models.ForeignKey(User, related_name="grades", on_delete=models.DO_NOTHING)
    teacher_subject = models.ForeignKey(TeacherSubject, related_name="grades", on_delete=models.DO_NOTHING)


class Parent(models.Model):
    name = models.CharField(max_length=70)
    cpf = models.CharField(max_length=14, unique=True)
    student = models.ForeignKey(User, related_name="parents", on_delete=models.CASCADE)

class Phone(models.Model):
    ddd = models.CharField(max_length=2)
    number = models.CharField(max_length=9)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

# (TURMA + ANO) + (PROFESSOR + DISCIPLINA)
class ClassYearTeacherSubject(models.Model):
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['class_year', 'teacher_subject']]


# SEGUNDA | TURMA 1A | 7h | 0m  | PROFESSOR 1 | DISCIPLINA 1
# SEGUNDA | TURMA 2A | 7h | 0m  | PROFESSOR 2 | DISCIPLINA 1
# SEGUNDA | TURMA 2A | 7h | 50m | PROFESSOR 2 | DISCIPLINA 1

class TimeSchedule(models.Model):
    day = models.CharField(max_length=7)
    hour = models.IntegerField(validators=[MinValueValidator(7), MaxValueValidator(18)])
    minute = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(59)])
    class_year_teacher_subject = models.ForeignKey(ClassYearTeacherSubject, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['day', 'hour', 'minute', 'class_year_teacher_subject']]


# X | PROFESSOR/ADMIN + COMUNICADO

# PARTIALLY | COMENTARIO + COMUNICADO

# PARTIALLY | COMENTARIO + USER

# # CONCEITO + DISCIPLINA
# class GradeSubject(models.Model):
#     grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = ('grade', 'subject')

# ADMINPROFILE + ADMIN
# PROFESSORPROFILE + PROFESSOR
# ALUNOPROFILE + ALUNO
