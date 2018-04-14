from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask
from tasks.ocr_compare import OCRCompare

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def get_or_create_admin():
    try:
        admin = Staff.objects.get(username='admin')
    except:
        admin = Staff(email='admin@example.com', username='admin')
        admin.set_password('admin')
        admin.is_admin = True
        admin.save()
    return admin

def save_reel(lqsutra, sid, reel_no, start_vol, start_vol_page, end_vol_page,
    path1='', path2='', path3='', ocr_ready=True, correct_ready=True):
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
        start_vol_page=start_vol_page, end_vol=start_vol, end_vol_page=end_vol_page,
        path1=path1, path2=path2, path3=path3,
        ocr_ready=ocr_ready, correct_ready=correct_ready)
        reel.save()
    try:
        reel_ocr_text = ReelOCRText.objects.get(reel=reel)
    except:
        text = get_reel_text(reel)
        reel_ocr_text = ReelOCRText(reel=reel, text = text)
        reel_ocr_text.save()
    return reel, reel_ocr_text

def get_reel(sid, reel_no):
    try:
        sutra = Sutra.objects.get(sid=sid)
        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
        return reel
    except:
        print('no reel')
        return

class Command(BaseCommand):
    def handle(self, *args, **options):
        print('init start')
        BASE_DIR = settings.BASE_DIR
        admin = get_or_create_admin()

        try:
            lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        except:
            # create LQSutra
            lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
            lqsutra.save()

        save_reel(lqsutra, 'YB000860', 1, 27, 1, 23, '27')

        # create BatchTask
        batchtask = BatchTask(priority=2, publisher=admin)
        batchtask.save()

        # create Tasks
        # 文字校对
        reel_lst = [(lqsutra, 1)]
        create_tasks_for_batchtask(batchtask, reel_lst, 2, 1)
        print('init done')