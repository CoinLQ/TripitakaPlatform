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
        YB = Tripitaka.objects.get(code='YB')
        try:
            huayan_yb = Sutra.objects.get(sid='YB000860')
        except:
            huayan_yb = Sutra(sid='YB000860', tripitaka=YB, code='00086', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_yb.save()

        # 永乐北藏第1卷的文本
        try:
            huayan_yb_1 = Reel.objects.get(sutra=huayan_yb, reel_no=1)
        except:
            huayan_yb_1 = Reel(sutra=huayan_yb, reel_no=1, start_vol=27,
            start_vol_page=1, end_vol=27, end_vol_page=23, edition_type=Reel.EDITION_TYPE_CHECKED,
            path1='27')
            huayan_yb_1.save()

        try:
            reel_ocr_text_yb_1 = ReelOCRText.objects.get(reel=huayan_yb_1)
        except:
            text = get_reel_text(huayan_yb_1)
            reel_ocr_text_yb_1 = ReelOCRText(reel=huayan_yb_1, text = text)
            reel_ocr_text_yb_1.save()

        # 高丽第1卷
        GL = Tripitaka.objects.get(code='GL')
        try:
            huayan_gl = Sutra.objects.get(sid='GL000800')
        except:
            huayan_gl = Sutra(sid='GL000800', tripitaka=GL, code='00080', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_gl.save()
        try:
            huayan_gl_1 = Reel.objects.get(sutra=huayan_gl, reel_no=1)
        except:
            huayan_gl_1 = Reel(sutra=huayan_gl, reel_no=1, start_vol=14,
            start_vol_page=31, end_vol=14, end_vol_page=37, edition_type=Reel.EDITION_TYPE_CHECKED,
            path1='80', path2='1')
            huayan_gl_1.save()

        try:
            reelcorrecttext_gl = ReelCorrectText.objects.get(reel=huayan_gl_1)
        except:
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_gl.sid)
            with open(filename, 'r') as f:
                text = f.read()
                reelcorrecttext_gl = ReelCorrectText(reel=huayan_gl_1, text=text)
                reelcorrecttext_gl.save()

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
        task1 = Task(id=1, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1, task_no=1, status=Task.STATUS_READY,
        publisher=admin, picker=admin)
        task1.reel = huayan_yb_1
        task1.save()

        task2 = Task(id=2, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1, task_no=2, status=Task.STATUS_READY,
        publisher=admin, picker=admin)
        task2.reel = huayan_yb_1
        task2.save()

        task3 = Task(id=3, batch_task=batch_task, typ=Task.TYPE_CORRECT_VERIFY, base_reel=huayan_gl_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin, picker=admin)
        task3.reel = huayan_yb_1
        task3.save()
        
        correctsegs = OCRCompare.generate_compare_reel(reelcorrecttext_gl.text, reel_ocr_text_yb_1.text)
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
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % huayan_yb.sid)
            with open(filename, 'r') as f:
                text = f.read()
                reelcorrecttext = ReelCorrectText(reel=huayan_yb_1, text=text)
                reelcorrecttext.save()

        # 得到精确的切分数据
        try:
            compute_accurate_cut(huayan_yb_1)
        except Exception:
            traceback.print_exc()




