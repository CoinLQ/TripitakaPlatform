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

    @transaction.atomic
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        schedule = Schedule(name='预处理计划任务1', status=ScheduleStatus.ACTIVE, schedule_no="pretask_schedule1")
        schedule.save()
        schedule.refresh_from_db()
        
        pretask_list = "%s/data/pretask_list.txt" % (BASE_DIR,)
        fo = open(pretask_list, "r")
        
        for line in fo.readlines():
            data = None                          
            line = line.strip()
            try:
                with urllib.request.urlopen(line) as f:
                    # print("read line content: %s" % (line))
                    print("ok")
                    data = f.read()
            except:
                print('no data: ', line)
                next

            if data:
                try:
                    cut_json = json.loads(data)
                except:
                    print('json data error: %s' % (line))
                    next
                page_dicts = {'image_url': cut_json["imgname"], 'bar_info': cut_json["char_data"]}
                page = PrePage.objects.create(**page_dicts)
                task_no = "%s_%05X" % (schedule.schedule_no, PrePageColTask.task_id())
                for r in page.bar_info:
                    r['op'] = 1
                task = PrePageColTask(number=task_no, schedule=schedule, page=page,
                        rect_set=page.bar_info, status=TaskStatus.NOT_GOT)
                task.save()