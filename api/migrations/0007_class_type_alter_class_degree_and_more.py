# Generated by Django 5.1 on 2024-09-28 02:09

import api.utils
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_announcement_created_at_announcement_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='class',
            name='type',
            field=models.CharField(choices=[('INFORMATICA', 'INFORMATICA'), ('LOGISTICA', 'LOGISTICA')], default='INFORMATICA', max_length=11),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
        migrations.AlterField(
            model_name='studentclass',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_class', to='api.student'),
        ),
    ]
