'''
更新已生成的参考标点数据
'''
import json

from django.core.management.base import BaseCommand

from tasks.models import Punct
from tasks.utils.auto_punct import AutoPunct
from tasks.utils.punct_process import PunctProcess
from tasks.common import clean_separators

class Command(BaseCommand):
    '''
    更新已生成的参考标点数据, task=None
    '''
    def handle(self, *args, **options):
        print('update_ref_punct')
        puncts = list(Punct.objects.filter(task=None))
        for punct in puncts:
            if punct.reel.sutra.sid.startswith('CB'):
                continue
            print(punct.reel)
            reel_correct_text = punct.reeltext
            text = clean_separators(reel_correct_text.text)
            task_puncts = AutoPunct.get_puncts_str(text)
            punct.punctuation = task_puncts
            punctuation = json.loads(punct.punctuation)
            head = clean_separators(punct.reeltext.head)
            tail = clean_separators(punct.reeltext.tail)
            body_puncts = PunctProcess().body_punct(text, head, tail, punctuation)
            punct.body_punctuation = json.dumps(body_puncts, separators=(',', ':'))
            punct.save()
