from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from sutradata.models import *
from tasks.models import *
from sutradata.common import *
from tasks.views.task_controller import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = User.objects.get(username='admin')

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷

        # create Sutra
        QL = Tripitaka.objects.get(code='QL')
        try:
            huayan_ql = Sutra.objects.get(sid='QL000870')
        except:
            huayan_ql = Sutra(sid='QL000870', tripitaka=QL, code='00087', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_ql.save()

        # 乾隆藏第1卷的文本
        try:
            huayan_ql_1 = Reel.objects.get(sutra=huayan_ql, reel_no=1)
        except:
            huayan_ql_1 = Reel(sutra=huayan_ql, reel_no=1, start_vol=24,
            start_vol_page=2, end_vol=24, end_vol_page=17, edition_type=Reel.EDITION_TYPE_CHECKED,
            path1='24')
            huayan_ql_1.save()
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_ql.sid)
            with open(filename, 'r') as f:
                text = f.read()
                reel_ocr_text = ReelOCRText(reel=huayan_ql_1, text = text)
                reel_ocr_text.save()
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % huayan_ql.sid)
            with open(filename, 'r') as f:
                text = f.read()
                ReelCorrectText(reel=huayan_ql_1, text=text).save()

        # CBETA第1卷
        CB = Tripitaka.objects.get(code='CB')
        try:
            huayan_cb = Sutra.objects.get(sid='CB000800')
        except:
            huayan_cb = Sutra(sid='CB000800', tripitaka=CB, code='00080', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_cb.save()
        try:
            huayan_cb_1 = Reel.objects.get(sutra=huayan_cb, reel_no=1)
        except:
            huayan_cb_1 = Reel(sutra=huayan_cb, reel_no=1, start_vol=14,
            start_vol_page=31, end_vol=14, end_vol_page=37, edition_type=Reel.EDITION_TYPE_BASE)
            huayan_cb_1.save()
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_punct.txt' % huayan_cb.sid)
            with open(filename, 'r') as f:
                text = f.read()
            punctuation, text = extract_punct(text)
            reel_ocr_text = ReelOCRText(reel=huayan_cb_1, text = text)
            reel_ocr_text.save()
            
            reelcorrecttext = ReelCorrectText(reel=huayan_cb_1, text=text)
            reelcorrecttext.save()
            punct = Punct(reel=huayan_cb_1, reeltext=reelcorrecttext, punctuation=json.dumps(punctuation))
            punct.save()

        # get LQReel
        try:
            lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=1)
        except:
            # create LQReel
            lqreel = LQReel(lqsutra=lqsutra, reel_no=1)
            lqreel.save()

        # create BatchTask
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        reel_no = 1
        batch_task = BatchTask.objects.all()[0]

        huayan_gl = Sutra.objects.get(sid='GL000800')
        huayan_gl_1 = Reel.objects.get(sutra=huayan_gl, reel_no=1)

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
        #task3.separators = separators_json
        task3.lqreel = lqreel
        task3.save()

        correct_task = Task.objects.get(pk=3)
        filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % 'YB000860')
        with open(filename, 'r') as f:
            correct_text = f.read()
            separators = extract_page_line_separators(correct_text)
            separators_json = json.dumps(separators, separators=(',', ':'))
            correct_task.result = correct_text
            correct_task.separators = separators_json
            Task.objects.filter(id=correct_task.id).update(result=correct_text, separators=separators_json)
            publish_correct_result(correct_task)

            # 得到精确的切分数据
            try:
                compute_accurate_cut(correct_task.reel)
            except Exception:
                traceback.print_exc()

        tasks = list(Task.objects.filter(id__in=[4, 5]).all())
        for task in tasks:
            for diffseg in task.reeldiff.diffseg_set.all():
                diffsegtexts = list(DiffSegText.objects.filter(diffseg=diffseg, tripitaka=CB))
                if len(diffsegtexts) == 1:
                    diffsegresult = DiffSegResult(task=task, diffseg=diffseg, selected_text=diffsegtexts[0].text, selected=1)
                    diffsegresult.save()
