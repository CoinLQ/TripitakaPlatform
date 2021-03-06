# Generated by Django 2.0.2 on 2018-03-30 07:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='batchtask',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.BatchTask', verbose_name='批次号'),
        ),
        migrations.AlterField(
            model_name='task',
            name='typ',
            field=models.SmallIntegerField(choices=[(1, '文字校对'), (2, '文字校对审定'), (3, '校勘判取'), (4, '校勘判取审定'), (5, '基础标点'), (6, '基础标点审定'), (7, '定本标点'), (8, '定本标点审定'), (9, '格式标注'), (10, '格式标注审定')], db_index=True, verbose_name='任务类型'),
        ),
    ]
