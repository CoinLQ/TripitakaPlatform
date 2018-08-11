from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from django.conf import settings
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask


import os, sys
from os.path import isfile, join
import traceback

import re, json


tcode_lst = ['PL', 'SX',  'QL', 'ZH', 'YB', 'QS', 'ZC', 'GL', 'LC']

reel_lst = (['ZH', 22],
            ['QL', 35],
            ['SX', 30],
            ['QS', 40],
            ['QS', 42],
            )

reel_lst = ()
page_lst = (['PL', 26, 7],
            ['PL', 21, 4],
            ['QS', 60, 18],
            ['QS', 56, 1],
            ['ZH', 38, 14],
            ['QL', 56, 22],
            ['QL', 39, 3],
            ['SX', 47, 40],
            ['SX', 47, 39],
            ['SX', 47, 38],
            ['SX', 39, 28],
            ['SX', 39, 29],
            ['SX', 39, 30],
            ['SX', 39, 31],
            ['SX', 39, 32],
            ['SX', 39, 33],
            ['SX', 39, 34],
            ['SX', 39, 35],
            ['SX', 39, 36],
            ['SX', 39, 37],
            ['SX', 39, 38],
            ['SX', 39, 39],
            ['SX', 39, 40],
            ['SX', 34, 48],
            ['SX', 34, 47],
            ['SX', 34, 42],
            ['SX', 51, 41],
            ['SX', 35, 49],
            ['SX', 45, 36],
            ['SX', 48, 37],
            ['SX', 37, 40],
            )
# LQ003100

class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个 

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        sid = 'LQ003100'
        lqsutra = LQSutra.objects.get(sid=sid)
        for reel in reel_lst:
            tcode = reel[0]
            tripitaka = Tripitaka.objects.get(code=tcode) 
            sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka=tripitaka)
            reel = sutra.reel_set.filter(reel_no=reel[1]).first()
            rebuild_reel_pagerects_for_s3(reel)
                    
        for page in page_lst:
            tcode = page[0]
            tripitaka = Tripitaka.objects.get(code=tcode) 
            sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka=tripitaka)
            reel = sutra.reel_set.filter(reel_no=page[1]).first()
            _page = reel.page_set.filter(page_no=reel.start_vol_page + page[2] -1 ).first()
            rebuild_page_pagerects_for_s3(_page)
