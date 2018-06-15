from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from .init import get_or_create_admin
from .initjudge import save_reel_with_correct_text

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def create_mark_task(sid, reel_no, batchtask):
    tcode = sid[:2]
    tripitaka = Tripitaka.objects.get(code=tcode)
    sutra = Sutra.objects.get(sid=sid)
    reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
    reel_correct_text = ReelCorrectText.objects.filter(reel=reel)[0]

    # try:
    #     mark = Mark.objects.get(reeltext=reel_correct_text)
    # except :
    #     mark = Mark(reel=reel, reeltext=reel_correct_text,  publisher=batchtask.publisher)
    #     mark.save()

    for task_no in [1, 2]:
        task = Task(batchtask=batchtask, typ=Task.TYPE_MARK, reel=reel,
        reeltext=reel_correct_text, result='[]',
        task_no=task_no, status=Task.STATUS_READY,
        publisher=batchtask.publisher)
        task.save()
        mark = Mark(reel=reel, reeltext=reel_correct_text, task=task)
        mark.save()
    task = Task(batchtask=batchtask, typ=Task.TYPE_MARK_VERIFY, reel=reel,
    reeltext=reel_correct_text,
    task_no=0, status=Task.STATUS_NOT_READY, publisher=batchtask.publisher)
    task.save()
    mark = Mark(reel=reel, reeltext=reel_correct_text, task=task)
    mark.save()
    

class Command(BaseCommand):
    def handle(self, *args, **options):
        # from tasks.reeldiff_processor import get_multireeltext
        # sutra = Sutra.objects.get(sid='GL000790')
        # get_multireeltext(sutra)
        # return 
        print('initmark start')
        BASE_DIR = settings.BASE_DIR
        admin = get_or_create_admin()

        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷

        # CBETA第1卷
        CB = Tripitaka.objects.get(code='CB')
        huayan_cb = Sutra.objects.get(sid='CB002780')
        huayan_cb_1 = Reel.objects.get(sutra=huayan_cb, reel_no=1)
        reelcorrecttext = ReelCorrectText.objects.filter(reel=huayan_cb_1)[0]
        #mark = mark.objects.filter(reel=huayan_cb_1)[0]
        markuation_json = '[]'
        # create BatchTask
        batchtask = BatchTask(priority=2, publisher=admin)
        batchtask.save()

        # 格式标注
        save_reel_with_correct_text(lqsutra, 'YB000860', 1, 27, 1, 23, '27')
        save_reel_with_correct_text(lqsutra, 'ZH000860', 1, 12, 1, 12, '12')
        save_reel_with_correct_text(lqsutra, 'QL000870', 1, 24, 1, 17, '24')
        create_mark_task('YB000860', 1, batchtask)
        create_mark_task('ZH000860', 1, batchtask)
        create_mark_task('QL000870', 1, batchtask)
        create_mark_task('CB002780', 1, batchtask)
        create_mark_task('GL000790', 1, batchtask)
        reel_lst = [(lqsutra, 1)]
        from tasks.task_controller import create_tasks_for_batchtask
        create_tasks_for_batchtask(batchtask, reel_lst, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0)
        print('initmark done')
