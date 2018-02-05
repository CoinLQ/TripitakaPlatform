from django.db.models import Min, Sum
from django.db import connection, transaction
from celery import shared_task
from cutrect import email_if_fails
from rect.models import Schedule, Schedule_Task_Statistical, SliceType, \
                        CharClassifyPlan, allocateTasks, CCTask, ClassifyTask, \
                        DelTask, PageTask, ReviewTask, AbsentTask, TaskStatus

class GenTask(object):

    @shared_task
    @email_if_fails
    def gen_classifytask_by_plan():
        with transaction.atomic():
            for stask in Schedule_Task_Statistical.objects.filter(amount_of_classifytasks=-1):
                # 检查所有准备表的wcc_threshold值都大于0，开启总计划。
                if CharClassifyPlan.objects.filter(wcc_threshold__lte=0).count() > 0:
                    continue
                count = allocateTasks(stask.schedule, None, SliceType.CLASSIFY)
                stask.amount_of_classifytasks = count
                stask.save(update_fields=['amount_of_classifytasks'])

    @shared_task
    @email_if_fails
    def gen_vdeltask():
        schedule = Schedule.objects.first()
        allocateTasks(schedule, None, SliceType.VDEL)


    @shared_task(ignore_result=True)
    @email_if_fails
    def clean_daily_emergeTask():
        for task in [CCTask, ClassifyTask, DelTask, PageTask, ReviewTask, AbsentTask]:
            task.objects.filter(status=TaskStatus.EMERGENCY).update(status=TaskStatus.EXPIRED)