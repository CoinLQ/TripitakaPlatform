from django.core.management.base import BaseCommand, CommandError
from tdata.models import *
from tasks.models import *
from tasks.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        reel_ids = []
        filename = os.path.join(BASE_DIR, 'data/ocr_ready_list.txt')
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                sid = line[0:8]
                reel_no = int(line[9:12])
                sutra = Sutra.objects.get(sid=sid)
                reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
                reel_ids.append(reel.id)
            Reel.objects.filter(id__in=reel_ids).update(ocr_ready=True)