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


tcode_lst1 = ['PL', 'SX', 'YB', 'QL', 'ZH', 'QS', 'ZC']
tcode_lst2 = ['GL', 'LC']

# LQ003100

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个 

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        
        for sid in options['LQSutra_sid']:
            lqsutra = LQSutra.objects.get(sid=sid)
            tripitaka = Tripitaka.objects.get(code='YB') 
            sutra = Sutra.objects.get(lqsutra=lqsutra, tripitaka=tripitaka)
            for reel in sutra.reel_set.all():
                rebuild_reel_pagerects_for_s3(reel)
                
