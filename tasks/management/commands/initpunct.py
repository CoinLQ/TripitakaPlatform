from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *
from tasks.utils.punct_process import PunctProcess
import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def create_punct_task(sid, reel_no, batch_task):
    tcode = sid[:2]
    tripitaka = Tripitaka.objects.get(code=tcode)
    sutra = Sutra.objects.get(sid=sid)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reel_correct_text = ReelCorrectText.objects.filter(reel=reel)[0]
    try:
        punct = Punct.objects.get(reeltext=reel_correct_text)
        task_puncts = punct.punctuation
    except:
        text = SEPARATORS_PATTERN.sub('', reel_correct_text.text)
        task_puncts = PunctProcess.create_new(reel, text)
        punct = Punct(reel=reel, reeltext=reel_correct_text, punctuation=task_puncts)
        punct.save()

    for task_no in [1, 2]:
        task = Task(batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=reel,
        reeltext=reel_correct_text, result=task_puncts,
        task_no=task_no, status=Task.STATUS_PROCESSING,
        publisher=batch_task.publisher, picker=batch_task.publisher)
        task.save()

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = Staff.objects.get(username='admin')

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷

        # CBETA第1卷
        CB = Tripitaka.objects.get(code='CB')
        huayan_cb = Sutra.objects.get(sid='CB002780')
        huayan_cb_1 = Reel.objects.get(sutra=huayan_cb, reel_no=1)
        reelcorrecttext = ReelCorrectText.objects.filter(reel=huayan_cb_1)[0]
        punct = Punct.objects.filter(reel=huayan_cb_1)[0]
        punctuation_json = punct.punctuation

        # create BatchTask
        batch_task = BatchTask.objects.all()[0]

        # 标点
        Task.objects.filter(batch_task=batch_task, typ=Task.TYPE_PUNCT).delete()

        task1 = Task(batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_cb_1,
        reeltext=reelcorrecttext, result=punctuation_json,
        task_no=1, status=Task.STATUS_PROCESSING,
        publisher=admin, picker=admin)
        task1.save()
        task2 = Task(batch_task=batch_task, typ=Task.TYPE_PUNCT, reel=huayan_cb_1,
        reeltext=reelcorrecttext, result=punctuation_json,
        task_no=2, status=Task.STATUS_READY, publisher=admin)
        task2.save()

        create_punct_task('YB000860', 1, batch_task)
        create_punct_task('ZH000860', 1, batch_task)
        create_punct_task('QL000870', 1, batch_task)