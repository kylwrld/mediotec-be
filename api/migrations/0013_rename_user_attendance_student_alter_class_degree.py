# Generated by Django 5.1.2 on 2024-10-22 01:26

import api.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_class_degree'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendance',
            old_name='user',
            new_name='student',
        ),
        migrations.AlterField(
            model_name='class',
            name='degree',
            field=models.IntegerField(validators=[api.utils.validate_range]),
        ),
    ]
