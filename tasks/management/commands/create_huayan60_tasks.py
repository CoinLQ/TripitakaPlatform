from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_tasks_for_batchtask

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        try:
            admin = Staff.objects.get(username='admin')
        except:
            admin = Staff(email='admin@example.com', username='admin')
            admin.set_password('admin')
            admin.is_admin = True
            admin.save()
        lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        reel_lst = [(lqsutra, reel_no) for reel_no in range(1, 61) ]
        BatchTask.objects.all().delete()
        batchtask = BatchTask(priority=2, publisher=admin)
        batchtask.save()
        create_tasks_for_batchtask(batchtask, reel_lst, 2, 1) # 2, 1, 2, 1)
        print('batchtask id: ', batchtask.id)
