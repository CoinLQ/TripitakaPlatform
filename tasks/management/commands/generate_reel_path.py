from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
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
        tcode_lst = []
        #tcode_lst = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC']
        for tcode in tcode_lst:
            tripitaka = Tripitaka.objects.get(code=tcode)
            for sutra in tripitaka.sutra_set.all():
                for reel in sutra.reel_set.all():
                    reel.path1 = str(reel.start_vol)
                    reel.save(update_fields=['path1'])

        tcode_lst = ['GL', 'LC']
        for tcode in tcode_lst:
            tripitaka = Tripitaka.objects.get(code=tcode)
            for sutra in tripitaka.sutra_set.all():
                for reel in sutra.reel_set.all():
                    try:
                        reel.path1 = str(int(sutra.code))
                        reel.path2 = str(reel.reel_no)
                        reel.save(update_fields=['path1', 'path2'])
                    except:
                        pass