from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from django.conf import settings
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask

from .init import get_or_create_admin

import os, sys
from os.path import isfile, join
import traceback

import re, json


tcode_lst = ['PL', 'SX',  'QL', 'ZH', 'YB', 'QS', 'ZC', 'GL', 'LC']
tcode_lst = ['PL']
# LQ003100

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个 

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        
        for sid in options['LQSutra_sid']:
            lqsutra = LQSutra.objects.get(sid=sid)
            for tcode in tcode_lst:
                tripitaka = Tripitaka.objects.get(code=tcode) 
                sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka=tripitaka)
                for reel in sutra.reel_set.all():
                    # 如果卷下有页，残卷无页要略过
                    if reel.page_set.first():
                        # 如果有页但是没有切分方案，重建切分方案
                        rebuild_reel_pagerects_for_s3(reel)
                    
