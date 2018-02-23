from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *
from .init import save_reel, get_reel

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def save_reel_with_correct_text(lqsutra, sid, reel_no, start_vol, start_vol_page, end_vol_page,
    path1='', path2='', path3=''):
    reel, reel_ocr_text = save_reel(lqsutra, sid, reel_no, start_vol, start_vol_page, end_vol_page, \
    path1, path2, path3)
    try:
        reel_correct_text = ReelCorrectText.get(reel=reel)
    except:
        filename = os.path.join(settings.BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % sid)
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
            ReelCorrectText(reel=reel, text=text).save()

    # 得到精确的切分数据
    try:
        compute_accurate_cut(reel)
    except Exception:
        traceback.print_exc()

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = Staff.objects.get(username='admin')

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        # CBETA第1卷
        huayan_cb_1 = get_reel('CB002780', 1)
        if not huayan_cb_1:
            print('please run ./manage.py import_cbeta_huayan60')
            return

        save_reel_with_correct_text(lqsutra, 'QL000870', 1, 24, 1, 17, '24')
        save_reel_with_correct_text(lqsutra, 'ZH000860', 1, 12, 1, 12, '12')
        save_reel_with_correct_text(lqsutra, 'GL000790', 1, 0, 1, 21, '79', '1')
        save_reel_with_correct_text(lqsutra, 'QS000810', 1, 21, 449, 461, '21')
        save_reel_with_correct_text(lqsutra, 'ZC000780', 1, 10, 21, 48, '10')
        save_reel_with_correct_text(lqsutra, 'SX000770', 1, 956, 2, 38, '956')
        save_reel_with_correct_text(lqsutra, 'PL000810', 1, 1114, 2, 25, '1114')

        # get LQReel
        try:
            lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=1)
        except:
            # create LQReel
            lqreel = LQReel(lqsutra=lqsutra, reel_no=1)
            lqreel.save()

        YB = Tripitaka.objects.get(code='YB')
        huayan_yb = Sutra.objects.get(sid='YB000860')
        huayan_yb_1 = Reel.objects.get(sutra=huayan_yb, reel_no=1)
        ReelCorrectText.objects.filter(reel=huayan_yb_1).delete()

        # create BatchTask
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        reel_no = 1
        batch_task = BatchTask.objects.all()[0]

        # 校勘判取
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_JUDGE).delete()
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_JUDGE_VERIFY).delete()
        ReelDiff.objects.all().delete()

        task1 = Task(id=4, batch_task=batch_task, typ=Task.TYPE_JUDGE, lqreel=lqreel, base_reel=huayan_cb_1, task_no=1, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task1.lqreel = lqreel
        task1.save()

        task2 = Task(id=5, batch_task=batch_task, typ=Task.TYPE_JUDGE, lqreel=lqreel, base_reel=huayan_cb_1, task_no=2, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task2.lqreel = lqreel
        task2.save()

        task3 = Task(id=6, batch_task=batch_task, typ=Task.TYPE_JUDGE_VERIFY, lqreel=lqreel, base_reel=huayan_cb_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task3.lqreel = lqreel
        task3.save()

        correct_task = Task.objects.get(pk=3)
        filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % 'YB000860')
        with open(filename, 'r', encoding='utf-8') as f:
            correct_text = f.read()
            correct_task.result = correct_text
            Task.objects.filter(id=correct_task.id).update(result=correct_text)
            ReelCorrectText.objects.filter(task=correct_task).delete()
            publish_correct_result(correct_task)

            task1.status = Task.STATUS_PROCESSING
            task1.picker = admin
            task1.picked_at = timezone.now()
            task1.save(update_fields=['status', 'picker', 'picked_at'])

        #     # 得到精确的切分数据
        #     try:
        #         compute_accurate_cut(correct_task.reel)
        #     except Exception:
        #         traceback.print_exc()

        # tasks = list(Task.objects.filter(id__in=[4, 5]).all())
        # for task in tasks:
        #     for diffseg in task.reeldiff.diffseg_set.all():
        #         diffsegtexts = list(DiffSegText.objects.filter(diffseg=diffseg, tripitaka=YB))
        #         if len(diffsegtexts) == 1:
        #             diffsegresult = DiffSegResult.objects.get(task=task, diffseg=diffseg)
        #             diffsegresult.selected_text = diffsegtexts[0].text
        #             diffsegresult.selected = 1
        #             diffsegresult.save()
