from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from enum import Enum

class User(AbstractUser):
    name = models.CharField(max_length=70)
    email = models.CharField(max_length=70)

    class Types(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    base_type = Types.STUDENT
    type = models.CharField(max_length=50, choices=Types.choices)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = self.base_type
            return super().save(*args, **kwargs)

class AlunoManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.STUDENT)

class Aluno(User):
    base_type = User.Types.STUDENT
    objects = AlunoManager()

    class Meta:
        proxy = True

class ProfessorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs) -> models.QuerySet:
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.TEACHER)

class Professor(User):
    base_type = User.Types.TEACHER
    objects = ProfessorManager()

    class Meta:
        proxy = True

class Turma(models.Model):
    name = models.CharField(max_length=50)
    degree = models.IntegerField()

class Disciplina(models.Model):
    name = models.CharField(max_length=70)

class Comunicado(models.Model):
    title = models.CharField(max_length=70)
    body = models.CharField(max_length=2000)

class Grade(Enum):
    NANA = "NA"
    NAPA = "NA"
    PANA = "NA"
    NAA = "NA"
    ANA = "NA"
    PAPA = "PA"
    PAA = "A"
    APA = "A"
    AA = "A"

class Conceito(models.Model):
    class Grades(models.TextChoices):
        NA = "NA", "NA"
        PA = "PA", "PA"
        A  = "A", "A"

    @classmethod
    def get_final_grade(cls, av1: str, av2: str, default=None):
        final = av1 + av2
        try:
            return Grade[final].value
        except:
            return default

    first_grade = models.CharField(max_length=2, choices=Grades.choices)
    second_grade = models.CharField(max_length=2, choices=Grades.choices)
