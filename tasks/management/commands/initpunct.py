from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = Staff.objects.get(username='admin')

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷

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
            reelcorrecttext = ReelCorrectText.objects.filter(reel=huayan_cb_1)[0]
            punct = Punct.objects.filter(reel=huayan_cb_1)[0]
            punctuation_json = punct.punctuation
        except:
            huayan_cb_1 = Reel(sutra=huayan_cb, reel_no=1, start_vol=14,
            start_vol_page=31, end_vol=14, end_vol_page=37, edition_type=Reel.EDITION_TYPE_BASE)
            huayan_cb_1.save()
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_punct.txt' % huayan_cb.sid)
            with open(filename, 'r') as f:
                text = f.read()
            punctuation, text = extract_punct(text)
            reelcorrecttext = ReelCorrectText(reel=huayan_cb_1, text=text)
            reelcorrecttext.save()
            punctuation_json = json.dumps(punctuation, separators=(',', ':'))
            punct = Punct(reel=huayan_cb_1, reeltext=reelcorrecttext, punctuation=punctuation_json)
            punct.save()

        # create BatchTask
        batch_task = BatchTask.objects.all()[0]

        YB = Tripitaka.objects.get(code='YB')
        huayan_yb = Sutra.objects.get(sid='YB000860')
        huayan_yb_1 = Reel.objects.get(sutra=huayan_yb, reel_no=1)

        # 标点
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_PUNCT).delete()

        task1 = Task(id=7, batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_cb_1,
        reeltext=reelcorrecttext, result=punctuation_json,
        task_no=1, status=Task.STATUS_READY,
        publisher=admin, picker=admin)
        task1.save()
        task2 = Task(id=8, batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_cb_1,
        reeltext=reelcorrecttext, result=punctuation_json,
        task_no=2, status=Task.STATUS_READY,
        publisher=admin, picker=admin)
        task2.save()

        task1 = Task(id=9, batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_yb_1,
        task_no=1, status=Task.STATUS_NOT_READY,
        publisher=admin, picker=admin)
        task1.save()
        task2 = Task(id=10, batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_yb_1,
        task_no=2, status=Task.STATUS_NOT_READY,
        publisher=admin, picker=admin)
        task2.save()

        # punct_tasks = list(Task.objects.filter(reel=huayan_yb_1, typ=Task.TYPE_PUNCT, status=Task.STATUS_NOT_READY))
        # if len(punct_tasks) > 0:
        #     task_puncts = Punct.create_new(huayan_cb_1, reelcorrecttext)
        #     punct = Punct(reel=huayan_cb_1, reeltext=reelcorrecttext, punctuation=task_puncts)
        #     punct.save()
        #     punct_task_ids = [task.id for task in punct_tasks]
        #     Task.objects.filter(id__in=punct_task_ids).update(reeltext=reelcorrecttext, result=task_puncts, status=Task.STATUS_READY)

