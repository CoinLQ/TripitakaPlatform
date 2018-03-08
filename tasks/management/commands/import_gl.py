from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *

import os, sys, requests, zipfile, io
from os.path import isfile, join
import traceback
import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        zip_file_url = 'https://s3.cn-north-1.amazonaws.com.cn/sutra-text/GL.zip'
        r = requests.get(zip_file_url)
        with zipfile.ZipFile(io.BytesIO(r.content)) as myzip:
            for name in myzip.namelist():
                if not name.endswith('/'):
                    filename = name[3:-4]
                    sid, reel_no_str = filename.split('_')
                    reel_no = int(reel_no_str)
                    try:
                        sutra = Sutra.objects.get(sid=sid)
                        reel = Reel.objects.get(sutra=sutra, reel_no=reel_no)
                    except:
                        continue
                    try:
                        reel_correct_text = ReelCorrectText.get(reel=reel)
                    except:
                        with myzip.open(name) as f:
                            data = f.read()
                            text = data.decode('utf-8')
                            reel_correct_text = ReelCorrectText(reel=reel)
                            reel_correct_text.set_text(text)
                            reel_correct_text.save()
