from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from enum import Enum
from .utils import validate_range

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
    students = models.ManyToManyField(Student, related_name="_class", through="StudentClass")

class Subject(models.Model):
    name = models.CharField(max_length=70)

class Announcement(models.Model):
    title = models.CharField(max_length=70)
    body = models.CharField(max_length=2000)
    user = models.ForeignKey(User, related_name="announcements", on_delete=models.DO_NOTHING)

class EGrade(Enum):
    NANA = "NA"
    NAPA = "NA"
    PANA = "NA"
    NAA = "NA"
    ANA = "NA"
    PAPA = "PA"
    PAA = "A"
    APA = "A"
    AA = "A"

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
    degree = models.IntegerField(validators=[validate_range(1, 3)])
    unit = models.IntegerField(validators=[validate_range(1, 3)])
    student = models.ForeignKey(User, related_name="grades", on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, related_name="grades", on_delete=models.DO_NOTHING)

class Parent(models.Model):
    name = models.CharField(max_length=70)
    cpf = models.CharField(max_length=14)
    student = models.ForeignKey(User, related_name="parents", on_delete=models.CASCADE)

class Comment(models.Model):
    body = models.CharField(max_length=1000)
    announcement = models.ForeignKey(Announcement, related_name="comments", on_delete=models.CASCADE)

# ALUNO + TURMA
class StudentClass(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    _class = models.ForeignKey(Class, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['student', '_class']]


# PROFESSOR + DISCIPLINA
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'subject',)

# TURMA + (PROFESSOR + DISCIPLINA)
class ClassTeacherSubject(models.Model):
    _class = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('_class', 'teacher_subject')

# class TimeSchedule(models.Model):
#     class_teacher_subject = models.ForeignKey(ClassTeacherSubject, on_delete=models.CASCADE)
#     hour = models.IntegerField(validators=[validate_range(7, 18)])
#     minute = models.IntegerField(validators=[validate_range(0, 59)])


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
