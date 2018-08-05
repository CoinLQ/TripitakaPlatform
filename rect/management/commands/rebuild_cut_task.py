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
page_lst = (['YB', 25, 3],
            ['SX', 25, 42],
            ['SX', 18, 43],
            ['SX', 17, 43],
            ['SX', 8, 50],
            ['SX', 4, 51],
            ['SX', 7, 48],
            ['PL', 3, 1],
            ['QL', 7, 20],
            ['QL', 34, 22],
            ['SX', 46, 5],
            ['SX', 46, 19],
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
