# Generated by Django 2.0.2 on 2018-06-30 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretask', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prepagecoltask',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, '未就绪'), (1, '未领取'), (2, '已过期'), (3, '已放弃'), (4, '加急'), (5, '进行中'), (7, '已完成'), (9, '已作废')], db_index=True, default=1, verbose_name='任务状态'),
        ),
        migrations.AlterField(
            model_name='prepagecolverifytask',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, '未就绪'), (1, '未领取'), (2, '已过期'), (3, '已放弃'), (4, '加急'), (5, '进行中'), (7, '已完成'), (9, '已作废')], db_index=True, default=1, verbose_name='任务状态'),
        ),
    ]
