from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from rect.models import *
from tasks.common import *
from rect.lib.gen_task import GenTask
import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback
import time
import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        schedule = Schedule(name='计划任务1', status=ScheduleStatus.ACTIVE, schedule_no="schedule1", cc_threshold=1)
        schedule.save()
        schedule.refresh_from_db()
        
        cut_filename = "%s/logs/%s%s.%s" % (BASE_DIR, 'QL', '_24_22', 'cut')
        with open(cut_filename, 'r') as f:
            data = f.read()
            if data:
                cut_json = json.loads(data)
                dic = {'image_url':'yangmv','bar_info':'123456'}
                page = PrePage.objects.create(**dic)