# Generated by Django 5.1 on 2024-09-14 00:19

import api.utils
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_class_students_alter_class_degree_alter_grade_degree_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classteachersubject',
            name='hour',
        ),
        migrations.RemoveField(
            model_name='classteachersubject',
            name='minutes',
        ),
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterField(
            model_name='grade',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterField(
            model_name='grade',
            name='unit',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.CreateModel(
            name='TimeSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hour', models.IntegerField(validators=[api.utils.validate_range])),
                ('minute', models.IntegerField(validators=[api.utils.validate_range])),
                ('class_teacher_subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classteachersubject')),
            ],
        ),
    ]
