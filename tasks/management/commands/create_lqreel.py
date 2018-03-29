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

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        # reels = list(Reel.objects.all())
        lqreels = list(LQReel.objects.all())
        lqreel_set = set()
        for lqreel in lqreels:
            key = '%s_%03d' % (lqreel.lqsutra.sid, lqreel.reel_no)
            lqreel_set.add( key )
        lqreel_lst = []
        
        for sid in options['LQSutra_sid']:
            #获得对象
            try:
                lqsutra = LQSutra.objects.get(sid=sid) # 需要命令行输入
            except:
                print('龙泉经目中未查到此编号：'+sid)
                continue
            if not lqsutra is None:
                total_reels=lqsutra.total_reels # 根据 sid从龙泉经目对象中获得
                for reel_no in range(1, total_reels+1):
                    try:
                        lqreel = LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
                    except:
                        lqreel = LQReel(lqsutra=lqsutra, reel_no=reel_no)
                        lqreel_lst.append(lqreel)       
        LQReel.objects.bulk_create(lqreel_lst)