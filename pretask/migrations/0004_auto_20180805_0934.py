# Generated by Django 2.0.1 on 2018-08-05 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretask', '0003_auto_20180715_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prepagecoltask',
            name='obtain_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='领取时间'),
        ),
        migrations.AlterField(
            model_name='prepagecoltask',
            name='update_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最近处理时间'),
        ),
        migrations.AlterField(
            model_name='prepagecolverifytask',
            name='obtain_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='领取时间'),
        ),
        migrations.AlterField(
            model_name='prepagecolverifytask',
            name='update_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最近处理时间'),
        ),
    ]
