from django.urls import path, include
from . import views

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

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

    path("student/", views.StudentView.as_view(), name="student"),
    path("student/<int:pk>/", views.StudentView.as_view(), name="student_id"),

    path("student_class/", views.StudentClassView.as_view(), name="student_class"),
    path("student_class/<int:class_pk>/<int:year>/", views.StudentClassView.as_view(), name="student_class_id"),

    path("teacher/", views.TeacherView.as_view(), name="teacher"),
    path("teacher/<int:pk>/", views.TeacherView.as_view(), name="teacher_id"),
    path("teacher/<int:pk>/subjects/", views.TeacherAllSubjects, name="teacher_id_subjects"),
    path("teacher/<int:_class_pk>/<int:year>/<int:teacher_pk>/", views.TeacherAllSubjectsFromClass, name="teacher_subjects_class"),
    path("teacher/<int:pk>/classes/", views.TeacherAllClasses, name="teacher_id_classes"),
    path("teacher/<int:pk>/time_schedule/", views.AllTimeSchedulesFromTeacher, name="teacher_id_time_schedule"),

    path("subject/", views.SubjectView.as_view(), name="subject"),
    path("subject/<int:pk>/", views.SubjectView.as_view(), name="subject_id"),
    path("subject/<int:pk>/teachers/", views.SubjectsAllTeachers, name="subject_teachers"),

    path("teacher_subject/", views.TeacherSubjectView.as_view(), name="teacher_subject"),
    path("teacher_subject/<int:pk>/", views.TeacherSubjectView.as_view(), name="teacher_subject_id"),
    path("all_teacher_subject_class/<int:class_year>/", views.AllTeacherSubjectFromClass, name="all_teacher_subject_class_id"),

    path("class/", views.ClassView.as_view(), name="class"),
    path("class/<int:pk>/", views.ClassView.as_view(), name="class_id"),

    path("class_year/", views.ClassYearView.as_view(), name="class_year"),
    path("class_year/<int:pk>/", views.ClassYearView.as_view(), name="class_year_id"),

    path("class_year_teacher_subject/", views.ClassYearTeacherSubjectView.as_view(), name="class_year_teacher_subject"),
    path("class_year_teacher_subject/<int:class_pk>/<int:year>/", views.ClassYearTeacherSubjectView.as_view(), name="class_year_teacher_subject_id"),

    path("announcement/", views.AnnouncementView.as_view(), name="announcement"),
    path("announcement/<int:pk>/", views.AnnouncementView.as_view(), name="announcement_id"),

    path("comment/", views.CommentView.as_view(), name="comment"),
    path("comment/<int:pk>/", views.CommentView.as_view(), name="comment_id"),

    path("parent/", views.ParentView.as_view(), name="parent"),
    path("parent/<int:student_pk>/", views.ParentView.as_view(), name="parent_id"),

    path("grade/", views.GradeView.as_view(), name="grade"),
    path("grade/<int:student_pk>/<int:year>/", views.GradeView.as_view(), name="grade_id"),

    path("attendance/", views.AttendanceView.as_view(), name="attendance"),
    path("attendance/<int:class_year>/<int:teacher_subject>/", views.AttendanceView.as_view(), name="attendance_id"),

    path("time_schedule/", views.TimeScheduleView.as_view(), name="time_schedule"),

    path("teste/", views.hello_world, name="teste"),

    path("api/token/", views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
