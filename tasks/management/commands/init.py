from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.ocr_compare import OCRCompare

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def save_reel(lqsutra, sid, reel_no, start_vol, start_vol_page, end_vol_page,
    path1='', path2='', path3=''):
    tcode = sid[:2]
    tripitaka = Tripitaka.objects.get(code=tcode)
    try:
        sutra = Sutra.objects.get(sid=sid)
    except:
        sutra = Sutra(sid=sid, tripitaka=tripitaka, code=sid[2:7], variant_code=sid[7],
        name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
        sutra.save()

    try:
        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    except:
        reel = Reel(sutra=sutra, reel_no=reel_no, start_vol=start_vol,
        start_vol_page=start_vol_page, end_vol=start_vol, end_vol_page=end_vol_page, edition_type=Reel.EDITION_TYPE_CHECKED,
        path1=path1, path2=path2, path3=path3)
        reel.save()
    try:
        reel_ocr_text = ReelOCRText.get(reel=reel)
    except:
        text = get_reel_text(reel)
        reel_ocr_text = ReelOCRText(reel=reel, text = text)
        reel_ocr_text.save()
    return reel, reel_ocr_text

def get_reel(sid, reel_no):
    tcode = sid[:2]
    tripitaka = Tripitaka.objects.get(code=tcode)
    try:
        sutra = Sutra.objects.get(sid=sid)
        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
        return reel
    except:
        print('no reel')
        return

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        try:
            auth.models.User.objects.create_superuser('admin', 'admin@example.com', 'longquan')
        except:
            pass
        try:
            admin = Staff.objects.get(username='admin')
        except:
            admin = Staff(email='admin@example.com', username='admin')
            admin.set_password('admin')
            admin.is_admin = True
            admin.save()

        try:
            lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        except:
            # create LQSutra
            lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
            lqsutra.save()

        # create Sutra
        # Sutra.objects.all().delete()

        # CBETA第1卷
        huayan_cb_1 = get_reel('CB002780', 1)
        if not huayan_cb_1:
            print('please run ./manage.py import_cbeta_huayan60')
            return
        huayan_cb_1_correct_text = ReelCorrectText.objects.get(reel=huayan_cb_1)

        huayan_yb_1, reel_ocr_text_yb_1 = save_reel(lqsutra, 'YB000860', 1, 27, 1, 23, '27')

        # create BatchTask
        BatchTask.objects.all().delete()
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        batch_task = BatchTask(priority=priority, publisher=admin)
        batch_task.save()

        # create Tasks
        # Correct Task
        # 文字校对
        task1 = Task(id=1, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_cb_1, task_no=1, status=Task.STATUS_PROCESSING,
        publisher=admin, picker=admin, picked_at=timezone.now())
        task1.reel = huayan_yb_1
        task1.save()

        task2 = Task(id=2, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_cb_1, task_no=2, status=Task.STATUS_READY,
        publisher=admin)
        task2.reel = huayan_yb_1
        task2.save()

        task3 = Task(id=3, batch_task=batch_task, typ=Task.TYPE_CORRECT_VERIFY, base_reel=huayan_cb_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task3.reel = huayan_yb_1
        task3.save()

        correctsegs = OCRCompare.generate_compare_reel(huayan_cb_1_correct_text.text, reel_ocr_text_yb_1.text)
        tasks = [task1, task2]
        for i in range(2):
            for correctseg in correctsegs:
                correctseg.task = tasks[i]
                correctseg.id = None
            CorrectSeg.objects.bulk_create(correctsegs)

        # 用于测试计算精确切分数据
        try:
            reelcorrecttext = ReelCorrectText.objects.get(reel=huayan_yb_1)
        except:
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % 'YB000860')
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
                reelcorrecttext = ReelCorrectText(reel=huayan_yb_1, text=text)
                reelcorrecttext.save()

        # 得到精确的切分数据
        # try:
        #     compute_accurate_cut(huayan_yb_1)
        # except Exception:
        #     traceback.print_exc()




