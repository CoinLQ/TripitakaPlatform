# Generated by Django 2.0.2 on 2018-05-21 01:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rect', '0003_auto_20180427_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagetask',
            name='pagerect',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rect.PageRect'),
        ),
    ]