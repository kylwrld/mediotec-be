# Generated by Django 5.1 on 2024-10-10 06:03

import api.utils
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_announcement_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterField(
            model_name='classyearteachersubject',
            name='teacher_subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_year_teacher_subject', to='api.teachersubject'),
        ),
    ]
