from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tdata.lib.image_name_encipher import get_image_url

import os, sys
from os.path import isfile, join
import traceback
import requests
import re, json

tcode_lst = ['YB', 'QL', 'ZH', 'QS', 'GL', 'SX', 'ZC', 'PL', 'LC']

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('sutra_reel', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个

    def check_sutra(self, sutra):
        if sutra.sid[:2] not in tcode_lst:
            return
        for reel in sutra.reel_set.all():
            if reel.start_vol_page == 0 and reel.end_vol_page == 0:
                continue
            for vol_page in range(reel.start_vol_page, reel.end_vol_page + 1):
                url = get_image_url(reel, vol_page)
                r = requests.head(url)
                if r.status_code != 200:
                    print('%s_%03d: image not exists.' % (sutra.sid, reel.reel_no), url, r.status_code)
                cut_url = url.replace('jpg', 'cut')
                try:
                    r = requests.get(cut_url)
                    if r.status_code != 200:
                        print('%s_%03d: cut not exists.' % (sutra.sid, reel.reel_no), cut_url, r.status_code)
                    else:
                        try:
                            cut_json = json.loads(r.content)
                            if not cut_json.get('char_data', []):
                                print('%s_%03d: no char data.' % (sutra.sid, reel.reel_no), cut_url)
                        except:
                            print('%s_%03d: not json format.' % (sutra.sid, reel.reel_no), cut_url)
                except:
                    print('%s_%03d: check cut exception.' % (sutra.sid, reel.reel_no), cut_url, r.status_code)
                txt_url = url.replace('jpg', 'txt')
                txt_exists = False
                try:
                    r = requests.get(cut_url)
                    if r.status_code == 200:
                        txt_exists = True
                except:
                    pass
                if not txt_exists:
                    print('%s_%03d: txt not exists.' % (sutra.sid, reel.reel_no), txt_url, r.status_code)

    def handle(self, *args, **options):
        for sutra_reel in options['sutra_reel']:
            if sutra_reel.startswith('LQ'):
                lqsutra = LQSutra.objects.get(sid=sutra_reel)
                for sutra in lqsutra.sutra_set.all():
                    self.check_sutra(sutra)
            else:
                sutra = Sutra.objects.get(sid=sutra_reel)
                self.check_sutra(sutra)
