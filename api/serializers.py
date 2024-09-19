from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "type"]
        read_only_fields = ("id",)

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ["id", "name", "cpf", "student"]
        read_only_fields = ("id", "student")


# CREATE USER
class SignupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "type"]
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        type = validated_data.pop("type")
        if type == "STUDENT":
            instance = Student(**validated_data)
        elif type == "TEACHER":
            instance = Teacher(**validated_data)
        elif type == "ADMIN":
            instance = Admin(**validated_data)

        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class SignupStudentSerializer(serializers.ModelSerializer):
    parents = ParentSerializer(read_only=True, many=True)
    class Meta:
        model = Student
        fields = ["id", "name", "email", "password", "parents"]
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        instance = Student(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


# LOGIN USER
class LoginUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password"]
        read_only_fields = ("id",)

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        # need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ("id", "name", "email", "type")

class StudentClassSerializer(serializers.ModelSerializer):
    # student_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = StudentClass
        fields = ["id", "student", "class_year"]
        read_only_fields = ("id",)

# NOT BEING USED
# class ClassSerializerAllStudents(serializers.ModelSerializer):
#     students = StudentSerializer(read_only=True, many=True)

#     class Meta:
#         model = Class
#         fields = ["id", "name", "degree", "students"]
#         read_only_fields = ("id", "name", "degree", "students")

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        # TODO: need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ("id", "name", "email", "type")

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]
        read_only_fields = ("id",)


class TeacherSubjectSerializer(serializers.ModelSerializer):
    teacher_field = TeacherSerializer(read_only=True, source="teacher")
    class Meta:
        model = TeacherSubject
        fields = ["id", "teacher", "subject", "teacher_field"]
        read_only_fields = ("id",)

class TeacherSubjectSerializerReadOnly(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    class Meta:
        model = TeacherSubject
        fields = ["id", "teacher", "subject"]
        read_only_fields = ("id",)


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name", "degree"]
        read_only_fields = ("id",)

class ClassYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassYear
        fields = ["id", "_class", "year"]
        read_only_fields = ("id",)

class ClassYearSerializerAllStudents(serializers.ModelSerializer):
    students = StudentSerializer(read_only=True, many=True)
    class Meta:
        model = ClassYear
        fields = ["id", "_class", "year", "students"]
        read_only_fields = ("id", "students")

class ClassYearSerializerAllTeachers(serializers.ModelSerializer):
    teacher_subject = TeacherSubjectSerializerReadOnly(read_only=True, many=True)
    class Meta:
        model = ClassYear
        fields = ["id", "_class", "year", "teacher_subject"]
        read_only_fields = ("id", "teacher_subject")

class ClassYearTeacherSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassYearTeacherSubject
        fields = ["id", "class_year", "teacher_subject"]
        read_only_fields = ("id",)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "body", "announcement", "user"]
        read_only_fields = ("id",)

class AnnouncementSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Announcement
        fields = ["id", "title", "body", "fixed", "user", "class_year", "comments"]
        read_only_fields = ("id",)

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "grade", "type", "year", "degree", "unit", "student", "teacher_subject"]
        read_only_fields = ("id",)

    # grade = models.CharField(max_length=2, choices=Grades.choices)
    # type = models.CharField(max_length=9, choices=Types.choices)
    # year = models.PositiveIntegerField()
    # degree = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    # unit = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    # student = models.ForeignKey(User, related_name="grades", on_delete=models.DO_NOTHING)
    # teacher_subject = models.ForeignKey(TeacherSubject, related_name="grades", on_delete=models.DO_NOTHING)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

class TimeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSchedule
        fields = ["day"]
