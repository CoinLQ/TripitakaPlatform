# Generated by Django 2.0.2 on 2018-04-13 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_auto_20180410_1557'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diffseg',
            name='diffseg_no',
        ),
    ]