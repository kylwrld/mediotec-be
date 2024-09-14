from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "type"]
        read_only_fields = ('id',)

# CREATE USER
class SignupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", 'name', 'email', 'password', 'type']
        read_only_fields = ('id',)

    def create(self, validated_data):
        password = validated_data.pop('password')
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

# LOGIN USER
class LoginUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", 'email', 'password']
        read_only_fields = ('id',)

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        # need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ('id', "name", "email", "type")

class StudentClassSerializer(serializers.ModelSerializer):
    # student_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = StudentClass
        fields = ["id", "student", "_class"]
        read_only_fields = ('id',)

class ClassSerializerAllStudents(serializers.ModelSerializer):
    students = StudentSerializer(read_only=True, many=True)

    class Meta:
        model = Class
        fields = ["id", "name", "degree", "students"]
        read_only_fields = ("id", "name", "degree", "students")

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        # TODO: need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ('id', "name", "email", "type")

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]
        read_only_fields = ('id',)

class TeacherSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSubject
        fields = ["id", "teacher", "subject"]
        read_only_fields = ('id',)

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name", "degree"]
        read_only_fields = ('id',)

class ClassTeacherSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTeacherSubject
        fields = ["id", "_class", "teacher_subject"]
        read_only_fields = ('id',)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "body", "announcement", "user"]
        read_only_fields = ("id",)

class AnnouncementSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(read_only=True, many=True)
    class Meta:
        model = Announcement
        fields = ["id", "title", "body", "user", "_class", "comments"]
        read_only_fields = ("id",)
