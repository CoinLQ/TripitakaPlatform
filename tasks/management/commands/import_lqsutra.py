from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tdata.models import *
from tasks.models import *
from tasks.common import *

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str)#设置一个龙泉id的参数，支持多个

    def handle(self, *args, **options):
        sids = options['LQSutra_sid']
        BASE_DIR = settings.BASE_DIR
        lqsutra_lst = []
        filename = os.path.join(BASE_DIR, 'data/sutra_list/lqsutra.txt')
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if (not line) or line.startswith('#'):
                    continue
                sid, name, total_reels, author = line.split('\t')
                if sids and sid not in sids:
                    continue
                lqsutra = LQSutra(sid=sid, code=sid[2:7], variant_code=sid[7], name=name,\
                total_reels=total_reels, author=author)
                lqsutra_lst.append(lqsutra)
        LQSutra.objects.bulk_create(lqsutra_lst)