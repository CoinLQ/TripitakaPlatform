from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from rect.models import *
from tasks.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback
import time
import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR

        huayan_yb = Sutra.objects.get(sid='YB000860')
        huayan_yb_1 = Reel.objects.get(sutra=huayan_yb, reel_no=1)
        Schedule.objects.all().delete()
        Schedule_Task_Statistical.objects.all().delete()
        schedule = Schedule(name='计划任务1',status=ScheduleStatus.ACTIVE,
        schedule_no="schedule1", cc_threshold=1)
        schedule.save()
        schedule.refresh_from_db()
        schedule.reels.add(huayan_yb_1)
        Schedule_Task_Statistical(schedule=schedule).save()
        time.sleep(2)
        CharClassifyPlan.create_charplan(schedule.pk.hex)
        Reel_Task_Statistical.gen_pptask_by_plan()
        Reel_Task_Statistical.gen_cctask_by_plan()
