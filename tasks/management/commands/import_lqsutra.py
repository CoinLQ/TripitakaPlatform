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
    def handle(self, *args, **options):
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
                lqsutra = LQSutra(sid=sid, code=sid[2:7], variant_code=sid[7], name=name,\
                total_reels=total_reels, author=author)
                lqsutra_lst.append(lqsutra)
        LQSutra.objects.bulk_create(lqsutra_lst)