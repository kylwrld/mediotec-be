from rest_framework import serializers
from .models import *

# TO CREATE USER
class SignupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'type']

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
        fields = ['email', 'password']
        # read_only_fields = ('email',)
        # extra_kwargs = {"email": {"null": False}, "password": {"null": False}}

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        # need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ('id', "name", "email", "type")

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        # need to add Class
        fields = ["id", "name", "email", "type"]
        read_only_fields = ('id', "name", "email", "type")

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["name"]

class TeacherSubjectSerializer(serializers.ModelSerializer):
    # teacher = serializers.SerializerMethodField()
    # subject = serializers.SerializerMethodField()

    class Meta:
        model = TeacherSubject
        fields = ["teacher", "subject"]

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["name", "degree"]
