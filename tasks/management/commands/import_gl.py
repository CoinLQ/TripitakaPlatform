from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *
from tasks.utils.auto_punct import AutoPunct

import os, sys, requests, zipfile, io
from os.path import isfile, join
import traceback
import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        zip_file_url = 'https://s3.cn-north-1.amazonaws.com.cn/sutra-text/GL.zip'
        local_file = '%s/logs/GL.zip' % settings.BASE_DIR
        if os.path.exists(local_file):
            with open(local_file, 'rb') as f:
                data = f.read()
        else:
            r = requests.get(zip_file_url)
            data = r.content
            with open(local_file, 'wb') as fout:
                fout.write(data)
        with zipfile.ZipFile(io.BytesIO(data)) as myzip:
            for name in myzip.namelist():
                if not name.endswith('/'):
                    filename = name[3:-4]
                    sid, reel_no_str = filename.split('_')
                    reel_no = int(reel_no_str)
                    if reel_no > 3:
                       continue 
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

                    # 得到精确的切分数据
                    try:
                        compute_accurate_cut(reel)
                    except Exception:
                        traceback.print_exc()

                    punct = Punct.objects.filter(reeltext=reel_correct_text).first()
                    if punct is None:
                        task_puncts = AutoPunct.get_puncts_str(clean_separators(reel_correct_text.text))
                        punct = Punct(reel=reel, reeltext=reel_correct_text, punctuation=task_puncts)
                        punct.save()
