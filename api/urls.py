from django.urls import path, include
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("signup/student/", views.SignupStudent.as_view(), name="signup_student"),
    # path("signup/teacher/"),
    # path("signup/admin/"),

    path("signup/", views.Signup.as_view(), name="signup"),
    path("login/", views.Login.as_view(), name="login"),

    # refactored to accept id in body instead of url pattern
    path("student/", views.StudentView.as_view(), name="student"),
    path("student/<int:pk>/", views.StudentView.as_view(), name="student_id"),

    path("student-class/", views.StudentClassView.as_view(), name="student_class"),
    path("student-class/<int:class_pk>/<int:year>/", views.StudentClassView.as_view(), name="student_class"),

    path("teacher/", views.TeacherView.as_view(), name="teacher"),
    path("teacher/<int:pk>/", views.TeacherView.as_view(), name="teacher_id"),
    # TODO: TEACHER SIGNUP VIEW

    path("subject/", views.SubjectView.as_view(), name="subject"),
    path("subject/<int:pk>/", views.SubjectView.as_view(), name="subject_id"),

    path("teacher_subject/", views.TeacherSubjectView.as_view(), name="teacher_subject"),
    path("teacher_subject/<int:pk>/", views.TeacherSubjectView.as_view(), name="teacher_subject_id"),
    path("teacher_subject/", views.TeacherSubjectView.as_view(), name="teacher_subject"),

    path("class/", views.ClassView.as_view(), name="class"),
    path("class/<int:pk>/", views.ClassView.as_view(), name="class_id"),

    path("class-year-teacher-subject/", views.ClassYearTeacherSubjectView.as_view(), name="class_year_teacher_subject"),
    path("class-year-teacher-subject/<int:class_pk>/<int:year>/", views.ClassYearTeacherSubjectView.as_view(), name="class_year_teacher_subject"),

    path("announcement/", views.AnnouncementView.as_view(), name="announcement"),
    path("announcement/<int:pk>/", views.AnnouncementView.as_view(), name="announcement_id"),

    path("comment/", views.CommentView.as_view(), name="comment"),
    path("comment/<int:pk>/", views.CommentView.as_view(), name="comment_id"),


    path("teste/", views.hello_world, name="teste"),

    path("api/token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name='token_refresh')
]
