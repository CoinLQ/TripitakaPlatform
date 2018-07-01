from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from rect.models import *
from pretask.serializers import *
from pretask.models import *
from tasks.common import *
from rect.lib.gen_task import GenTask
import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback
import time
import re, json

class Command(BaseCommand):
    def exclude_keys(self, x):
        for k in ['op', 'kselmarked', 'cc', 'wcc', 'red', 'char_id', 'char_no', 'ch']:
            x.pop(k, None)
        return x

    @transaction.atomic
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        schedule = Schedule(name='预处理计划任务1', status=ScheduleStatus.ACTIVE, schedule_no="pretask_schedule1")
        prepage_queryset = PrePageColTask.objects.all()
        prepageverify_queryset = PrePageColVerifyTask.objects.all()
        if prepage_queryset.filter(status=TaskStatus.COMPLETED).count() == prepage_queryset.count() and \
           prepageverify_queryset.filter(status=TaskStatus.COMPLETED).count() == prepageverify_queryset.count():
           print('all done!')
        
        output_pretask_list = "%s/data/output_pretask_list.txt" % (BASE_DIR,)
        fo = open(output_pretask_list, "w")
        for task in prepageverify_queryset.filter(status=TaskStatus.COMPLETED):
            page = task.page
            print(task.page.image_url)
            fo.write(task.page.image_url + '\r\n')
            #rects = list(map(lambda x: self.exclude_keys(x), task.rect_set))
            fo.write(json.dumps(task.page.bar_info) + '\r\n')
        fo.close()
