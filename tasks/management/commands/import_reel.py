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
        # get LQSutra
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        reel_lst = []
        filename = os.path.join(BASE_DIR, 'data/%s' % 'huayan_60_reel_info.txt')
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.rstrip()
                sutra_no, name, reel_no, start_vol, start_vol_page, end_vol_page, end_vol = line.split('\t')
                tcode = sutra_no[:2]
                sutra_code = int(sutra_no[2:])
                sid = '%s%05d0' % (tcode, sutra_code)
                reel_no = int(reel_no)
                try:
                    start_vol = int(start_vol)
                    start_vol_page = int(start_vol_page)
                    end_vol = int(end_vol)
                    end_vol_page = int(end_vol_page)
                except:
                    start_vol = 0
                    end_vol = 0
                    start_vol_page = 0
                    end_vol_page = 0
                sutra = Sutra.objects.get(sid=sid)
                reel = Reel(sutra=sutra, reel_no=reel_no, start_vol=start_vol, start_vol_page=start_vol_page,
                end_vol=end_vol, end_vol_page=end_vol_page)
                reel_lst.append(reel)
            Reel.objects.bulk_create(reel_lst)
