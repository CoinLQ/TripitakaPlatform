from django.core.management.base import BaseCommand, CommandError
from jwt_auth.models import Staff
from tdata.models import *
from tasks.models import *
from tasks.common import *
from tasks.task_controller import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

CLEAN_PATTERN = re.compile('[「」『』◎　　 \r]')
CLEAN_PATTERN_PUNCT = re.compile('[、？「」◎　　 ，；。：！　]')
def read_reel_info(huayan_cb, reel_no, lines):
    start_vol = 0
    start_vol_page = 0
    end_vol = 0
    end_vol_page = 0
    for line in lines:
        line = line.strip()
        if not line.startswith('T'):
            continue
        pos = line.find('║')
        cbeta_code = line[:pos]
        line_text = line[pos+1:].strip()
        vol = int(cbeta_code[1:3])
        vol_page = int(cbeta_code[10:14])
        if not line_text or line_text.startswith('No'):
            continue
        if not start_vol:
            start_vol = vol
            start_vol_page = vol_page
        if vol > end_vol:
            end_vol = vol
        if vol == end_vol and vol_page > end_vol_page:
            end_vol_page = vol_page

    reel = Reel(sutra=huayan_cb, reel_no=reel_no, start_vol=start_vol,
    start_vol_page=start_vol_page, end_vol=end_vol, end_vol_page=end_vol_page,
    edition_type=Reel.EDITION_TYPE_BASE)
    reel.save()

def process_cbeta_text(huayan_cb, reel_no, lines1, lines2):
    reel = Reel.objects.get(sutra=huayan_cb, reel_no=reel_no)
    results = []
    for line in lines2[1:]:
        if line.find('----------') != -1:
            break
        if line.startswith('No.'):
            continue
        pos = line.find(']')
        if pos != -1:
            line = line[pos+1:]
        line = line.strip()
        line_text = CLEAN_PATTERN.sub('', line)
        if line_text:
            results.append(line_text + '\n')
    sutra_text = ''.join(results)
    punctuation, text = extract_punct(sutra_text)
    text = read_text_info(lines1)
    reelcorrecttext = ReelCorrectText(reel=reel)
    reelcorrecttext.set_text(text)
    reelcorrecttext.save()
    punct = Punct(reel=reel, reeltext=reelcorrecttext, punctuation=json.dumps(punctuation))
    punct.save()

#得到卷信息的同时也要得到文本信息
def read_text_info(lines):
    reeltext = []
    for line in lines:
        line = line.strip()
        if not line.startswith('T'):
            continue
        pos = line.find('║')
        line_text = line[pos+1:].strip()
        if not line_text or line_text.startswith('No') :
            continue
        line_text = line_text.strip()
        line_text = CLEAN_PATTERN_PUNCT.sub('', line_text)
        if line_text:
            reeltext.append( line_text )
    return '\n'.join(reeltext)

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        # get LQSutra
        try:
            lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        except:
            # create LQSutra
            lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
            lqsutra.save()

        # CBETA第1卷
        CB = Tripitaka.objects.get(code='CB')
        try:
            huayan_cb = Sutra.objects.get(sid='CB002780')
        except:
            huayan_cb = Sutra(sid='CB002780', tripitaka=CB, code='00278', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_cb.save()
        Reel.objects.filter(sutra=huayan_cb).delete()

        for reel_no in range(1, 61):
            filename = os.path.join(BASE_DIR, 'data/cbeta_huayan/reel_info/CBETA_60_%s.txt' % reel_no)
            with open(filename, 'r', encoding='utf-8') as f:
                lines1 = f.readlines()
            filename = os.path.join(BASE_DIR, 'data/cbeta_huayan/text/CB_278_%s.txt' % reel_no)
            text = ''
            with open(filename, 'r', encoding='utf-8') as f:
                lines2 = f.readlines()
            read_reel_info(huayan_cb, reel_no, lines1)
            process_cbeta_text(huayan_cb, reel_no, lines1, lines2)