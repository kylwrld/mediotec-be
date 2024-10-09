# Generated by Django 5.1 on 2024-10-09 21:17

import api.utils
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_grade_unique_together_alter_class_degree_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='user',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='api.notstudent'),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='class_year_teacher_subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classyearteachersubject'),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='api.student'),
        ),
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterField(
            model_name='class',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='grade',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='grade',
            name='teacher_subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='api.teachersubject'),
        ),
        migrations.AlterUniqueTogether(
            name='class',
            unique_together={('name', 'type')},
        ),
    ]
