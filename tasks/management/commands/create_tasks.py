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

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('LQSutra_sid', nargs='+', type=str) #设置一个龙泉sid的参数，支持多个 

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        admin = get_or_create_admin()
        for sid in options['LQSutra_sid']:
            lqsutra = LQSutra.objects.get(sid=sid)
            reel_lst = [(lqsutra, reel_no) for reel_no in range(1, lqsutra.total_reels + 1) ]
            batchtask = BatchTask(priority=2, publisher=admin)
            batchtask.save()
            create_tasks_for_batchtask(batchtask, reel_lst, 3, 1, 2, 1, 2, 1, 2, 1)
            print('batchtask id: ', batchtask.id)
