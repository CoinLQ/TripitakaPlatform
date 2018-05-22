# Generated by Django 2.0.2 on 2018-05-22 03:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tdata', '0007_tripitaka_bar_line_count'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0010_merge_20180522_1102'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbnormalLineCountTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reel_page_no', models.SmallIntegerField(verbose_name='卷中页序号')),
                ('page_no', models.SmallIntegerField(verbose_name='页序号')),
                ('bar_no', models.SmallIntegerField(verbose_name='第几栏')),
                ('line_count', models.SmallIntegerField(verbose_name='文本行数')),
                ('status', models.SmallIntegerField(choices=[(2, '待领取'), (3, '进行中'), (4, '已完成')], db_index=True, default=2, verbose_name='状态')),
                ('picked_at', models.DateTimeField(blank=True, null=True, verbose_name='领取时间')),
                ('correct_text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.ReelCorrectText')),
                ('picker', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='领取用户')),
                ('reel', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='tdata.Reel', verbose_name='实体藏经卷')),
            ],
            options={
                'verbose_name': '异常文本行数检查任务',
                'verbose_name_plural': '异常文本行数检查任务',
            },
        ),
        migrations.AlterField(
            model_name='markunit',
            name='typ',
            field=models.SmallIntegerField(choices=[(1, '标注'), (2, '存疑标注'), (3, '标注反馈')], default=1, verbose_name='类型'),
        ),
    ]
