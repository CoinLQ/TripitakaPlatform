# Generated by Django 2.0.1 on 2018-08-07 06:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tsdata', '0004_auto_20180805_1110'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lqreel',
            old_name='is_exist',
            new_name='is_existed',
        ),
    ]
