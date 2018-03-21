from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

tcode_lst1 = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC']
tcode_lst2 = ['GL', 'LC']

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str)#设置一个龙泉id的参数，支持多个                

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        reel_lst = []
        for lqsutra_sid in options['LQSutra_sid']:
            # get LQSutra
            print(lqsutra_sid)
            lqsutra = LQSutra.objects.get(sid=lqsutra_sid)
            filename = os.path.join(BASE_DIR, 'data/reel_info/%s.txt' % lqsutra_sid)
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if (not line) or line.startswith('#'):
                        continue
                    sid, name, reel_no, start_vol, start_vol_page, end_vol_page = line.split('\t')
                    tcode = sid[:2]
                    reel_no = int(reel_no)
                    try:
                        start_vol = int(start_vol)
                        start_vol_page = int(start_vol_page)
                        end_vol = start_vol
                        end_vol_page = int(end_vol_page)
                    except:
                        start_vol = 0
                        end_vol = 0
                        start_vol_page = 0
                        end_vol_page = 0
                    try:
                        sutra = Sutra.objects.get(sid=sid)
                    except:
                        tripitaka = Tripitaka.objects.get(code=sid[:2])
                        sutra = Sutra(sid=sid, tripitaka=tripitaka, code=sid[2:7], \
                        variant_code=sid[7], name=name, lqsutra=lqsutra, total_reels=60)
                        sutra.save()
                    try:
                        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
                    except:
                        reel = Reel(sutra=sutra, reel_no=reel_no, start_vol=start_vol, start_vol_page=start_vol_page,
                        end_vol=end_vol, end_vol_page=end_vol_page)
                        if tcode in tcode_lst1:
                            reel.path1 = str(reel.start_vol)
                        elif tcode in tcode_lst2:
                            reel.path1 = str(int(sutra.code))
                            reel.path2 = str(reel.reel_no)
                        if tcode == 'GL':
                            reel.correct_ready = True
                        reel_lst.append(reel)
        Reel.objects.bulk_create(reel_lst)
