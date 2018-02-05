from TripitakaPlatform import celery_app
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from rect.lib.gen_task import GenTask


# FIXME: http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
# 目前的版本celery不工作，用admin配置的办法解决。
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every day at 1:02 a.m.
    sender.add_periodic_task(
        crontab(hour='1', minute='02', day_of_week="*"),
        every_morning.s(), name='good morning')

    # Calls gen_vdeltask every 300 seconds
    sender.add_periodic_task(300.0, every_5_minute.s('hello world.'), expires=10)


@celery_app.task
def every_morning():
    GenTask.clean_daily_emergeTask()
    GenTask.gen_classifytask_by_plan()
    return 'good morning'

@celery_app.task
def every_5_minute(arg):
    GenTask.gen_vdeltask()
    return 'ok'

@celery_app.task
def test(arg):
    print(arg)

