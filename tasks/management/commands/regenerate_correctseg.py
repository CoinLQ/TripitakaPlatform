from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import regenerate_correctseg

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--sid', nargs='?', type=str)
        parser.add_argument('--reel_no', nargs='?', type=int)
        parser.add_argument('--updated_pages', nargs='*', type=int, help='更新页在卷中的页序号')

    def handle(self, *args, **options):
        sid = options['sid']
        reel_no = options['reel_no']
        updated_pages = options['updated_pages']
        try:
            sutra = Sutra.objects.get(sid=sid)
            reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
            regenerate_correctseg(reel, updated_pages)
        except:
            traceback.print_exc()
        