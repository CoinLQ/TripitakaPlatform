from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        for sid in options['LQSutra_sid']:
            lqsutra = LQSutra.objects.get(sid=sid)
            tcode_lst = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC', 'GL', 'LC']
            for tcode in tcode_lst:
                tripitaka = Tripitaka.objects.get(code=tcode)
                print(tripitaka)
                for sutra in tripitaka.sutra_set.all():
                    if sutra.lqsutra != lqsutra:
                        continue
                    reel_ocr_text_lst = []
                    for reel in Reel.objects.filter(sutra=sutra, ocr_ready=True):
                        try:
                            reel_ocr_text = ReelOCRText.objects.get(reel_id = reel.id)
                        except:
                            reel_ocr_text = None
                        if reel_ocr_text:
                            print('reel: ', reel)
                            text = get_reel_text(reel)
                            if text:
                                reel_ocr_text.text = text
                                reel_ocr_text.save(update_fields=['text'])

                        # 得到精确的切分数据
                        try:
                            compute_accurate_cut(reel)
                        except Exception:
                            traceback.print_exc()
