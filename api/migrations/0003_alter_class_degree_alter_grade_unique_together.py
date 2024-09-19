# Generated by Django 5.1 on 2024-09-19 18:58

import api.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_notstudent_grade_created_at_grade_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together={('student', 'year', 'degree', 'unit', 'type', 'teacher_subject')},
        ),
    ]
