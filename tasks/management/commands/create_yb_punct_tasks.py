from django.core.management.base import BaseCommand, CommandError
from django.contrib import auth
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import create_punct_tasks

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        yb_reel001_content = clean_separators(open(settings.BASE_DIR+"/data/sutra_text/YB000860_001_fixed.txt").read())
        sutra = Sutra.objects.filter(sid='YB000860').first()
        reel, created =Reel.objects.get_or_create(sutra=sutra, reel_no=1)
        reeltext, created = ReelCorrectText.objects.get_or_create(reel=reel, text=yb_reel001_content)
        reeltext.task = Task.objects.first()
        reeltext.publisher = Staff.objects.first()
        reeltext.save()
        batchtask = BatchTask.objects.first()
        create_punct_tasks(batchtask, reel, 2, 1)