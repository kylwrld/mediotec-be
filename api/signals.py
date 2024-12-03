from django.db.models. signals import post_save
from django.dispatch import receiver
from .models import Announcement, ClassYear
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone


# @receiver(post_save, sender=Announcement, dispatch_uid="notify_users_email")
# def notify_users_email(sender, instance: Announcement, created, **kwargs):
#     if created:
#         context = {
#             "author":instance.user.name,
#             "title":instance.title,
#             "body":instance.body,
#             "created_at":instance.created_at.strftime("%H:%M:%S, %d %m %Y")
#         }
#         template_name = settings.BASE_DIR.joinpath("api\\templates\\email_template.html")
#         convert_to_html_content =  render_to_string(
#             template_name=template_name,
#             context=context
#         )
#         plain_message = strip_tags(convert_to_html_content)
#         try:
#             # only students from a specific classYear
#             class_year = ClassYear.objects.get(id=instance.class_year.id)
#             students_emails = [student.email for student in class_year.students.all()]

#             send = send_mail(
#                 subject="Novo aviso",
#                 message=plain_message,
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=students_emails,
#                 html_message=convert_to_html_content,
#                 fail_silently=True
#             )
#         except:
#             # all students
#             class_years = ClassYear.objects.filter(year=timezone.now().year)
#             all_students = [class_year.students.all() for class_year in class_years]
#             flat_students = []
#             for students in all_students:
#                 for student in students:
#                     flat_students.append(student.email)

#             print(flat_students)
#             send = send_mail(
#                 subject="Novo aviso",
#                 message=plain_message,
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=flat_students,
#                 html_message=convert_to_html_content,
#                 fail_silently=True
#             )


from django.core.mail import get_connection, EmailMultiAlternatives

# it might slow down the server
@receiver(post_save, sender=Announcement, dispatch_uid="notify_users_email")
def notify_users_email(sender, instance: Announcement, created, **kwargs):
    if created:
        context = {
            "author":instance.user.name,
            "title":instance.title,
            "body":instance.body,
            "created_at":instance.created_at.strftime("%H:%M:%S, %d %m %Y")
        }

        connection = get_connection()
        connection.open()

        template_name = settings.BASE_DIR.joinpath("api/templates/email_template.html")
        html_content =  render_to_string(
            template_name=template_name,
            context=context
        )
        plain_message = strip_tags(html_content)

        try:
            # only students from a specific classYear | students_emails
            class_year = ClassYear.objects.get(id=instance.class_year.id)
            students_emails = [student.email for student in class_year.students.all()]

            msg = EmailMultiAlternatives("Novo Aviso", plain_message, settings.EMAIL_HOST_USER, ["noreply@example.com"], bcc=students_emails, connection=connection)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            # all students | flat_students
            class_years = ClassYear.objects.filter(year=timezone.now().year)
            all_students = [class_year.students.all() for class_year in class_years]
            flat_students = []
            for students in all_students:
                for student in students:
                    flat_students.append(student.email)

            plain_message = strip_tags(html_content)
            msg = EmailMultiAlternatives("Novo Aviso", plain_message, settings.EMAIL_HOST_USER, ["noreply@example.com"], bcc=flat_students, connection=connection)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        finally:
            connection.close()
