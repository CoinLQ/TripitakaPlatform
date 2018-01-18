from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from sutradata.models import *
from tasks.models import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

from difflib import SequenceMatcher
import re, json


class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        admin = User.objects.create_superuser('admin', 'admin@example.com', 'longquan')
        # create LQSutra
        lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
        lqsutra.save()

        # create Sutra
        YB = Tripitaka.objects.get(code='YB')
        huayan_yb = Sutra(sid='YB000860', tripitaka=YB, code='00086', variant_code='0',
        name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
        huayan_yb.save()

        # 永乐北藏第1卷的文本
        huayan_yb_1 = Reel(sutra=huayan_yb, reel_no=1, start_vol=27,
        start_vol_page=1, end_vol=27, end_vol_page=23)
        filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_yb.sid)
        with open(filename, 'r') as f:
            huayan_yb_1.text = f.read()
        huayan_yb_1.save()

        page_texts = huayan_yb_1.text.split('p\n')
        page_count = len(page_texts)

        vol_no = 27
        page_no = 1
        while page_no < page_count:
            pid = '%sv%03dp%04d0' % (huayan_yb.sid, vol_no, page_no)
            page = Page(pid=pid, reel=huayan_yb_1, vol_no=vol_no,
            page_no=page_no, text=page_texts[page_no])
            page.save()
            page_no += 1

        # create LQReel
        lqreel = LQReel(lqsutra=lqsutra, reel_no=1)
        lqreel.save()

        # 高丽第1卷
        GL = Tripitaka.objects.get(code='GL')
        huayan_gl = Sutra(sid='GL000800', tripitaka=GL, code='00080', variant_code='0',
        name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
        huayan_gl.save()
        huayan_gl_1 = Reel(sutra=huayan_gl, reel_no=1, start_vol=14,
        start_vol_page=31, end_vol=14, end_vol_page=37)
        filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_gl.sid)
        with open(filename, 'r') as f:
            huayan_gl_1.text = f.read()
        huayan_gl_1.save()

        # create BatchTask
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        batch_task = BatchTask(priority=priority, publisher=admin)
        batch_task.save()

        # create Tasks
        # Correct Task
        separators = Reel.extract_page_line_separators(huayan_yb_1.text)
        separators_json = json.dumps(separators, separators=(',', ':'))

        # 文字校对
        compare_reel = CompareReel(reel=huayan_yb_1, base_reel=huayan_gl_1)
        compare_reel.save()

        task1 = Task(batch_task=batch_task, typ=1, base_reel=huayan_gl_1, task_no=1, status=Task.STATUS_READY,
        publisher=admin)
        task1.compare_reel = compare_reel
        task1.separators = separators_json
        task1.reel = huayan_yb_1
        task1.save()

        task2 = Task(batch_task=batch_task, typ=1, base_reel=huayan_gl_1, task_no=2, status=Task.STATUS_READY,
        publisher=admin)
        task2.compare_reel = compare_reel
        task2.separators = separators_json
        task2.reel = huayan_yb_1
        #task2.base_reel = huayan_gl_1
        task2.save()

        task3 = Task(batch_task=batch_task, typ=2, base_reel=huayan_gl_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task3.compare_reel = compare_reel
        #task3.separators = separators_json
        task3.reel = huayan_yb_1
        task3.save()
        
        diff_lst = CompareReel.generate_compare_reel(huayan_gl_1.text, huayan_yb_1.text)
        #compare_segs = []
        for tag, base_pos, pos, base_text, ocr_text in diff_lst:
            compare_seg = CompareSeg(compare_reel=compare_reel,
            base_pos=base_pos,
            ocr_text=ocr_text, base_text=base_text)
            compare_seg.save()
            correct_seg = CorrectSeg(task=task1, compare_seg=compare_seg)
            correct_seg.selected_text = compare_seg.ocr_text
            correct_seg.position = pos
            correct_seg.save()
            correct_seg = CorrectSeg(task=task2, compare_seg=compare_seg)
            correct_seg.selected_text = compare_seg.ocr_text
            correct_seg.position = pos
            correct_seg.save()
            #compare_segs.append(compare_seg)
            


