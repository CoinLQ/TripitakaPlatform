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

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        reels = list(Reel.objects.all())
        lqreels = list(LQReel.objects.all())
        lqreel_set = set()
        for lqreel in lqreels:
            key = '%s_%03d' % (lqreel.lqsutra.sid, lqreel.reel_no)
            lqreel_set.add( key )
        lqreel_lst = []
        
        # 華嚴經60卷
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        for reel_no in range(1, 61):
            lqreel = LQReel(lqsutra=lqsutra, reel_no=reel_no)
            lqreel_lst.append(lqreel)

        # for reel in reels:
        #     if not reel.sutra.lqsutra:
        #         continue
        #     key = '%s_%03d' % (reel.sutra.lqsutra.sid, reel.reel_no)
        #     if key in lqreel_set:
        #         continue
        #     print('add: ', key)
        #     lqreel = LQReel(lqsutra=reel.sutra.lqsutra, reel_no=reel.reel_no)
        #     lqreel_lst.append(lqreel)
        LQReel.objects.bulk_create(lqreel_lst)