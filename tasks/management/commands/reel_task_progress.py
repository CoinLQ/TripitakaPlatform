from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from rect.models import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

def check_finished(tasks):
    finished = None
    if tasks:
        finished = False
        for task in tasks:
            if task.status == Task.STATUS_FINISHED:
                finished = True
    return finished

class Command(BaseCommand):
    def handle(self, *args, **options):
        progress_lst = []
        for reel in Reel.objects.all():
            for task_no in range(1, 5):
                tasks = list(Task.objects.filter(reel=reel, typ=Task.TYPE_CORRECT, task_no=task_no))
                key = 'correct_%d' % task_no
                finished = check_finished(tasks)
                setattr(reel, key, finished)
            tasks = list(Task.objects.filter(reel=reel, typ=Task.TYPE_CORRECT_VERIFY))
            reel.correct_verify = check_finished(tasks)
            tasks = list(Task.objects.filter(reel=reel, typ=Task.TYPE_CORRECT_DIFFICULT))
            reel.correct_difficult = check_finished(tasks)

            for task_no in range(1, 3):
                tasks = list(Task.objects.filter(reel=reel, typ=Task.TYPE_MARK, task_no=task_no))
                key = 'mark_%d' % task_no
                finished = check_finished(tasks)
                setattr(reel, key, finished)
            tasks = list(Task.objects.filter(reel=reel, typ=Task.TYPE_MARK_VERIFY))
            reel.mark_verify = check_finished(tasks)

            reel.finished_cut_count = PageVerifyTask.objects.filter(pagerect__reel=reel, status=TaskStatus.COMPLETED).count()
            reel.save()
            