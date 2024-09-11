from django.urls import path, include
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("signup/", views.Signup.as_view(), name="signup"),
    path("login/", views.Login.as_view(), name="login"),
    path("student/", views.StudentView.as_view(), name="student"),
    path("student/<int:pk>/", views.StudentView.as_view(), name="student_id"),
    path("student-class/<int:class_pk>/", views.StudentClassView.as_view(), name="student_class"),
    path("student-class/<int:student_pk>/<int:class_pk>/", views.StudentClassView.as_view(), name="student_class"),
    path("teacher/", views.TeacherView.as_view(), name="teacher"),
    path("teacher/<int:pk>/", views.TeacherView.as_view(), name="teacher_id"),
    path("subject/", views.SubjectView.as_view(), name="subject"),
    path("teacher_subject/<int:teacher_pk>/<int:subject_pk>/", views.TeacherSubjectView.as_view(), name="teacher_subject"),
    path("class/", views.ClassView.as_view(), name="class"),
    path("class/<int:pk>/", views.ClassView.as_view(), name="class"),

    path("teste/", views.hello_world, name="teste"),
    path("api/token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name='token_refresh')
]
